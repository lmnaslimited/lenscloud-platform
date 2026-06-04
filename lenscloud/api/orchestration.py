import re

import frappe
from frappe import _


SAFE_NAME_PATTERN = re.compile(r"[^a-z0-9-]+")


def slugify(value):
	value = (value or "").strip().lower()
	value = SAFE_NAME_PATTERN.sub("-", value)
	return value.strip("-")


def get_platform_settings():
	return frappe.get_single("Platform Settings")


def get_region_cluster(region):
	if not region:
		frappe.throw(_("Region is required for cluster placement."))

	cluster = frappe.db.get_value("Region", region, "cluster")
	if not cluster:
		frappe.throw(_("Region {0} is not linked to a Cluster runtime target.").format(region))

	return frappe.get_doc("Cluster", cluster)


def default_operator_namespace(cluster=None):
	settings = get_platform_settings()
	return (cluster and cluster.operator_namespace) or settings.operator_namespace or "frappe-operator-system"


def default_storage_class(cluster=None):
	settings = get_platform_settings()
	return (cluster and cluster.default_storage_class) or settings.default_storage_class or "local-path"


def default_runtime_namespace(cluster=None):
	return (cluster and cluster.default_runtime_namespace) or "default"


def namespace_from_pattern(pattern, bench_name):
	bench_slug = slugify(bench_name)
	return (pattern or "bench-{bench}").format(bench=bench_slug, bench_name=bench_slug)


def get_free_plan():
	plan = frappe.db.get_value("Plan", {"is_default": 1, "status": "Active"}, "name")
	if plan:
		return plan
	plan = frappe.db.get_value("Plan", {"is_free": 1, "status": "Active"}, "name")
	if plan:
		return plan
	return None


def ensure_operator_fields(doc, cluster=None):
	cluster = cluster or get_region_cluster(doc.region)
	if doc.doctype in {"Bench", "Site"}:
		doc.cluster = cluster.name

	if doc.doctype == "Bench":
		if not doc.operator_resource_name:
			doc.operator_resource_name = slugify(doc.title or doc.name)
		if not doc.kubernetes_namespace:
			doc.kubernetes_namespace = namespace_from_pattern(cluster.default_bench_namespace_pattern, doc.operator_resource_name)
		if not doc.storage_class:
			doc.storage_class = default_storage_class(cluster)
		doc.cluster_derivation_note = f"Derived from Region {doc.region} -> Cluster {cluster.name}"

	if doc.doctype == "Site":
		if not doc.operator_resource_name:
			doc.operator_resource_name = slugify(doc.subdomain or doc.title or doc.name)

	return cluster


def get_release_image(bench):
	if not bench.current_release:
		frappe.throw(_("Bench {0} needs Current Release for FrappeBench manifest generation.").format(bench.name))

	release = frappe.get_doc("Release", bench.current_release)
	release_group = frappe.get_doc("Release Group", release.release_group)
	repository = "/".join(filter(None, [release_group.registry_url, release_group.image_repository]))
	if not repository:
		frappe.throw(_("Release Group {0} needs registry URL and image repository.").format(release_group.name))

	return release, release_group, repository


def yaml_scalar(value):
	if value is None or value == "":
		return '""'
	return str(value)


def build_frappebench_manifest(bench):
	cluster = get_region_cluster(bench.region)
	ensure_operator_fields(bench, cluster)
	release, release_group, repository = get_release_image(bench)
	operator_namespace = default_operator_namespace(cluster)
	storage_class = bench.storage_class or default_storage_class(cluster)

	return f"""apiVersion: vyogo.tech/v1
kind: FrappeBench
metadata:
  name: {yaml_scalar(bench.operator_resource_name)}
  namespace: {yaml_scalar(bench.kubernetes_namespace or default_runtime_namespace(cluster))}
spec:
  imageConfig:
    repository: {yaml_scalar(repository)}
    tag: {yaml_scalar(release.image_tag)}
  storageClass: {yaml_scalar(storage_class)}
  operatorNamespace: {yaml_scalar(operator_namespace)}
  nodeSelector:
    lenscloud.io/node-role: worker
"""



def get_site_hostname(site):
	domain = (site.domain or '').strip().lower().strip('.')
	subdomain = slugify(site.subdomain)
	if subdomain and domain:
		legacy_prefix = f"{subdomain}."
		if domain.startswith(legacy_prefix):
			return domain
		return f"{subdomain}.{domain}"
	hostname = (site.title or site.name or '').strip().lower().strip('.')
	if "." in hostname:
		return hostname
	if subdomain:
		settings = get_platform_settings()
		root_domain = (settings.root_domain or '').strip().lower().strip('.')
		if root_domain:
			return f"{subdomain}.{root_domain}"
	frappe.throw(_("Site {0} needs a subdomain and root/approved domain before FrappeSite manifest generation.").format(site.name))

def build_frappesite_manifest(site):
	cluster = get_region_cluster(site.region)
	ensure_operator_fields(site, cluster)
	if not site.bench:
		frappe.throw(_("Site {0} needs Bench for FrappeSite manifest generation.").format(site.name))
	bench = frappe.get_doc("Bench", site.bench)
	if not bench.operator_resource_name:
		ensure_operator_fields(bench, cluster)
	return f"""apiVersion: vyogo.tech/v1
kind: FrappeSite
metadata:
  name: {yaml_scalar(site.operator_resource_name)}
  namespace: {yaml_scalar(bench.kubernetes_namespace or default_runtime_namespace(cluster))}
spec:
  siteName: {yaml_scalar(get_site_hostname(site))}
  benchRef:
    name: {yaml_scalar(bench.operator_resource_name)}
"""


def create_action_log(action_type, status="Dry Run", bench=None, site=None, cluster=None, region=None, release=None, manifest=None, message=None, error=None, dry_run=True):
	doc = frappe.get_doc({
		"doctype": "Orchestration Action Log",
		"title": action_type,
		"action_type": action_type,
		"status": status,
		"dry_run": "1" if dry_run else "0",
		"bench": bench,
		"site": site,
		"cluster": cluster,
		"region": region,
		"release": release,
		"manifest": manifest,
		"message": message,
		"error": error,
	})
	doc.insert(ignore_permissions=False)
	return doc


@frappe.whitelist()
def dry_run_bench_manifest(bench):
	bench_doc = frappe.get_doc("Bench", bench)
	cluster = get_region_cluster(bench_doc.region)
	manifest = build_frappebench_manifest(bench_doc)
	log = create_action_log("Bench Dry Run", bench=bench_doc.name, cluster=cluster.name, region=bench_doc.region, release=bench_doc.current_release, manifest=manifest, message="Generated FrappeBench manifest dry-run.")
	return {"manifest": manifest, "cluster": cluster.name, "action_log": log.name, "dry_run": True}


@frappe.whitelist()
def reconcile_bench(bench, dry_run=True):
	dry_run = str(dry_run).lower() not in {"false", "0", "no"}
	bench_doc = frappe.get_doc("Bench", bench)
	cluster = get_region_cluster(bench_doc.region)
	manifest = build_frappebench_manifest(bench_doc)
	settings = get_platform_settings()
	if dry_run or not settings.kubernetes_apply_enabled:
		bench_doc.bench_status = "Pending"
		bench_doc.save(ignore_permissions=False)
		log = create_action_log("Bench Reconcile", status="Dry Run", bench=bench_doc.name, cluster=cluster.name, region=bench_doc.region, release=bench_doc.current_release, manifest=manifest, message="Kubernetes apply is disabled; dry-run manifest generated.", dry_run=True)
		return {"status": "dry_run", "manifest": manifest, "cluster": cluster.name, "action_log": log.name}
	frappe.throw(_("Real Kubernetes apply is not wired in this platform slice. Use dry-run or complete the credential/apply integration first."))


@frappe.whitelist()
def dry_run_site_manifest(site):
	site_doc = frappe.get_doc("Site", site)
	cluster = get_region_cluster(site_doc.region)
	manifest = build_frappesite_manifest(site_doc)
	log = create_action_log("Site Dry Run", site=site_doc.name, bench=site_doc.bench, cluster=cluster.name, region=site_doc.region, manifest=manifest, message="Generated FrappeSite manifest dry-run.")
	return {"manifest": manifest, "cluster": cluster.name, "action_log": log.name, "dry_run": True}


@frappe.whitelist()
def reconcile_site(site, dry_run=True):
	dry_run = str(dry_run).lower() not in {"false", "0", "no"}
	site_doc = frappe.get_doc("Site", site)
	cluster = get_region_cluster(site_doc.region)
	manifest = build_frappesite_manifest(site_doc)
	settings = get_platform_settings()
	if dry_run or not settings.kubernetes_apply_enabled:
		site_doc.provisioning_status = "Pending"
		site_doc.site_status = "Requested"
		site_doc.save(ignore_permissions=False)
		log = create_action_log("Site Reconcile", status="Dry Run", site=site_doc.name, bench=site_doc.bench, cluster=cluster.name, region=site_doc.region, manifest=manifest, message="Kubernetes apply is disabled; dry-run manifest generated.", dry_run=True)
		return {"status": "dry_run", "manifest": manifest, "cluster": cluster.name, "action_log": log.name}
	frappe.throw(_("Real Kubernetes apply is not wired in this platform slice. Use dry-run or complete the credential/apply integration first."))


@frappe.whitelist()
def queue_or_apply_dns_record(site):
	site_doc = frappe.get_doc("Site", site)
	settings = get_platform_settings()
	hostname = get_site_hostname(site_doc)

	dns_record = frappe.get_doc({
		"doctype": "DNS Record",
		"title": hostname,
		"site": site_doc.name,
		"domain": hostname,
		"record_type": site_doc.dns_record_type or "CNAME",
		"target": site_doc.dns_target or "pending-platform-target",
		"provider": settings.dns_provider or "Route53",
		"hosted_zone_id": settings.route53_hosted_zone_id,
		"status": "Queued" if settings.dns_automation_enabled else "Pending",
	})
	dns_record.insert(ignore_permissions=False)
	site_doc.dns_status = dns_record.status
	site_doc.dns_record_name = dns_record.name
	site_doc.save(ignore_permissions=False)
	log = create_action_log("DNS Queue", status=dns_record.status, site=site_doc.name, cluster=site_doc.cluster, region=site_doc.region, message="Route53 apply is disabled or queued; DNS is not marked active until verification succeeds.")
	return {"status": dns_record.status, "dns_record": dns_record.name, "action_log": log.name}


@frappe.whitelist()
def request_customer_site(site_name, company_name=None, subdomain=None, region=None, plan=None, notes=None):
	settings = get_platform_settings()
	if not settings.root_domain:
		frappe.throw(_("Platform Settings root_domain is required before customer site creation."))
	if not region:
		frappe.throw(_("Region is required."))

	cluster = get_region_cluster(region)
	plan = plan or get_free_plan()
	if not plan:
		frappe.throw(_("A default or Free Plan is required before customer site creation."))

	user = frappe.session.user
	customer = frappe.db.get_value("Customer", {"user": user}, "name")
	if not customer:
		customer_doc = frappe.get_doc({"doctype": "Customer", "first_name": frappe.db.get_value("User", user, "first_name") or user, "user": user, "region": region})
		customer_doc.insert(ignore_permissions=False)
		customer = customer_doc.name

	subdomain = slugify(subdomain or site_name or company_name)
	if not subdomain:
		frappe.throw(_("Subdomain could not be derived."))
	domain = settings.root_domain.strip().lower().strip(".")
	title = f"{subdomain}.{domain}"

	site_doc = frappe.get_doc({
		"doctype": "Site",
		"title": title,
		"customer": customer,
		"region": region,
		"cluster": cluster.name,
		"plan": plan,
		"subdomain": subdomain,
		"domain": domain,
		"site_status": "Requested",
		"provisioning_status": "Pending",
		"dns_status": "Pending",
		"operator_resource_name": subdomain,
	})
	site_doc.insert(ignore_permissions=False)
	log = create_action_log("Site Request", status="Pending", site=site_doc.name, cluster=cluster.name, region=region, message=notes or "Customer Free-plan site request captured.")
	dns = queue_or_apply_dns_record(site_doc.name)
	return {"site": site_doc.name, "domain": domain, "hostname": title, "cluster": cluster.name, "plan": plan, "action_log": log.name, "dns": dns}
