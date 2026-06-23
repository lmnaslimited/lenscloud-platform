import frappe
from frappe import _
from frappe.model.document import Document

from lenscloud.api.policy import allowed_privacy_names


class Plan(Document):
    def validate(self):
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
            if self.default_privacy_profile and self.default_privacy_profile != "Public":
                frappe.throw(_("Free Plan must use the Public Privacy Profile."))
            self.availability = "Public"
        allowed = allowed_privacy_names(self)
        if self.default_privacy_profile and self.default_privacy_profile not in allowed:
            frappe.throw(_("Default Privacy Profile must be included in Allowed Privacy Profiles."))
