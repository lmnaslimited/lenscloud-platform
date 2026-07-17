import json
from datetime import datetime

import frappe
from frappe import _


CAPABILITY_ACTIVE_STATUSES = {"Approved", "Provisioning", "Active"}


def audit_now():
	return datetime.utcnow().replace(microsecond=0)


def get_logged_in_membership():
	user = frappe.session.user
	if user == "Guest":
		frappe.throw(_("You must be logged in to do this."), frappe.PermissionError)

	membership = frappe.db.get_value(
		"Customer Member",
		{"user": user, "status": "Active"},
		["name", "customer"],
		as_dict=True,
	)
	if membership:
		return membership.name, membership.customer

	customer = frappe.db.get_value("Customer", {"user": user}, "name")
	if not customer:
		frappe.throw(_("No Customer account is linked to your user. Contact support."), frappe.PermissionError)
	return None, customer


def get_logged_in_customer():
	_, customer = get_logged_in_membership()
	return customer


def get_link_labels(doctype, names):
	names = [name for name in set(names) if name]
	if not names:
		return {}
	try:
		rows = frappe.get_all(doctype, filters={"name": ["in", names]}, fields=["name", "title"])
		return {row.name: (row.title or row.name) for row in rows}
	except Exception:
		return {name: name for name in names}


def get_prerequisite_map(capability_codes):
	if not capability_codes:
		return {}
	rows = frappe.get_all(
		"Capability Prerequisite",
		filters={"parenttype": "Capability", "parent": ["in", capability_codes]},
		fields=["parent", "capability"],
	)
	result = {}
	for row in rows:
		result.setdefault(row.parent, []).append(row.capability)
	return result


def get_capability_name_map(capability_codes):
	if not capability_codes:
		return {}
	rows = frappe.get_all(
		"Capability",
		filters={"name": ["in", list(capability_codes)]},
		fields=["name", "capability_name"],
	)
	return {row.name: row.capability_name for row in rows}


def capability_app_rows(capability):
	doc = frappe.get_doc("Capability", capability)
	rows = []
	for row in doc.get("apps") or []:
		if not row.app:
			continue
		rows.append({
			"app": row.app,
			"required": bool(row.required),
			"install_at_site_creation": bool(row.install_at_site_creation),
			"install_sequence": row.install_sequence,
			"install_scope": row.install_scope or "Site",
		})
	return sorted(rows, key=lambda item: (item.get("install_sequence") is None, item.get("install_sequence") or 0, item.get("app") or ""))


def customer_subscriptions(customer):
	return frappe.get_all(
		"Subscription",
		filters={"customer": customer, "status": ["not in", ["Cancelled"]]},
		fields=["name", "plan", "status", "landscape", "release_group", "region"],
		order_by="creation desc",
	)


def subscription_capability_map(customer):
	rows = frappe.get_all(
		"Subscription Capability",
		filters={"customer": customer},
		fields=["name", "subscription", "capability", "status", "landscape", "environment", "policy"],
	)
	result = {}
	for row in rows:
		result.setdefault(row.capability, []).append(row)
	return result


def get_opted_capability_codes(customer):
	rows = frappe.get_all(
		"Capability Opted",
		filters={"customer": customer, "opted_in": 1},
		fields=["capability"],
	)
	return [row.capability for row in rows]


@frappe.whitelist()
def get_marketplace_context():
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
	all_prereq_codes = {code for rows in prereq_map.values() for code in rows}
	prereq_name_map = get_capability_name_map(all_prereq_codes)

	for capability in capabilities:
		capability["category_label"] = category_labels.get(capability.category, capability.category)
		capability["pricing_model_label"] = pricing_labels.get(capability.pricing_model, capability.pricing_model)
		capability["prerequisites"] = [
			{"capability_code": code, "capability_name": prereq_name_map.get(code, code)}
			for code in prereq_map.get(capability.name, [])
		]

		try:
			capability["apps"] = capability_app_rows(capability.name)
		except frappe.DoesNotExistError:
			capability["apps"] = []

	customer = None
	subscriptions = []
	opted_capabilities = []
	subscription_capabilities = {}
	try:
		customer = get_logged_in_customer()
		subscriptions = customer_subscriptions(customer)
		opted_capabilities = get_opted_capability_codes(customer)
		subscription_capabilities = subscription_capability_map(customer)
	except frappe.PermissionError:
		frappe.clear_last_message()

	return {
		"customer": customer,
		"capabilities": capabilities,
		"subscriptions": subscriptions,
		"opted_capabilities": opted_capabilities,
		"subscription_capabilities": subscription_capabilities,
	}


def validate_prerequisites(capability, customer):
	prereqs = get_prerequisite_map([capability]).get(capability, [])
	if not prereqs:
		return
	active = {
		row.capability
		for row in frappe.get_all(
			"Subscription Capability",
			filters={"customer": customer, "capability": ["in", prereqs], "status": ["in", list(CAPABILITY_ACTIVE_STATUSES)]},
			fields=["capability"],
		)
	}
	missing = [code for code in prereqs if code not in active]
	if missing:
		names = get_capability_name_map(missing)
		frappe.throw(_("Enable prerequisite capabilities first: {0}").format(", ".join(names.get(code, code) for code in missing)))


def find_policy(capability, subscription, environment=None):
	landscape = frappe.db.get_value("Subscription", subscription, "landscape")
	if not landscape:
		return None
	filters = {"capability": capability, "landscape": landscape, "status": "Active"}
	if environment:
		filters["environment"] = environment
	policy = frappe.db.get_value("Capability Landscape Policy", filters, "name")
	if policy:
		return policy
	return frappe.db.get_value("Capability Landscape Policy", {"capability": capability, "landscape": landscape, "status": "Active"}, "name")


def upsert_capability_opted(customer_member, customer, capability, opted_in):
	record_name = f"{customer}-{capability}"
	exists = frappe.db.exists("Capability Opted", record_name)
	if exists:
		doc = frappe.get_doc("Capability Opted", record_name)
	else:
		doc = frappe.get_doc({"doctype": "Capability Opted", "customer_member": customer_member, "customer": customer, "capability": capability})
	doc.customer_member = customer_member
	doc.customer = customer
	doc.opted_in = 1 if opted_in else 0
	if opted_in:
		doc.opted_on = audit_now()
	else:
		doc.opted_out_on = audit_now()
	doc.opted_by = frappe.session.user
	if exists:
		doc.save(ignore_permissions=True)
	else:
		doc.insert(ignore_permissions=True)
	return doc


@frappe.whitelist()
def request_capability(capability_code, subscription=None, environment=None, notes=None, opted_in=None):
	customer_member, customer = get_logged_in_membership()
	if not frappe.db.exists("Capability", capability_code):
		frappe.throw(_("Unknown capability: {0}").format(capability_code))
	capability = frappe.get_doc("Capability", capability_code)
	if not capability.enabled:
		frappe.throw(_("Capability {0} is not enabled.").format(capability_code))
	validate_prerequisites(capability_code, customer)

	if not subscription:
		subs = customer_subscriptions(customer)
		if len(subs) == 1:
			subscription = subs[0].name
		elif not subs:
			frappe.throw(_("Create a Subscription before requesting capabilities."))
		else:
			frappe.throw(_("Select the Subscription this capability should be enabled for."))

	sub = frappe.get_doc("Subscription", subscription)
	if sub.customer != customer:
		frappe.throw(_("Subscription does not belong to your Customer."), frappe.PermissionError)

	policy = find_policy(capability_code, subscription, environment=environment)
	status = "Pending Approval" if capability.request_access_only or not capability.allow_self_service else "Requested"
	if policy:
		policy_doc = frappe.get_doc("Capability Landscape Policy", policy)
		if policy_doc.approval_required or policy_doc.progression_policy in {"Approval Required", "Platform Managed"}:
			status = "Pending Approval"

	name = f"SUBCAP-{subscription}-{capability_code}"
	if frappe.db.exists("Subscription Capability", name):
		doc = frappe.get_doc("Subscription Capability", name)
	else:
		doc = frappe.get_doc({"doctype": "Subscription Capability", "subscription": subscription, "capability": capability_code})
	doc.customer = customer
	doc.subscription = subscription
	doc.capability = capability_code
	doc.status = doc.status if doc.name and doc.status in {"Approved", "Provisioning", "Active"} else status
	doc.landscape = sub.landscape
	doc.environment = environment
	doc.policy = policy
	doc.requested_by = frappe.session.user
	doc.requested_on = audit_now()
	if notes:
		doc.notes = notes
	doc.save(ignore_permissions=True) if doc.name else doc.insert(ignore_permissions=True)
	upsert_capability_opted(customer_member, customer, capability_code, True)
	frappe.db.commit()
	return {"subscription_capability": doc.name, "capability": capability_code, "subscription": subscription, "status": doc.status}


@frappe.whitelist()
def toggle_opt_in(capability_code, opted_in, subscription=None):
	opted_in = frappe.parse_json(opted_in) if isinstance(opted_in, str) else bool(opted_in)
	customer_member, customer = get_logged_in_membership()
	if not frappe.db.exists("Capability", capability_code):
		frappe.throw(_("Unknown capability: {0}").format(capability_code))
	opted = upsert_capability_opted(customer_member, customer, capability_code, opted_in)
	result = {"capability_code": capability_code, "opted_in": bool(opted.opted_in)}
	if opted_in and subscription:
		result.update(request_capability(capability_code, subscription=subscription))
	else:
		frappe.db.commit()
	return result


def site_capability_payload(site, subscription_capability, status="Pending", source="Platform", error_excerpt=None, installed_apps=None):
	site_doc = frappe.get_doc("Site", site) if isinstance(site, str) else site
	subcap = frappe.get_doc("Subscription Capability", subscription_capability) if isinstance(subscription_capability, str) else subscription_capability
	apps = capability_app_rows(subcap.capability)
	return {
		"capability": subcap.capability,
		"subscription_capability": subcap.name,
		"status": status,
		"source": source,
		"landscape": subcap.landscape,
		"environment": subcap.environment or site_doc.environment,
		"policy": subcap.policy,
		"release": frappe.db.get_value("Bench", site_doc.bench, "current_release") if site_doc.bench else None,
		"required_apps_json": json.dumps(apps, sort_keys=True),
		"installed_apps_json": json.dumps(installed_apps or [], sort_keys=True),
		"last_synced_on": audit_now(),
		"last_action_log": subcap.last_action_log,
		"error_excerpt": error_excerpt,
	}


def upsert_site_capability_state(site, subscription_capability, status="Pending", source="Platform", error_excerpt=None, installed_apps=None):
	site_doc = frappe.get_doc("Site", site) if isinstance(site, str) else site
	payload = site_capability_payload(site_doc, subscription_capability, status=status, source=source, error_excerpt=error_excerpt, installed_apps=installed_apps)
	matched = None
	for row in site_doc.get("site_capability_state") or []:
		if row.subscription_capability == payload["subscription_capability"] or row.capability == payload["capability"]:
			matched = row
			break
	if matched:
		for key, value in payload.items():
			setattr(matched, key, value)
	else:
		site_doc.append("site_capability_state", payload)
	site_doc.save(ignore_permissions=True)
	return payload


@frappe.whitelist()
def sync_site_capability_state(site):
	site_doc = frappe.get_doc("Site", site)
	if not site_doc.subscription:
		return {"site": site_doc.name, "updated": 0, "message": "Site has no Subscription."}
	rows = frappe.get_all(
		"Subscription Capability",
		filters={"subscription": site_doc.subscription, "status": ["in", ["Requested", "Pending Approval", "Approved", "Provisioning", "Active", "Failed"]]},
		fields=["name", "status"],
	)
	updated = []
	for row in rows:
		status = "Active" if row.status == "Active" else "Pending"
		updated.append(upsert_site_capability_state(site_doc, row.name, status=status, source="Capability Fulfillment"))
	frappe.db.commit()
	return {"site": site_doc.name, "updated": len(updated), "states": updated}
