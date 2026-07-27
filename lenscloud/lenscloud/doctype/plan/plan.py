import json

import frappe
from frappe import _
from frappe.model.document import Document

from lenscloud.api.policy import allowed_privacy_names, is_active_submitted_policy


FORBIDDEN_CUSTOMER_TERMS = {
    "kubernetes",
    "namespace",
    "bench",
    "mariadb",
    "database server",
    "secret",
    "kubeconfig",
    "pod log",
    "action log",
    "cr name",
}


class Plan(Document):
    def validate(self):
        self.validate_portal_flags()
        self.validate_portal_features()
        if self.is_free:
            if not self.release_group:
                frappe.throw(_("Free Plan requires a Release Group."))
            duplicate = frappe.db.exists("Plan", {
                "release_group": self.release_group,
                "is_free": 1,
                "status": "Active",
                "name": ["!=", self.name],
            })
            if duplicate and self.status == "Active":
                frappe.throw(_("Only one active Free Plan is allowed per Release Group."))
            if self.landscape and self.landscape != "Single Tier":
                frappe.throw(_("Free Plan must use the Single Tier Landscape."))
            if self.default_privacy_profile:
                profile = frappe.get_doc("Privacy Profile", self.default_privacy_profile)
                if profile.privacy != "Public":
                    frappe.throw(_("Free Plan must use a Public Privacy Profile."))
            self.availability = "Public"
        allowed = allowed_privacy_names(self)
        if self.default_privacy_profile and self.default_privacy_profile not in allowed:
            frappe.throw(_("Default Privacy Profile must be included in Allowed Privacy Profiles."))
        for privacy_name in allowed:
            profile = frappe.get_doc("Privacy Profile", privacy_name)
            if not is_active_submitted_policy(profile):
                frappe.throw(_("Allowed Privacy Profile {0} must be submitted.").format(profile.name))

    def validate_portal_flags(self):
        if self.allow_self_service and self.request_access_only:
            frappe.throw(_("A Plan cannot be both self-service and request-access only."))
        if self.allow_self_service and not self.publish_in_customer_portal:
            frappe.throw(_("Self-service Plans must be published in the customer portal."))
        if self.show_draft_in_customer_portal and not self.publish_in_customer_portal:
            frappe.throw(_("Draft preview requires Publish in Customer Portal."))

    def validate_portal_features(self):
        if not self.portal_feature_json:
            return

        try:
            data = json.loads(self.portal_feature_json)
        except Exception as exc:
            frappe.throw(_("Portal Feature JSON must be valid JSON: {0}").format(exc))

        if not isinstance(data, dict):
            frappe.throw(_("Portal Feature JSON must be a JSON object containing 'features' or 'highlights'."))

        # Helper function to validate lists of items (features or highlights)
        def validate_items(items, list_name, text_key):
            if not isinstance(items, list):
                frappe.throw(_("'{0}' in Portal Feature JSON must be an array.").format(list_name))

            for index, item in enumerate(items, start=1):
                if not isinstance(item, dict):
                    frappe.throw(_("{0} row {1} must be an object.").format(list_name.capitalize(), index))
                
                value = item.get(text_key)
                if not value:
                    frappe.throw(_("{0} row {1} requires a '{2}' value.").format(list_name.capitalize(), index, text_key))

                # Check forbidden terms
                text = f"{item.get('icon', '')} {value}".lower()
                for term in FORBIDDEN_CUSTOMER_TERMS:
                    if term in text:
                        frappe.throw(
                            _("{0} row {1} contains customer-hidden runtime term: {2}").format(
                                list_name.capitalize(), index, term
                            )
                        )

        # Validate features if provided
        if "features" in data:
            validate_items(data["features"], "features", "feature")

        # Validate highlights if provided
        if "highlights" in data:
            validate_items(data["highlights"], "highlights", "highlight")
