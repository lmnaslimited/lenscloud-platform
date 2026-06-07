import json
import re
import secrets
from urllib.parse import urljoin, urlparse

import frappe
import requests
import yaml
from frappe import _
from frappe.utils import now_datetime

from lenscloud.api.kubernetes_client import KubernetesClient, KubernetesClientError, RESOURCE_PATHS, sanitize_error


SAFE_NAME_PATTERN = re.compile(r"[^a-z0-9-]+")
READY_DATABASE_STATES = {"Ready", "Healthy"}


def slugify(value):
	value = (value or "").strip().lower()
	value = SAFE_NAME_PATTERN.sub("-", value)
	return value.strip("-")


def as_bool(value):
	return str(value).lower() not in {"false", "0", "no", "none", ""}


def manifest_yaml(manifest):
	return yaml.safe_dump(manifest, sort_keys=False, default_flow_style=False)


def get_platform_settings():
	return frappe.get_single("Platform Settings")


def get_region_cluster(region):
	if not region:
		frappe.throw(_("Region is required for cluster placement."))
	cluster = frappe.db.get_value("Region", region, "cluster")
	if not cluster:
		frappe.throw(_("Region {0} is not linked to a Cluster runtime target.").format(region))
	return frappe.get_doc("Cluster", cluster)


def get_cluster_client(cluster):
	return KubernetesClient(cluster.kubeconfig_reference)


def default_storage_class(cluster=None):
	settings = get_platform_settings()
	return (cluster and cluster.default_storage_class) or settings.default_storage_class or "local-path"


def default_runtime_namespace(cluster=None):
	return (cluster and cluster.default_runtime_namespace) or "default"


def namespace_from_pattern(pattern, bench_name):
	bench_slug = slugify(bench_name)
	return (pattern or "bench-{bench}").format(bench=bench_slug, bench_name=bench_slug)


def get_free_plan():
	return frappe.db.get_value("Plan", {"is_default": 1, "status": "Active"}, "name") or frappe.db.get_value("Plan", {"is_free": 1, "status": "Active"}, "name")


def ensure_operator_fields(doc, cluster=None):
	cluster = cluster or get_region_cluster(doc.region)
	if doc.doctype in {"Bench", "Site", "Database Server"}:
		doc.cluster = cluster.name
	if doc.doctype == "Bench":
		doc.operator_resource_name = doc.operator_resource_name or slugify(doc.title or doc.name)
		doc.kubernetes_namespace = doc.kubernetes_namespace or namespace_from_pattern(cluster.default_bench_namespace_pattern, doc.operator_resource_name)
		doc.storage_class = doc.storage_class or default_storage_class(cluster)
		doc.cluster_derivation_note = f"Derived from Region {doc.region} -> Cluster {cluster.name}"
	elif doc.doctype == "Site":
		doc.operator_resource_name = doc.operator_resource_name or slugify(doc.subdomain or doc.title or doc.name)
		doc.admin_password_secret_reference = doc.admin_password_secret_reference or f"{doc.operator_resource_name}-admin-password"
		doc.access_url = f"https://{get_site_hostname(doc)}"
	elif doc.doctype == "Database Server":
		doc.operator_resource_name = doc.operator_resource_name or slugify(doc.title or doc.name)
		doc.kubernetes_namespace = doc.kubernetes_namespace or default_runtime_namespace(cluster)
		doc.storage_class = doc.storage_class or default_storage_class(cluster)
	return cluster


def get_release_image(bench):
	if not bench.current_release:
		frappe.throw(_("Bench {0} needs Current Release for manifest generation.").format(bench.name))
	release = frappe.get_doc("Release", bench.current_release)
	release_group = frappe.get_doc("Release Group", release.release_group)
	if bench.release_group and bench.release_group != release.release_group:
		frappe.throw(_("Current Release must belong to the Bench Release Group."))
	repository = "/".join(filter(None, [(release_group.registry_url or "").rstrip("/"), (release_group.image_repository or "").lstrip("/")]))
	if not repository:
		frappe.throw(_("Release Group {0} needs registry URL and image repository.").format(release_group.name))
	return release, release_group, repository



def frappe_major(value):
	match = re.search(r"(\d+)", str(value or "15"))
	return match.group(1) if match else "15"


def release_group_apps(release_group):
	return [{"name": row.app, "source": "image"} for row in release_group.get("included_apps") or [] if row.app]


def bench_boundary(bench):
	return (bench.privacy_boundary or bench.owner_customer or "").strip()


def database_boundary(database_server):
	return (database_server.privacy_boundary or database_server.owner_customer or "").strip()


def validate_database_server_placement_doc(bench, database_server, allow_pending=False):
	cluster = get_region_cluster(bench.region)
	if database_server.region != bench.region:
		frappe.throw(_("Bench Region must match Database Server Region."))
	if database_server.cluster != cluster.name:
		frappe.throw(_("Bench and Database Server must resolve to the same Cluster."))
	if bench.cluster and bench.cluster != database_server.cluster:
		frappe.throw(_("Bench Cluster must match Database Server Cluster."))
	if bench.privacy and bench.privacy != database_server.privacy:
		frappe.throw(_("Bench Privacy must match Database Server Privacy."))
	if not allow_pending and database_server.database_status not in READY_DATABASE_STATES and database_server.health_status not in READY_DATABASE_STATES:
		frappe.throw(_("Only ready Database Server capacity can be used for live apply."))
	filters = {"database_server": database_server.name}
	attached = frappe.get_all("Bench", filters=filters, fields=["name", "owner_customer", "privacy_boundary"])
	attached = [row for row in attached if row.name != bench.name]
	if database_server.privacy in {"Private", "Private Shared"}:
		boundary = bench_boundary(bench)
		expected = database_boundary(database_server)
		if not boundary or not expected or boundary != expected:
			frappe.throw(_("Bench owner/privacy boundary does not match the Database Server boundary."))
		for existing in attached:
			if (existing.privacy_boundary or existing.owner_customer or "").strip() != expected:
				frappe.throw(_("Private Shared Database Server cannot cross customer/privacy boundaries."))
	if database_server.privacy == "Private" and attached:
		frappe.throw(_("Private Database Server permits exactly one Bench."))
	maximum = int(database_server.maximum_bench_count or 0)
	if maximum and len(attached) + 1 > maximum:
		frappe.throw(_("Database Server capacity limit of {0} Benches is reached.").format(maximum))
	return True


@frappe.whitelist()
def validate_database_server_placement(bench, database_server, allow_pending=False):
	bench_doc = frappe.get_doc("Bench", bench)
	database_doc = frappe.get_doc("Database Server", database_server)
	validate_database_server_placement_doc(bench_doc, database_doc, allow_pending=as_bool(allow_pending))
	return {"valid": True, "privacy": database_doc.privacy, "database_server": database_doc.name}


@frappe.whitelist()
def attach_database_server_to_bench(bench, database_server):
	bench_doc = frappe.get_doc("Bench", bench)
	database_doc = frappe.get_doc("Database Server", database_server)
	validate_database_server_placement_doc(bench_doc, database_doc, allow_pending=True)
	bench_doc.database_server = database_doc.name
	bench_doc.save()
	update_database_server_count(database_doc.name)
	return {"bench": bench_doc.name, "database_server": database_doc.name, "attached": True}


def update_database_server_count(database_server):
	count = frappe.db.count("Bench", {"database_server": database_server})
	frappe.db.set_value("Database Server", database_server, "attached_bench_count", count, update_modified=False)
	return count


def build_database_server_manifest_data(database_server):
	if database_server.provisioning_type != "Operator Managed":
		frappe.throw(_("External Database Server records do not generate MariaDB CR manifests."))
	cluster = get_region_cluster(database_server.region)
	ensure_operator_fields(database_server, cluster)
	if not database_server.root_credential_secret_reference:
		frappe.throw(_("Root Secret Reference is required for an operator-managed Database Server."))
	spec = {
		"nodeSelector": {"lenscloud.io/node-role": "worker"},
		"rootPasswordSecretKeyRef": {"name": database_server.root_credential_secret_reference, "key": database_server.root_credential_secret_key or "password"},
		"image": database_server.image or "mariadb:10.11",
		"storage": {"size": database_server.storage_size or "8Gi", "storageClassName": database_server.storage_class or default_storage_class(cluster)},
		"resources": {"requests": {"cpu": "250m", "memory": "512Mi"}, "limits": {"cpu": "1", "memory": "1536Mi"}},
		"replicas": int(database_server.replica_count or 1),
		"port": int(database_server.service_port or 3306),
	}
	if database_server.node_placement_policy:
		try:
			placement = json.loads(database_server.node_placement_policy)
		except json.JSONDecodeError:
			frappe.throw(_("Node Placement Policy must be valid JSON."))
		if placement:
			spec.update(placement)
	return {"apiVersion": "k8s.mariadb.com/v1alpha1", "kind": "MariaDB", "metadata": {"name": database_server.operator_resource_name, "namespace": database_server.kubernetes_namespace, "labels": {"lenscloud.io/database-server": slugify(database_server.name), "lenscloud.io/privacy": slugify(database_server.privacy)}}, "spec": spec}


def build_frappebench_manifest_data(bench, allow_pending_database=False):
	cluster = get_region_cluster(bench.region)
	ensure_operator_fields(bench, cluster)
	if not bench.database_server:
		frappe.throw(_("Bench {0} needs a Database Server before manifest generation.").format(bench.name))
	database_server = frappe.get_doc("Database Server", bench.database_server)
	validate_database_server_placement_doc(bench, database_server, allow_pending=allow_pending_database)
	release, release_group, repository = get_release_image(bench)
	spec = {
		"frappeVersion": frappe_major(release_group.supported_frappe_major_version),
		"podConfig": {"nodeSelector": {"lenscloud.io/node-role": "worker"}},
		"imageConfig": {"repository": repository, "tag": release.image_tag, "pullPolicy": "IfNotPresent"},
		"apps": release_group_apps(release_group),
		"componentAutoscaling": {
			"gunicorn": {"enabled": False, "staticReplicas": 1},
			"scheduler": {"enabled": False, "staticReplicas": 0},
			"worker-default": {"enabled": False, "staticReplicas": 0},
			"worker-short": {"enabled": False, "staticReplicas": 0},
			"worker-long": {"enabled": False, "staticReplicas": 0},
		},
		"componentResources": {
			"nginx": {"requests": {"cpu": "25m", "memory": "64Mi"}},
			"gunicorn": {"requests": {"cpu": "50m", "memory": "128Mi"}},
			"socketio": {"requests": {"cpu": "25m", "memory": "64Mi"}},
			"scheduler": {"requests": {"cpu": "25m", "memory": "64Mi"}},
			"workerDefault": {"requests": {"cpu": "25m", "memory": "64Mi"}},
			"workerShort": {"requests": {"cpu": "25m", "memory": "64Mi"}},
			"workerLong": {"requests": {"cpu": "25m", "memory": "64Mi"}},
		},
		"storageSize": "3Gi",
		"storageClassName": bench.storage_class or default_storage_class(cluster),
		"dbConfig": {"provider": "mariadb", "mode": "shared", "mariadbRef": {"name": database_server.operator_resource_name, "namespace": database_server.kubernetes_namespace}},
	}
	return {"apiVersion": "vyogo.tech/v1", "kind": "FrappeBench", "metadata": {"name": bench.operator_resource_name, "namespace": bench.kubernetes_namespace or default_runtime_namespace(cluster)}, "spec": spec}


def get_site_hostname(site):
	domain = (site.domain or "").strip().lower().strip(".")
	subdomain = slugify(site.subdomain)
	if subdomain and domain:
		return domain if domain.startswith(f"{subdomain}.") else f"{subdomain}.{domain}"
	hostname = (site.title or site.name or "").strip().lower().strip(".")
	if "." in hostname:
		return hostname
	frappe.throw(_("Site requires a subdomain and root/approved domain."))


def build_frappesite_manifest_data(site):
	cluster = get_region_cluster(site.region)
	ensure_operator_fields(site, cluster)
	if not site.bench:
		frappe.throw(_("Site {0} needs Bench before manifest generation.").format(site.name))
	bench = frappe.get_doc("Bench", site.bench)
	if bench.region != site.region or bench.cluster != cluster.name:
		frappe.throw(_("Site and Bench placement must use the same Region and Cluster."))
	if not bench.operator_resource_name:
		ensure_operator_fields(bench, cluster)
	hostname = get_site_hostname(site)
	spec = {
		"benchRef": {"name": bench.operator_resource_name, "namespace": bench.kubernetes_namespace},
		"siteName": hostname,
		"domain": hostname,
		"adminPasswordSecretRef": {"name": site.admin_password_secret_reference or f"{site.operator_resource_name}-admin-password"},
		"encryptionKeySecretRef": {"name": f"{site.operator_resource_name}-encryption-key", "key": "encryption_key"},
		"ingressClassName": cluster.ingress_class or "traefik",
		"ingress": {
			"enabled": True,
			"className": cluster.ingress_class or "traefik",
			"annotations": {
				"traefik.ingress.kubernetes.io/router.entrypoints": "websecure",
				"traefik.ingress.kubernetes.io/router.tls": "true",
			},
		},
		"tls": {"enabled": False},
	}
	return {"apiVersion": "vyogo.tech/v1", "kind": "FrappeSite", "metadata": {"name": site.operator_resource_name, "namespace": bench.kubernetes_namespace or default_runtime_namespace(cluster)}, "spec": spec}


def create_action_log(action_type, status="Pending", database_server=None, bench=None, site=None, cluster=None, region=None, release=None, manifest=None, message=None, error=None, dry_run=True, resource_kind=None, operation=None):
	doc = frappe.get_doc({
		"doctype": "Orchestration Action Log", "title": action_type, "action_type": action_type, "status": status,
		"dry_run": "1" if dry_run else "0", "database_server": database_server, "bench": bench, "site": site,
		"cluster": cluster, "region": region, "release": release, "manifest": manifest, "message": message,
		"error": sanitize_error(error), "resource_kind": resource_kind, "operation": operation,
		"last_transition_time": now_datetime(),
	})
	doc.insert(ignore_permissions=True)
	return doc


def finish_action_log(log, status, message=None, error=None):
	log.status = status
	log.message = message or log.message
	log.error = sanitize_error(error)
	log.last_transition_time = now_datetime()
	log.save(ignore_permissions=True)
	return log


def phase_from_resource(resource):
	status = resource.get("status") or {}
	phase = status.get("phase") or status.get("state")
	if phase:
		return str(phase)
	for condition in reversed(status.get("conditions") or []):
		if condition.get("type") == "Ready":
			return "Ready" if condition.get("status") == "True" else condition.get("reason") or "Pending"
	return "Unknown"


def reconcile_manifest(cluster, manifest):
	with get_cluster_client(cluster) as client:
		return client.apply_custom_resource(manifest)


def ensure_site_admin_secret(cluster, site, namespace):
	name = site.admin_password_secret_reference or f"{site.operator_resource_name}-admin-password"
	with get_cluster_client(cluster) as client:
		try:
			client.get_secret(namespace, name)
		except KubernetesClientError as exc:
			if " 404:" not in str(exc):
				raise
			client.create_secret(namespace, name, {"password": secrets.token_urlsafe(30)})
		encryption_name = f"{site.operator_resource_name}-encryption-key"
		try:
			client.get_secret(namespace, encryption_name)
		except KubernetesClientError as exc:
			if " 404:" not in str(exc):
				raise
			client.create_secret(namespace, encryption_name, {"encryption_key": secrets.token_urlsafe(36)})
	return name


def ensure_database_root_secret(cluster, database_server):
	name = database_server.root_credential_secret_reference
	key = database_server.root_credential_secret_key or "password"
	with get_cluster_client(cluster) as client:
		try:
			client.get_secret(database_server.kubernetes_namespace, name)
		except KubernetesClientError as exc:
			if " 404:" not in str(exc):
				raise
			client.create_secret(database_server.kubernetes_namespace, name, {key: secrets.token_urlsafe(36)})
	return name


@frappe.whitelist()
def dry_run_database_server_manifest(database_server):
	doc = frappe.get_doc("Database Server", database_server)
	cluster = get_region_cluster(doc.region)
	manifest = build_database_server_manifest_data(doc)
	text = manifest_yaml(manifest)
	log = create_action_log("Database Server Dry Run", "Dry Run", database_server=doc.name, cluster=cluster.name, region=doc.region, manifest=text, message="Generated secret-safe MariaDB manifest dry-run.", resource_kind="MariaDB", operation="dry-run")
	return {"manifest": text, "cluster": cluster.name, "action_log": log.name, "dry_run": True}


@frappe.whitelist()
def reconcile_database_server(database_server, dry_run=True):
	doc = frappe.get_doc("Database Server", database_server)
	cluster = get_region_cluster(doc.region)
	manifest = build_database_server_manifest_data(doc)
	text = manifest_yaml(manifest)
	dry_run = as_bool(dry_run)
	log = create_action_log("Database Server Reconcile", "Pending", database_server=doc.name, cluster=cluster.name, region=doc.region, manifest=text, dry_run=dry_run, resource_kind="MariaDB", operation="apply")
	try:
		if dry_run or not get_platform_settings().kubernetes_apply_enabled:
			doc.provisioning_status = "Pending"; doc.database_status = "Pending"; doc.save()
			finish_action_log(log, "Dry Run", "Kubernetes apply is disabled; MariaDB manifest generated.")
			return {"status": "dry_run", "manifest": text, "cluster": cluster.name, "action_log": log.name}
		ensure_database_root_secret(cluster, doc)
		resource = reconcile_manifest(cluster, manifest)
		doc.provisioning_status = "Accepted"; doc.database_status = phase_from_resource(resource); doc.last_error = None; doc.save()
		finish_action_log(log, "Succeeded", "MariaDB resource accepted by Kubernetes API.")
		return {"status": "accepted", "phase": doc.database_status, "cluster": cluster.name, "action_log": log.name}
	except Exception as exc:
		doc.provisioning_status = "Failed"; doc.database_status = "Failed"; doc.last_error = sanitize_error(exc); doc.save(ignore_permissions=True)
		finish_action_log(log, "Failed", error=exc)
		raise


@frappe.whitelist()
def dry_run_bench_manifest(bench):
	doc = frappe.get_doc("Bench", bench)
	cluster = get_region_cluster(doc.region)
	manifest = build_frappebench_manifest_data(doc, allow_pending_database=True)
	text = manifest_yaml(manifest)
	log = create_action_log("Bench Dry Run", "Dry Run", bench=doc.name, database_server=doc.database_server, cluster=cluster.name, region=doc.region, release=doc.current_release, manifest=text, message="Generated FrappeBench manifest dry-run.", resource_kind="FrappeBench", operation="dry-run")
	return {"manifest": text, "cluster": cluster.name, "action_log": log.name, "dry_run": True}


@frappe.whitelist()
def reconcile_bench(bench, dry_run=True):
	doc = frappe.get_doc("Bench", bench); cluster = get_region_cluster(doc.region); dry_run = as_bool(dry_run)
	manifest = build_frappebench_manifest_data(doc, allow_pending_database=dry_run or not get_platform_settings().kubernetes_apply_enabled)
	text = manifest_yaml(manifest)
	log = create_action_log("Bench Reconcile", "Pending", bench=doc.name, database_server=doc.database_server, cluster=cluster.name, region=doc.region, release=doc.current_release, manifest=text, dry_run=dry_run, resource_kind="FrappeBench", operation="apply")
	try:
		if dry_run or not get_platform_settings().kubernetes_apply_enabled:
			doc.bench_status = "Pending"; doc.save(); finish_action_log(log, "Dry Run", "Kubernetes apply is disabled; FrappeBench manifest generated.")
			return {"status": "dry_run", "manifest": text, "cluster": cluster.name, "action_log": log.name}
		resource = reconcile_manifest(cluster, manifest)
		doc.bench_status = phase_from_resource(resource); doc.save(); finish_action_log(log, "Succeeded", "FrappeBench accepted by Kubernetes API.")
		return {"status": "accepted", "phase": doc.bench_status, "cluster": cluster.name, "action_log": log.name}
	except Exception as exc:
		doc.bench_status = "Failed"; doc.save(ignore_permissions=True); finish_action_log(log, "Failed", error=exc); raise


@frappe.whitelist()
def dry_run_site_manifest(site):
	doc = frappe.get_doc("Site", site); cluster = get_region_cluster(doc.region)
	manifest = build_frappesite_manifest_data(doc); text = manifest_yaml(manifest)
	log = create_action_log("Site Dry Run", "Dry Run", site=doc.name, bench=doc.bench, cluster=cluster.name, region=doc.region, manifest=text, message="Generated FrappeSite manifest dry-run.", resource_kind="FrappeSite", operation="dry-run")
	return {"manifest": text, "cluster": cluster.name, "action_log": log.name, "dry_run": True}


@frappe.whitelist()
def reconcile_site(site, dry_run=True):
	doc = frappe.get_doc("Site", site); cluster = get_region_cluster(doc.region); dry_run = as_bool(dry_run)
	manifest = build_frappesite_manifest_data(doc); text = manifest_yaml(manifest)
	log = create_action_log("Site Reconcile", "Pending", site=doc.name, bench=doc.bench, cluster=cluster.name, region=doc.region, manifest=text, dry_run=dry_run, resource_kind="FrappeSite", operation="apply")
	try:
		if dry_run or not get_platform_settings().kubernetes_apply_enabled:
			doc.provisioning_status = "Pending"; doc.site_status = "Requested"; doc.route_status = "Pending"; doc.save(ignore_permissions=True)
			finish_action_log(log, "Dry Run", "Kubernetes apply is disabled; FrappeSite manifest generated.")
			return {"status": "dry_run", "manifest": text, "cluster": cluster.name, "action_log": log.name}
		namespace = manifest["metadata"]["namespace"]
		ensure_site_admin_secret(cluster, doc, namespace)
		resource = reconcile_manifest(cluster, manifest)
		doc.provisioning_status = "Accepted"; doc.site_status = phase_from_resource(resource); doc.route_status = "Pending"; doc.save(ignore_permissions=True)
		finish_action_log(log, "Succeeded", "FrappeSite accepted by Kubernetes API.")
		return {"status": "accepted", "phase": doc.site_status, "cluster": cluster.name, "action_log": log.name}
	except Exception as exc:
		doc.provisioning_status = "Failed"; doc.site_status = "Failed"; doc.route_status = "Failed"; doc.route_error = sanitize_error(exc); doc.save(ignore_permissions=True)
		finish_action_log(log, "Failed", error=exc); raise


def sync_custom_resource(cluster, kind, namespace, name):
	with get_cluster_client(cluster) as client:
		return client.get_custom_resource(kind, namespace, name)


@frappe.whitelist()
def sync_database_server_status(database_server):
	doc = frappe.get_doc("Database Server", database_server); cluster = get_region_cluster(doc.region)
	log = create_action_log("Database Server Status Sync", database_server=doc.name, cluster=cluster.name, region=doc.region, dry_run=False, resource_kind="MariaDB", operation="status-sync")
	try:
		resource = sync_custom_resource(cluster, "MariaDB", doc.kubernetes_namespace, doc.operator_resource_name)
		phase = phase_from_resource(resource); doc.database_status = "Ready" if phase.lower() == "ready" else phase; doc.health_status = "Healthy" if doc.database_status == "Ready" else "Unknown"; doc.provisioning_status = "Ready" if doc.database_status == "Ready" else "Running"; doc.last_sync_time = now_datetime(); doc.last_error = None; doc.save()
		finish_action_log(log, "Succeeded", f"MariaDB runtime phase: {phase}.")
		return {"status": doc.database_status, "health": doc.health_status, "action_log": log.name}
	except Exception as exc:
		doc.health_status = "Failed"; doc.last_sync_time = now_datetime(); doc.last_error = sanitize_error(exc); doc.save(ignore_permissions=True); finish_action_log(log, "Failed", error=exc); raise


@frappe.whitelist()
def sync_bench_status(bench):
	doc = frappe.get_doc("Bench", bench); cluster = get_region_cluster(doc.region)
	log = create_action_log("Bench Status Sync", bench=doc.name, database_server=doc.database_server, cluster=cluster.name, region=doc.region, dry_run=False, resource_kind="FrappeBench", operation="status-sync")
	try:
		resource = sync_custom_resource(cluster, "FrappeBench", doc.kubernetes_namespace, doc.operator_resource_name); doc.bench_status = phase_from_resource(resource); doc.save(); finish_action_log(log, "Succeeded", f"FrappeBench runtime phase: {doc.bench_status}.")
		return {"status": doc.bench_status, "action_log": log.name}
	except Exception as exc:
		doc.bench_status = "Failed"; doc.save(ignore_permissions=True); finish_action_log(log, "Failed", error=exc); raise


def get_route_response(url, timeout):
	for attempt in range(3):
		try:
			return requests.get(url, timeout=timeout, allow_redirects=True)
		except requests.RequestException:
			if attempt == 2:
				raise


def check_site_route(doc, timeout=15):
	url = doc.access_url or f"https://{get_site_hostname(doc)}"
	response = get_route_response(url, timeout)
	if not 200 <= response.status_code < 300:
		raise RuntimeError(f"Route returned HTTP {response.status_code}.")
	asset_match = re.search(r"(?:href|src)=[\"\x27]([^\"\x27]*/assets/[^\"\x27]+\.(?:css|js)(?:\?[^\"\x27]*)?)[\"\x27]", response.text or "", re.IGNORECASE)
	if not asset_match:
		raise RuntimeError("Route returned no generated static asset reference.")
	asset_url = urljoin(response.url or url, asset_match.group(1))
	asset_response = get_route_response(asset_url, timeout)
	if not 200 <= asset_response.status_code < 300:
		raise RuntimeError(f"Static asset returned HTTP {asset_response.status_code}.")
	return {"url": response.url or url, "status_code": response.status_code, "asset_url": asset_response.url or asset_url, "asset_status_code": asset_response.status_code}


@frappe.whitelist()
def sync_site_status(site, check_route=True):
	doc = frappe.get_doc("Site", site); cluster = get_region_cluster(doc.region); bench = frappe.get_doc("Bench", doc.bench)
	log = create_action_log("Site Status Sync", site=doc.name, bench=doc.bench, cluster=cluster.name, region=doc.region, dry_run=False, resource_kind="FrappeSite", operation="status-sync")
	try:
		resource = sync_custom_resource(cluster, "FrappeSite", bench.kubernetes_namespace, doc.operator_resource_name)
		phase = phase_from_resource(resource); status = resource.get("status") or {}
		doc.site_status = phase; doc.provisioning_status = "Ready" if phase.lower() == "ready" else "Running"
		doc.access_url = f"https://{get_site_hostname(doc)}"; doc.hostname_reservation_status = "Reserved"
		if as_bool(check_route) and phase.lower() == "ready":
			result = check_site_route(doc); doc.route_status = "Ready"; doc.tls_status = "Ready"; doc.last_route_check = now_datetime(); doc.route_error = None
		else:
			result = None; doc.route_status = "Pending"
		doc.save(); finish_action_log(log, "Succeeded", f"FrappeSite runtime phase: {phase}; route: {doc.route_status}.")
		return {"status": doc.site_status, "provisioning_status": doc.provisioning_status, "route_status": doc.route_status, "access_url": doc.access_url, "route": result, "action_log": log.name}
	except Exception as exc:
		doc.last_route_check = now_datetime(); doc.route_status = "Failed"; doc.route_error = sanitize_error(exc); doc.save(ignore_permissions=True); finish_action_log(log, "Failed", error=exc); raise


@frappe.whitelist()
def check_cluster_permissions(cluster):
	doc = frappe.get_doc("Cluster", cluster)
	checks = []
	with get_cluster_client(doc) as client:
		for kind, (group, _version, plural) in RESOURCE_PATHS.items():
			for verb in ("get", "patch"):
				allowed, reason = client.can_i(verb, group, plural, doc.default_runtime_namespace or "default")
				checks.append({"kind": kind, "verb": verb, "allowed": allowed, "reason": reason})
		for verb in ("get", "create"):
			allowed, reason = client.can_i(verb, "", "secrets", doc.default_runtime_namespace or "default")
			checks.append({"kind": "Secret", "verb": verb, "allowed": allowed, "reason": reason})
	return {"cluster": doc.name, "checks": checks, "all_required_allowed": all(item["allowed"] for item in checks)}


@frappe.whitelist()
def get_customer_portal_context():
	settings = get_platform_settings()
	user = frappe.session.user
	if user == "Guest":
		frappe.throw(_("Authentication is required."), frappe.PermissionError)
	customer_name = frappe.db.get_value("Customer", {"user": user}, "name")
	customer = frappe.db.get_value("Customer", customer_name, ["name", "first_name", "last_name", "region"], as_dict=True) if customer_name else None
	regions = frappe.get_all("Region", filters={"deployment_status": "Active", "cluster": ["!=", ""]}, fields=["name", "title", "cluster"], order_by="lft asc")
	plans = frappe.get_all("Plan", filters={"status": "Active"}, fields=["name", "title", "plan_code", "is_default", "is_free", "monthly_price", "site_limit", "bench_policy", "description"])
	return {
		"customer": customer,
		"regions": regions,
		"plans": plans,
		"settings": {
			"root_domain": settings.root_domain,
			"billing_system": settings.billing_system,
			"crm_system": settings.crm_system,
			"support_system": settings.support_system,
		},
	}


def eligible_customer_bench(region, customer):
	for row in frappe.get_all("Bench", filters={"region": region, "bench_status": "Ready"}, fields=["name"], order_by="modified desc"):
		bench = frappe.get_doc("Bench", row.name)
		if not bench.database_server:
			continue
		database_server = frappe.get_doc("Database Server", bench.database_server)
		if database_server.privacy != "Public":
			continue
		try:
			validate_database_server_placement_doc(bench, database_server, allow_pending=False)
			return bench
		except frappe.ValidationError:
			continue
	frappe.throw(_("No ready Public Bench capacity is available in Region {0}.").format(region))


@frappe.whitelist()
def request_customer_site(site_name, company_name=None, subdomain=None, region=None, plan=None, notes=None):
	settings = get_platform_settings()
	if not settings.root_domain or settings.domain_strategy != "Wildcard":
		frappe.throw(_("Platform wildcard root domain must be configured before customer Site creation."))
	if not region:
		frappe.throw(_("Region is required."))
	cluster = get_region_cluster(region); plan = plan or get_free_plan()
	if not plan:
		frappe.throw(_("A default or Free Plan is required."))
	user = frappe.session.user; customer = frappe.db.get_value("Customer", {"user": user}, "name")
	if not customer:
		customer_doc = frappe.get_doc({"doctype": "Customer", "first_name": frappe.db.get_value("User", user, "first_name") or user, "user": user, "region": region}); customer_doc.insert(ignore_permissions=True); customer = customer_doc.name
	plan_doc = frappe.get_doc("Plan", plan); limit = int(plan_doc.site_limit or 0)
	if limit and frappe.db.count("Site", {"customer": customer, "plan": plan, "site_status": ["!=", "Deleted"]}) >= limit:
		frappe.throw(_("The {0} Plan Site limit has been reached.").format(plan_doc.title))
	subdomain = slugify(subdomain or site_name or company_name)
	if not subdomain:
		frappe.throw(_("Subdomain could not be derived."))
	domain = settings.root_domain.strip().lower().strip("."); title = f"{subdomain}.{domain}"
	if frappe.db.exists("Site", {"title": title}):
		frappe.throw(_("Hostname {0} is already reserved.").format(title))
	bench = eligible_customer_bench(region, customer)
	site_doc = frappe.get_doc({"doctype": "Site", "customer": customer, "bench": bench.name, "region": region, "cluster": cluster.name, "plan": plan, "subdomain": subdomain, "domain": domain, "site_status": "Requested", "provisioning_status": "Pending", "hostname_reservation_status": "Reserved", "route_status": "Pending", "tls_status": "Inherited", "operator_resource_name": subdomain, "access_url": f"https://{title}"})
	site_doc.insert(ignore_permissions=True)
	request_log = create_action_log("Site Request", "Succeeded", site=site_doc.name, dry_run=False, bench=bench.name, cluster=cluster.name, region=region, message=notes or "Customer Free Plan Site request captured and hostname reserved.", resource_kind="Site", operation="request")
	reconcile = reconcile_site(site_doc.name, dry_run=not bool(settings.kubernetes_apply_enabled))
	return {"site": site_doc.name, "domain": domain, "hostname": title, "access_url": site_doc.access_url, "cluster": cluster.name, "bench": bench.name, "plan": plan, "action_log": request_log.name, "reconcile": reconcile}


@frappe.whitelist()
def queue_or_apply_dns_record(site):
	frappe.throw(_("Standard wildcard Sites do not create DNS Records. Use Site reconcile and route status sync."))
