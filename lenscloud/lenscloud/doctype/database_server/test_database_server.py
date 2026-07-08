# Copyright (c) 2026, LMNAs Cloud Solutions and contributors

from types import SimpleNamespace
from unittest.mock import Mock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from lenscloud.api.kubernetes_client import KubernetesClientError
from lenscloud.api.orchestration import (
	CUSTOMER_LABEL,
	PLATFORM_MANAGER_LABEL,
	RESOURCE_ID_LABEL,
	RESOURCE_KIND_LABEL,
	build_database_server_manifest_data,
	build_frappebench_manifest_data,
	build_frappesite_manifest_data,
	check_cluster_permissions,
	check_site_route,
	delete_bench,
	delete_database_server,
	dry_run_result,
	frappe_major,
	remaining_required_dependents,
	slugify,
	sync_runtime_namespaces,
	validate_cluster_readiness,
	validate_database_server_placement_doc,
	validate_runtime_owner,
	validate_runtime_namespace_placement_doc,
	warning_event_summary,
)


def bench(**values):
	defaults = dict(name="bench-a", region="EU", cluster="eu", privacy="Public", owner_customer=None, privacy_boundary=None)
	defaults.update(values)
	return SimpleNamespace(**defaults)


def database(**values):
	defaults = dict(name="db-a", region="EU", cluster="eu", privacy="Public", owner_customer=None, privacy_boundary=None, database_status="Ready", health_status="Healthy", maximum_bench_count=0)
	defaults.update(values)
	return SimpleNamespace(**defaults)


class TestDatabaseServer(FrappeTestCase):
	def test_operator_resource_slug(self):
		self.assertEqual(slugify("EU Shared MariaDB 01"), "eu-shared-mariadb-01")

	def test_release_version_normalizes_to_frappe_major(self):
		self.assertEqual(frappe_major("v15.91.2"), "15")

	@patch("lenscloud.lenscloud.doctype.database_server.database_server.frappe.db.count", return_value=0)
	@patch("lenscloud.lenscloud.doctype.database_server.database_server.get_region_cluster", return_value=SimpleNamespace(name="eu-test", default_runtime_namespace="lenscloud-runtime-eu", default_storage_class="local-path"))
	def test_new_platform_database_cannot_use_default_namespace(self, _cluster, _count):
		from lenscloud.lenscloud.doctype.database_server.database_server import DatabaseServer

		doc = DatabaseServer({
			"doctype": "Database Server",
			"title": "EU Test Private MariaDB",
			"region": "EU Test",
			"provisioning_type": "Operator Managed",
			"operator_resource_name": "eu-test-private-mariadb",
			"kubernetes_namespace": "default",
			"privacy": "Private",
			"privacy_boundary": "customer-a",
		})
		with self.assertRaises(frappe.ValidationError):
			doc.validate()

	@patch("lenscloud.lenscloud.doctype.database_server.database_server.frappe.db.count", return_value=0)
	@patch("lenscloud.lenscloud.doctype.database_server.database_server.get_region_cluster", return_value=SimpleNamespace(name="eu-test", default_runtime_namespace="lenscloud-runtime-eu", default_storage_class="local-path"))
	def test_new_platform_database_rejects_misspelled_runtime_namespace(self, _cluster, _count):
		from lenscloud.lenscloud.doctype.database_server.database_server import DatabaseServer

		doc = DatabaseServer({
			"doctype": "Database Server",
			"title": "EU Test Private MariaDB",
			"region": "EU Test",
			"provisioning_type": "Operator Managed",
			"operator_resource_name": "eu-test-private-mariadb",
			"kubernetes_namespace": "lenscould-runtime-eu",
			"privacy": "Private",
			"privacy_boundary": "customer-a",
		})
		with self.assertRaises(frappe.ValidationError):
			doc.validate()

	@patch("lenscloud.lenscloud.doctype.database_server.database_server.frappe.db.count", return_value=0)
	@patch("lenscloud.lenscloud.doctype.database_server.database_server.get_region_cluster", return_value=SimpleNamespace(name="eu-test", default_runtime_namespace="lenscloud-runtime-eu", default_storage_class="local-path"))
	def test_protected_shared_database_can_register_default_namespace(self, _cluster, _count):
		from lenscloud.lenscloud.doctype.database_server.database_server import DatabaseServer

		doc = DatabaseServer({
			"doctype": "Database Server",
			"title": "EU Test Shared MariaDB",
			"region": "EU Test",
			"provisioning_type": "Operator Managed",
			"operator_resource_name": "frappe-mariadb",
			"kubernetes_namespace": "default",
			"privacy": "Public",
		})
		doc.validate()
		self.assertEqual(doc.kubernetes_namespace, "default")

	@patch("lenscloud.api.orchestration.frappe.get_all", return_value=[])
	@patch("lenscloud.api.orchestration.get_region_cluster", return_value=SimpleNamespace(name="eu"))
	def test_public_database_accepts_compatible_bench(self, _cluster, _attached):
		self.assertTrue(validate_database_server_placement_doc(bench(), database()))

	@patch("lenscloud.api.orchestration.frappe.get_all", return_value=[])
	@patch("lenscloud.api.orchestration.get_region_cluster", return_value=SimpleNamespace(name="eu"))
	def test_private_shared_rejects_cross_boundary_bench(self, _cluster, _attached):
		with self.assertRaises(frappe.ValidationError):
			validate_database_server_placement_doc(
				bench(privacy="Private Shared", privacy_boundary="customer-b"),
				database(privacy="Private Shared", privacy_boundary="customer-a"),
			)

	@patch("lenscloud.api.orchestration.frappe.get_all", return_value=[SimpleNamespace(name="bench-existing", owner_customer="customer-a", privacy_boundary="customer-a")])
	@patch("lenscloud.api.orchestration.get_region_cluster", return_value=SimpleNamespace(name="eu"))
	def test_private_database_rejects_second_bench(self, _cluster, _attached):
		with self.assertRaises(frappe.ValidationError):
			validate_database_server_placement_doc(
				bench(privacy="Private", privacy_boundary="customer-a"),
				database(privacy="Private", privacy_boundary="customer-a"),
			)

	@patch("lenscloud.api.orchestration.requests.get")
	def test_route_requires_page_and_generated_asset(self, get):
		page = Mock(status_code=200, text='<link rel="stylesheet" href="/assets/frappe/dist/css/website.bundle.css">', url="https://site.example/")
		asset = Mock(status_code=200, url="https://site.example/assets/frappe/dist/css/website.bundle.css")
		get.side_effect = [page, asset]
		result = check_site_route(SimpleNamespace(access_url="https://site.example"))
		self.assertEqual(result["asset_status_code"], 200)

	@patch("lenscloud.api.orchestration.requests.get")
	def test_route_rejects_page_without_generated_asset(self, get):
		get.return_value = Mock(status_code=200, text='<link rel="icon" href="/assets/frappe/images/frappe-favicon.svg">', url="https://site.example/")
		with self.assertRaises(RuntimeError):
			check_site_route(SimpleNamespace(access_url="https://site.example"))


	def test_retain_policy_allows_owned_pvc_to_remain(self):
		inventory = {"related": {"PersistentVolumeClaim": [{"metadata": {"name": "db-a-data"}}]}}
		self.assertEqual(
			remaining_required_dependents(SimpleNamespace(doctype="Database Server", data_retention_policy="Retain"), inventory),
			[],
		)

	def test_delete_policy_waits_for_owned_pvc_cleanup(self):
		inventory = {"related": {"PersistentVolumeClaim": [{"metadata": {"name": "db-a-data"}}]}}
		self.assertEqual(
			remaining_required_dependents(SimpleNamespace(doctype="Database Server", data_retention_policy="Delete"), inventory),
			[("PersistentVolumeClaim", "db-a-data")],
		)

class ReleaseGroupStub(SimpleNamespace):
	def get(self, key):
		return getattr(self, key, None)


def cluster(**values):
	defaults = dict(name="eu", default_runtime_namespace="lenscloud-runtime-eu", default_storage_class="local-path", default_bench_namespace_pattern="lenscloud-runtime-eu", ingress_class="traefik")
	defaults.update(values)
	return SimpleNamespace(**defaults)


def db_doc(**values):
	defaults = dict(
		doctype="Database Server",
		name="db-a",
		title="DB A",
		provisioning_type="Operator Managed",
		region="EU",
		cluster="eu",
		privacy="Private Shared",
		owner_customer="customer-a",
		privacy_boundary="customer-a",
		operator_resource_name="db-a",
		kubernetes_namespace="lenscloud-runtime-eu",
		root_credential_secret_reference="db-a-root",
		root_credential_secret_key="password",
		image="mariadb:10.11",
		storage_size="8Gi",
		storage_class="local-path",
		replica_count=1,
		service_port=3306,
		node_placement_policy=None,
		provisioning_status="Ready",
		database_status="Ready",
		health_status="Healthy",
		last_error=None,
	)
	defaults.update(values)
	return SimpleNamespace(**defaults)


def bench_doc(**values):
	defaults = dict(
		doctype="Bench",
		name="bench-a",
		title="Bench A",
		region="EU",
		cluster="eu",
		privacy="Private Shared",
		owner_customer="customer-a",
		privacy_boundary="customer-a",
		database_server="db-a",
		current_release="release-a",
		release_group="lens-pure",
		operator_resource_name="bench-a",
		kubernetes_namespace="lenscloud-runtime-eu",
		storage_class="local-path",
		bench_status="Ready",
		cluster_derivation_note=None,
	)
	defaults.update(values)
	return SimpleNamespace(**defaults)


def site_doc(**values):
	defaults = dict(
		doctype="Site",
		name="site-a.cloud.lmnaslens.com",
		title="site-a.cloud.lmnaslens.com",
		customer="customer-a",
		bench="bench-a",
		region="EU",
		cluster="eu",
		subdomain="site-a",
		domain="cloud.lmnaslens.com",
		operator_resource_name="site-a",
		admin_password_secret_reference="site-a-admin-password",
		access_url="https://site-a.cloud.lmnaslens.com",
		site_status="Ready",
		provisioning_status="Ready",
		last_error=None,
	)
	defaults.update(values)
	return SimpleNamespace(**defaults)


class TestActionGuidance(FrappeTestCase):
	def action_log(self):
		return SimpleNamespace(name="ORCH-2026-99999", status="Pending", message=None, error=None, last_transition_time=None, save=Mock())

	def test_selected_dry_run_says_no_resource_was_created(self):
		result = dry_run_result(self.action_log(), "manifest", SimpleNamespace(name="eu"), "MariaDB", True, True)
		self.assertEqual(result["status"], "dry_run")
		self.assertIn("Dry run was selected", result["message"])
		self.assertIn("no Kubernetes resource was created", result["message"])

	def test_disabled_apply_has_distinct_recovery(self):
		result = dry_run_result(self.action_log(), "manifest", SimpleNamespace(name="eu"), "MariaDB", False, False)
		self.assertIn("Kubernetes apply is disabled", result["message"])
		self.assertIn("Enable Kubernetes apply", result["next_actions"][0])


class TestRuntimeLifecycle(FrappeTestCase):
	@patch("lenscloud.api.orchestration.get_region_cluster", return_value=cluster())
	def test_database_manifest_carries_platform_ownership_labels(self, _cluster):
		manifest = build_database_server_manifest_data(db_doc())
		labels = manifest["metadata"]["labels"]
		self.assertEqual(labels[PLATFORM_MANAGER_LABEL], "platform")
		self.assertEqual(labels[RESOURCE_KIND_LABEL], "database-server")
		self.assertEqual(labels[RESOURCE_ID_LABEL], "db-a")
		self.assertEqual(labels[CUSTOMER_LABEL], "customer-a")

	@patch("lenscloud.api.orchestration.release_group_apps", return_value=[])
	@patch("lenscloud.api.orchestration.get_release_image")
	@patch("lenscloud.api.orchestration.validate_database_server_placement_doc", return_value=True)
	@patch("lenscloud.api.orchestration.frappe.get_doc")
	@patch("lenscloud.api.orchestration.get_region_cluster", return_value=cluster())
	def test_bench_manifest_carries_platform_ownership_labels(self, _cluster, get_doc, _validate, get_release_image, _apps):
		get_doc.return_value = db_doc()
		get_release_image.return_value = (SimpleNamespace(image_tag="v16.14.1"), ReleaseGroupStub(supported_frappe_major_version="16"), "ghcr.io/lens/lens-pure")
		manifest = build_frappebench_manifest_data(bench_doc())
		labels = manifest["metadata"]["labels"]
		self.assertEqual(labels[PLATFORM_MANAGER_LABEL], "platform")
		self.assertEqual(labels[RESOURCE_KIND_LABEL], "bench")
		self.assertEqual(labels[RESOURCE_ID_LABEL], "bench-a")
		self.assertEqual(labels[CUSTOMER_LABEL], "customer-a")

	@patch("lenscloud.api.orchestration.frappe.get_doc")
	@patch("lenscloud.api.orchestration.get_region_cluster", return_value=cluster())
	def test_site_manifest_carries_platform_ownership_labels(self, _cluster, get_doc):
		get_doc.return_value = bench_doc()
		manifest = build_frappesite_manifest_data(site_doc())
		labels = manifest["metadata"]["labels"]
		self.assertEqual(labels[PLATFORM_MANAGER_LABEL], "platform")
		self.assertEqual(labels[RESOURCE_KIND_LABEL], "site")
		self.assertEqual(labels[RESOURCE_ID_LABEL], "site-a-cloud-lmnaslens-com")
		self.assertEqual(labels[CUSTOMER_LABEL], "customer-a")

	def test_warning_event_summary_redacts_secret_like_values(self):
		summary = warning_event_summary({"type": "Warning", "reason": "Failed", "message": "password: super-secret-token", "metadata": {"name": "evt"}})
		self.assertNotIn("super-secret-token", summary["message"])
		self.assertIn("[REDACTED]", summary["message"])

	def test_unlabelled_runtime_owner_is_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			validate_runtime_owner({"metadata": {"name": "site-a", "namespace": "lenscloud-runtime-eu", "labels": {}}}, site_doc(), "site")

	@patch("lenscloud.api.orchestration.frappe.get_all", return_value=[SimpleNamespace(name="site-a", site_status="Ready")])
	@patch("lenscloud.api.orchestration.frappe.get_doc", return_value=bench_doc())
	def test_bench_delete_rejects_active_sites(self, _get_doc, _get_all):
		with self.assertRaises(frappe.ValidationError):
			delete_bench("bench-a", "bench-a")

	@patch("lenscloud.api.orchestration.create_action_log")
	@patch("lenscloud.api.orchestration.get_region_cluster", return_value=cluster(default_runtime_namespace="lenscloud-runtime-eu"))
	@patch("lenscloud.api.orchestration.frappe.get_all", return_value=[])
	@patch("lenscloud.api.orchestration.frappe.get_doc")
	def test_database_delete_rejects_protected_default_mariadb(self, get_doc, _get_all, _cluster, create_log):
		doc = db_doc(name="frappe-mariadb", operator_resource_name="frappe-mariadb", kubernetes_namespace="default")
		doc.set = lambda field, value: setattr(doc, field, value)
		doc.save = Mock()
		get_doc.return_value = doc
		create_log.return_value = SimpleNamespace(name="ORCH-2026-99998", status="Pending", message=None, error=None, last_transition_time=None, save=Mock())
		with self.assertRaises(frappe.ValidationError):
			delete_database_server("frappe-mariadb", "frappe-mariadb")

	@patch("lenscloud.api.orchestration.get_cluster_client")
	@patch("lenscloud.api.orchestration.frappe.get_doc", return_value=SimpleNamespace(name="eu", default_runtime_namespace="lenscloud-runtime-eu", kubeconfig_reference="file:/run/secrets/lenscloud-eu.kubeconfig"))
	def test_permission_preflight_uses_python_client_contract(self, _get_doc, get_cluster_client):
		client = get_cluster_client.return_value.__enter__.return_value
		client.can_i.side_effect = lambda verb, group, resource, namespace=None: (False, "denied") if (verb, resource) in {("list", "secrets"), ("delete", "namespaces"), ("delete", "customresourcedefinitions"), ("get", "pods")} or namespace == "default" and verb in {"patch", "delete"} else (True, "allowed")
		result = check_cluster_permissions("eu")
		self.assertTrue(result["all_required_allowed"])
		self.assertTrue(result["all_denied_blocked"])
		self.assertFalse(result["kubectl_required"])

	@patch("lenscloud.api.orchestration.requests.get")
	@patch("lenscloud.api.orchestration.kubeconfig_path", return_value="/run/secrets/lenscloud-eu-test.kubeconfig")
	@patch("lenscloud.api.orchestration.get_cluster_client")
	@patch("lenscloud.api.orchestration.get_platform_settings", return_value=SimpleNamespace(root_domain="testcloud.lmnaslens.com", kubernetes_apply_enabled=False))
	@patch("lenscloud.api.orchestration.frappe.db.get_value", return_value="eu-test")
	@patch("lenscloud.api.orchestration.frappe.get_doc")
	@patch("lenscloud.api.orchestration.require_platform_operator")
	def test_cluster_readiness_gates_use_python_client_and_block_without_dry_run_records(self, _role, get_doc, _region_cluster, _settings, get_cluster_client, _kubeconfig, http_get):
		cluster_doc = SimpleNamespace(
			name="eu-test",
			region="EU Test",
			default_runtime_namespace="lenscloud-runtime-eu",
			kubeconfig_reference="file:/run/secrets/lenscloud-eu-test.kubeconfig",
			ingress_class="traefik",
			headlamp_url="https://headlamp.testcloud.lmnaslens.com",
			status="Active",
			health_status="Unknown",
			save=Mock(),
		)
		get_doc.return_value = cluster_doc
		client = get_cluster_client.return_value.__enter__.return_value
		client.request.side_effect = lambda method, request_path, **_kwargs: {
			"/version": {"gitVersion": "v1.33.0"},
			"/apis/vyogo.tech/v1": {"resources": [{"name": "frappebenches"}, {"name": "frappesites"}]},
			"/apis/k8s.mariadb.com/v1alpha1": {"resources": [{"name": "mariadbs"}]},
		}.get(request_path, {})
		client.get_custom_resource.return_value = {"status": {"phase": "Ready"}}
		client.list_custom_resources.return_value = []
		client.list_namespaced.return_value = []
		client.can_i.side_effect = lambda verb, group, resource, namespace=None: (False, "denied") if (verb, resource) in {("list", "secrets"), ("delete", "namespaces"), ("delete", "customresourcedefinitions")} or namespace == "default" and verb in {"patch", "delete"} else (True, "allowed")
		http_get.return_value = SimpleNamespace(status_code=200)
		result = validate_cluster_readiness("eu-test")
		self.assertFalse(result["kubectl_required"])
		self.assertFalse(result["all_gates_passed"])
		self.assertFalse(result["apply_allowed"])
		self.assertIn("dry-run-manifests", {gate["key"] for gate in result["gates"] if not gate["passed"]})
		client.list_custom_resources.assert_any_call("FrappeBench", "lenscloud-runtime-eu")
		client.list_namespaced.assert_any_call("ingresses", "lenscloud-runtime-eu", group="networking.k8s.io", version="v1")

	@patch("lenscloud.api.orchestration.frappe.db.exists", return_value=None)
	@patch("lenscloud.api.orchestration.frappe.get_doc")
	@patch("lenscloud.api.orchestration.get_cluster_client")
	@patch("lenscloud.api.orchestration.require_platform_operator")
	def test_sync_runtime_namespaces_falls_back_to_runtime_probe_when_namespace_list_denied(self, _role, get_cluster_client, get_doc, _exists):
		cluster_doc = cluster(name="eu-test", default_runtime_namespace="lenscloud-runtime-eu", save=Mock())
		created = []

		def get_doc_side_effect(*args, **_kwargs):
			if args and args[0] == "Cluster":
				return cluster_doc
			doc = SimpleNamespace(**args[0], name=args[0]["namespace"], save=Mock())
			doc.insert = Mock(side_effect=lambda ignore_permissions=True: created.append(doc))
			return doc

		get_doc.side_effect = get_doc_side_effect
		client = get_cluster_client.return_value.__enter__.return_value
		client.request.side_effect = KubernetesClientError("Kubernetes API 403: namespace list forbidden")
		client.list_custom_resources.return_value = []
		result = sync_runtime_namespaces("eu-test")
		self.assertEqual(result["synced"], ["lenscloud-runtime-eu"])
		self.assertEqual(created[0].source, "Cluster Runtime Probe")
		client.list_custom_resources.assert_called_once_with("FrappeBench", "lenscloud-runtime-eu")

	@patch("lenscloud.api.orchestration.frappe.db.exists", return_value=None)
	@patch("lenscloud.api.orchestration.frappe.get_doc")
	@patch("lenscloud.api.orchestration.get_cluster_client")
	@patch("lenscloud.api.orchestration.require_platform_operator")
	def test_sync_runtime_namespaces_filters_cluster_namespace_list_to_platform_targets(self, _role, get_cluster_client, get_doc, _exists):
		cluster_doc = cluster(name="eu-test", region="EU Test", cluster_name="lenscloud-eu-test", default_runtime_namespace="lenscloud-runtime-eu", save=Mock())
		created = []

		def get_doc_side_effect(*args, **_kwargs):
			if args and args[0] == "Cluster":
				return cluster_doc
			doc = SimpleNamespace(**args[0], name=args[0]["namespace"], save=Mock())
			doc.insert = Mock(side_effect=lambda ignore_permissions=True: created.append(doc))
			return doc

		get_doc.side_effect = get_doc_side_effect
		client = get_cluster_client.return_value.__enter__.return_value
		client.request.return_value = {"items": [
			{"metadata": {"name": "kube-system"}, "status": {"phase": "Active"}},
			{"metadata": {"name": "lenscloud-runtime-eu"}, "status": {"phase": "Active"}},
			{"metadata": {"name": "lenscloud-half-labelled", "labels": {"lenscloud.io/runtime-namespace": "true"}}, "status": {"phase": "Active"}},
			{"metadata": {"name": "lenscloud-enterprise-acme", "labels": {"lenscloud.io/runtime-namespace": "true", "lenscloud.io/managed-by": "platform", "lenscloud.io/customer": "customer-a", "lenscloud.io/runtime-purpose": "enterprise", "lenscloud.io/region": "EU Test", "lenscloud.io/cluster": "lenscloud-eu-test"}}, "status": {"phase": "Active"}},
		]}
		result = sync_runtime_namespaces("eu-test")
		self.assertEqual(result["synced"], ["lenscloud-runtime-eu", "lenscloud-enterprise-acme"])
		self.assertEqual([doc.namespace for doc in created], ["lenscloud-runtime-eu", "lenscloud-enterprise-acme"])
		enterprise = created[1]
		self.assertEqual(enterprise.customer, "customer-a")
		self.assertEqual(enterprise.runtime_purpose, "enterprise")
		self.assertEqual(enterprise.region, "EU Test")
		self.assertEqual(enterprise.cluster_label, "lenscloud-eu-test")
		self.assertEqual(enterprise.approved_for_platform, 1)
		self.assertEqual(enterprise.verification_status, "Verified")

	@patch("lenscloud.api.orchestration.frappe.get_doc")
	@patch("lenscloud.api.orchestration.frappe.db.exists", return_value=True)
	def test_runtime_namespace_placement_rejects_cross_customer_namespace(self, _exists, get_doc):
		get_doc.return_value = SimpleNamespace(
			name="lenscloud-enterprise-acme",
			cluster="eu",
			region="EU",
			status="Active",
			approved_for_platform=1,
			runtime_purpose="enterprise",
			customer="customer-a",
		)
		with self.assertRaises(frappe.ValidationError):
			validate_runtime_namespace_placement_doc(
				db_doc(kubernetes_namespace="lenscloud-enterprise-acme", owner_customer="customer-b", privacy_boundary="customer-b", privacy="Private"),
				cluster(name="eu"),
			)

	@patch("lenscloud.api.orchestration.frappe.get_doc")
	@patch("lenscloud.api.orchestration.frappe.db.exists", return_value=True)
	def test_runtime_namespace_placement_accepts_matching_customer_enterprise_namespace(self, _exists, get_doc):
		get_doc.return_value = SimpleNamespace(
			name="lenscloud-enterprise-acme",
			cluster="eu",
			region="EU",
			status="Active",
			approved_for_platform=1,
			runtime_purpose="enterprise",
			customer="customer-a",
		)
		self.assertTrue(validate_runtime_namespace_placement_doc(
			db_doc(kubernetes_namespace="lenscloud-enterprise-acme", owner_customer="customer-a", privacy_boundary="customer-a", privacy="Private"),
			cluster(name="eu"),
		))
