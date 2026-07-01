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
            features = json.loads(self.portal_feature_json)
        except Exception as exc:
            frappe.throw(_("Portal Feature JSON must be valid JSON: {0}").format(exc))
        if not isinstance(features, list):
            frappe.throw(_("Portal Feature JSON must be an array."))
        for index, feature in enumerate(features, start=1):
            if not isinstance(feature, dict):
                frappe.throw(_("Portal feature row {0} must be an object.").format(index))
            if not feature.get("feature"):
                frappe.throw(_("Portal feature row {0} requires a feature value.").format(index))
            text = f"{feature.get('icon', '')} {feature.get('feature', '')}".lower()
            for term in FORBIDDEN_CUSTOMER_TERMS:
                if term in text:
                    frappe.throw(_("Portal feature row {0} contains customer-hidden runtime term: {1}").format(index, term))
