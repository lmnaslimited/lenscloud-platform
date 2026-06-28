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

	def test_connection_failure_next_action_points_to_api_authorization(self):
		message = bench_command.failure_next_action(Exception("Max retries exceeded with url: /api/v1/namespaces/x/configmaps"))
		self.assertIn("Kubernetes API is reachable", message)
		self.assertIn("52-authorize-platform-api.sh --watch", message)
