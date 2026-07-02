import frappe
from frappe.tests.utils import FrappeTestCase

from lenscloud.api.orchestration import customer_plan_summary, customer_reconcile_state, get_customer_portal_context, plan_customer_entitlement, plan_payment_summary, subscription_next_renewal


class TestCustomerPlanCatalog(FrappeTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        frappe.get_attr("lenscloud.patches.seed_self_service_plan_catalog.execute")()

    def test_seeded_plan_visibility_and_cta_modes(self):
        rows = frappe.get_all(
            "Plan",
            fields=["name", "plan_code", "docstatus", "publish_in_customer_portal", "allow_self_service", "request_access_only"],
            order_by="portal_sort_order asc",
        )
        by_code = {row.plan_code: row for row in rows}
        self.assertIn("tier-1-free", by_code)
        self.assertIn("tier-2-growth", by_code)
        self.assertIn("tier-3-scale", by_code)
        self.assertIn("tier-4-enterprise", by_code)
        self.assertEqual(by_code["tier-1-free"].docstatus, 1)
        self.assertEqual(by_code["tier-1-free"].publish_in_customer_portal, 1)
        self.assertEqual(by_code["tier-1-free"].allow_self_service, 1)
        self.assertEqual(by_code["tier-2-growth"].request_access_only, 1)
        self.assertEqual(by_code["tier-3-scale"].request_access_only, 1)
        self.assertEqual(by_code["tier-4-enterprise"].publish_in_customer_portal, 0)

    def test_customer_plan_summary(self):
        free = frappe.get_doc("Plan", {"plan_code": "tier-1-free"})
        summary = customer_plan_summary(free)
        self.assertEqual(summary["cta_mode"], "self_service")
        self.assertTrue(summary["is_default"])
        self.assertEqual(summary["environments"], ["Prod"])
        self.assertTrue(summary["features"])
        self.assertEqual(summary["billing_frequency"], "Monthly")
        tier_2 = frappe.get_doc("Plan", {"plan_code": "tier-2-growth"})
        self.assertEqual(customer_plan_summary(tier_2)["cta_mode"], "request_access")
        tier_4 = frappe.get_doc("Plan", {"plan_code": "tier-4-enterprise"})
        self.assertEqual(customer_plan_summary(tier_4)["cta_mode"], "hidden")


    def test_plan_payment_summary_and_renewal_copy(self):
        free = frappe.get_doc("Plan", {"plan_code": "tier-1-free"})
        paid = frappe.get_doc("Plan", {"plan_code": "tier-2-growth"})
        free_summary = plan_payment_summary(free, "Monthly")
        paid_summary = plan_payment_summary(paid, "Monthly")
        self.assertEqual(free_summary["amount"], 0)
        self.assertIn("No payment method", free_summary["payment_note"])
        self.assertNotIn("No payment method", paid_summary["payment_note"])
        self.assertEqual(str(subscription_next_renewal("2026-07-01", "Quarterly")), "2026-10-01")


    def test_plan_entitlement_marks_exhausted_limits(self):
        free = frappe.get_doc("Plan", {"plan_code": "tier-1-free"})
        summary = plan_customer_entitlement(
            free,
            "TEST-CUSTOMER",
            [{"plan": free.name, "status": "Approved"}],
            [{"plan": free.name, "site_status": "Ready"}],
        )
        self.assertTrue(summary["exhausted"])
        self.assertIn("Subscription limit reached", summary["reason"])
        self.assertIn("Site limit reached", summary["reason"])

    def test_customer_reconcile_state_does_not_treat_dry_run_as_started(self):
        self.assertEqual(customer_reconcile_state({"status": "accepted"}), "started")
        self.assertEqual(customer_reconcile_state({"status": "dry_run"}), "paused")
        self.assertEqual(customer_reconcile_state(None), "failed")

    def test_customer_portal_context_plan_catalog(self):
        user = frappe.session.user
        if user == "Guest":
            frappe.set_user("Administrator")
        context = get_customer_portal_context()
        titles = [plan["title"] for plan in context["plans"]]
        self.assertIn("Free", titles)
        self.assertIn("Tier 2 Growth", titles)
        self.assertIn("Tier 3 Scale", titles)
        self.assertNotIn("Tier 4 Enterprise", titles)
        self.assertEqual([plan["cta_mode"] for plan in context["plans"]], ["request_access", "self_service", "request_access"])
        for plan in context["plans"]:
            text = " ".join([plan.get("description") or "", plan.get("customer_summary") or ""] + [feature["feature"] for feature in plan.get("features", [])]).lower()
            for term in ["kubernetes", "namespace", "mariadb", "database server", "secret", "kubeconfig", "pod log", "action log"]:
                self.assertNotIn(term, text)
