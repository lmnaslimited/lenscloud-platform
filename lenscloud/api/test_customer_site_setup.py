import frappe
from frappe.tests.utils import FrappeTestCase

from lenscloud.api.orchestration import clean_setup_data, customer_site_setup_schema, setup_identity_args, setup_is_complete


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
		doc.append("included_apps", {"app": app})
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

	def test_setup_identity_uses_logged_in_user_profile(self):
		user = make_setup_user(f"setup-{frappe.generate_hash(length=8).lower()}@example.com", first_name="Nithu", last_name="Customer")
		customer = make_customer_with_member(user)
		frappe.set_user(user.name)
		identity = setup_identity_args(frappe._dict({"customer": customer.name, "owner": "Administrator"}))
		self.assertEqual(identity["email"], user.email)
		self.assertEqual(identity["full_name"], "Nithu Customer")
