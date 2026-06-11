# Copyright (c) 2026, LMNAs Cloud Solutions and contributors

from types import SimpleNamespace
from unittest.mock import Mock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

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
	frappe_major,
	slugify,
	validate_database_server_placement_doc,
	validate_runtime_owner,
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

	@patch("lenscloud.api.orchestration.get_region_cluster", return_value=cluster(default_runtime_namespace="lenscloud-runtime-eu"))
	@patch("lenscloud.api.orchestration.frappe.get_all", return_value=[])
	@patch("lenscloud.api.orchestration.frappe.get_doc", return_value=db_doc(name="frappe-mariadb", operator_resource_name="frappe-mariadb", kubernetes_namespace="default"))
	def test_database_delete_rejects_protected_default_mariadb(self, _get_doc, _get_all, _cluster):
		with self.assertRaises(frappe.ValidationError):
			delete_database_server("frappe-mariadb", "frappe-mariadb")

	@patch("lenscloud.api.orchestration.get_cluster_client")
	@patch("lenscloud.api.orchestration.frappe.get_doc", return_value=SimpleNamespace(name="eu", default_runtime_namespace="lenscloud-runtime-eu", kubeconfig_reference="file:/run/secrets/lenscloud-eu.kubeconfig"))
	def test_permission_preflight_uses_python_client_contract(self, _get_doc, get_cluster_client):
		client = get_cluster_client.return_value.__enter__.return_value
		client.can_i.side_effect = lambda verb, group, resource, namespace=None: (False, "denied") if (verb, resource) in {("list", "secrets"), ("delete", "namespaces"), ("delete", "customresourcedefinitions")} or namespace == "default" and verb in {"patch", "delete"} else (True, "allowed")
		result = check_cluster_permissions("eu")
		self.assertTrue(result["all_required_allowed"])
		self.assertTrue(result["all_denied_blocked"])
		self.assertFalse(result["kubectl_required"])
