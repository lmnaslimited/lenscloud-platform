import frappe

from lenscloud.api.messages import MESSAGE_CATALOG


def execute():
	for message_id, values in MESSAGE_CATALOG.items():
		source, template, customer_resolution, retryability, owner = values
		doc = frappe.get_doc("LensCloud Message", message_id) if frappe.db.exists("LensCloud Message", message_id) else frappe.new_doc("LensCloud Message")
		doc.update({
			"message_id": message_id, "message_type": "Error", "status": "Active", "revision": 1,
			"source": source, "destination": "Customer, Platform Operator", "short_text": template.split("{")[0].strip(" ."),
			"message_template": template, "customer_resolution": customer_resolution,
			"retryability": retryability, "resolution_owner": owner, "sanitization_level": "Operator Safe",
		})
		doc.save(ignore_permissions=True) if doc.name else doc.insert(ignore_permissions=True)
