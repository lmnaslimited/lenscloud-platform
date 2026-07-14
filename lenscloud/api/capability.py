import frappe
from frappe.utils import now_datetime


def get_logged_in_customer():
	"""Resolve the Customer document for the currently logged-in User.

	Tries Customer Member first (multi-user-per-customer membership model),
	then falls back to a direct Customer.user link. Raises PermissionError
	if the logged-in user has no associated Customer.
	"""
	user = frappe.session.user

	if user == "Guest":
		frappe.throw("You must be logged in to do this.", frappe.PermissionError)

	customer = frappe.db.get_value(
		"Customer Member",
		{"user": user, "status": "Active"},
		"customer",
	)

	if not customer:
		customer = frappe.db.get_value("Customer", {"user": user}, "name")

	if not customer:
		frappe.throw(
			"No Customer account is linked to your user. Contact support.",
			frappe.PermissionError,
		)

	return customer


@frappe.whitelist()
def toggle_opt_in(capability_code, opted_in):
	"""Opt the logged-in customer in or out of a capability.

	Writes to Capability Opted, keyed by {customer}-{capability} via
	autoname. Opting out flips opted_in to 0 rather than deleting the
	record, preserving history for auditing.
	"""
	customer = get_logged_in_customer()

	if not frappe.db.exists("Capability", capability_code):
		frappe.throw(f"Unknown capability: {capability_code}")

	opted_in = frappe.parse_json(opted_in) if isinstance(opted_in, str) else bool(opted_in)

	record_name = f"{customer}-{capability_code}"

	if frappe.db.exists("Capability Opted", record_name):
		doc = frappe.get_doc("Capability Opted", record_name)
		doc.opted_in = 1 if opted_in else 0
		if opted_in:
			doc.opted_on = now_datetime()
		else:
			doc.opted_out_on = now_datetime()
		doc.opted_by = frappe.session.user
		doc.save(ignore_permissions=True)
	else:
		doc = frappe.get_doc({
			"doctype": "Capability Opted",
			"customer": customer,
			"capability": capability_code,
			"opted_in": 1 if opted_in else 0,
			"opted_on": now_datetime() if opted_in else None,
			"opted_by": frappe.session.user,
		})
		doc.insert(ignore_permissions=True)

	frappe.db.commit()

	return {
		"capability_code": capability_code,
		"opted_in": bool(doc.opted_in),
	}


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