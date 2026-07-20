import base64
import json
import unittest
from unittest.mock import patch
from types import SimpleNamespace

import frappe

from lenscloud.api import bench_command
from lenscloud.api.orchestration import generate_site_encryption_key
from lenscloud.api.orchestration import PLATFORM_MANAGER_LABEL, RESOURCE_KIND_LABEL


class FakeCleanupClient:
	def __init__(self, pods):
		self.pods = list(pods)
		self.deleted = []

	def __enter__(self):
		return self

	def __exit__(self, *_args):
		return False

	def list_namespaced(self, resource, namespace, label_selector=None, group="", version="v1", field_selector=None):
		if resource != "pods":
			return []
		return list(self.pods)

	def delete_namespaced(self, resource, namespace, name, group="", version="v1"):
		self.deleted.append((resource, namespace, name, group))
		if resource == "pods":
			self.pods = [pod for pod in self.pods if (pod.get("metadata") or {}).get("name") != name]
		return {}


def pod(name, phase, labels=True):
	metadata = {"name": name}
	if labels:
		metadata["labels"] = {PLATFORM_MANAGER_LABEL: "platform", RESOURCE_KIND_LABEL: "bench-command"}
	return {"metadata": metadata, "status": {"phase": phase, "containerStatuses": []}}


class BenchCommandContractTest(unittest.TestCase):
	def test_generated_site_encryption_key_is_fernet_compatible(self):
		key = generate_site_encryption_key()
		self.assertEqual(len(key), 44)
		self.assertEqual(len(base64.urlsafe_b64decode(key.encode("ascii"))), 32)

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

	def test_app_aware_timeout_allows_install_window(self):
		self.assertEqual(bench_command.app_aware_timeout_value(900), 900)
		for value in (1, 1801):
			with self.assertRaises(frappe.ValidationError):
				bench_command.app_aware_timeout_value(value)

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


	def test_runner_image_uses_inf_026_digest(self):
		self.assertIn("sha256:0ba81c0f4031d452eab71a463a562d5f07ace308ae87967725dd807e00c97570", bench_command.RUNNER_IMAGE)

	def test_cluster_contract_runner_image_uses_synced_cluster_value(self):
		image = "ghcr.io/lmnaslimited/lenscloud-bench-command-runner@sha256:" + "a" * 64
		cluster = SimpleNamespace(name="cluster-a", bench_command_runner_image=image)
		self.assertEqual(bench_command.bench_command_runner_image(cluster), image)

	def test_cluster_contract_runner_image_rejects_mutable_tag(self):
		cluster = SimpleNamespace(name="cluster-a", bench_command_runner_image="ghcr.io/lmnaslimited/lenscloud-bench-command-runner:latest")
		with self.assertRaises(frappe.ValidationError):
			bench_command.bench_command_runner_image(cluster)

	def test_cluster_contract_runner_image_requires_sync(self):
		cluster = SimpleNamespace(name="cluster-a", bench_command_runner_image=None)
		with self.assertRaises(frappe.ValidationError):
			bench_command.bench_command_runner_image(cluster)

	def test_runner_supported_command_accepts_cluster_contract_runner(self):
		labels = {PLATFORM_MANAGER_LABEL: "platform", RESOURCE_KIND_LABEL: "bench-command", "lenscloud.io/resource-id": "bcmd-test"}
		annotations = bench_command.metadata_annotations("site_setup.status", "bcmd-test-request")
		bench = SimpleNamespace(name="bench-doc", operator_resource_name="runtime-bench")
		runner = "ghcr.io/lmnaslimited/lenscloud-bench-command-runner@sha256:" + "b" * 64
		job = bench_command.job_manifest("bcmd-test-job", "lenscloud-runtime-eu", labels, annotations, "bcmd-test-request", "site_setup.status", bench=bench, runner_image=runner)
		self.assertEqual(job["spec"]["template"]["spec"]["containers"][0]["image"], runner)

	def test_validate_cluster_runner_contract_dry_runs_synced_image(self):
		image = "ghcr.io/lmnaslimited/lenscloud-bench-command-runner@sha256:" + "c" * 64

		class FakeCluster(SimpleNamespace):
			def save(self, ignore_permissions=False):
				self.saved = True

		class FakeClient:
			def __enter__(self):
				return self

			def __exit__(self, *_args):
				return False

			def create_namespaced(self, resource, namespace, body, **kwargs):
				self.resource = resource
				self.namespace = namespace
				self.body = body
				self.kwargs = kwargs
				return {}

		cluster = FakeCluster(name="cluster-a", default_runtime_namespace="runtime-a", bench_command_runner_image=image)
		client = FakeClient()
		with patch("lenscloud.api.bench_command.frappe.only_for"), patch("lenscloud.api.bench_command.frappe.get_doc", return_value=cluster), patch("lenscloud.api.bench_command.get_cluster_client", return_value=client), patch("lenscloud.api.bench_command.now_datetime", return_value="2026-07-20 00:00:00"), patch("lenscloud.api.bench_command.frappe.db.commit"):
			result = bench_command.validate_cluster_bench_command_runner_contract("cluster-a")
		self.assertEqual(result["status"], "Accepted")
		self.assertEqual(result["bench_command_runner_image"], image)
		self.assertEqual(client.kwargs.get("dry_run"), "All")
		self.assertEqual(client.body["spec"]["template"]["spec"]["containers"][0]["image"], image)
		self.assertEqual(cluster.bench_command_runner_contract_status, "Synced")
		self.assertIsNone(cluster.bench_command_runner_contract_error)

	def test_validate_cluster_runner_contract_records_admission_failure(self):
		image = "ghcr.io/lmnaslimited/lenscloud-bench-command-runner@sha256:" + "d" * 64

		class FakeCluster(SimpleNamespace):
			def save(self, ignore_permissions=False):
				self.saved = True

		class FakeClient:
			def __enter__(self):
				return self

			def __exit__(self, *_args):
				return False

			def create_namespaced(self, *_args, **_kwargs):
				raise bench_command.KubernetesClientError("denied: approved execution image required")

		cluster = FakeCluster(name="cluster-a", default_runtime_namespace="runtime-a", bench_command_runner_image=image)
		with patch("lenscloud.api.bench_command.frappe.only_for"), patch("lenscloud.api.bench_command.frappe.get_doc", return_value=cluster), patch("lenscloud.api.bench_command.get_cluster_client", return_value=FakeClient()), patch("lenscloud.api.bench_command.now_datetime", return_value="2026-07-20 00:00:00"), patch("lenscloud.api.bench_command.frappe.db.commit"):
			with self.assertRaises(frappe.ValidationError):
				bench_command.validate_cluster_bench_command_runner_contract("cluster-a")
		self.assertEqual(cluster.bench_command_runner_contract_status, "Failed")
		self.assertIn(bench_command.RUNNER_IMAGE_REJECTED_CODE, cluster.bench_command_runner_contract_error)

	def test_runner_dry_run_maps_approved_image_rejection(self):
		class Client:
			def create_namespaced(self, *args, **kwargs):
				self.kwargs = kwargs
				raise bench_command.KubernetesClientError("denied: approved execution image required")

		client = Client()
		with self.assertRaises(bench_command.KubernetesClientError) as ctx:
			bench_command.dry_run_bench_command_job(client, "runtime", {"kind": "Job"}, bench_command.RUNNER_IMAGE)
		self.assertEqual(client.kwargs.get("dry_run"), "All")
		self.assertIn(bench_command.RUNNER_IMAGE_REJECTED_CODE, str(ctx.exception))

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
		self.assertIn({"name": "sites", "mountPath": "/home/frappe/frappe-bench/sites", "readOnly": False}, container["volumeMounts"])
		self.assertIn({"name": "sites", "persistentVolumeClaim": {"claimName": "runtime-bench-sites"}}, spec["volumes"])

	def test_site_setup_status_mounts_sites_pvc_read_only(self):
		labels = {PLATFORM_MANAGER_LABEL: "platform", RESOURCE_KIND_LABEL: "bench-command", "lenscloud.io/resource-id": "bcmd-test"}
		annotations = bench_command.metadata_annotations("site_setup.status", "bcmd-test-request")
		bench = SimpleNamespace(name="bench-doc", operator_resource_name="runtime-bench")
		job = bench_command.job_manifest("bcmd-test-job", "lenscloud-runtime-eu", labels, annotations, "bcmd-test-request", "site_setup.status", bench=bench)
		container = job["spec"]["template"]["spec"]["containers"][0]
		self.assertIn({"name": "sites", "mountPath": "/home/frappe/frappe-bench/sites", "readOnly": True}, container["volumeMounts"])

	def test_oauth_status_mounts_sites_pvc_read_only(self):
		labels = {PLATFORM_MANAGER_LABEL: "platform", RESOURCE_KIND_LABEL: "bench-command", "lenscloud.io/resource-id": "bcmd-test"}
		annotations = bench_command.metadata_annotations("oauth.status", "bcmd-test-request")
		bench = SimpleNamespace(name="bench-doc", operator_resource_name="runtime-bench")
		job = bench_command.job_manifest("bcmd-test-job", "lenscloud-runtime-eu", labels, annotations, "bcmd-test-request", "oauth.status", bench=bench)
		container = job["spec"]["template"]["spec"]["containers"][0]
		self.assertIn({"name": "sites", "mountPath": "/home/frappe/frappe-bench/sites", "readOnly": True}, container["volumeMounts"])
		self.assertNotIn("oauth-client-secret", [mount["name"] for mount in container["volumeMounts"]])

	def test_oauth_configure_mounts_only_contract_secret(self):
		labels = {PLATFORM_MANAGER_LABEL: "platform", RESOURCE_KIND_LABEL: "bench-command", "lenscloud.io/resource-id": "bcmd-test"}
		annotations = bench_command.metadata_annotations("oauth.configure", "bcmd-test-request")
		bench = SimpleNamespace(name="bench-doc", operator_resource_name="runtime-bench")
		job = bench_command.job_manifest("bcmd-test-job", "lenscloud-runtime-eu", labels, annotations, "bcmd-test-request", "oauth.configure", bench=bench, oauth_secret_name="bcmd-test-oauth-secret")
		spec = job["spec"]["template"]["spec"]
		container = spec["containers"][0]
		self.assertIn({"name": "LENS_COMMAND_OAUTH_CLIENT_SECRET_PATH", "value": "/lenscloud/secrets/client_secret"}, container["env"])
		self.assertIn({"name": "oauth-client-secret", "mountPath": "/lenscloud/secrets", "readOnly": True}, container["volumeMounts"])
		self.assertIn({"name": "oauth-client-secret", "secret": {"secretName": "bcmd-test-oauth-secret", "items": [{"key": "client_secret", "path": "client_secret"}]}}, spec["volumes"])

	def test_runner_pending_commands_remain_unsupported(self):
		self.assertIn("maintenance_mode.enable", bench_command.SUPPORTED_COMMANDS)
		self.assertIn("developer_mode.status", bench_command.SUPPORTED_COMMANDS)
		self.assertIn("cors.allowlist.update", bench_command.SUPPORTED_COMMANDS)
		self.assertIn("backup.status", bench_command.CONTRACTED_COMMANDS)
		self.assertIn("backup.status", bench_command.SUPPORTED_COMMANDS)
		self.assertIn("site_setup.status", bench_command.SUPPORTED_COMMANDS)
		self.assertIn("site_setup.complete", bench_command.CONTRACTED_COMMANDS)
		self.assertIn("site_setup.complete", bench_command.APP_AWARE_COMMANDS)
		self.assertNotIn("site_setup.complete", bench_command.RUNNER_SUPPORTED_COMMANDS)
		self.assertNotIn("site_setup.complete", bench_command.SUPPORTED_COMMANDS)
		self.assertIn("oauth.status", bench_command.SUPPORTED_COMMANDS)
		self.assertIn("oauth.configure", bench_command.SUPPORTED_COMMANDS)
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

	def test_backup_status_args_are_empty(self):
		self.assertEqual(bench_command.command_args("backup.status", {"ignored": "value"}), {})

	def test_site_setup_complete_orchestration_uses_release_runtime_job(self):
		site = SimpleNamespace(name="site.example.test", region="EU")
		bench = SimpleNamespace(name="bench-doc", current_release="REL-1", operator_resource_name="runtime-bench")
		cluster = SimpleNamespace(name="cluster-doc")
		result = {"status": "Succeeded", "action_log": "ORCH-TEST"}
		with patch("lenscloud.api.bench_command.validate_site_target", return_value=(site, bench, cluster, "lenscloud-runtime-eu", None, None)), patch("lenscloud.api.bench_command.release_runtime_image", return_value=("registry.example/lens-pure@sha256:" + "a" * 64, SimpleNamespace(name="REL-1"), SimpleNamespace(name="RG-1"))), patch("lenscloud.api.bench_command.run_app_aware_job", return_value=result) as run_job:
			out = bench_command.run_site_setup_command_for_orchestration(
				"site.example.test",
				"site_setup.complete",
				args={"language": "English", "email": "owner@example.test", "full_name": "Owner", "country": "India", "timezone": "Asia/Kolkata", "currency": "INR"},
			)
		self.assertEqual(out, result)
		run_job.assert_called_once()
		call = run_job.call_args
		self.assertEqual(call.args[0], "site_setup.complete")
		self.assertEqual(call.args[4], "registry.example/lens-pure@sha256:" + "a" * 64)
		self.assertIn("setup_complete", call.args[5])


	def test_site_setup_status_args_are_empty(self):
		self.assertEqual(bench_command.command_args("site_setup.status", {"ignored": "value"}), {})

	def test_oauth_client_app_name_uses_site_prefix_and_environment(self):
		site = SimpleNamespace(name="run-20260707-cua-oauth.cloud.lmnaslens.com", subdomain="run-20260707-cua-oauth", environment="Prod")
		self.assertEqual(bench_command.site_oauth_client_app_name(site), "run-20260707-cua-oauth-Prod")

	def test_oauth_client_allows_customer_users(self):
		class FakeOAuthClient:
			def __init__(self):
				self.allowed_roles = [SimpleNamespace(role="Desk User")]

			def append(self, fieldname, value):
				self.allowed_roles.append(SimpleNamespace(**value))

		doc = FakeOAuthClient()
		bench_command.ensure_oauth_client_customer_roles(doc)
		self.assertIn("All", {row.role for row in doc.allowed_roles})
		bench_command.ensure_oauth_client_customer_roles(doc)
		self.assertEqual([row.role for row in doc.allowed_roles].count("All"), 1)

	def test_oauth_args_are_secret_safe_and_typed(self):
		self.assertEqual(bench_command.command_args("oauth.status", {"provider": "lenscloud"}), {"provider": "lenscloud"})
		args = bench_command.command_args("oauth.configure", {
			"provider": "lenscloud",
			"provider_name": "LensCloud",
			"social_login_provider": "Custom",
			"enable_social_login": True,
			"client_id": "oauth-client",
			"client_secret_source": "mounted_file",
			"base_url": "http://dev.localhost:8000",
			"authorize_url": "/api/method/frappe.integrations.oauth2.authorize",
			"access_token_url": "/api/method/frappe.integrations.oauth2.get_token",
			"redirect_url": "https://site.example.com/api/method/frappe.integrations.oauth2_logins.custom/lenscloud",
			"api_endpoint": "/api/method/frappe.integrations.oauth2.openid_profile",
			"custom_base_url": True,
			"allow_local_oauth_http": True,
			"auth_url_data": {"response_type": "code", "scope": "openid"},
		})
		self.assertEqual(args["client_secret_source"], "mounted_file")
		self.assertTrue(args["allow_local_oauth_http"])
		self.assertNotIn("client_secret", args)
		with self.assertRaises(frappe.ValidationError):
			bench_command.command_args("oauth.configure", {"client_secret": "nope"})
		with self.assertRaises(frappe.ValidationError):
			bench_command.command_args("oauth.configure", {"provider": "Nectar Space"})

	def test_site_setup_complete_script_uses_native_setup_wizard(self):
		script = bench_command.site_setup_complete_script(
			"site.example.test",
			{"language": "English", "email": "owner@example.test", "full_name": "Owner", "country": "India", "timezone": "Asia/Kolkata", "currency": "INR"},
			{"phase": "Succeeded", "command": "site_setup.complete", "redacted": True},
		)
		self.assertIn("frappe.desk.page.setup_wizard.setup_wizard.setup_complete", script)
		self.assertIn("--site site.example.test", script)
		self.assertIn("/dev/termination-log", script)
		self.assertIn("Site setup completion failed", script)


	def test_site_setup_complete_args_are_non_secret_and_typed(self):
		args = bench_command.command_args("site_setup.complete", {
			"language": "English",
			"email": "first.user@example.com",
			"full_name": "First User",
			"country": "United States",
			"timezone": "America/New_York",
			"currency": "USD",
			"company_name": "Example Inc",
		})
		self.assertEqual(args["language"], "English")
		self.assertEqual(args["company_name"], "Example Inc")
		with self.assertRaises(frappe.ValidationError):
			bench_command.command_args("site_setup.complete", {"language": "English", "password": "secret"})
		with self.assertRaises(frappe.ValidationError):
			bench_command.command_args("site_setup.complete", {"language": "English", "raw_setup_doc": "{}"})
		with self.assertRaises(frappe.ValidationError):
			bench_command.command_args("site_setup.complete", {"language": "English"})


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

	def test_backup_status_display_preserves_safe_metadata(self):
		summary = {
			"display": {
				"label": "Backups",
				"value": "0 available",
				"kind": "backup-status",
				"rawValue": {"count": 0, "latest": None},
				"safe": True,
			}
		}
		display = bench_command.safe_command_display(summary)
		self.assertEqual(bench_command.command_display_text(display), "Backups: 0 available")
		self.assertEqual(display["rawValue"], {"count": 0, "latest": None})

	def test_safe_display_rejects_unsafe_or_missing_display(self):
		self.assertIsNone(bench_command.safe_command_display({"display": {"label": "Token", "value": "secret", "safe": False}}))
		self.assertIsNone(bench_command.safe_command_display({"details": {"key": "maintenance_mode", "value": 1}}))
		self.assertIn("code: COMMAND_UNSUPPORTED", bench_command.sanitized_status_summary({"phase": "Unsupported", "code": "COMMAND_UNSUPPORTED", "summary": "No runner"}))

	def test_remaining_families_stay_unsupported(self):
		for command in ("backup.create", "restore.preview", "restore.execute", "restore.status", "bench_test.trigger", "latp.trigger", "latp.status", "user.ensure", "user.disable", "user.roles.set", "site_access.status"):
			with self.subTest(command=command):
				self.assertIn(command, bench_command.CONTRACTED_COMMANDS)
				self.assertIn(command, bench_command.RUNNER_PENDING_COMMANDS)
				self.assertNotIn(command, bench_command.SUPPORTED_COMMANDS)

	def test_display_contract_examples(self):
		examples = [
			("developer_mode.status", {"label": "Developer mode", "value": "Off", "kind": "boolean", "safe": True}, "Developer mode: Off"),
			("site_config.get", {"label": "Server script", "value": "On", "kind": "boolean", "safe": True}, "Server script: On"),
			("cors.allowlist.get", {"label": "CORS allowlist", "value": ["https://app.example.com"], "kind": "origin-list", "safe": True}, "CORS allowlist: https://app.example.com"),
			("backup.status", {"label": "Backups", "value": "0 available", "kind": "backup-status", "safe": True}, "Backups: 0 available"),
			("site_setup.status", {"label": "Setup wizard", "value": "Pending", "kind": "setup-status", "safe": True}, "Setup wizard: Pending"),
			("oauth.status", {"label": "Social login", "value": "Enabled", "kind": "oauth-status", "safe": True}, "Social login: Enabled"),
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

	def test_cleanup_deletes_terminal_command_pods_and_verifies_absence(self):
		client = FakeCleanupClient([pod("bcmd-test-job-abc", "Succeeded")])
		with patch("lenscloud.api.bench_command.get_cluster_client", return_value=client):
			deleted = bench_command.cleanup_command_resources(SimpleNamespace(name="cluster"), "lenscloud-runtime-eu", "bcmd-test-job", "bcmd-test-request", pod_wait_seconds=0, secret_name="bcmd-test-secret")
		self.assertIn("secrets/lenscloud-runtime-eu/bcmd-test-secret", deleted)
		self.assertIn("pods/lenscloud-runtime-eu/bcmd-test-job-abc", deleted)
		self.assertIn("jobs/lenscloud-runtime-eu/bcmd-test-job", deleted)
		self.assertIn("configmaps/lenscloud-runtime-eu/bcmd-test-request", deleted)

	def test_cleanup_refuses_to_hide_active_command_pods(self):
		client = FakeCleanupClient([pod("bcmd-test-job-active", "Running")])
		with patch("lenscloud.api.bench_command.get_cluster_client", return_value=client):
			with self.assertRaises(bench_command.KubernetesClientError):
				bench_command.cleanup_command_resources(SimpleNamespace(name="cluster"), "lenscloud-runtime-eu", "bcmd-test-job", "bcmd-test-request", pod_wait_seconds=0)

	def test_cleanup_refuses_unlabelled_terminal_command_pods(self):
		client = FakeCleanupClient([pod("bcmd-test-job-unsafe", "Succeeded", labels=False)])
		with patch("lenscloud.api.bench_command.get_cluster_client", return_value=client):
			with self.assertRaises(bench_command.KubernetesClientError):
				bench_command.cleanup_command_resources(SimpleNamespace(name="cluster"), "lenscloud-runtime-eu", "bcmd-test-job", "bcmd-test-request", pod_wait_seconds=0)
		self.assertNotIn(("pods", "lenscloud-runtime-eu", "bcmd-test-job-unsafe", ""), client.deleted)

	def test_app_aware_job_uses_bench_command_action_type(self):
		created = {}

		class FakeLog:
			name = "ORCH-APP-AWARE"
			manifest = ""
			message = ""
			status = "Pending"

			def save(self, ignore_permissions=False):
				return None

		class FakeClient:
			def __enter__(self):
				return self

			def __exit__(self, *_args):
				return False

			def create_namespaced(self, *_args, **_kwargs):
				return {}

		def fake_create_action_log(action_type, *args, **kwargs):
			created["action_type"] = action_type
			created["operation"] = kwargs.get("operation")
			return FakeLog()

		cluster = SimpleNamespace(name="cluster")
		bench = SimpleNamespace(name="bench-doc", region="EU", operator_resource_name="runtime-bench")
		site = SimpleNamespace(name="site.example.com", customer="CUST001", region="EU")
		with (
			patch("lenscloud.api.bench_command.create_action_log", side_effect=fake_create_action_log),
			patch("lenscloud.api.bench_command.get_cluster_client", return_value=FakeClient()),
			patch("lenscloud.api.bench_command.wait_for_job", return_value=("Succeeded", {}, [])),
			patch("lenscloud.api.bench_command.sanitized_termination_summary", return_value={"phase": "Succeeded", "redacted": True}),
			patch("lenscloud.api.bench_command.cleanup_command_resources", return_value=[]),
			patch("lenscloud.api.bench_command.finish_action_log"),
		):
			result = bench_command.run_app_aware_job("site_bootstrap.install_apps", cluster, "runtime", bench, "image@sha256:" + "a" * 64, "echo ok", site_doc=site)

		self.assertEqual(created["action_type"], "Bench Command")
		self.assertEqual(created["operation"], "site_bootstrap.install_apps")
		self.assertEqual(result["status"], "Succeeded")
