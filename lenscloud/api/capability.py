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


def get_opted_capability_codes(customer):
	"""Return the set of capability_codes the given customer currently has
	opted_in = 1 for, per Capability Opted."""
	rows = frappe.get_all(
		"Capability Opted",
		filters={"customer": customer, "opted_in": 1},
		fields=["capability"],
	)
	return [row.capability for row in rows]


def get_link_labels(doctype, names):
	"""Resolve a display label for each Link value in `names`.

	Tries a `title` field first (the convention used elsewhere in this app,
	e.g. Plan). Falls back to the raw name if the doctype has no such field
	so this never breaks the whole page over a schema assumption.
	"""
	names = [name for name in set(names) if name]
	if not names:
		return {}

	try:
		rows = frappe.get_all(doctype, filters={"name": ["in", names]}, fields=["name", "title"])
		return {row.name: (row.title or row.name) for row in rows}
	except Exception:
		return {name: name for name in names}


def get_prerequisite_map(capability_codes):
	"""Return {capability_code: [prerequisite_code, ...]} for the given
	capabilities, read from the Capability Prerequisite child table."""
	if not capability_codes:
		return {}

	rows = frappe.get_all(
		"Capability Prerequisite",
		filters={"parenttype": "Capability", "parent": ["in", capability_codes]},
		fields=["parent", "capability"],
	)

	prereq_map = {}
	for row in rows:
		prereq_map.setdefault(row.parent, []).append(row.capability)
	return prereq_map


def get_capability_name_map(capability_codes):
	"""Return {capability_code: capability_name} for display purposes,
	looked up regardless of a capability's own enabled/published state
	(a prerequisite might legitimately not be portal-published itself)."""
	if not capability_codes:
		return {}

	rows = frappe.get_all(
		"Capability",
		filters={"name": ["in", list(capability_codes)]},
		fields=["name", "capability_name"],
	)
	return {row.name: row.capability_name for row in rows}


@frappe.whitelist()
def get_marketplace_context():
	"""Return the capability catalogue plus the logged-in customer's
	current opt-in state, for the customer marketplace page.
	"""
	capabilities = frappe.get_all(
		"Capability",
		filters={"enabled": 1, "publish_in_customer_portal": 1},
		fields=[
			"name",
			"capability_name",
			"capability_code",
			"short_description",
			"long_description",
			"icon",
			"category",
			"status",
			"pricing_model",
			"monthly_price",
			"billing_frequency",
			"docs_link",
			"publish_in_customer_portal",
			"allow_self_service",
			"request_access_only",
			"experimental",
			"sort_order",
		],
		order_by="sort_order asc",
	)

	codes = [c.name for c in capabilities]

	category_labels = get_link_labels("Category", [c.category for c in capabilities])
	pricing_labels = get_link_labels("Pricing Model", [c.pricing_model for c in capabilities])
	prereq_map = get_prerequisite_map(codes)

	all_prereq_codes = {code for codes_list in prereq_map.values() for code in codes_list}
	prereq_name_map = get_capability_name_map(all_prereq_codes)

	for c in capabilities:
		c["category_label"] = category_labels.get(c.category, c.category)
		c["pricing_model_label"] = pricing_labels.get(c.pricing_model, c.pricing_model)
		c["prerequisites"] = [
			{"capability_code": code, "capability_name": prereq_name_map.get(code, code)}
			for code in prereq_map.get(c.name, [])
		]

	opted_capabilities = []
	try:
		customer = get_logged_in_customer()
		opted_capabilities = get_opted_capability_codes(customer)
	except frappe.PermissionError:
		# No Customer linked to this session (e.g. viewed by a non-customer
		# user in a lower environment). Degrade gracefully rather than
		# failing the whole marketplace load.
		frappe.clear_last_message()

	return {
		"capabilities": capabilities,
		"opted_capabilities": opted_capabilities,
	}