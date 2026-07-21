import frappe
from frappe.tests.utils import FrappeTestCase

from lenscloud.api.orchestration import create_action_log, finish_action_log


class TestMessageFramework(FrappeTestCase):
	def test_failed_runner_action_is_message_instance(self):
		log = create_action_log(
			"Bench Command",
			"Running",
			dry_run=False,
			resource_kind="bench-command",
			operation="site_setup.status",
		)
		finish_action_log(log, "Failed", error="phase: Failed; code: RUNNER_FAILED")
		log.reload()
		self.assertEqual(log.message_id, "LC-INFRA-RUNNER-0002")
		self.assertEqual(log.resolution_owner, "Infra")
		self.assertEqual(log.retryability, "Retry After Infra Action")
		self.assertNotIn("secret", log.message_params_json.lower())
