import frappe
from frappe import _
from frappe.model.document import Document

from lenscloud.api.policy import apply_subscription_policy


class Subscription(Document):
    def validate(self):
        plan = frappe.get_doc("Plan", self.plan)
        if plan.status != "Active" or plan.availability == "Retired":
            frappe.throw(_("Subscription requires an active available Plan."))
        if plan.subscription_limit:
            filters = {"customer": self.customer, "plan": self.plan, "status": ["not in", ["Cancelled", "Failed"]], "name": ["!=", self.name]}
            if frappe.db.count("Subscription", filters) >= int(plan.subscription_limit):
                frappe.throw(_("Plan subscription limit has been reached."))
        if self.is_new() or not self.policy_hash:
            apply_subscription_policy(self)
        if plan.availability == "Beta" and self.status == "Requested":
            self.status = "Pending Approval"
