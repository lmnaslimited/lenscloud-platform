from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from lenscloud.www.lenscloud import get_boot, get_context_for_dev


class TestRealtimeBoot(FrappeTestCase):
	def test_get_boot_matches_development_site(self):
		self.assertEqual(frappe.local.site, "dev.localhost")

		boot = get_boot()

		self.assertEqual(boot.site_name, "dev.localhost")
		self.assertIsInstance(boot.socketio_port, int)
		self.assertEqual(boot.socketio_port, 9000)
		self.assertTrue(boot.csrf_token)

	def test_development_endpoint_is_disabled_outside_developer_mode(self):
		with patch.dict(frappe.conf, {"developer_mode": 0}):
			with self.assertRaises(frappe.PermissionError):
				get_context_for_dev()
