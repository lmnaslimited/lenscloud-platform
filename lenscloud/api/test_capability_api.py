from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from lenscloud.api.capability import (
    get_capability_name_map,
    get_link_labels,
    get_logged_in_membership,
    get_marketplace_context,
    get_opted_capability_codes,
    get_prerequisite_map,
    toggle_opt_in,
)


class TestCapabilityApi(FrappeTestCase):
    @patch("frappe.db.get_value")
    def test_get_logged_in_membership_returns_customer_member(self, mock_get_value):
        frappe.session.user = "test@example.com"

        mock_get_value.side_effect = [
            frappe._dict(
                {
                    "name": "CM-0001",
                    "customer": "CUST-0001",
                }
            )
        ]

        member, customer = get_logged_in_membership()

        self.assertEqual(member, "CM-0001")
        self.assertEqual(customer, "CUST-0001")

    @patch("frappe.db.get_value")
    def test_get_logged_in_membership_falls_back_to_customer(self, mock_get_value):
        frappe.session.user = "test@example.com"

        mock_get_value.side_effect = [
            None,
            "CUST-0001",
        ]

        member, customer = get_logged_in_membership()

        self.assertIsNone(member)
        self.assertEqual(customer, "CUST-0001")

    @patch("frappe.db.get_value")
    def test_get_logged_in_membership_requires_customer(self, mock_get_value):
        frappe.session.user = "test@example.com"

        mock_get_value.side_effect = [None, None]

        with self.assertRaises(frappe.PermissionError):
            get_logged_in_membership()

    def test_get_logged_in_membership_rejects_guest(self):
        frappe.session.user = "Guest"

        with self.assertRaises(frappe.PermissionError):
            get_logged_in_membership()

    @patch("frappe.db.commit")
    @patch("frappe.get_doc")
    @patch("frappe.db.exists")
    def test_toggle_opt_in_creates_record(self, mock_exists, mock_get_doc, _commit):
        mock_exists.side_effect = [
            True,   # Capability exists
            False,  # Capability Opted does not exist
        ]

        doc = MagicMock()
        doc.opted_in = 1
        mock_get_doc.return_value = doc

        with patch(
            "lenscloud.api.capability.get_logged_in_membership",
            return_value=("CM-1", "CUST-1"),
        ):
            result = toggle_opt_in("LATP", True)

        doc.insert.assert_called_once()
        self.assertTrue(result["opted_in"])

    @patch("frappe.db.commit")
    @patch("frappe.get_doc")
    @patch("frappe.db.exists")
    def test_toggle_opt_in_updates_existing(self, mock_exists, mock_get_doc, _commit):
        mock_exists.side_effect = [
            True,  # Capability exists
            True,  # Capability Opted exists
        ]

        doc = MagicMock()
        doc.opted_in = 0
        mock_get_doc.return_value = doc

        with patch(
            "lenscloud.api.capability.get_logged_in_membership",
            return_value=("CM-1", "CUST-1"),
        ):
            toggle_opt_in("LATP", False)

        doc.save.assert_called_once()

    @patch("frappe.db.exists")
    @patch("lenscloud.api.capability.get_logged_in_membership")
    def test_toggle_opt_in_unknown_capability(
        self,
        mock_get_logged_in_membership,
        mock_exists,
    ):
        mock_get_logged_in_membership.return_value = ("CM-1", "CUST-1")
        mock_exists.return_value = False

        with self.assertRaises(frappe.ValidationError):
            toggle_opt_in("INVALID", True)

    @patch("frappe.get_all")
    def test_get_opted_capability_codes(self, mock_get_all):
        mock_get_all.return_value = [
            frappe._dict(capability="LATP"),
            frappe._dict(capability="Chordium"),
        ]

        self.assertEqual(
            get_opted_capability_codes("CUST"),
            ["LATP", "Chordium"],
        )

    @patch("frappe.get_all")
    def test_get_link_labels(self, mock_get_all):
        mock_get_all.return_value = [
            frappe._dict(name="FREE", title="Free Plan"),
        ]

        labels = get_link_labels("Plan", ["FREE"])

        self.assertEqual(labels["FREE"], "Free Plan")

    @patch("frappe.get_all")
    def test_get_link_labels_fallback(self, mock_get_all):
        mock_get_all.side_effect = Exception()

        labels = get_link_labels("Plan", ["FREE"])

        self.assertEqual(labels["FREE"], "FREE")

    @patch("frappe.get_all")
    def test_get_prerequisite_map(self, mock_get_all):
        mock_get_all.return_value = [
            frappe._dict(parent="LATP", capability="Core"),
            frappe._dict(parent="LATP", capability="CRM"),
        ]

        result = get_prerequisite_map(["LATP"])

        self.assertEqual(result["LATP"], ["Core", "CRM"])

    @patch("frappe.get_all")
    def test_get_capability_name_map(self, mock_get_all):
        mock_get_all.return_value = [
            frappe._dict(
                name="LATP",
                capability_name="Lens AI Test Pilot",
            ),
        ]

        result = get_capability_name_map(["LATP"])

        self.assertEqual(result["LATP"], "Lens AI Test Pilot")

    @patch("lenscloud.api.capability.get_opted_capability_codes")
    @patch("lenscloud.api.capability.get_logged_in_customer")
    @patch("lenscloud.api.capability.get_capability_name_map")
    @patch("lenscloud.api.capability.get_prerequisite_map")
    @patch("lenscloud.api.capability.get_link_labels")
    @patch("frappe.get_all")
    def test_get_marketplace_context(
        self,
        mock_get_all,
        mock_labels,
        mock_prereqs,
        mock_names,
        mock_customer,
        mock_opted,
    ):
        mock_get_all.return_value = [
            frappe._dict(
                name="LATP",
                capability_name="Lens AI Test Pilot",
                capability_code="LATP",
                short_description="Short",
                long_description="Long",
                icon=None,
                category="AI",
                status="Active",
                pricing_model="FREE",
                monthly_price=0,
                billing_frequency="Monthly",
                docs_link=None,
                publish_in_customer_portal=1,
                allow_self_service=1,
                request_access_only=0,
                experimental=0,
                sort_order=1,
            )
        ]

        mock_labels.side_effect = [
            {"AI": "Artificial Intelligence"},
            {"FREE": "Free"},
        ]
        mock_prereqs.return_value = {
            "LATP": ["CORE"]
        }
        mock_names.return_value = {
            "CORE": "Core Platform"
        }
        mock_customer.return_value = "CUST-001"
        mock_opted.return_value = ["LATP"]

        context = get_marketplace_context()

        self.assertIn("capabilities", context)
        self.assertIn("opted_capabilities", context)
        self.assertEqual(context["opted_capabilities"], ["LATP"])

        capability = context["capabilities"][0]

        self.assertEqual(
            capability["category_label"],
            "Artificial Intelligence",
        )
        self.assertEqual(
            capability["pricing_model_label"],
            "Free",
        )
        self.assertEqual(
            capability["prerequisites"][0]["capability_name"],
            "Core Platform",
        )

    @patch("frappe.clear_last_message")
    @patch("lenscloud.api.capability.get_logged_in_customer")
    @patch("frappe.get_all")
    def test_get_marketplace_context_without_customer(
        self,
        mock_get_all,
        mock_customer,
        _clear,
    ):
        mock_get_all.return_value = []

        mock_customer.side_effect = frappe.PermissionError

        context = get_marketplace_context()

        self.assertEqual(context["opted_capabilities"], [])
        self.assertEqual(context["capabilities"], [])