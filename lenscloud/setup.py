import frappe


def upsert_doc(doctype, name, values):
	if frappe.db.exists(doctype, name):
		doc = frappe.get_doc(doctype, name)
		for key, value in values.items():
			doc.set(key, value)
		doc.save(ignore_permissions=True)
		return doc
	doc = frappe.get_doc({"doctype": doctype, **values})
	if "title" in doc.meta.get_fieldnames() and not doc.get("title"):
		doc.title = name
	doc.insert(ignore_permissions=True)
	return doc


def seed_defaults():
	if not frappe.db.exists("Plan", "Free"):
		frappe.get_doc({
			"doctype": "Plan",
			"title": "Free",
			"plan_code": "free",
			"status": "Active",
			"is_default": 1,
			"is_free": 1,
			"monthly_price": "0",
			"site_limit": "1",
			"bench_policy": "Shared Bench",
			"description": "Free self-service starter plan for first LensCloud site requests.",
		}).insert(ignore_permissions=True)

	if not frappe.db.exists("Region", "EU"):
		frappe.get_doc({"doctype": "Region", "title": "EU", "is_group": 0, "deployment_status": "Active"}).insert(ignore_permissions=True)

	if not frappe.db.exists("Cluster", "lenscloud-eu-dev"):
		frappe.get_doc({
			"doctype": "Cluster",
			"title": "lenscloud-eu-dev",
			"cluster_name": "lenscloud-eu-dev",
			"region": "EU",
			"provider": "Hcloud",
			"environment": "Development",
			"status": "Active",
			"manager_host": "lenscloud-eu-manager-1",
			"manager_public_ip": "116.203.22.81",
			"manager_private_ip": "10.20.1.1",
			"headlamp_url": "http://headlamp.eu.lmnaslens.com",
			"access_method": "SSH to manager VM; run kubectl on manager",
			"kubeconfig_reference": "manager:/etc/rancher/k3s/k3s.yaml",
			"credential_reference": "server-side:ssh-manager-lenscloud-eu-dev",
			"operator_namespace": "frappe-operator-system",
			"default_runtime_namespace": "default",
			"default_storage_class": "local-path",
			"default_bench_namespace_pattern": "bench-{bench}",
			"health_status": "Healthy",
		}).insert(ignore_permissions=True)

	region = frappe.get_doc("Region", "EU")
	if region.get("cluster") != "lenscloud-eu-dev":
		region.cluster = "lenscloud-eu-dev"
		region.deployment_status = "Active"
		region.save(ignore_permissions=True)

	settings = frappe.get_single("Platform Settings")
	changed = False
	defaults = {
		"default_plan": "Free",
		"root_domain": "lmnaslens.com",
		"operator_namespace": "frappe-operator-system",
		"default_storage_class": "local-path",
		"default_bench_namespace_pattern": "bench-{bench}",
		"dns_provider": "Route53",
		"aws_region": "eu-central-1",
	}
	for key, value in defaults.items():
		if not settings.get(key):
			settings.set(key, value)
			changed = True
	if changed:
		settings.save(ignore_permissions=True)
