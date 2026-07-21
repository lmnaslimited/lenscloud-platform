import frappe
from frappe.model.document import Document


class LensCloudMessage(Document):
	def validate(self):
		self.message_id = (self.message_id or "").strip().upper()
		if not self.message_id.startswith("LC-"):
			frappe.throw("LensCloud Message IDs must start with LC-.")
