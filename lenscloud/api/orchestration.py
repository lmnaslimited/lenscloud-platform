import hashlib
import json
import re
import secrets
from urllib.parse import quote, urljoin, urlparse

import frappe
import requests
import yaml
from frappe import _
from frappe.utils import now_datetime

from lenscloud.api.kubernetes_client import KubernetesClient, KubernetesClientError, RESOURCE_PATHS, kubeconfig_path, sanitize_error


SAFE_NAME_PATTERN = re.compile(r"[^a-z0-9-]+")
READY_DATABASE_STATES = {"Ready", "Healthy"}
PLATFORM_MANAGER_LABEL = "lenscloud.io/managed-by"
RESOURCE_KIND_LABEL = "lenscloud.io/resource-kind"
RESOURCE_ID_LABEL = "lenscloud.io/resource-id"
CUSTOMER_LABEL = "lenscloud.io/customer"
PLATFORM_MANAGER_VALUE = "platform"
RUNTIME_NAMESPACE_RESOURCE_KINDS = {"MariaDB", "FrappeBench", "FrappeSite"}
DELETE_STATES = {"Deletion Requested", "Quiescing", "Deleting", "Deleted", "Deletion Failed"}
PROTECTED_RUNTIME_RESOURCES = {("MariaDB", "default", "frappe-mariadb")}
RELATED_RUNTIME_RESOURCES = (
	("pods", "Pod", "", "v1"),
	("jobs", "Job", "batch", "v1"),
	("persistentvolumeclaims", "PersistentVolumeClaim", "", "v1"),
	("services", "Service", "", "v1"),
	("ingresses", "Ingress", "networking.k8s.io", "v1"),
)


def slugify(value):
	value = (value or "").strip().lower()
	value = SAFE_NAME_PATTERN.sub("-", value)
	return value.strip("-")


def as_bool(value):
	return str(value).lower() not in {"false", "0", "no", "none", ""}


def label_value(value):
	value = slugify(value)
	if len(value) <= 63:
		return value
	digest = hashlib.sha256(value.encode()).hexdigest()[:12]
	return f"{value[:50].rstrip('-')}-{digest}"


def resource_id_label(doc):
	return label_value(doc.name)


def owner_customer_value(doc):
	return getattr(doc, "owner_customer", None) or getattr(doc, "customer", None) or None


def platform_owner_labels(resource_kind, doc):
	labels = {
		PLATFORM_MANAGER_LABEL: PLATFORM_MANAGER_VALUE,
		RESOURCE_KIND_LABEL: label_value(resource_kind),
		RESOURCE_ID_LABEL: resource_id_label(doc),
	}
	customer = owner_customer_value(doc)
	if customer:
		labels[CUSTOMER_LABEL] = label_value(customer)
	return labels


def merge_metadata_labels(manifest, labels):
	metadata = manifest.setdefault("metadata", {})
	metadata["labels"] = {**(metadata.get("labels") or {}), **labels}
	return manifest


def runtime_label_selector(doc):
	return ",".join([
		f"{PLATFORM_MANAGER_LABEL}={PLATFORM_MANAGER_VALUE}",
		f"{RESOURCE_ID_LABEL}={resource_id_label(doc)}",
	])


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
	manifest = {"apiVersion": "k8s.mariadb.com/v1alpha1", "kind": "MariaDB", "metadata": {"name": database_server.operator_resource_name, "namespace": database_server.kubernetes_namespace, "labels": {"lenscloud.io/database-server": slugify(database_server.name), "lenscloud.io/privacy": slugify(database_server.privacy)}}, "spec": spec}
	return merge_metadata_labels(manifest, platform_owner_labels("database-server", database_server))


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
	manifest = {"apiVersion": "vyogo.tech/v1", "kind": "FrappeBench", "metadata": {"name": bench.operator_resource_name, "namespace": bench.kubernetes_namespace or default_runtime_namespace(cluster)}, "spec": spec}
	return merge_metadata_labels(manifest, platform_owner_labels("bench", bench))


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
	manifest = {"apiVersion": "vyogo.tech/v1", "kind": "FrappeSite", "metadata": {"name": site.operator_resource_name, "namespace": bench.kubernetes_namespace or default_runtime_namespace(cluster)}, "spec": spec}
	return merge_metadata_labels(manifest, platform_owner_labels("site", site))


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


def fail_action(log, exc, next_action):
	finish_action_log(log, "Failed", error=exc)
	frappe.db.commit()
	safe_error = sanitize_error(exc)
	frappe.throw(_("{0} Action log: {1}. Next action: {2}").format(safe_error, log.name, next_action))


def dry_run_result(log, manifest, cluster, resource_label, requested_dry_run, apply_enabled):
	if requested_dry_run:
		message = f"Dry run was selected. {resource_label} manifest generated; no Kubernetes resource was created."
		next_actions = ["Switch Dry run off.", "Run Reconcile again and require status accepted before status sync."]
	else:
		message = f"Kubernetes apply is disabled. {resource_label} manifest generated; no Kubernetes resource was created."
		next_actions = ["Enable Kubernetes apply for the controlled test window.", "Run Reconcile again with Dry run off and require status accepted."]
	finish_action_log(log, "Dry Run", message)
	return {
		"status": "dry_run",
		"dry_run": True,
		"manifest": manifest,
		"cluster": cluster.name,
		"action_log": log.name,
		"message": message,
		"next_actions": next_actions,
		"apply_enabled": bool(apply_enabled),
	}


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
			client.create_secret(namespace, name, {"password": secrets.token_urlsafe(30)}, labels=platform_owner_labels("site", site))
		encryption_name = f"{site.operator_resource_name}-encryption-key"
		try:
			client.get_secret(namespace, encryption_name)
		except KubernetesClientError as exc:
			if " 404:" not in str(exc):
				raise
			client.create_secret(namespace, encryption_name, {"encryption_key": secrets.token_urlsafe(36)}, labels=platform_owner_labels("site", site))
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
			client.create_secret(database_server.kubernetes_namespace, name, {key: secrets.token_urlsafe(36)}, labels=platform_owner_labels("database-server", database_server))
	return name


def attach_manifest_to_log(log, manifest):
	log.manifest = manifest
	log.save(ignore_permissions=True)


@frappe.whitelist()
def dry_run_database_server_manifest(database_server):
	doc = frappe.get_doc("Database Server", database_server)
	cluster = get_region_cluster(doc.region)
	log = create_action_log("Database Server Dry Run", "Pending", database_server=doc.name, cluster=cluster.name, region=doc.region, message="Generating secret-safe MariaDB manifest.", resource_kind="MariaDB", operation="dry-run")
	try:
		text = manifest_yaml(build_database_server_manifest_data(doc))
		attach_manifest_to_log(log, text)
		message = "Generated secret-safe MariaDB manifest dry-run; no Kubernetes resource was created."
		finish_action_log(log, "Dry Run", message)
		return {"manifest": text, "cluster": cluster.name, "action_log": log.name, "dry_run": True, "status": "dry_run", "message": message, "next_actions": ["Review ownership labels, namespace, storage, and Secret reference names.", "To create it, use Reconcile Database Server with Dry run off while apply is enabled."]}
	except Exception as exc:
		fail_action(log, exc, "Correct the Database Server fields named in the error, then retry Preview MariaDB manifest.")


@frappe.whitelist()
def reconcile_database_server(database_server, dry_run=True):
	doc = frappe.get_doc("Database Server", database_server)
	cluster = get_region_cluster(doc.region)
	dry_run = as_bool(dry_run)
	log = create_action_log("Database Server Reconcile", "Pending", database_server=doc.name, cluster=cluster.name, region=doc.region, dry_run=dry_run, message="Preparing MariaDB reconciliation.", resource_kind="MariaDB", operation="apply")
	try:
		text = manifest_yaml(build_database_server_manifest_data(doc))
		attach_manifest_to_log(log, text)
		apply_enabled = bool(get_platform_settings().kubernetes_apply_enabled)
		if dry_run or not apply_enabled:
			doc.provisioning_status = "Pending"; doc.database_status = "Pending"; doc.save()
			return dry_run_result(log, text, cluster, "MariaDB", dry_run, apply_enabled)
		require_cluster_apply_ready(cluster)
		ensure_database_root_secret(cluster, doc)
		resource = reconcile_manifest(cluster, yaml.safe_load(text))
		doc.provisioning_status = "Accepted"; doc.database_status = phase_from_resource(resource); doc.last_error = None; doc.save()
		message = "MariaDB resource accepted by Kubernetes API."
		finish_action_log(log, "Succeeded", message)
		return {"status": "accepted", "phase": doc.database_status, "cluster": cluster.name, "action_log": log.name, "message": message, "next_actions": ["Run Sync runtime status until Ready/Healthy.", "Run Inspect runtime to review conditions, finalizers, workloads, Services, PVCs, and warning Events."]}
	except Exception as exc:
		doc.provisioning_status = "Failed"; doc.database_status = "Failed"; doc.last_error = sanitize_error(exc); doc.save(ignore_permissions=True)
		fail_action(log, exc, "Open this action log, correct the reported cluster/manifest issue, then retry Reconcile Database Server.")


@frappe.whitelist()
def dry_run_bench_manifest(bench):
	doc = frappe.get_doc("Bench", bench)
	cluster = get_region_cluster(doc.region)
	log = create_action_log("Bench Dry Run", "Pending", bench=doc.name, database_server=doc.database_server, cluster=cluster.name, region=doc.region, release=doc.current_release, message="Generating secret-safe FrappeBench manifest.", resource_kind="FrappeBench", operation="dry-run")
	try:
		text = manifest_yaml(build_frappebench_manifest_data(doc, allow_pending_database=True))
		attach_manifest_to_log(log, text)
		message = "Generated secret-safe FrappeBench manifest dry-run; no Kubernetes resource was created."
		finish_action_log(log, "Dry Run", message)
		return {"manifest": text, "cluster": cluster.name, "action_log": log.name, "dry_run": True, "status": "dry_run", "message": message, "next_actions": ["Review release image, ownership labels, namespace, and Database Server reference.", "To create it, use Reconcile Bench with Dry run off while apply is enabled."]}
	except Exception as exc:
		fail_action(log, exc, "Correct the Bench placement, Database Server, privacy, or Release field named in the error, then retry the dry run.")


@frappe.whitelist()
def reconcile_bench(bench, dry_run=True):
	doc = frappe.get_doc("Bench", bench)
	cluster = get_region_cluster(doc.region)
	dry_run = as_bool(dry_run)
	log = create_action_log("Bench Reconcile", "Pending", bench=doc.name, database_server=doc.database_server, cluster=cluster.name, region=doc.region, release=doc.current_release, dry_run=dry_run, message="Preparing FrappeBench reconciliation.", resource_kind="FrappeBench", operation="apply")
	try:
		apply_enabled = bool(get_platform_settings().kubernetes_apply_enabled)
		text = manifest_yaml(build_frappebench_manifest_data(doc, allow_pending_database=dry_run or not apply_enabled))
		attach_manifest_to_log(log, text)
		if dry_run or not apply_enabled:
			doc.bench_status = "Pending"; doc.save()
			return dry_run_result(log, text, cluster, "FrappeBench", dry_run, apply_enabled)
		require_cluster_apply_ready(cluster)
		resource = reconcile_manifest(cluster, yaml.safe_load(text))
		doc.bench_status = phase_from_resource(resource); doc.save()
		message = "FrappeBench accepted by Kubernetes API."
		finish_action_log(log, "Succeeded", message)
		return {"status": "accepted", "phase": doc.bench_status, "cluster": cluster.name, "action_log": log.name, "message": message, "next_actions": ["Run Sync runtime status until Ready.", "Run Inspect runtime before creating a Site."]}
	except Exception as exc:
		doc.bench_status = "Failed"; doc.save(ignore_permissions=True)
		fail_action(log, exc, "Open this action log, correct the placement/database/release issue, then retry Reconcile Bench.")


@frappe.whitelist()
def dry_run_site_manifest(site):
	doc = frappe.get_doc("Site", site)
	cluster = get_region_cluster(doc.region)
	log = create_action_log("Site Dry Run", "Pending", site=doc.name, bench=doc.bench, cluster=cluster.name, region=doc.region, message="Generating secret-safe FrappeSite manifest.", resource_kind="FrappeSite", operation="dry-run")
	try:
		text = manifest_yaml(build_frappesite_manifest_data(doc))
		attach_manifest_to_log(log, text)
		message = "Generated secret-safe FrappeSite manifest dry-run; no Kubernetes resource was created."
		finish_action_log(log, "Dry Run", message)
		return {"manifest": text, "cluster": cluster.name, "action_log": log.name, "dry_run": True, "status": "dry_run", "message": message, "next_actions": ["Review hostname, ownership labels, Bench reference, and wildcard ingress settings.", "To create it, use Reconcile Site with Dry run off while apply is enabled."]}
	except Exception as exc:
		fail_action(log, exc, "Correct the Site placement, Bench, hostname, or route field named in the error, then retry the dry run.")


@frappe.whitelist()
def reconcile_site(site, dry_run=True):
	doc = frappe.get_doc("Site", site)
	cluster = get_region_cluster(doc.region)
	dry_run = as_bool(dry_run)
	log = create_action_log("Site Reconcile", "Pending", site=doc.name, bench=doc.bench, cluster=cluster.name, region=doc.region, dry_run=dry_run, message="Preparing FrappeSite reconciliation.", resource_kind="FrappeSite", operation="apply")
	try:
		text = manifest_yaml(build_frappesite_manifest_data(doc))
		attach_manifest_to_log(log, text)
		apply_enabled = bool(get_platform_settings().kubernetes_apply_enabled)
		if dry_run or not apply_enabled:
			doc.provisioning_status = "Pending"; doc.site_status = "Requested"; doc.route_status = "Pending"; doc.save(ignore_permissions=True)
			return dry_run_result(log, text, cluster, "FrappeSite", dry_run, apply_enabled)
		require_cluster_apply_ready(cluster)
		namespace = yaml.safe_load(text)["metadata"]["namespace"]
		ensure_site_admin_secret(cluster, doc, namespace)
		resource = reconcile_manifest(cluster, yaml.safe_load(text))
		doc.provisioning_status = "Accepted"; doc.site_status = phase_from_resource(resource); doc.route_status = "Pending"; doc.save(ignore_permissions=True)
		message = "FrappeSite accepted by Kubernetes API."
		finish_action_log(log, "Succeeded", message)
		return {"status": "accepted", "phase": doc.site_status, "cluster": cluster.name, "action_log": log.name, "message": message, "next_actions": ["Run Sync provisioning and access until Ready.", "When Ready, verify the HTTPS page and generated static asset.", "Run Inspect runtime for finalizers, Jobs, Services, Ingresses, and warning Events."]}
	except Exception as exc:
		doc.provisioning_status = "Failed"; doc.site_status = "Failed"; doc.route_status = "Failed"; doc.route_error = sanitize_error(exc); doc.save(ignore_permissions=True)
		fail_action(log, exc, "Open this action log, correct the Bench/secret/route issue, then retry Reconcile Site.")


def sync_custom_resource(cluster, kind, namespace, name):
	with get_cluster_client(cluster) as client:
		return client.get_custom_resource(kind, namespace, name)


def is_not_found(exc):
	return "Kubernetes API 404:" in str(exc)


def require_platform_operator():
	frappe.only_for("System Manager")


def expected_runtime_identity(doc, kind):
	cluster = get_region_cluster(doc.region)
	ensure_operator_fields(doc, cluster)
	if doc.doctype == "Site":
		bench = frappe.get_doc("Bench", doc.bench)
		namespace = bench.kubernetes_namespace or default_runtime_namespace(cluster)
	elif doc.doctype == "Bench":
		namespace = doc.kubernetes_namespace or default_runtime_namespace(cluster)
	else:
		namespace = doc.kubernetes_namespace or default_runtime_namespace(cluster)
	return cluster, namespace, doc.operator_resource_name


def validate_runtime_namespace(cluster, kind, namespace, name):
	if (kind, namespace, name) in PROTECTED_RUNTIME_RESOURCES:
		frappe.throw(_("Protected runtime resource {0}/{1} cannot be mutated by Platform lifecycle actions.").format(namespace, name))
	if kind in RUNTIME_NAMESPACE_RESOURCE_KINDS and namespace != default_runtime_namespace(cluster):
		frappe.throw(_("Platform lifecycle delete is allowed only in runtime namespace {0}.").format(default_runtime_namespace(cluster)))


def validate_runtime_owner(resource, doc, resource_kind):
	metadata = resource.get("metadata") or {}
	labels = metadata.get("labels") or {}
	expected = platform_owner_labels(resource_kind, doc)
	for key, value in expected.items():
		if labels.get(key) != value:
			frappe.throw(_("Runtime resource {0}/{1} is not owned by this Platform document.").format(metadata.get("namespace"), metadata.get("name")))
	return True


def scrub_metadata(metadata):
	return {
		"name": metadata.get("name"),
		"namespace": metadata.get("namespace"),
		"uid": metadata.get("uid"),
		"labels": metadata.get("labels") or {},
		"ownerReferences": metadata.get("ownerReferences") or [],
		"finalizers": metadata.get("finalizers") or [],
		"creationTimestamp": metadata.get("creationTimestamp"),
		"deletionTimestamp": metadata.get("deletionTimestamp"),
	}


def summarize_conditions(status):
	conditions = []
	for condition in status.get("conditions") or []:
		conditions.append({
			"type": condition.get("type"),
			"status": condition.get("status"),
			"reason": condition.get("reason"),
			"message": sanitize_error(condition.get("message")),
			"lastTransitionTime": condition.get("lastTransitionTime"),
		})
	return conditions


def summarize_resource(item, include_status=True):
	metadata = item.get("metadata") or {}
	spec = item.get("spec") or {}
	status = item.get("status") or {}
	kind = item.get("kind")
	summary = {"kind": kind, "metadata": scrub_metadata(metadata)}
	if include_status:
		summary["status"] = {
			"phase": status.get("phase") or status.get("state"),
			"observedGeneration": status.get("observedGeneration"),
			"conditions": summarize_conditions(status),
			"readyReplicas": status.get("readyReplicas"),
			"replicas": status.get("replicas"),
			"availableReplicas": status.get("availableReplicas"),
			"succeeded": status.get("succeeded"),
			"failed": status.get("failed"),
		}
	if kind == "PersistentVolumeClaim":
		summary["storage"] = {
			"storageClassName": spec.get("storageClassName"),
			"requestedCapacity": ((spec.get("resources") or {}).get("requests") or {}).get("storage"),
			"boundCapacity": (status.get("capacity") or {}).get("storage"),
			"volumeName": spec.get("volumeName"),
		}
	elif kind == "Service":
		summary["service"] = {
			"type": spec.get("type"),
			"clusterIP": spec.get("clusterIP"),
			"ports": [{"name": port.get("name"), "port": port.get("port"), "protocol": port.get("protocol"), "targetPort": port.get("targetPort")} for port in spec.get("ports") or []],
		}
	elif kind == "Ingress":
		summary["route"] = {
			"ingressClassName": spec.get("ingressClassName"),
			"hosts": [rule.get("host") for rule in spec.get("rules") or [] if rule.get("host")],
			"loadBalancer": status.get("loadBalancer") or {},
		}
	elif kind == "Pod":
		summary["workload"] = {
			"nodeName": spec.get("nodeName"),
			"readyContainers": sum(1 for container in status.get("containerStatuses") or [] if container.get("ready")),
			"containerCount": len(status.get("containerStatuses") or []),
		}
	return summary


def warning_event_summary(event):
	return {
		"kind": "Event",
		"metadata": scrub_metadata(event.get("metadata") or {}),
		"type": event.get("type"),
		"reason": event.get("reason"),
		"message": sanitize_error(event.get("message")),
		"involvedObject": event.get("involvedObject"),
		"lastTimestamp": event.get("lastTimestamp") or event.get("eventTime"),
	}


def matches_runtime_owner(item, doc, owner_uid=None, owner_kind=None, owner_name=None):
	metadata = item.get("metadata") or {}
	labels = metadata.get("labels") or {}
	if labels.get(PLATFORM_MANAGER_LABEL) == PLATFORM_MANAGER_VALUE and labels.get(RESOURCE_ID_LABEL) == resource_id_label(doc):
		return True
	for reference in metadata.get("ownerReferences") or []:
		if owner_uid and reference.get("uid") == owner_uid:
			return True
		if owner_kind and owner_name and reference.get("kind") == owner_kind and reference.get("name") == owner_name:
			return True
	return False


def build_runtime_inventory(doc, kind, resource_kind):
	cluster, namespace, name = expected_runtime_identity(doc, kind)
	owner = None
	warnings = []
	related = {}
	with get_cluster_client(cluster) as client:
		try:
			owner = client.get_custom_resource(kind, namespace, name)
		except KubernetesClientError as exc:
			if not is_not_found(exc):
				raise
		owner_uid = None
		if owner:
			validate_runtime_owner(owner, doc, resource_kind)
			owner_uid = (owner.get("metadata") or {}).get("uid")
		for resource, label, group, version in RELATED_RUNTIME_RESOURCES:
			items = client.list_namespaced(resource, namespace, group=group, version=version)
			related[label] = [summarize_resource(item) for item in items if matches_runtime_owner(item, doc, owner_uid, kind, name)]
		for event in client.list_namespaced("events", namespace, field_selector=f"involvedObject.name={name}"):
			if event.get("type") == "Warning":
				warnings.append(warning_event_summary(event))
	return {
		"cluster": cluster.name,
		"namespace": namespace,
		"name": name,
		"owner": summarize_resource(owner) if owner else None,
		"owner_present": bool(owner),
		"related": related,
		"warning_events": warnings,
		"secret_values_returned": False,
	}


def owned_secret_names(doc):
	if doc.doctype == "Site":
		return [
			doc.admin_password_secret_reference or f"{doc.operator_resource_name}-admin-password",
			f"{doc.operator_resource_name}-encryption-key",
		]
	if doc.doctype == "Database Server" and doc.root_credential_secret_reference:
		return [doc.root_credential_secret_reference]
	return []


def cleanup_owned_secrets(doc, cluster, namespace, resource_kind):
	deleted = []
	with get_cluster_client(cluster) as client:
		for name in owned_secret_names(doc):
			try:
				secret = client.get_secret(namespace, name)
			except KubernetesClientError as exc:
				if is_not_found(exc):
					continue
				raise
			validate_runtime_owner(secret, doc, resource_kind)
			client.delete_namespaced("secrets", namespace, name)
			deleted.append(name)
	return deleted


def remaining_required_dependents(doc, inventory):
	remaining = []
	for label, items in inventory.get("related", {}).items():
		if doc.doctype == "Database Server" and label == "PersistentVolumeClaim" and getattr(doc, "data_retention_policy", "Retain") == "Retain":
			continue
		remaining.extend((label, item["metadata"].get("name")) for item in items)
	return remaining


def finalize_deleted_state(doc, inventory, status_field, resource_kind):
	if inventory["owner_present"]:
		return False
	if doc.get(status_field) not in {"Deletion Requested", "Quiescing", "Deleting"}:
		return False
	cluster = get_region_cluster(doc.region)
	deleted_secrets = cleanup_owned_secrets(doc, cluster, inventory["namespace"], resource_kind)
	remaining = remaining_required_dependents(doc, inventory)
	if deleted_secrets or remaining:
		return False
	doc.set(status_field, "Deleted")
	if hasattr(doc, "provisioning_status"):
		doc.provisioning_status = "Deleted"
	doc.save(ignore_permissions=True)
	return True


def inspect_runtime(doc, kind, resource_kind, status_field):
	cluster = get_region_cluster(doc.region)
	log = create_action_log(
		"Runtime Inventory",
		"Pending",
		database_server=doc.name if doc.doctype == "Database Server" else None,
		bench=doc.name if doc.doctype == "Bench" else getattr(doc, "bench", None),
		site=doc.name if doc.doctype == "Site" else None,
		cluster=cluster.name,
		region=doc.region,
		message=f"Collecting secret-safe runtime inventory for {kind}.",
		dry_run=False,
		resource_kind=kind,
		operation="inventory",
	)
	try:
		inventory = build_runtime_inventory(doc, kind, resource_kind)
		finalize_deleted_state(doc, inventory, status_field, resource_kind)
		message = f"Runtime inventory collected for {inventory['namespace']}/{inventory['name']} without Secret values."
		finish_action_log(log, "Succeeded", message)
		inventory.update({
			"action_log": log.name,
			"message": message,
			"next_actions": ["Review owner conditions/finalizers and related resources below.", "If provisioning is still running, wait for the operator and run status sync again."] if inventory["owner_present"] else ["No owner CR is present. If creation was intended, run Reconcile with Dry run off and require status accepted."]
		})
		return inventory
	except Exception as exc:
		fail_action(log, exc, "Open this action log, verify API reachability and ownership identity, then retry Inspect runtime.")


@frappe.whitelist()
def inspect_database_server_runtime(database_server):
	require_platform_operator()
	return inspect_runtime(frappe.get_doc("Database Server", database_server), "MariaDB", "database-server", "database_status")


@frappe.whitelist()
def inspect_bench_runtime(bench):
	require_platform_operator()
	return inspect_runtime(frappe.get_doc("Bench", bench), "FrappeBench", "bench", "bench_status")


@frappe.whitelist()
def inspect_site_runtime(site):
	require_platform_operator()
	return inspect_runtime(frappe.get_doc("Site", site), "FrappeSite", "site", "site_status")


def validate_delete_confirmation(doc, confirmation):
	if (confirmation or "").strip() != doc.name:
		frappe.throw(_("Type the exact document name to confirm deletion."))


def delete_owner_resource(doc, kind, resource_kind, status_field, reason=None):
	cluster, namespace, name = expected_runtime_identity(doc, kind)
	log = create_action_log(
		f"{doc.doctype} Delete",
		"Deletion Requested",
		database_server=doc.name if doc.doctype == "Database Server" else None,
		bench=doc.name if doc.doctype == "Bench" else getattr(doc, "bench", None),
		site=doc.name if doc.doctype == "Site" else None,
		cluster=cluster.name,
		region=doc.region,
		message=f"Deletion requested for {kind} {namespace}/{name}. Reason: {sanitize_error(reason) if reason else 'Not supplied'}",
		dry_run=False,
		resource_kind=kind,
		operation="delete",
	)
	try:
		validate_runtime_namespace(cluster, kind, namespace, name)
		doc.set(status_field, "Deletion Requested")
		if hasattr(doc, "provisioning_status"):
			doc.provisioning_status = "Deletion Requested"
		doc.save(ignore_permissions=True)
		with get_cluster_client(cluster) as client:
			try:
				resource = client.get_custom_resource(kind, namespace, name)
			except KubernetesClientError as exc:
				if is_not_found(exc):
					doc.set(status_field, "Deleted")
					if hasattr(doc, "provisioning_status"):
						doc.provisioning_status = "Deleted"
					doc.save(ignore_permissions=True)
					message = f"{kind} {namespace}/{name} was already absent."
					finish_action_log(log, "Deleted", message)
					return {"status": "deleted", "action_log": log.name, "namespace": namespace, "name": name, "message": message, "next_actions": ["Run Inspect runtime to confirm required dependent cleanup and final Platform status."]}
				raise
			validate_runtime_owner(resource, doc, resource_kind)
			doc.set(status_field, "Deleting")
			if hasattr(doc, "provisioning_status"):
				doc.provisioning_status = "Deleting"
			doc.save(ignore_permissions=True)
			client.delete_custom_resource(kind, namespace, name)
		message = f"{kind} {namespace}/{name} delete accepted; waiting on normal operator finalizers."
		finish_action_log(log, "Deleting", message)
		return {"status": "deleting", "action_log": log.name, "namespace": namespace, "name": name, "message": message, "next_actions": ["Run Inspect runtime until the owner CR is absent and the Platform status is Deleted.", "Never remove finalizers manually; use Retry delete only after correcting a reported blocker."]}
	except Exception as exc:
		doc.set(status_field, "Deletion Failed")
		if hasattr(doc, "provisioning_status"):
			doc.provisioning_status = "Deletion Failed"
		if hasattr(doc, "last_error"):
			doc.last_error = sanitize_error(exc)
		doc.save(ignore_permissions=True)
		fail_action(log, exc, "Open this action log, correct the ownership/dependency/finalizer blocker, then use Retry delete.")


@frappe.whitelist()
def delete_site(site, confirmation, reason=None):
	require_platform_operator()
	doc = frappe.get_doc("Site", site)
	validate_delete_confirmation(doc, confirmation)
	return delete_owner_resource(doc, "FrappeSite", "site", "site_status", reason=reason)


@frappe.whitelist()
def delete_bench(bench, confirmation, reason=None):
	require_platform_operator()
	doc = frappe.get_doc("Bench", bench)
	validate_delete_confirmation(doc, confirmation)
	active_sites = frappe.get_all("Site", filters={"bench": doc.name, "site_status": ["not in", ["Deleted"]]}, fields=["name", "site_status"])
	if active_sites:
		frappe.throw(_("Bench cannot be deleted until dependent Sites are Deleted: {0}").format(", ".join(row.name for row in active_sites)))
	return delete_owner_resource(doc, "FrappeBench", "bench", "bench_status", reason=reason)


@frappe.whitelist()
def delete_database_server(database_server, confirmation, reason=None):
	require_platform_operator()
	doc = frappe.get_doc("Database Server", database_server)
	validate_delete_confirmation(doc, confirmation)
	if doc.provisioning_type != "Operator Managed":
		frappe.throw(_("Only operator-managed Database Servers can be deleted through Platform lifecycle actions."))
	active_benches = frappe.get_all("Bench", filters={"database_server": doc.name, "bench_status": ["not in", ["Deleted", "Retired"]]}, fields=["name", "bench_status"])
	if active_benches:
		frappe.throw(_("Database Server cannot be deleted until attached Benches are absent: {0}").format(", ".join(row.name for row in active_benches)))
	return delete_owner_resource(doc, "MariaDB", "database-server", "database_status", reason=reason)


@frappe.whitelist()
def retry_lifecycle_delete(doctype, name, confirmation):
	require_platform_operator()
	if doctype == "Site":
		return delete_site(name, confirmation)
	if doctype == "Bench":
		return delete_bench(name, confirmation)
	if doctype == "Database Server":
		return delete_database_server(name, confirmation)
	frappe.throw(_("Unsupported lifecycle delete DocType."))


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
		doc.health_status = "Failed"; doc.last_sync_time = now_datetime(); doc.last_error = sanitize_error(exc); doc.save(ignore_permissions=True)
		next_action = "Run Reconcile Database Server with Dry run off, require status accepted, then retry Sync runtime status." if is_not_found(exc) else "Open this action log, correct the reported runtime access or operator issue, then retry Sync runtime status."
		fail_action(log, exc, next_action)


@frappe.whitelist()
def sync_bench_status(bench):
	doc = frappe.get_doc("Bench", bench); cluster = get_region_cluster(doc.region)
	log = create_action_log("Bench Status Sync", bench=doc.name, database_server=doc.database_server, cluster=cluster.name, region=doc.region, dry_run=False, resource_kind="FrappeBench", operation="status-sync")
	try:
		resource = sync_custom_resource(cluster, "FrappeBench", doc.kubernetes_namespace, doc.operator_resource_name); doc.bench_status = phase_from_resource(resource); doc.save(); finish_action_log(log, "Succeeded", f"FrappeBench runtime phase: {doc.bench_status}.")
		return {"status": doc.bench_status, "action_log": log.name}
	except Exception as exc:
		doc.bench_status = "Failed"; doc.save(ignore_permissions=True)
		next_action = "Run Reconcile Bench with Dry run off, require status accepted, then retry Sync runtime status." if is_not_found(exc) else "Open this action log, correct the reported runtime issue, then retry Bench status sync."
		fail_action(log, exc, next_action)


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
		doc.last_route_check = now_datetime(); doc.route_status = "Failed"; doc.route_error = sanitize_error(exc); doc.save(ignore_permissions=True)
		next_action = "Run Reconcile Site with Dry run off, require status accepted, then retry Sync provisioning and access." if is_not_found(exc) else "Open this action log, inspect operator conditions and route diagnostics, then retry Site status sync."
		fail_action(log, exc, next_action)


def gate_result(key, label, passed, message, next_action=None, evidence=None):
	return {
		"key": key,
		"label": label,
		"passed": bool(passed),
		"message": sanitize_error(message),
		"next_action": next_action,
		"evidence": evidence,
	}


def api_resources(client, group, version):
	result = client.request("GET", f"/apis/{quote(group)}/{quote(version)}")
	return {item.get("name") for item in result.get("resources") or []}


def headlamp_reachable(url):
	if not url or not str(url).startswith("https://"):
		return False, "Headlamp URL must be HTTPS."
	try:
		response = requests.get(url, timeout=15, allow_redirects=True)
		return response.status_code < 500, f"HTTPS status {response.status_code}."
	except requests.RequestException as exc:
		return False, sanitize_error(exc)


def validate_dry_run_records(database_server=None, bench=None, site=None):
	selected = [value for value in (database_server, bench, site) if value]
	if not selected:
		return False, "No dry-run records were supplied for manifest validation."
	for name in selected:
		# The builders return structured data and never expose Secret values.
		if name == database_server:
			build_database_server_manifest_data(frappe.get_doc("Database Server", database_server))
		elif name == bench:
			build_frappebench_manifest_data(frappe.get_doc("Bench", bench), allow_pending_database=True)
		elif name == site:
			build_frappesite_manifest_data(frappe.get_doc("Site", site))
	return True, "Selected dry-run manifest builders completed without validation errors."


@frappe.whitelist()
def validate_cluster_readiness(cluster, expected_root_domain="testcloud.lmnaslens.com", database_server=None, bench=None, site=None):
	require_platform_operator()
	doc = frappe.get_doc("Cluster", cluster)
	settings = get_platform_settings()
	runtime_namespace = doc.default_runtime_namespace or "default"
	gates = []

	def add(key, label, passed, message, next_action=None, evidence=None):
		gates.append(gate_result(key, label, passed, message, next_action, evidence))

	try:
		path = kubeconfig_path(doc.kubeconfig_reference)
		add("kubeconfig-readable", "Restricted kubeconfig readable", True, f"Server-side kubeconfig reference is readable at {path}.")
	except Exception as exc:
		add("kubeconfig-readable", "Restricted kubeconfig readable", False, exc, "Mount the restricted kubeconfig read-only into the Platform backend and store only the file: reference.")

	try:
		region_cluster = frappe.db.get_value("Region", doc.region, "cluster") if doc.region else None
		add("region-cluster", "Region resolves to selected Cluster", region_cluster == doc.name, f"Region {doc.region or '-'} resolves to Cluster {region_cluster or '-' }.", "Set Region.cluster to this Cluster before creating runtime records.")
	except Exception as exc:
		add("region-cluster", "Region resolves to selected Cluster", False, exc, "Fix the Region record and retry validation.")

	try:
		with get_cluster_client(doc) as client:
			version = client.request("GET", "/version")
			add("api-reachable", "Kubernetes API reachable", True, "Kubernetes API version endpoint responded.", evidence=version.get("gitVersion"))
			frappe_resources = api_resources(client, "vyogo.tech", "v1")
			add("frappe-crds", "Frappe Operator CRDs exist", {"frappebenches", "frappesites"}.issubset(frappe_resources), f"Frappe resources discovered: {', '.join(sorted(frappe_resources))}.", "Ask Infra to verify Frappe Operator and CRDs.")
			client.list_custom_resources("FrappeBench", runtime_namespace)
			add("runtime-namespace", "Runtime namespace accepts Platform-scoped reads", True, f"Namespace {runtime_namespace} accepted a namespace-scoped FrappeBench list request.")
			mariadb_resources = api_resources(client, "k8s.mariadb.com", "v1alpha1")
			add("mariadb-crds", "MariaDB Operator CRDs exist", "mariadbs" in mariadb_resources, f"MariaDB resources discovered: {', '.join(sorted(mariadb_resources))}.", "Ask Infra to verify MariaDB Operator and CRDs.")
			mariadb = client.get_custom_resource("MariaDB", "default", "frappe-mariadb")
			phase = phase_from_resource(mariadb)
			add("default-mariadb-ready", "default/frappe-mariadb readable and Ready", phase == "Ready", f"default/frappe-mariadb phase is {phase}.", "Ask Infra to restore the protected shared Public MariaDB before Platform apply.")
			ingress_class = (doc.ingress_class or "").strip()
			add("ingress-class", "Traefik ingress class configured", ingress_class == "traefik", f"Cluster ingress_class is {ingress_class or '-'}; expected traefik from the Infra handoff.", "Set Cluster.ingress_class to traefik, or ask Infra for a corrected handoff if the test cluster uses another class.")
			client.list_namespaced("ingresses", runtime_namespace, group="networking.k8s.io", version="v1")
			add("runtime-ingress-read", "Runtime Ingress API is namespace-readable", True, f"Namespace {runtime_namespace} accepted a namespaced Ingress list request.")
	except Exception as exc:
		add("cluster-api-runtime", "Cluster API runtime checks", False, exc, "Check Platform API firewall authorization, restricted RBAC, operators, and runtime namespace with Infra.")

	expected = (expected_root_domain or "").strip().lower().strip(".")
	actual = (settings.root_domain or "").strip().lower().strip(".")
	add("root-domain", "Root domain matches handoff", bool(expected and actual == expected), f"Platform Settings root_domain is {actual or '-'}; expected {expected or '-'}.", "Set Platform Settings root_domain to the Infra handoff root domain.")
	reachable, headlamp_message = headlamp_reachable(doc.headlamp_url)
	add("headlamp-https", "Headlamp HTTPS reachable", reachable, headlamp_message, "Ask Infra to verify wildcard DNS/TLS, Traefik, and Headlamp before Platform apply.")

	try:
		permissions = check_cluster_permissions(cluster)
		add("positive-rbac", "Positive RBAC checks pass", permissions["all_required_allowed"], "Required namespace and protected-read checks completed.", "Stop and hand the RBAC evidence back to Infra.")
		add("negative-rbac", "Negative RBAC checks remain denied", permissions["all_denied_blocked"], "Protected operations were checked for denial.", "Stop immediately; Platform apply must remain disabled until Infra fixes the restricted access contract.")
	except Exception as exc:
		add("rbac-preflight", "RBAC preflight completed", False, exc, "Fix API reachability or restricted access before enabling apply.")

	try:
		dry_run_ok, dry_run_message = validate_dry_run_records(database_server=database_server, bench=bench, site=site)
		add("dry-run-manifests", "Dry-run manifest validation passes", dry_run_ok, dry_run_message, "Create/select the Database Server, Bench, and/or Site control-plane records, then rerun validation.")
	except Exception as exc:
		add("dry-run-manifests", "Dry-run manifest validation passes", False, exc, "Correct the record fields named in the error and rerun dry-run validation.")

	all_passed = all(item["passed"] for item in gates)
	doc.health_status = "Healthy" if all_passed else "Degraded"
	doc.last_sync_time = now_datetime()
	doc.last_error = None if all_passed else "; ".join(item["label"] for item in gates if not item["passed"])
	doc.save(ignore_permissions=True)
	return {
		"cluster": doc.name,
		"all_gates_passed": all_passed,
		"apply_allowed": all_passed,
		"client": "python-kubernetes-api-wrapper",
		"kubectl_required": False,
		"gates": gates,
		"next_actions": ["Enable Kubernetes apply only for the controlled test window after all gates pass."] if all_passed else ["Keep Kubernetes apply disabled.", "Resolve every failed gate and rerun Validate cluster gates."],
	}


def require_cluster_apply_ready(cluster):
	settings = get_platform_settings()
	if not settings.kubernetes_apply_enabled:
		return True
	root_domain = (settings.root_domain or "").strip().lower().strip(".")
	if not root_domain:
		frappe.throw(_("Platform Settings root_domain is required before live apply."))
	if cluster.status != "Active" or cluster.health_status != "Healthy":
		frappe.throw(_("Cluster {0} must pass Validate cluster gates and be Healthy before live apply.").format(cluster.name))
	return True


@frappe.whitelist()
def check_cluster_permissions(cluster):
	doc = frappe.get_doc("Cluster", cluster)
	runtime_namespace = doc.default_runtime_namespace or "default"
	checks = []
	denied_checks = []
	with get_cluster_client(doc) as client:
		for kind, (group, _version, plural) in RESOURCE_PATHS.items():
			for verb in ("get", "list", "patch", "delete"):
				allowed, reason = client.can_i(verb, group, plural, runtime_namespace)
				checks.append({"kind": kind, "verb": verb, "group": group, "resource": plural, "namespace": runtime_namespace, "allowed": allowed, "reason": reason})
		for resource, group in (("pods", ""), ("services", ""), ("persistentvolumeclaims", ""), ("events", ""), ("jobs", "batch"), ("ingresses", "networking.k8s.io")):
			for verb in ("get", "list"):
				allowed, reason = client.can_i(verb, group, resource, runtime_namespace)
				checks.append({"kind": resource, "verb": verb, "group": group, "resource": resource, "namespace": runtime_namespace, "allowed": allowed, "reason": reason})
		for verb in ("get", "create", "delete"):
			allowed, reason = client.can_i(verb, "", "secrets", runtime_namespace)
			checks.append({"kind": "Secret", "verb": verb, "group": "", "resource": "secrets", "namespace": runtime_namespace, "allowed": allowed, "reason": reason})
		for verb in ("get", "list"):
			allowed, reason = client.can_i(verb, "k8s.mariadb.com", "mariadbs", "default")
			checks.append({"kind": "Default MariaDB", "verb": verb, "group": "k8s.mariadb.com", "resource": "mariadbs", "namespace": "default", "allowed": allowed, "reason": reason})
		for verb, group, resource, namespace, label in (
			("patch", "k8s.mariadb.com", "mariadbs", "default", "default MariaDB patch"),
			("delete", "k8s.mariadb.com", "mariadbs", "default", "default MariaDB delete"),
			("list", "", "secrets", runtime_namespace, "runtime Secret list"),
			("delete", "", "namespaces", None, "namespace delete"),
			("delete", "apiextensions.k8s.io", "customresourcedefinitions", None, "CRD delete"),
		):
			allowed, reason = client.can_i(verb, group, resource, namespace)
			denied_checks.append({"kind": label, "verb": verb, "group": group, "resource": resource, "namespace": namespace, "allowed": allowed, "reason": reason})
	return {
		"cluster": doc.name,
		"runtime_namespace": runtime_namespace,
		"checks": checks,
		"denied_checks": denied_checks,
		"all_required_allowed": all(item["allowed"] for item in checks),
		"all_denied_blocked": all(not item["allowed"] for item in denied_checks),
		"client": "python-kubernetes-api-wrapper",
		"kubectl_required": False,
	}


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
