from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from lenscloud.api.orchestration import clean_setup_data, customer_progress_advanced_past_runtime_gate, customer_site_progress_state, customer_site_setup_schema, setup_identity_args, setup_is_complete


def ensure_app(name):
	if not frappe.db.exists("App", name):
		frappe.get_doc({"doctype": "App", "app_name": name, "title": name}).insert(ignore_permissions=True)
	return name


def make_release_group(apps):
	title = f"LC Setup Test {frappe.generate_hash(length=8)}"
	doc = frappe.get_doc({
		"doctype": "Release Group",
		"title": title,
		"status": "Active",
		"registry_url": "registry.example.com",
		"image_repository": "lenscloud/test",
		"supported_frappe_major_version": "15",
	})
	for app in apps:
		ensure_app(app)
		doc.append("included_apps", {"app": app, "install_at_site_creation": 1})
	doc.insert(ignore_permissions=True)
	return doc


def make_plan(release_group):
	doc = frappe.get_doc({
		"doctype": "Plan",
		"title": f"LC Setup Plan {frappe.generate_hash(length=8)}",
		"plan_code": f"lc-setup-{frappe.generate_hash(length=8).lower()}",
		"status": "Active",
		"release_group": release_group.name,
		"availability": "Invite Only",
	})
	doc.insert(ignore_permissions=True)
	return doc


def make_setup_user(email, first_name="Setup", last_name="Owner"):
	user = frappe.get_doc({
		"doctype": "User",
		"email": email,
		"first_name": first_name,
		"last_name": last_name,
		"enabled": 1,
		"user_type": "Website User",
		"send_welcome_email": 0,
		"new_password": frappe.generate_hash(length=12),
	})
	user.flags.ignore_password_policy = True
	user.insert(ignore_permissions=True)
	return user


def ensure_region():
	region = frappe.db.exists("Region", "EU") or frappe.db.get_value("Region", {}, "name")
	if region:
		return region
	return frappe.get_doc({
		"doctype": "Region",
		"title": "EU",
		"deployment_status": "Active",
	}).insert(ignore_permissions=True).name


def make_customer_with_member(user):
	customer = frappe.get_doc({
		"doctype": "Customer",
		"first_name": "Setup",
		"last_name": "Customer",
		"user": user.name,
		"region": ensure_region(),
		"signup_source": "Signup",
	}).insert(ignore_permissions=True)
	frappe.get_doc({
		"doctype": "Customer Member",
		"customer": customer.name,
		"user": user.name,
		"status": "Active",
		"member_role": "Owner",
		"is_primary_owner": 1,
	}).insert(ignore_permissions=True)
	return customer


class TestCustomerSiteSetup(FrappeTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()
	def test_schema_uses_core_fields_without_erpnext(self):
		plan = make_plan(make_release_group(["frappe"]))
		schema = customer_site_setup_schema(plan.name)
		fields = {field["name"] for field in schema["fields"]}
		self.assertTrue({"language", "country", "timezone", "currency"}.issubset(fields))
		self.assertNotIn("company_name", fields)
		self.assertNotIn("chart_of_accounts", fields)

	def test_schema_includes_app_fields_for_erpnext(self):
		plan = make_plan(make_release_group(["frappe", "erpnext"]))
		schema = customer_site_setup_schema(plan.name)
		fields = {field["name"] for field in schema["fields"]}
		self.assertIn("company_name", fields)
		self.assertIn("chart_of_accounts", fields)
		self.assertIn("fiscal_year_start_date", fields)
		self.assertNotIn("fiscal_year_end_date", fields)

	def test_schema_omits_release_group_apps_not_installed_at_site_creation(self):
		release_group = make_release_group(["frappe", "erpnext", "brandkit"])
		for row in release_group.included_apps:
			if row.app == "brandkit":
				row.install_at_site_creation = 0
		release_group.save(ignore_permissions=True)
		plan = make_plan(release_group)
		schema = customer_site_setup_schema(plan.name)
		self.assertIn("erpnext", schema["apps"])
		self.assertNotIn("brandkit", schema["apps"])

	def test_clean_setup_data_requires_only_schema_required_fields(self):
		plan = make_plan(make_release_group(["frappe"]))
		schema, clean = clean_setup_data(plan.name, {
			"language": "English",
			"country": "India",
			"timezone": "Asia/Kolkata",
			"currency": "INR",
			"company_name": "Ignored",
		})
		fields = {field["name"] for field in schema["fields"]}
		self.assertNotIn("company_name", fields)
		self.assertNotIn("company_name", clean)
		self.assertEqual(clean["currency"], "INR")

	def test_country_defaults_use_frappe_country_metadata(self):
		plan = make_plan(make_release_group(["frappe"]))
		schema = customer_site_setup_schema(plan.name, country="United States")
		self.assertEqual(schema["defaults"]["currency"], "USD")
		self.assertIn("America/New_York", [option["value"] for option in next(field for field in schema["fields"] if field["name"] == "timezone")["options"]])


	def test_setup_status_accepts_safe_display_text_complete(self):
		self.assertTrue(setup_is_complete({
			"status": "Succeeded",
			"display_text": "Setup wizard: Complete",
			"message": "Bench Command site_setup.status finished with phase Succeeded; cleanup removed 3 resource(s). Result: Setup wizard: Complete.",
		}))

	def test_progress_moves_to_setup_defaults_when_setup_required(self):
		site = frappe._dict({
			"site_status": "Ready",
			"provisioning_status": "Ready",
			"route_status": "Ready",
			"access_url": "https://example.test",
			"setup_status": "Required",
			"oauth_status": "Not Checked",
		})
		self.assertEqual(customer_site_progress_state(site), "setup_running")

	def test_progress_moves_to_route_pending_when_runtime_reports_route_pending(self):
		site = frappe._dict({
			"site_status": "Provisioning",
			"provisioning_status": "Running",
			"route_status": "Pending",
			"access_url": "https://example.test",
			"setup_status": "Pending",
			"oauth_status": "Not Checked",
		})
		self.assertEqual(customer_site_progress_state(site), "route_pending")

	def test_progress_stays_on_bootstrap_while_install_apps_is_queued(self):
		site = frappe._dict({
			"name": "bootstrap-running.example.test",
			"site_status": "Ready",
			"provisioning_status": "Ready",
			"route_status": "Ready",
			"access_url": "https://bootstrap-running.example.test",
			"setup_status": "Pending",
			"oauth_status": "Not Checked",
		})
		for status in ("Queued", "Running"):
			with patch("lenscloud.api.orchestration.latest_site_bootstrap_status", return_value=frappe._dict({"status": status})):
				self.assertEqual(customer_site_progress_state(site), "bootstrap_installing")

	def test_bootstrap_in_progress_wins_over_stale_setup_state(self):
		site = frappe._dict({
			"name": "bootstrap-stale-setup.example.test",
			"site_status": "Ready",
			"provisioning_status": "Ready",
			"route_status": "Ready",
			"access_url": "https://bootstrap-stale-setup.example.test",
			"setup_status": "Complete",
			"oauth_status": "Configured",
		})
		with patch("lenscloud.api.orchestration.latest_site_bootstrap_status", return_value=frappe._dict({"status": "Queued"})):
			self.assertEqual(customer_site_progress_state(site), "bootstrap_installing")

	def test_customer_retry_pauses_after_runtime_stage_advances(self):
		self.assertTrue(customer_progress_advanced_past_runtime_gate("started", "route_pending"))
		self.assertTrue(customer_progress_advanced_past_runtime_gate("route_pending", "bootstrap_installing"))
		self.assertTrue(customer_progress_advanced_past_runtime_gate("route_pending", "setup_checking"))
		self.assertFalse(customer_progress_advanced_past_runtime_gate("setup_checking", "setup_running"))
		self.assertFalse(customer_progress_advanced_past_runtime_gate("started", "failed"))

	def test_setup_complete_failure_marks_site_failed(self):
		from lenscloud.api.orchestration import orchestrate_customer_site_setup

		class FakeSite(frappe._dict):
			def reload(self):
				return None

			def save(self, ignore_permissions=False):
				self.saved = True

		site = FakeSite({
			"name": "failed-setup.example.test",
			"route_status": "Ready",
			"access_url": "https://failed-setup.example.test",
			"setup_status": "Required",
			"setup_schema_json": '{"fields": []}',
		})
		args = {
			"language": "English",
			"email": "owner@example.test",
			"full_name": "Owner",
			"country": "India",
			"timezone": "Asia/Kolkata",
			"currency": "INR",
		}
		result = {"status": "Failed", "fallback_summary": "phase: Failed; code: RUNNER_FAILED"}
		with patch("lenscloud.api.orchestration.orchestrate_customer_site_bootstrap", return_value=None), patch("lenscloud.api.orchestration.site_setup_args", return_value=args), patch("lenscloud.api.bench_command.run_site_setup_command_for_orchestration", return_value=result):
			orchestrate_customer_site_setup(site)
		self.assertEqual(site.setup_status, "Failed")
		self.assertIn("RUNNER_FAILED", site.setup_error)
		self.assertTrue(site.saved)

	def test_setup_status_failure_marks_site_failed(self):
		from lenscloud.api.orchestration import orchestrate_customer_site_setup

		class FakeSite(frappe._dict):
			def reload(self):
				return None

			def save(self, ignore_permissions=False):
				self.saved = True

		site = FakeSite({
			"name": "status-failed.example.test",
			"route_status": "Ready",
			"access_url": "https://status-failed.example.test",
			"setup_status": "Pending",
		})
		result = {"status": "Failed", "fallback_summary": "phase: Failed; summary: containerd mount failed"}
		with patch("lenscloud.api.orchestration.orchestrate_customer_site_bootstrap", return_value=None), patch("lenscloud.api.bench_command.run_site_setup_command_for_orchestration", return_value=result):
			orchestrate_customer_site_setup(site)
		self.assertEqual(site.setup_status, "Failed")
		self.assertIn("containerd mount failed", site.setup_error)
		self.assertTrue(site.saved)

	def test_final_setup_status_failure_marks_site_failed(self):
		from lenscloud.api.orchestration import orchestrate_customer_site_setup

		class FakeSite(frappe._dict):
			def reload(self):
				return None

			def save(self, ignore_permissions=False):
				self.saved = True

		site = FakeSite({
			"name": "final-status-failed.example.test",
			"route_status": "Ready",
			"access_url": "https://final-status-failed.example.test",
			"setup_status": "Running",
		})
		result = {"status": "Failed", "message": "Bench Command site_setup.status finished with phase Failed"}
		with patch("lenscloud.api.orchestration.orchestrate_customer_site_bootstrap", return_value=None), patch("lenscloud.api.bench_command.run_site_setup_command_for_orchestration", return_value=result):
			orchestrate_customer_site_setup(site)
		self.assertEqual(site.setup_status, "Failed")
		self.assertIn("phase Failed", site.setup_error)
		self.assertTrue(site.saved)

	def test_bootstrap_success_returns_before_setup_status_poll(self):
		from lenscloud.api.orchestration import orchestrate_customer_site_setup

		class FakeSite(frappe._dict):
			def reload(self):
				return None

			def save(self, ignore_permissions=False):
				self.saved = True

		site = FakeSite({
			"name": "bootstrap-split.example.test",
			"route_status": "Ready",
			"access_url": "https://bootstrap-split.example.test",
			"setup_status": "Pending",
		})
		bootstrap_result = {"status": "Succeeded", "message": "Default apps installed"}
		with patch("lenscloud.api.orchestration.orchestrate_customer_site_bootstrap", return_value=bootstrap_result), patch("lenscloud.api.bench_command.run_site_setup_command_for_orchestration") as setup_status:
			result = orchestrate_customer_site_setup(site)
		self.assertEqual(result, bootstrap_result)
		setup_status.assert_not_called()

	def test_bootstrap_running_returns_before_setup_status_poll(self):
		from lenscloud.api.orchestration import orchestrate_customer_site_setup

		class FakeSite(frappe._dict):
			def reload(self):
				return None

			def save(self, ignore_permissions=False):
				self.saved = True

		site = FakeSite({
			"name": "bootstrap-running.example.test",
			"route_status": "Ready",
			"access_url": "https://bootstrap-running.example.test",
			"setup_status": "Pending",
		})
		bootstrap_result = {"status": "Queued", "action_log": "ORCH-TEST"}
		with patch("lenscloud.api.orchestration.orchestrate_customer_site_bootstrap", return_value=bootstrap_result), patch("lenscloud.api.bench_command.run_site_setup_command_for_orchestration") as setup_status:
			result = orchestrate_customer_site_setup(site)
		self.assertEqual(result, bootstrap_result)
		self.assertEqual(site.setup_status, "Pending")
		setup_status.assert_not_called()

	def test_setup_status_in_progress_does_not_enqueue_duplicate_status(self):
		from lenscloud.api.orchestration import orchestrate_customer_site_setup

		class FakeSite(frappe._dict):
			def reload(self):
				return None

		site = FakeSite({
			"name": "setup-status-running.example.test",
			"route_status": "Ready",
			"access_url": "https://setup-status-running.example.test",
			"setup_status": "Pending",
		})
		with patch("lenscloud.api.orchestration.orchestrate_customer_site_bootstrap", return_value=None), patch("lenscloud.api.orchestration.site_command_in_progress", return_value={"status": "Queued", "command": "site_setup.status", "action_log": "ORCH-TEST"}), patch("lenscloud.api.bench_command.run_site_setup_command_for_orchestration") as setup_status:
			result = orchestrate_customer_site_setup(site)
		self.assertEqual(result["command"], "site_setup.status")
		setup_status.assert_not_called()

	def test_setup_complete_in_progress_does_not_enqueue_duplicate_complete(self):
		from lenscloud.api.orchestration import orchestrate_customer_site_setup

		class FakeSite(frappe._dict):
			def reload(self):
				return None

			def save(self, ignore_permissions=False):
				self.saved = True

		site = FakeSite({
			"name": "setup-complete-running.example.test",
			"route_status": "Ready",
			"access_url": "https://setup-complete-running.example.test",
			"setup_status": "Required",
			"setup_schema_json": '{"fields": []}',
		})
		args = {"language": "English", "email": "owner@example.test", "full_name": "Owner", "country": "India", "timezone": "Asia/Kolkata", "currency": "INR"}
		with patch("lenscloud.api.orchestration.orchestrate_customer_site_bootstrap", return_value=None), patch("lenscloud.api.orchestration.site_setup_args", return_value=args), patch("lenscloud.api.orchestration.site_command_in_progress", return_value={"status": "Running", "command": "site_setup.complete", "action_log": "ORCH-TEST"}), patch("lenscloud.api.bench_command.run_site_setup_command_for_orchestration") as runner:
			result = orchestrate_customer_site_setup(site)
		self.assertEqual(result["command"], "site_setup.complete")
		runner.assert_not_called()

	def test_bootstrap_in_progress_does_not_enqueue_duplicate_install(self):
		from lenscloud.api.orchestration import orchestrate_customer_site_bootstrap

		site = frappe._dict({"name": "bootstrap-queued.example.test"})
		with patch("lenscloud.api.orchestration.site_command_in_progress", return_value={"status": "Running", "action_log": "ORCH-TEST", "message": "already running"}), patch("lenscloud.api.bench_command.install_site_bootstrap_apps") as install:
			result = orchestrate_customer_site_bootstrap(site)
		self.assertEqual(result["status"], "Running")
		self.assertEqual(result["action_log"], "ORCH-TEST")
		install.assert_not_called()

	def test_oauth_status_in_progress_does_not_enqueue_duplicate_status(self):
		from lenscloud.api.orchestration import orchestrate_customer_site_oauth

		site = frappe._dict({"name": "oauth-status.example.test", "setup_status": "Complete", "oauth_status": "Not Checked"})
		with patch("lenscloud.api.orchestration.site_command_in_progress", return_value={"status": "Queued", "command": "oauth.status", "action_log": "ORCH-TEST"}), patch("lenscloud.api.bench_command.run_site_oauth_status_for_orchestration") as status:
			result = orchestrate_customer_site_oauth(site)
		self.assertEqual(result["command"], "oauth.status")
		status.assert_not_called()

	def test_oauth_configure_in_progress_does_not_enqueue_duplicate_configure(self):
		from lenscloud.api.orchestration import orchestrate_customer_site_oauth

		site = frappe._dict({"name": "oauth-configure.example.test", "setup_status": "Complete", "oauth_status": "Pending"})
		with patch("lenscloud.api.orchestration.site_command_in_progress", return_value={"status": "Running", "command": "oauth.configure", "action_log": "ORCH-TEST"}), patch("lenscloud.api.bench_command.configure_site_oauth_for_orchestration") as configure:
			result = orchestrate_customer_site_oauth(site)
		self.assertEqual(result["command"], "oauth.configure")
		configure.assert_not_called()

	def test_setup_failed_does_not_reset_without_force(self):
		from lenscloud.api.orchestration import orchestrate_customer_site_setup

		class FakeSite(frappe._dict):
			def reload(self):
				return None

			def save(self, ignore_permissions=False):
				self.saved = True

		site = FakeSite({
			"name": "failed-terminal.example.test",
			"route_status": "Ready",
			"access_url": "https://failed-terminal.example.test",
			"setup_status": "Failed",
			"setup_error": "containerd mount failed",
		})
		with patch("lenscloud.api.orchestration.orchestrate_customer_site_bootstrap", return_value=None), patch("lenscloud.api.bench_command.run_site_setup_command_for_orchestration") as setup_status:
			result = orchestrate_customer_site_setup(site)
		self.assertEqual(result["status"], "Failed")
		self.assertEqual(site.setup_status, "Failed")
		setup_status.assert_not_called()

	def test_setup_failed_resets_with_force(self):
		from lenscloud.api.orchestration import orchestrate_customer_site_setup

		class FakeSite(frappe._dict):
			def reload(self):
				return None

			def save(self, ignore_permissions=False):
				self.saved = True

		site = FakeSite({
			"name": "failed-force.example.test",
			"route_status": "Ready",
			"access_url": "https://failed-force.example.test",
			"setup_status": "Failed",
			"setup_error": "containerd mount failed",
		})
		result = {"status": "Succeeded", "display_text": "Setup wizard: Required"}
		with patch("lenscloud.api.orchestration.orchestrate_customer_site_bootstrap", return_value=None), patch("lenscloud.api.bench_command.run_site_setup_command_for_orchestration", return_value=result):
			orchestrate_customer_site_setup(site, force=True)
		self.assertEqual(site.setup_status, "Required")
		self.assertIsNone(site.setup_error)

	def test_setup_identity_uses_logged_in_user_profile(self):
		user = make_setup_user(f"setup-{frappe.generate_hash(length=8).lower()}@example.com", first_name="Nithu", last_name="Customer")
		customer = make_customer_with_member(user)
		frappe.set_user(user.name)
		identity = setup_identity_args(frappe._dict({"customer": customer.name, "owner": "Administrator"}))
		self.assertEqual(identity["email"], user.email)
		self.assertEqual(identity["full_name"], "Nithu Customer")

	def test_frappesite_manifest_requests_release_group_creation_apps(self):
		from lenscloud.api.orchestration import build_frappesite_manifest_data

		site = frappe._dict(name="apps.example.test", title="apps.example.test", subdomain="apps", domain="example.test", region="EU", bench="BENCH", operator_resource_name="apps", admin_password_secret_reference="apps-admin")
		bench = frappe._dict(name="BENCH", region="EU", cluster="CLUSTER", operator_resource_name="bench", kubernetes_namespace="runtime", current_release="REL")
		cluster = frappe._dict(name="CLUSTER", ingress_class="traefik")
		with patch("lenscloud.api.orchestration.get_region_cluster", return_value=cluster), patch("lenscloud.api.orchestration.ensure_operator_fields"), patch("lenscloud.api.orchestration.frappe.get_doc", return_value=bench), patch("lenscloud.api.orchestration.site_creation_apps_for_bench", return_value=["erpnext", "brandkit"]):
			manifest = build_frappesite_manifest_data(site)
		self.assertEqual(manifest["spec"]["apps"], ["erpnext", "brandkit"])

	def test_operator_installed_apps_records_bootstrap_success(self):
		from lenscloud.api.orchestration import record_operator_site_creation_apps

		site = frappe._dict(name="apps.example.test", region="EU")
		bench = frappe._dict(name="BENCH")
		cluster = frappe._dict(name="CLUSTER")
		resource = {"status": {"phase": "Ready", "installedApps": ["erpnext"], "appInstallationStatus": "Apps installed"}}
		log = frappe._dict(name="ORCH-TEST")
		with patch("lenscloud.api.orchestration.frappe.db.exists", return_value=False), patch("lenscloud.api.orchestration.site_creation_apps_for_bench", return_value=["erpnext"]), patch("lenscloud.api.orchestration.phase_from_resource", return_value="Ready"), patch("lenscloud.api.orchestration.create_action_log", return_value=log) as create, patch("lenscloud.api.orchestration.finish_action_log") as finish:
			record_operator_site_creation_apps(site, bench, cluster, resource)
		self.assertEqual(create.call_args.args[0], "Bench Command")
		self.assertEqual(create.call_args.kwargs["operation"], "site_bootstrap.install_apps")
		finish.assert_called_once_with(log, "Succeeded", "Operator confirmed Site creation apps installed: erpnext.")

	def test_operator_missing_requested_app_does_not_skip_bootstrap(self):
		from lenscloud.api.orchestration import record_operator_site_creation_apps

		site = frappe._dict(name="apps.example.test", region="EU")
		bench = frappe._dict(name="BENCH")
		cluster = frappe._dict(name="CLUSTER")
		resource = {"status": {"phase": "Ready", "installedApps": [], "appInstallationStatus": "Pending"}}
		with patch("lenscloud.api.orchestration.frappe.db.exists", return_value=False), patch("lenscloud.api.orchestration.site_creation_apps_for_bench", return_value=["erpnext"]), patch("lenscloud.api.orchestration.phase_from_resource", return_value="Ready"), patch("lenscloud.api.orchestration.create_action_log") as create:
			record_operator_site_creation_apps(site, bench, cluster, resource)
		create.assert_not_called()
