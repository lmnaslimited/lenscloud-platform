import re

import frappe
from frappe import _
from frappe.utils import now_datetime

PLATFORM_ROLES = {"Administrator", "System Manager", "Workspace Manager", "LensCloud Platform Admin", "LensCloud Operator", "LensCloud Platform User"}
PUBLIC_EMAIL_DOMAINS = {
	"gmail.com", "googlemail.com", "outlook.com", "hotmail.com", "live.com", "msn.com",
	"yahoo.com", "icloud.com", "me.com", "mac.com", "aol.com", "proton.me", "protonmail.com",
	"zoho.com", "hey.com", "pm.me", "mail.com", "gmx.com", "gmx.net", "yandex.com",
}


CUSTOMER_ADMIN_MEMBER_ROLES = {"Owner", "Admin"}
ROLE_PROFILE_HOME_FIELDS = ("home_page_path", "home_page", "default_home_page")
DEFAULT_CUSTOMER_ADMIN_ROLE_PROFILE = "LensCloud Customer Admin"
DEFAULT_CUSTOMER_MEMBER_ROLE_PROFILE = "LensCloud Customer Member"


def platform_setting(fieldname):
	try:
		return frappe.db.get_single_value("Platform Settings", fieldname)
	except Exception:
		return None


def customer_role_profile(role="Member", status="Active"):
	if status == "Active" and role in CUSTOMER_ADMIN_MEMBER_ROLES:
		configured = platform_setting("default_customer_admin_role_profile")
		return configured or (DEFAULT_CUSTOMER_ADMIN_ROLE_PROFILE if frappe.db.exists("Role Profile", DEFAULT_CUSTOMER_ADMIN_ROLE_PROFILE) else None)
	configured = platform_setting("default_customer_member_role_profile")
	return configured or (DEFAULT_CUSTOMER_MEMBER_ROLE_PROFILE if frappe.db.exists("Role Profile", DEFAULT_CUSTOMER_MEMBER_ROLE_PROFILE) else None)


def configured_customer_role_profiles():
	return {
		value for value in [
			platform_setting("default_customer_admin_role_profile"),
			platform_setting("default_customer_member_role_profile"),
			DEFAULT_CUSTOMER_ADMIN_ROLE_PROFILE if frappe.db.exists("Role Profile", DEFAULT_CUSTOMER_ADMIN_ROLE_PROFILE) else None,
			DEFAULT_CUSTOMER_MEMBER_ROLE_PROFILE if frappe.db.exists("Role Profile", DEFAULT_CUSTOMER_MEMBER_ROLE_PROFILE) else None,
		] if value
	}


def assign_role_profile(user, role="Member", status="Active"):
	profile = customer_role_profile(role, status)
	if not profile or not frappe.db.exists("Role Profile", profile):
		return None
	user_doc = frappe.get_doc("User", user)
	configured = configured_customer_role_profiles()
	existing = [row.role_profile for row in (user_doc.get("role_profiles") or [])]
	current = [item for item in existing if item not in configured]
	if profile not in current:
		current.append(profile)
	if existing == current:
		return profile
	user_doc.set("role_profiles", [{"role_profile": item} for item in current])
	user_doc.save(ignore_permissions=True)
	frappe.clear_cache(user=user)
	return profile


def ensure_customer_user_permission(user, customer):
	if not user or not customer:
		return None
	for row in frappe.get_all("User Permission", filters={"user": user, "allow": "Customer", "for_value": ["!=", customer]}, pluck="name"):
		frappe.delete_doc("User Permission", row, ignore_permissions=True)
	existing = frappe.db.exists("User Permission", {"user": user, "allow": "Customer", "for_value": customer, "apply_to_all_doctypes": 1})
	if existing:
		if not frappe.db.get_value("User Permission", existing, "is_default"):
			frappe.db.set_value("User Permission", existing, "is_default", 1, update_modified=False)
		return existing
	doc = frappe.get_doc({
		"doctype": "User Permission",
		"user": user,
		"allow": "Customer",
		"for_value": customer,
		"is_default": 1,
		"apply_to_all_doctypes": 1,
	})
	doc.insert(ignore_permissions=True)
	frappe.clear_cache(user=user)
	return doc.name


def apply_customer_access(user, customer, role="Member", status="Active"):
	if not user or not customer:
		return None
	ensure_customer_user_permission(user, customer)
	return assign_role_profile(user, role, status)


def ensure_customer_access_for_user(user=None):
	user = user or frappe.session.user
	if not user or user == "Guest":
		return None
	membership = customer_membership_for_user(user)
	if membership:
		apply_customer_access(user, membership.customer, membership.member_role, membership.status)
		return membership
	customer = frappe.db.get_value("Customer", {"user": user}, "name")
	if customer:
		apply_customer_access(user, customer, "Owner", "Active")
		return frappe._dict({"customer": customer, "status": "Active", "member_role": "Owner", "is_primary_owner": 1})
	return None


def role_profile_home_page(user):
	profiles = frappe.get_all("User Role Profile", filters={"parent": user, "parenttype": "User"}, pluck="role_profile")
	meta = frappe.get_meta("Role Profile")
	for profile in profiles:
		if not frappe.db.exists("Role Profile", profile):
			continue
		for fieldname in ROLE_PROFILE_HOME_FIELDS:
			if meta.has_field(fieldname):
				value = frappe.db.get_value("Role Profile", profile, fieldname)
				if value:
					return str(value).strip().lstrip("/")
	return None


def can_manage_customer_members(user=None):
	user = user or frappe.session.user
	if user == "Guest":
		return False
	return bool(frappe.has_permission("Customer Member", "read", user=user))


def can_create_subscription(user=None):
	user = user or frappe.session.user
	if user == "Guest":
		return False
	return bool(frappe.has_permission("Subscription", "create", user=user))


def customer_doctype_permissions(user=None):
	user = user or frappe.session.user
	if user == "Guest":
		return {}
	return {
		"Plan": {"read": bool(frappe.has_permission("Plan", "read", user=user))},
		"Capability": {"read": bool(frappe.has_permission("Capability", "read", user=user))},
		"Subscription": {
			"read": bool(frappe.has_permission("Subscription", "read", user=user)),
			"create": bool(frappe.has_permission("Subscription", "create", user=user)),
		},
		"Site": {"read": bool(frappe.has_permission("Site", "read", user=user))},
		"Customer Member": {
			"read": bool(frappe.has_permission("Customer Member", "read", user=user)),
			"write": bool(frappe.has_permission("Customer Member", "write", user=user)),
		},
	}


def can_read_customer_doctype(doctype, user=None):
	return bool(customer_doctype_permissions(user).get(doctype, {}).get("read"))


def require_subscription_create_permission(user=None):
	user = user or frappe.session.user
	if not can_create_subscription(user):
		frappe.throw(_("Your LensCloud role does not allow creating subscriptions. Ask a Customer admin to start or approve subscriptions for this Customer."), frappe.PermissionError)


def normalize_email(value):
	return (value or "").strip().lower()


def email_domain(email):
	email = normalize_email(email)
	if "@" not in email:
		return ""
	return email.rsplit("@", 1)[1]


def is_public_email_domain(domain):
	return (domain or "").lower() in PUBLIC_EMAIL_DOMAINS


def organization_from_domain(domain):
	if not domain:
		return "Individual Customer"
	name = domain.split(".", 1)[0]
	return re.sub(r"[^A-Za-z0-9]+", " ", name).strip().title() or domain


def split_name(user_doc):
	first = (user_doc.get("first_name") or user_doc.get("full_name") or user_doc.name or "").strip()
	last = (user_doc.get("last_name") or "").strip()
	if not last and first and " " in first:
		parts = first.split()
		first = parts[0]
		last = " ".join(parts[1:])
	return first, last


def resolve_signup_region():
	settings_region = None
	try:
		settings_region = frappe.db.get_single_value("Platform Settings", "default_signup_region")
	except Exception:
		settings_region = None
	if settings_region and frappe.db.exists("Region", settings_region):
		return settings_region
	active = frappe.get_all("Region", filters={"deployment_status": "Active"}, pluck="name", limit=2)
	if len(active) == 1:
		return active[0]
	if frappe.db.exists("Region", "EU"):
		return "EU"
	return active[0] if active else None


def user_has_platform_role(user):
	roles = set(frappe.get_roles(user) or [])
	return bool(roles & PLATFORM_ROLES)


def should_provision_customer_for_user(user_doc):
	if user_doc.name in {"Guest", "Administrator"}:
		return False
	if not int(user_doc.get("enabled") or 0):
		return False
	if user_doc.get("user_type") != "Website User":
		return False
	if user_has_platform_role(user_doc.name):
		return False
	return bool(normalize_email(user_doc.get("email") or user_doc.name))


def existing_active_customer_for_user(user):
	customer = frappe.db.get_value("Customer", {"user": user}, "name")
	if customer:
		return customer
	member = frappe.db.get_value("Customer Member", {"user": user, "status": "Active"}, "customer")
	return member


def customer_membership_for_user(user):
	return frappe.db.get_value("Customer Member", {"user": user}, ["name", "customer", "status", "member_role", "is_primary_owner"], as_dict=True)


def upsert_member(customer, user, role="Member", status="Pending", source="Signup", primary_owner=0):
	existing = frappe.db.exists("Customer Member", {"customer": customer, "user": user})
	if existing:
		doc = frappe.get_doc("Customer Member", existing)
		changed = False
		for field, value in {"member_role": role, "status": status, "source": source, "is_primary_owner": primary_owner}.items():
			if doc.get(field) != value:
				doc.set(field, value)
				changed = True
		if status == "Active" and not doc.approved_on:
			doc.approved_on = now_datetime()
			changed = True
		if changed:
			doc.save(ignore_permissions=True)
		apply_customer_access(user, customer, role, status)
		return doc
	doc = frappe.get_doc({
		"doctype": "Customer Member",
		"customer": customer,
		"user": user,
		"member_role": role,
		"status": status,
		"source": source,
		"is_primary_owner": primary_owner,
		"approved_on": now_datetime() if status == "Active" else None,
	})
	doc.insert(ignore_permissions=True)
	apply_customer_access(user, customer, role, status)
	return doc


def create_customer_for_user(user_doc, domain, source="Signup", status="Active"):
	first, last = split_name(user_doc)
	region = resolve_signup_region()
	if not region:
		frappe.throw(_("A default signup Region or active Region is required before customer signup can create an account."))
	is_public = is_public_email_domain(domain)
	customer = frappe.get_doc({
		"doctype": "Customer",
		"first_name": first or user_doc.name,
		"last_name": last,
		"organization_name": user_doc.get("company") or (first or user_doc.name if is_public else organization_from_domain(domain)),
		"primary_domain": "" if is_public else domain,
		"signup_source": source,
		"user": user_doc.name if status == "Active" else None,
		"region": region,
	})
	customer.insert(ignore_permissions=True)
	upsert_member(customer.name, user_doc.name, role="Owner", status=status, source=source, primary_owner=1 if status == "Active" else 0)
	return customer.name


def provision_customer_for_user(user_doc, source="Signup"):
	if isinstance(user_doc, str):
		user_doc = frappe.get_doc("User", user_doc)
	if not should_provision_customer_for_user(user_doc):
		return None
	existing = customer_membership_for_user(user_doc.name)
	if existing:
		return existing.customer
	active_customer = existing_active_customer_for_user(user_doc.name)
	if active_customer:
		upsert_member(active_customer, user_doc.name, role="Owner", status="Active", source=source, primary_owner=1)
		return active_customer
	domain = email_domain(user_doc.get("email") or user_doc.name)
	if domain and not is_public_email_domain(domain):
		matched_customer = frappe.db.get_value("Customer", {"primary_domain": domain}, "name")
		if matched_customer:
			upsert_member(matched_customer, user_doc.name, role="Member", status="Pending", source="Domain Match", primary_owner=0)
			return matched_customer
	return create_customer_for_user(user_doc, domain, source=source, status="Active")


def get_lenscloud_home_page(user=None):
	user = user or frappe.session.user
	if not user or user == "Guest":
		return "login"
	profile_home = role_profile_home_page(user)
	if profile_home:
		return profile_home
	if user_has_platform_role(user):
		return "lenscloud/platform/dashboard"
	if customer_membership_for_user(user) or frappe.db.exists("Customer", {"user": user}):
		return "lenscloud/customer/dashboard"
	user_type = frappe.db.get_value("User", user, "user_type")
	if user_type == "Website User":
		return "lenscloud/customer/dashboard"
	return None


def provision_customer_for_user_after_insert(doc, method=None):
	public_signup = frappe.session.user == "Guest" or bool(getattr(doc.flags, "lenscloud_signup_provision_customer", False))
	if not public_signup:
		return
	try:
		provision_customer_for_user(doc, source="Signup")
	except Exception:
		frappe.log_error(title="LensCloud customer signup provisioning failed", message=frappe.get_traceback())


def require_active_customer_membership(user=None):
	user = user or frappe.session.user
	ensure_customer_access_for_user(user)
	membership = customer_membership_for_user(user)
	if membership and membership.status == "Active":
		return membership
	if frappe.db.exists("Customer", {"user": user}):
		customer = frappe.db.get_value("Customer", {"user": user}, "name")
		return frappe._dict({"customer": customer, "status": "Active", "member_role": "Owner", "is_primary_owner": 1})
	if membership and membership.status == "Pending":
		frappe.throw(_("Your LensCloud account is linked to an organization and is waiting for approval by a Customer admin."), frappe.PermissionError)
	frappe.throw(_("Your LensCloud customer account is not active yet."), frappe.PermissionError)


@frappe.whitelist()
def get_customer_access_context():
	membership = ensure_customer_access_for_user(frappe.session.user) if frappe.session.user != "Guest" else None
	recent_plan = None
	if membership:
		latest = frappe.get_all(
			"Subscription",
			filters={"customer": membership.customer, "status": ["not in", ["Cancelled", "Failed"]]},
			fields=["plan"],
			order_by="modified desc",
			limit=1,
		)
		if latest:
			recent_plan = frappe.db.get_value("Plan", latest[0].plan, "title") or latest[0].plan
	permissions = customer_doctype_permissions()
	return {
		"membership": membership,
		"recent_plan": recent_plan,
		"can_manage_members": permissions.get("Customer Member", {}).get("read", False),
		"can_create_subscription": permissions.get("Subscription", {}).get("create", False),
		"doctype_permissions": permissions,
	}


@frappe.whitelist()
def list_customer_members():
	membership = require_active_customer_membership()
	if not frappe.has_permission("Customer Member", "read"):
		frappe.throw(_("You do not have access to Customer Members."), frappe.PermissionError)
	return frappe.get_list(
		"Customer Member",
		filters={"customer": membership.customer},
		fields=["name", "customer", "user", "member_role", "status", "source", "is_primary_owner", "approved_by", "approved_on", "modified"],
		order_by="modified desc",
	)


@frappe.whitelist(methods=["POST"])
def approve_customer_member(member, member_role="Member"):
	actor_membership = require_active_customer_membership()
	if not frappe.has_permission("Customer Member", "write"):
		frappe.throw(_("You do not have permission to approve Customer Members."), frappe.PermissionError)
	doc = frappe.get_doc("Customer Member", member)
	if doc.customer != actor_membership.customer:
		frappe.throw(_("This member does not belong to your Customer."), frappe.PermissionError)
	if member_role not in {"Admin", "Member", "Viewer"}:
		frappe.throw(_("Choose a valid member role."))
	doc.member_role = member_role
	doc.status = "Active"
	doc.approved_by = frappe.session.user
	doc.approved_on = now_datetime()
	doc.save(ignore_permissions=True)
	apply_customer_access(doc.user, doc.customer, doc.member_role, doc.status)
	return {"name": doc.name, "status": doc.status, "member_role": doc.member_role}
