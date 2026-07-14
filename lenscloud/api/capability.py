import frappe


@frappe.whitelist()
def get_marketplace_context():
	"""Return the capability catalogue for the customer marketplace page.

	Phase 2 scope: capability list only.
	Phase 4 will extend this (or a sibling method) to merge in the
	logged-in customer's Capability Opted state.
	"""
	capabilities = frappe.get_all(
		"Capability",
		filters={"enabled": 1, "status": "Active"},
		fields=[
			"name",
			"capability_name",
			"capability_code",
			"short_description",
			"long_description",
			"icon",
			"category",
			"status",
			"is_featured",
			"pricing_model",
			"docs_link",
			"sort_order",
		],
		order_by="sort_order asc",
	)

	return {
		"capabilities": capabilities,
	}