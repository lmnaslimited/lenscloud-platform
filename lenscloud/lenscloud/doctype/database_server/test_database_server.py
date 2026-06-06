# Copyright (c) 2026, LMNAs Cloud Solutions and contributors

from types import SimpleNamespace
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from lenscloud.api.orchestration import frappe_major, slugify, validate_database_server_placement_doc


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
