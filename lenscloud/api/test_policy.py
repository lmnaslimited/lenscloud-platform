from types import SimpleNamespace
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from lenscloud.api.launch import get_doctype_editor_schema, get_document_connections, get_platform_dashboard
from lenscloud.api.orchestration import get_customer_portal_context
from lenscloud.api.policy import placement_keys, resolve_subscription_policy_doc


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


    def test_seeded_policy_profiles_are_submitted_defaults(self):
        for environment in ("Dev", "QA", "Pre-Prod", "Prod"):
            profile_name = frappe.db.exists("Site Control Profile", {"environment": environment, "is_default": 1, "status": "Active", "docstatus": 1})
            profile = frappe.get_doc("Site Control Profile", profile_name)
            self.assertEqual(profile.docstatus, 1)
            self.assertEqual(profile.environment, environment)
            self.assertTrue(profile.profile_code)
        for privacy in ("Public", "Private Shared", "Private"):
            self.assertTrue(frappe.db.exists("Privacy", privacy))
            profile_name = frappe.db.exists("Privacy Profile", {"privacy": privacy, "is_default": 1, "docstatus": 1})
            profile = frappe.get_doc("Privacy Profile", profile_name)
            self.assertEqual(profile.docstatus, 1)
            self.assertEqual(profile.privacy, privacy)
            self.assertTrue(profile.is_default)

    def test_site_control_default_is_unique_per_environment(self):
        doc = frappe.get_doc({
            "doctype": "Site Control Profile",
            "title": "Duplicate Prod Controls Test",
            "environment": "Prod",
            "profile_code": "Prod Controls",
            "version": 99,
            "status": "Active",
            "is_default": 1,
            "protection_level": "Restricted",
            "cors_policy": "Disabled",
            "enable_latp": 1,
            "require_latp": 1,
            "latp_mode": "Non-destructive",
        })
        doc.insert()
        with self.assertRaises(frappe.ValidationError):
            doc.submit()

    def test_privacy_default_is_unique_per_family(self):
        source = frappe.get_doc("Privacy Profile", frappe.db.exists("Privacy Profile", {"privacy": "Public", "is_default": 1, "docstatus": 1}))
        doc = frappe.get_doc({
            "doctype": "Privacy Profile",
            "title": "Duplicate Public Privacy Test",
            "privacy": "Public",
            "is_default": 1,
            "customer_summary": source.customer_summary,
            "environment_rules": [
                {
                    "environment": row.environment,
                    "bench_boundary": row.bench_boundary,
                    "bench_group": row.bench_group,
                    "database_boundary": row.database_boundary,
                    "database_group": row.database_group,
                }
                for row in source.environment_rules
            ],
        })
        doc.insert()
        with self.assertRaises(frappe.ValidationError):
            doc.submit()

    def test_landscape_autopicks_default_site_control_profile(self):
        doc = frappe.get_doc({
            "doctype": "Landscape",
            "title": "Autopick Landscape Test",
            "tier_count": 1,
            "version": 1,
            "status": "Draft",
            "environments": [{"environment": "Prod", "sequence": 10, "bench_group": "prod", "database_group": "prod"}],
        })
        doc.insert()
        self.assertEqual(doc.environments[0].site_control_profile, "Prod Controls v1")

    def test_private_shared_keeps_prod_database_separate(self):
        profile = frappe.get_doc("Privacy Profile", frappe.db.exists("Privacy Profile", {"privacy": "Private Shared", "is_default": 1, "docstatus": 1}))
        rules = {row.environment: row for row in profile.environment_rules}
        self.assertEqual(rules["Dev"].database_group, rules["QA"].database_group)
        self.assertNotEqual(rules["Prod"].database_group, rules["QA"].database_group)
        self.assertEqual(rules["Prod"].database_boundary, "Customer")

    def test_subscription_policy_snapshot_includes_site_controls(self):
        plan_name = frappe.db.get_value("Plan", {"is_free": 1}, "name") or frappe.db.get_value("Plan", {}, "name")
        snapshot = resolve_subscription_policy_doc(SimpleNamespace(plan=plan_name, region="EU", customer="CUST-SNAPSHOT"))
        prod = next(row for row in snapshot["environments"] if row["environment"] == "Prod")
        self.assertIn("site_controls", prod)
        self.assertIn("enable_developer_mode", prod["site_controls"])
        self.assertIn("allow_client_scripts", prod["site_controls"])
        self.assertIn("allow_server_scripts", prod["site_controls"])
        self.assertIn("cors_policy", prod["site_controls"])

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

        self.assertTrue(plan["is_submittable"])
        self.assertIn("can_submit", plan)
        self.assertIn("can_cancel", plan)
        self.assertIn("can_amend", plan)
        self.assertIn("can_delete", plan)

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
        customer_doc = frappe.get_doc({
            "doctype": "Customer",
            "first_name": "Connection",
            "last_name": "Probe",
            "region": "EU",
        }).insert(ignore_permissions=True)
        self.addCleanup(lambda: frappe.delete_doc("Customer", customer_doc.name, force=True, ignore_permissions=True, ignore_missing=True))
        result = get_document_connections("Customer", customer_doc.name)
        by_doctype = {row["doctype"]: row for row in result}
        self.assertIn("Subscription", by_doctype)
        self.assertIn("Site", by_doctype)
        for connection in result:
            self.assertLessEqual(len(connection["items"]), 5)
            self.assertGreaterEqual(connection["count"], len(connection["items"]))
    def test_customer_portal_context_is_plan_first_and_secret_safe(self):
        context = get_customer_portal_context()
        self.assertIn("plans", context)
        self.assertIn("subscriptions", context)
        self.assertIn("sites", context)
        self.assertIn("usage", context)
        self.assertIn("onboarding_step", context)
        self.assertTrue(context["plans"])
        plan = context["plans"][0]
        self.assertIn("customer_summary", plan)
        self.assertIn("environments", plan)
        for forbidden in ("bench", "database_server", "runtime_namespace", "secret", "kubeconfig"):
            self.assertNotIn(forbidden, plan)

    def test_lenscloud_document_links_reference_real_fields(self):
        for doctype in frappe.get_all("DocType", filters={"module": "Lenscloud", "istable": 0}, pluck="name"):
            meta = frappe.get_meta(doctype)
            for link in meta.links or []:
                self.assertTrue(
                    frappe.get_meta(link.link_doctype).has_field(link.link_fieldname),
                    f"{doctype} connection {link.link_doctype}.{link.link_fieldname} is invalid",
                )
