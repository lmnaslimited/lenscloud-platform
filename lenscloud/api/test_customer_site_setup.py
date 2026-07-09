import frappe
from frappe.tests.utils import FrappeTestCase

from lenscloud.api.orchestration import clean_setup_data, customer_site_setup_schema


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


class TestCustomerSiteSetup(FrappeTestCase):
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
