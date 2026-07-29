import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import cint

from lenscloud.www.lenscloud import get_boot


class TestRealtimeBoot(FrappeTestCase):
	def test_get_boot_has_initialized_site_context(self):
		self.assertTrue(frappe.local.site)

		boot = get_boot()

		self.assertEqual(boot.site_name, frappe.local.site)
		self.assertIsInstance(boot.socketio_port, int)
		self.assertGreater(boot.socketio_port, 0)
		self.assertTrue(boot.csrf_token)

	def test_get_boot_matches_site_configuration(self):
		boot = get_boot()
		configured_port = cint(frappe.conf.get("socketio_port") or 9000)

		self.assertEqual(boot.socketio_port, configured_port)