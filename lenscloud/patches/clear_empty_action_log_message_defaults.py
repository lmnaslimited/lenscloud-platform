import frappe


def execute():
	frappe.db.sql(
		"""
		update `tabOrchestration Action Log`
		set message_type = null,
			matched_by = null,
			match_confidence = 0,
			resolution_owner = null,
			retryability = null
		where coalesce(message_id, '') = ''
		"""
	)
