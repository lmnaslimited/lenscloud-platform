import json

import frappe
from frappe.tests.utils import FrappeTestCase
from types import SimpleNamespace
from unittest.mock import patch

from lenscloud.api import bench_command

from lenscloud.api.infra_messages import resolve_infra_message
from lenscloud.api.orchestration import create_action_log, finish_action_log


INFRA_RESULT_MESSAGE = {
	"message_id": "LC-INFRA-STORAGE-0001",
	"message_type": "Error",
	"source": "Runner",
	"destination": "Platform",
	"params": {
		"operation": "site_setup.status",
		"reason": "TARGET_NOT_FOUND",
		"mount_kind": "bench-sites",
	},
	"safe_summary": "Bench sites storage contract is unavailable.",
	"details_ref": None,
}


class TestInfraMessageEnvelope(FrappeTestCase):
	def test_resolves_canonical_nested_envelope_without_changing_params(self):
		envelope = resolve_infra_message(INFRA_RESULT_MESSAGE, operation="site_setup.status")
		self.assertEqual(envelope["message_id"], "LC-INFRA-STORAGE-0001")
		self.assertEqual(envelope["matched_by"], "Infra Supplied")
		self.assertEqual(envelope["params"], INFRA_RESULT_MESSAGE["params"])
		self.assertEqual(envelope["destination"], "Platform")

	def test_unknown_supplied_id_is_not_accepted_as_catalog_match(self):
		self.assertIsNone(resolve_infra_message({"message_id": "LC-INFRA-NOT-CATALOGED", "params": {}}, operation="oauth.status"))

	def test_secret_named_params_are_dropped_defensively(self):
		message = {**INFRA_RESULT_MESSAGE, "params": {**INFRA_RESULT_MESSAGE["params"], "client_secret": "must-not-leak"}}
		envelope = resolve_infra_message(message, operation="site_setup.status")
		self.assertNotIn("client_secret", envelope["params"])

	def test_failed_action_log_prefers_infra_supplied_message(self):
		log = create_action_log("Bench Command", "Running", dry_run=False, resource_kind="bench-command", operation="site_setup.status")
		finish_action_log(log, "Failed", message="legacy RUNNER_FAILED", result_message=INFRA_RESULT_MESSAGE)
		log.reload()
		self.assertEqual(log.message_id, "LC-INFRA-STORAGE-0001")
		self.assertEqual(log.matched_by, "Infra Supplied")
		self.assertEqual(json.loads(log.message_params_json), INFRA_RESULT_MESSAGE["params"])
		self.assertEqual(log.safe_summary, INFRA_RESULT_MESSAGE["safe_summary"])
		self.assertEqual(log.resolution_owner, "Infra")
		self.assertEqual(log.retryability, "Retry After Infra Action")

	def test_app_aware_job_persists_supplied_nested_message(self):
		result_message = {
			"message_id": "LC-INFRA-BOOTSTRAP-0001",
			"message_type": "Error",
			"source": "Release Runtime",
			"destination": "Platform",
			"params": {"operation": "site_bootstrap.install_apps", "reason": "APP_INSTALL_FAILED", "app": "erpnext", "exit_code": 1},
			"safe_summary": "A required Site application could not be installed.",
			"details_ref": None,
		}
		log = create_action_log("Bench Command", "Pending", dry_run=False, resource_kind="bench-command", operation="site_bootstrap.install_apps")

		class FakeClient:
			def __enter__(self):
				return self

			def __exit__(self, *_args):
				return False

			def create_namespaced(self, *_args, **_kwargs):
				return {}

		cluster = SimpleNamespace(name="cluster")
		bench = SimpleNamespace(name="bench-doc", region="EU", operator_resource_name="runtime-bench")
		site = SimpleNamespace(name="site.example.com", customer="CUST001", region="EU")
		with (
			patch("lenscloud.api.bench_command.create_action_log", return_value=log),
			patch("lenscloud.api.bench_command.get_cluster_client", return_value=FakeClient()),
			patch("lenscloud.api.bench_command.wait_for_job", return_value=("Failed", {}, [{}])),
			patch("lenscloud.api.bench_command.sanitized_termination_summary", return_value={"phase": "Failed", "message": result_message, "redacted": True}),
			patch("lenscloud.api.bench_command.schedule_command_cleanup", return_value=["cleanup scheduled"]),
		):
			result = bench_command.run_app_aware_job("site_bootstrap.install_apps", cluster, "runtime", bench, "image@sha256:" + "a" * 64, "exit 1", site_doc=site)
		log.reload()
		self.assertEqual(result["status"], "Failed")
		self.assertEqual(log.message_id, "LC-INFRA-BOOTSTRAP-0001")
		self.assertEqual(log.matched_by, "Infra Supplied")
		self.assertEqual(log.source, "Release Runtime")
		self.assertEqual(json.loads(log.message_params_json), result_message["params"])
		frappe.delete_doc("Orchestration Action Log", log.name, force=True)
		frappe.db.commit()

	def test_success_does_not_attach_failure_message(self):
		log = create_action_log("Bench Command", "Running", dry_run=False, resource_kind="bench-command", operation="site_setup.status")
		finish_action_log(log, "Succeeded", message="Setup wizard: Pending")
		log.reload()
		self.assertFalse(log.message_id)
		self.assertFalse(log.message_type)
		self.assertFalse(log.matched_by)
		self.assertFalse(log.resolution_owner)
		self.assertFalse(log.retryability)
