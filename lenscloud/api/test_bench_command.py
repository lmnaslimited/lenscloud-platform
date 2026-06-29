import json
import unittest
from types import SimpleNamespace

import frappe

from lenscloud.api import bench_command
from lenscloud.api.orchestration import PLATFORM_MANAGER_LABEL, RESOURCE_KIND_LABEL


class BenchCommandContractTest(unittest.TestCase):
	def test_bench_test_status_args_default_to_status_mode(self):
		self.assertEqual(bench_command.command_args("bench_test.status", None), {"mode": "status"})
		self.assertEqual(bench_command.command_args("bench_test.status", '{"mode":"status"}'), {"mode": "status"})

	def test_bench_test_status_rejects_other_modes(self):
		with self.assertRaises(frappe.ValidationError):
			bench_command.command_args("bench_test.status", '{"mode":"trigger"}')

	def test_timeout_is_bounded(self):
		self.assertEqual(bench_command.timeout_value(60), 60)
		for value in (1, 600):
			with self.assertRaises(frappe.ValidationError):
				bench_command.timeout_value(value)

	def test_job_manifest_uses_secret_safe_shape(self):
		labels = {
			PLATFORM_MANAGER_LABEL: "platform",
			RESOURCE_KIND_LABEL: "bench-command",
			"lenscloud.io/resource-id": "bcmd-test",
		}
		annotations = bench_command.metadata_annotations("bench_test.status", "bcmd-test-request")
		job = bench_command.job_manifest("bcmd-test-job", "lenscloud-runtime-eu", labels, annotations, "bcmd-test-request", "bench_test.status")
		spec = job["spec"]["template"]["spec"]
		container = spec["containers"][0]
		self.assertEqual(job["kind"], "Job")
		self.assertFalse(spec["automountServiceAccountToken"])
		self.assertEqual(spec["restartPolicy"], "Never")
		self.assertEqual(len(spec["containers"]), 1)
		self.assertNotIn("envFrom", container)
		self.assertNotIn("env", container)
		self.assertEqual(spec["volumes"][0]["configMap"]["name"], "bcmd-test-request")
		self.assertEqual(container["volumeMounts"][0]["name"], "request")

	def test_configmap_contains_request_json_only(self):
		request = {"apiVersion": "lenscloud.io/v1", "kind": "BenchCommand", "command": "bench_test.status"}
		labels = {PLATFORM_MANAGER_LABEL: "platform", RESOURCE_KIND_LABEL: "bench-command"}
		annotations = bench_command.metadata_annotations("bench_test.status", "bcmd-test-request")
		configmap = bench_command.configmap_manifest("bcmd-test-request", "lenscloud-runtime-eu", labels, annotations, request)
		self.assertEqual(configmap["kind"], "ConfigMap")
		self.assertEqual(set(configmap["data"]), {"request.json"})
		self.assertEqual(json.loads(configmap["data"]["request.json"])["command"], "bench_test.status")


	def test_runner_supported_command_uses_pinned_runner_and_sites_pvc(self):
		labels = {
			PLATFORM_MANAGER_LABEL: "platform",
			RESOURCE_KIND_LABEL: "bench-command",
			"lenscloud.io/resource-id": "bcmd-test",
		}
		annotations = bench_command.metadata_annotations("maintenance_mode.enable", "bcmd-test-request")
		bench = SimpleNamespace(name="bench-doc", operator_resource_name="runtime-bench")
		job = bench_command.job_manifest("bcmd-test-job", "lenscloud-runtime-eu", labels, annotations, "bcmd-test-request", "maintenance_mode.enable", bench=bench)
		spec = job["spec"]["template"]["spec"]
		container = spec["containers"][0]
		self.assertEqual(container["image"], bench_command.RUNNER_IMAGE)
		self.assertIn({"name": "BENCH_COMMAND_REQUEST", "value": "/lenscloud/request/request.json"}, container["env"])
		self.assertIn({"name": "sites", "mountPath": "/home/frappe/frappe-bench/sites"}, container["volumeMounts"])
		self.assertIn({"name": "sites", "persistentVolumeClaim": {"claimName": "runtime-bench-sites"}}, spec["volumes"])

	def test_runner_pending_commands_remain_unsupported(self):
		self.assertIn("maintenance_mode.enable", bench_command.SUPPORTED_COMMANDS)
		self.assertIn("developer_mode.status", bench_command.SUPPORTED_COMMANDS)
		self.assertIn("cors.allowlist.update", bench_command.SUPPORTED_COMMANDS)
		self.assertNotIn("backup.create", bench_command.SUPPORTED_COMMANDS)
		self.assertNotIn("restore.execute", bench_command.SUPPORTED_COMMANDS)
		self.assertNotIn("bench_test.trigger", bench_command.SUPPORTED_COMMANDS)
		self.assertNotIn("latp.trigger", bench_command.SUPPORTED_COMMANDS)

	def test_site_config_args_reject_unapproved_keys(self):
		with self.assertRaises(frappe.ValidationError):
			bench_command.command_args("site_config.get", {"key": "db_password"})
		self.assertEqual(bench_command.command_args("site_config.set", {"key": "server_script_enabled", "value": 1}), {"key": "server_script_enabled", "value": 1})

	def test_cors_args_reject_wildcard_origin(self):
		with self.assertRaises(frappe.ValidationError):
			bench_command.command_args("cors.allowlist.update", {"origins": ["*"]})
		self.assertEqual(bench_command.command_args("cors.allowlist.update", {"origins": ["https://example.com", "https://example.com"]}), {"origins": ["https://example.com"]})


	def test_safe_display_uses_top_level_safe_display_only(self):
		summary = {
			"phase": "Succeeded",
			"summary": "Read maintenance_mode status",
			"details": {"key": "maintenance_mode", "value": 0},
			"display": {"label": "Maintenance mode", "value": "Off", "kind": "boolean", "rawValue": 0, "safe": True},
		}
		display = bench_command.safe_command_display(summary)
		self.assertEqual(display["label"], "Maintenance mode")
		self.assertEqual(display["value"], "Off")
		self.assertEqual(display["kind"], "boolean")
		self.assertEqual(bench_command.command_display_text(display), "Maintenance mode: Off")

	def test_safe_display_rejects_unsafe_or_missing_display(self):
		self.assertIsNone(bench_command.safe_command_display({"display": {"label": "Token", "value": "secret", "safe": False}}))
		self.assertIsNone(bench_command.safe_command_display({"details": {"key": "maintenance_mode", "value": 1}}))
		self.assertIn("code: COMMAND_UNSUPPORTED", bench_command.sanitized_status_summary({"phase": "Unsupported", "code": "COMMAND_UNSUPPORTED", "summary": "No runner"}))

	def test_display_contract_examples(self):
		examples = [
			("developer_mode.status", {"label": "Developer mode", "value": "Off", "kind": "boolean", "safe": True}, "Developer mode: Off"),
			("site_config.get", {"label": "Server script", "value": "On", "kind": "boolean", "safe": True}, "Server script: On"),
			("cors.allowlist.get", {"label": "CORS allowlist", "value": ["https://app.example.com"], "kind": "origin-list", "safe": True}, "CORS allowlist: https://app.example.com"),
		]
		for _command, display_data, text in examples:
			with self.subTest(command=_command):
				display = bench_command.safe_command_display({"display": display_data})
				self.assertEqual(bench_command.command_display_text(display), text)

	def test_runner_target_not_found_guides_mount_contract(self):
		actions = bench_command.command_result_next_actions({"code": "TARGET_NOT_FOUND", "summary": "site_config.json was not found"})
		self.assertIn("Bench Command runner mount/path contract", actions[0])

	def test_connection_failure_next_action_points_to_api_authorization(self):
		message = bench_command.failure_next_action(Exception("Max retries exceeded with url: /api/v1/namespaces/x/configmaps"))
		self.assertIn("Kubernetes API is reachable", message)
		self.assertIn("52-authorize-platform-api.sh --watch", message)
