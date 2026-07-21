import frappe

from lenscloud.api.infra_messages import INFRA_MESSAGE_CATALOG


def execute():
	for message_id, (safe_summary, customer_resolution) in INFRA_MESSAGE_CATALOG.items():
		doc = frappe.get_doc("LensCloud Message", message_id) if frappe.db.exists("LensCloud Message", message_id) else frappe.new_doc("LensCloud Message")
		doc.update({
			"message_id": message_id, "message_type": "Error", "status": "Active", "revision": 1,
			"source": "Runner", "destination": "Platform", "short_text": safe_summary,
			"message_template": safe_summary, "customer_resolution": customer_resolution,
			"retryability": "Retry After Infra Action", "resolution_owner": "Infra",
			"sanitization_level": "Operator Safe",
		})
		doc.save(ignore_permissions=True) if doc.name else doc.insert(ignore_permissions=True)
