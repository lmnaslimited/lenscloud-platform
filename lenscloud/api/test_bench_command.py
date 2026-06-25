import json
import unittest

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

