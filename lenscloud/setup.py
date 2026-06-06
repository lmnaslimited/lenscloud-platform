import frappe


def upsert_doc(doctype, name, values):
	if frappe.db.exists(doctype, name):
		doc = frappe.get_doc(doctype, name)
		for key, value in values.items():
			doc.set(key, value)
		doc.save(ignore_permissions=True)
		return doc
	doc = frappe.get_doc({"doctype": doctype, **values})
	if doc.meta.has_field("title") and not doc.get("title"):
		doc.title = name
	doc.insert(ignore_permissions=True)
	return doc


def seed_defaults():
	for privacy in ("Public", "Private Shared", "Private"):
		if not frappe.db.exists("Privacy", privacy):
			frappe.get_doc({"doctype": "Privacy", "title": privacy}).insert(ignore_permissions=True)

	if not frappe.db.exists("Plan", "Free"):
		frappe.get_doc({
			"doctype": "Plan", "title": "Free", "plan_code": "free", "status": "Active",
			"is_default": 1, "is_free": 1, "monthly_price": "0", "site_limit": "1",
			"bench_policy": "Shared Bench",
			"description": "Free self-service starter plan for first LensCloud Site creation.",
		}).insert(ignore_permissions=True)

	if not frappe.db.exists("Region", "EU"):
		frappe.get_doc({"doctype": "Region", "title": "EU", "is_group": 0, "deployment_status": "Active"}).insert(ignore_permissions=True)

	cluster = upsert_doc("Cluster", "lenscloud-eu-dev", {
		"title": "lenscloud-eu-dev", "cluster_name": "lenscloud-eu-dev", "region": "EU",
		"provider": "Hcloud", "environment": "Development", "status": "Active",
		"manager_host": "lenscloud-eu-manager-1", "manager_public_ip": "116.203.22.81",
		"manager_private_ip": "10.20.1.1", "headlamp_url": "https://headlamp.cloud.lmnaslens.com",
		"access_method": "Restricted Kubernetes API kubeconfig mounted server-side",
		"kubeconfig_reference": "file:/run/secrets/lenscloud-eu.kubeconfig",
		"credential_reference": "mounted-secret:lenscloud-eu.kubeconfig",
		"operator_namespace": "frappe-operator-system", "default_runtime_namespace": "lenscloud-runtime-eu",
		"default_storage_class": "local-path", "default_bench_namespace_pattern": "bench-{bench}",
		"health_status": "Healthy", "domain_strategy": "Wildcard",
		"wildcard_dns_status": "Ready", "wildcard_tls_status": "Ready", "ingress_status": "Ready",
		"ingress_class": "traefik", "wildcard_hostname": "*.cloud.lmnaslens.com",
	})

	region = frappe.get_doc("Region", "EU")
	if region.get("cluster") != cluster.name or region.deployment_status != "Active":
		region.cluster = cluster.name; region.deployment_status = "Active"; region.save(ignore_permissions=True)

	settings = frappe.get_single("Platform Settings")
	for key, value in {
		"default_plan": "Free", "root_domain": "cloud.lmnaslens.com", "domain_strategy": "Wildcard",
		"wildcard_dns_status": "Ready", "wildcard_tls_status": "Ready", "ingress_status": "Ready",
		"operator_namespace": "frappe-operator-system", "default_storage_class": "local-path",
		"default_bench_namespace_pattern": "bench-{bench}", "dns_automation_enabled": 0, "route53_apply_enabled": 0,
	}.items():
		settings.set(key, value)
	settings.save(ignore_permissions=True)

	if frappe.db.exists("DocType", "Database Server"):
		upsert_doc("Database Server", "EU Shared MariaDB 01", {
			"title": "EU Shared MariaDB 01", "database_engine": "MariaDB", "provisioning_type": "Operator Managed",
			"region": "EU", "privacy": "Public", "kubernetes_namespace": "default",
			"operator_resource_name": "frappe-mariadb", "image": "mariadb:10.11",
			"storage_class": "local-path", "storage_size": "8Gi", "replica_count": 1,
			"service_port": 3306, "root_credential_secret_reference": "frappe-mariadb-root",
			"root_credential_secret_key": "password", "node_placement_policy": '{"nodeSelector":{"lenscloud.io/node-role":"worker"}}',
			"database_status": "Ready", "provisioning_status": "Ready", "health_status": "Healthy",
			"maximum_bench_count": 0,
		})
