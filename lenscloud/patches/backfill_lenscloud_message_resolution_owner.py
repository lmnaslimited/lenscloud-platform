import frappe

from lenscloud.api.messages import MESSAGE_CATALOG


def execute():
	for message_id, values in MESSAGE_CATALOG.items():
		if not frappe.db.exists("LensCloud Message", message_id):
			continue
		resolution_owner = values[4]
		frappe.db.set_value(
			"LensCloud Message",
			message_id,
			"resolution_owner",
			resolution_owner,
			update_modified=False,
		)
