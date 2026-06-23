from frappe import _
from frappe.model.document import Document
import frappe


class Environment(Document):
    def validate(self):
        self.code = (self.code or "").strip().lower()
        if self.is_production and self.deployment_tier != "production":
            frappe.throw(_("Production Environment must use the production deployment tier."))
        if self.deployment_tier == "production":
            self.is_production = 1
            self.protection_level = "Restricted"
