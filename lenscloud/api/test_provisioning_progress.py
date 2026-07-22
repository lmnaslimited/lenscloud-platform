from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from lenscloud.api.messages import resolve_message, safe_params
from lenscloud.api.provisioning_progress import advance_customer_site_provisioning, get_customer_site_progress, progress_snapshot
from lenscloud.api.provisioning_realtime import publish_customer_site_progress


class FakeSite(frappe._dict):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.setdefault("provisioning_status", "Ready")
		self.setdefault("site_status", "Ready")

	def save(self, ignore_permissions=False):
		self.saved = True

	def reload(self):
		return None


class TestProvisioningProgress(FrappeTestCase):
	def test_message_resolver_matches_runner_failure(self):
		message = resolve_message(operation="site_setup.status", error="phase: Failed; code: RUNNER_FAILED", source="Runner")
		self.assertEqual(message["message_id"], "LC-INFRA-RUNNER-0002")
		self.assertEqual(message["resolution_owner"], "Infra")
		self.assertIn("site_setup.status", message["operator_message"])

	def test_message_params_drop_secrets(self):
		self.assertEqual(safe_params({"command": "oauth.configure", "client_secret": "hidden"}), {"command": "oauth.configure"})

	def test_read_only_endpoint_only_loads_and_renders(self):
		site = FakeSite(name="read-only.test", customer="CUST-1", route_status="Pending", access_url="https://read-only.test", provisioning_status="Running", site_status="Provisioning", modified="now")
		with patch("lenscloud.api.provisioning_progress.require_customer_site", return_value=site), patch("lenscloud.api.provisioning_progress.frappe.get_all", return_value=[]) as get_all:
			result = get_customer_site_progress(site.name)
		self.assertEqual(result["stage"], "route_pending")
		get_all.assert_called_once()

	def test_snapshot_uses_active_backend_operation(self):
		site = FakeSite(name="active.test", route_status="Ready", access_url="https://active.test", setup_status="Complete", oauth_status="Configured", modified="now")
		row = frappe._dict(name="ORCH-TEST", operation="site_bootstrap.install_apps", status="Queued", modified="now", message_id=None, customer_message=None, operator_message=None, retryability=None, resolution_owner=None)
		with patch("lenscloud.api.provisioning_progress.frappe.get_all", return_value=[row]):
			result = progress_snapshot(site)
		self.assertEqual(result["stage"], "bootstrap_installing")
		self.assertEqual(result["active_action_log"], "ORCH-TEST")

	def test_snapshot_exposes_app_aware_infra_failure(self):
		site = FakeSite(name="failed.test", route_status="Ready", access_url="https://failed.test", setup_status="Pending", oauth_status="Not Checked", modified="now")
		row = frappe._dict(
			name="ORCH-APP-AWARE-FAILED", operation="site_setup.complete", status="Failed", modified="now",
			message_id="LC-INFRA-QUEUE-0001", customer_message="Site setup is waiting for runtime capacity to recover.",
			operator_message="Target runtime background jobs did not drain in time.", retryability="Retry After Infra Action", resolution_owner="Infra",
		)
		with patch("lenscloud.api.provisioning_progress.frappe.get_all", return_value=[row]):
			result = progress_snapshot(site)
		self.assertEqual(result["stage"], "blocked_infra_action")
		self.assertEqual(result["stage_status"], "failed")
		self.assertEqual(result["message_id"], "LC-INFRA-QUEUE-0001")
		self.assertEqual(result["resolution_owner"], "Infra")
		self.assertFalse(result["can_retry"])
		self.assertFalse(result["can_continue"])

	def test_realtime_progress_is_scoped_to_active_customer_users(self):
		site = FakeSite(doctype="Site", name="realtime.test", customer="CUST-1", route_status="Ready", access_url="https://realtime.test", modified="now")
		snapshot = {"site": site.name, "stage": "route_pending", "stage_status": "pending"}
		with (
			patch("lenscloud.api.provisioning_realtime.frappe.get_all", return_value=["owner@example.com", "member@example.com"]),
			patch("lenscloud.api.provisioning_realtime.frappe.db.get_value", return_value="owner@example.com"),
			patch("lenscloud.api.provisioning_realtime.frappe.publish_realtime") as publish,
		):
			result = publish_customer_site_progress(site, snapshot=snapshot)
		self.assertEqual(result, snapshot)
		self.assertEqual(publish.call_count, 2)
		publish.assert_any_call("lenscloud_site_progress", snapshot, user="owner@example.com", after_commit=True)
		publish.assert_any_call("lenscloud_site_progress", snapshot, user="member@example.com", after_commit=True)

	def test_advance_does_not_duplicate_active_command(self):
		site = FakeSite(name="dedupe.test", route_status="Ready", access_url="https://dedupe.test")
		with patch("lenscloud.api.provisioning_progress.require_customer_site", return_value=site), patch("lenscloud.api.provisioning_progress.site_command_in_progress", side_effect=lambda _site, operation: {"status": "Queued"} if operation == "site_setup.complete" else None), patch("lenscloud.api.provisioning_progress.progress_transition", return_value={"stage": "setup_completing"}) as snapshot, patch("lenscloud.api.provisioning_progress.orchestrate_customer_site_bootstrap") as bootstrap:
			result = advance_customer_site_provisioning(site.name)
		self.assertEqual(result["stage"], "setup_completing")
		bootstrap.assert_not_called()
		snapshot.assert_called_once_with(site)

	def test_advance_runs_setup_complete_without_initial_status(self):
		site = FakeSite(name="direct-setup.test", route_status="Ready", access_url="https://direct-setup.test", setup_status="Pending")
		bootstrap = frappe._dict(status="Succeeded")
		with patch("lenscloud.api.provisioning_progress.require_customer_site", return_value=site), patch("lenscloud.api.provisioning_progress.site_command_in_progress", return_value=None), patch("lenscloud.api.provisioning_progress.latest_site_bootstrap_status", return_value=bootstrap), patch("lenscloud.api.provisioning_progress.orchestrate_customer_site_setup") as setup, patch("lenscloud.api.provisioning_progress.progress_transition", return_value={"stage": "setup_completing"}):
			advance_customer_site_provisioning(site.name)
		self.assertEqual(site.setup_status, "Required")
		setup.assert_called_once_with(site, force=0)

	def test_advance_does_not_start_oauth_before_setup_success(self):
		site = FakeSite(name="setup-running.test", route_status="Ready", access_url="https://setup-running.test", setup_status="Running", oauth_status="Pending")
		bootstrap = frappe._dict(status="Succeeded")
		with patch("lenscloud.api.provisioning_progress.require_customer_site", return_value=site), patch("lenscloud.api.provisioning_progress.site_command_in_progress", return_value=None), patch("lenscloud.api.provisioning_progress.latest_site_bootstrap_status", return_value=bootstrap), patch("lenscloud.api.provisioning_progress.orchestrate_customer_site_setup") as setup, patch("lenscloud.api.provisioning_progress.orchestrate_customer_site_oauth") as oauth, patch("lenscloud.api.provisioning_progress.progress_transition", return_value={"stage": "setup_verifying"}):
			advance_customer_site_provisioning(site.name)
		setup.assert_called_once()
		oauth.assert_not_called()
