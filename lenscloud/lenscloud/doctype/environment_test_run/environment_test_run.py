import frappe
from frappe import _
from frappe.model.document import Document


class EnvironmentTestRun(Document):
    def validate(self):
        subscription = frappe.get_doc("Subscription", self.subscription)
        if self.policy_hash != subscription.policy_hash:
            frappe.throw(_("Test evidence must match the active Subscription policy version."))
        environment = frappe.get_doc("Environment", self.environment)
        if environment.is_production and self.test_type == "LATP" and self.execution_mode != "Non-destructive":
            frappe.throw(_("Production LATP must be non-destructive."))
