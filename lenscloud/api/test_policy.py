from types import SimpleNamespace
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from lenscloud.api.launch import get_doctype_editor_schema, get_document_connections, get_platform_dashboard
from lenscloud.api.policy import placement_keys


class TestTopologyPolicy(FrappeTestCase):
    def test_seeded_landscapes_have_expected_environment_order(self):
        expected = {
            "Single Tier": ["Prod"],
            "Two Tier": ["QA", "Prod"],
            "Three Tier": ["Dev", "QA", "Prod"],
            "Four Tier": ["Dev", "QA", "Pre-Prod", "Prod"],
        }
        for landscape, environments in expected.items():
            doc = frappe.get_doc("Landscape", landscape)
            self.assertEqual([row.environment for row in sorted(doc.environments, key=lambda row: row.sequence)], environments)

    def test_private_shared_keeps_prod_database_separate(self):
        profile = frappe.get_doc("Privacy", "Private Shared")
        rules = {row.environment: row for row in profile.environment_rules}
        self.assertEqual(rules["Dev"].database_group, rules["QA"].database_group)
        self.assertNotEqual(rules["Prod"].database_group, rules["QA"].database_group)
        self.assertEqual(rules["Prod"].database_boundary, "Customer")

    def test_policy_resolves_same_database_and_different_benches(self):
        snapshot = {"environments": [
            {"environment": "Dev", "bench_boundary": "Customer", "bench_group": "dev", "database_boundary": "Customer", "database_group": "nonprod"},
            {"environment": "QA", "bench_boundary": "Customer", "bench_group": "qa", "database_boundary": "Customer", "database_group": "nonprod"},
        ]}
        subscription = SimpleNamespace(name="SUB-TEST", customer="CUST-TEST", effective_policy_snapshot=frappe.as_json(snapshot))
        dev = placement_keys(subscription, "Dev", bench=SimpleNamespace(name="bench-dev"))
        qa = placement_keys(subscription, "QA", bench=SimpleNamespace(name="bench-qa"))
        self.assertNotEqual(dev["bench"], qa["bench"])
        self.assertEqual(dev["database"], qa["database"])

    def test_restricted_profile_rejects_developer_mode(self):
        doc = frappe.get_doc({"doctype": "Site Control Profile", "title": "Invalid Restricted", "version": 1, "status": "Draft", "protection_level": "Restricted", "enable_developer_mode": 1})
        with self.assertRaises(frappe.ValidationError):
            doc.validate()

    @patch("lenscloud.api.launch.require_platform")
    def test_dashboard_uses_database_counts(self, _require_platform):
        result = get_platform_dashboard()
        self.assertEqual(result["metrics"]["customers"], frappe.db.count("Customer"))
        self.assertEqual(result["metrics"]["ready_sites"], frappe.db.count("Site", {"site_status": ["in", ["Ready", "Active"]]}))
    @patch("lenscloud.api.launch.require_platform")
    def test_editor_schema_preserves_layout_and_child_metadata(self, _require_platform):
        release_group = get_doctype_editor_schema("Release Group")
        fields = {field["fieldname"]: field for field in release_group["fields"]}
        self.assertTrue(any(field["fieldtype"] in {"Section Break", "Column Break", "Tab Break"} for field in release_group["fields"]))
        self.assertEqual(fields["included_apps"]["fieldtype"], "Table MultiSelect")
        plan = get_doctype_editor_schema("Plan")
        plan_fields = {field["fieldname"]: field for field in plan["fields"]}
        self.assertEqual(plan_fields["allowed_privacy_profiles"]["fieldtype"], "Table MultiSelect")
        self.assertEqual(fields["included_apps"]["columns"][0]["fieldtype"], "Link")
        self.assertEqual(fields["included_apps"]["columns"][0]["options"], "App")
        self.assertEqual(release_group["naming_field"], "title")
        self.assertTrue(release_group["allow_rename"])

        cluster_tabs = [field["label"] for field in get_doctype_editor_schema("Cluster")["fields"] if field["fieldtype"] == "Tab Break"]
        self.assertEqual(cluster_tabs, ["Access and Operations", "Operator Defaults", "Health"])

        customer_types = [field["fieldtype"] for field in get_doctype_editor_schema("Customer")["fields"]]
        settings_types = [field["fieldtype"] for field in get_doctype_editor_schema("Platform Settings")["fields"]]
        self.assertIn("Column Break", customer_types)
        self.assertIn("Tab Break", settings_types)
    def test_platform_role_can_manage_customers_and_sites_without_raw_delete(self):
        for doctype in ("Customer", "Site"):
            permission = next(
                row for row in frappe.get_meta(doctype).permissions
                if row.role == "LensCloud Platform User"
            )
            self.assertTrue(permission.read)
            self.assertTrue(permission.create)
            self.assertTrue(permission.write)
            self.assertFalse(permission.delete)
    @patch("lenscloud.api.launch.require_platform")
    def test_customer_connections_are_metadata_driven_and_limited(self, _require_platform):
        customer = frappe.get_all("Customer", pluck="name", limit=1)[0]
        result = get_document_connections("Customer", customer)
        by_doctype = {row["doctype"]: row for row in result}
        self.assertIn("Subscription", by_doctype)
        self.assertIn("Site", by_doctype)
        for connection in result:
            self.assertLessEqual(len(connection["items"]), 5)
            self.assertGreaterEqual(connection["count"], len(connection["items"]))
    def test_lenscloud_document_links_reference_real_fields(self):
        for doctype in frappe.get_all("DocType", filters={"module": "Lenscloud", "istable": 0}, pluck="name"):
            meta = frappe.get_meta(doctype)
            for link in meta.links or []:
                self.assertTrue(
                    frappe.get_meta(link.link_doctype).has_field(link.link_fieldname),
                    f"{doctype} connection {link.link_doctype}.{link.link_fieldname} is invalid",
                )

