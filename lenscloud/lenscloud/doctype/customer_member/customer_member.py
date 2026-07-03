# Copyright (c) 2026, LMNAs Cloud Solutions and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import now_datetime
from frappe.model.document import Document


class CustomerMember(Document):
	def validate(self):
		if self.status == "Active" and not self.approved_on:
			self.approved_on = now_datetime()
		if self.status == "Active" and not self.approved_by:
			self.approved_by = frappe.session.user if frappe.session.user != "Guest" else None

	def on_update(self):
		from lenscloud.api.customer_identity import apply_customer_access

		apply_customer_access(self.user, self.customer, self.member_role, self.status)
