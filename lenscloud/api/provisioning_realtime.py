import frappe


EVENT = "lenscloud_site_progress"


def customer_progress_users(site_doc):
	users = frappe.get_all(
		"Customer Member",
		filters={"customer": site_doc.customer, "status": "Active"},
		pluck="user",
	)
	legacy_user = frappe.db.get_value("Customer", site_doc.customer, "user")
	if legacy_user:
		users.append(legacy_user)
	return sorted({user for user in users if user and user != "Guest"})


def publish_customer_site_progress(site, snapshot=None, after_commit=True):
	"""Publish one canonical, customer-scoped progress snapshot."""
	site_doc = site if getattr(site, "doctype", None) == "Site" else frappe.get_doc("Site", site)
	if snapshot is None:
		from lenscloud.api.provisioning_progress import progress_snapshot
		snapshot = progress_snapshot(site_doc)
	for user in customer_progress_users(site_doc):
		frappe.publish_realtime(EVENT, snapshot, user=user, after_commit=after_commit)
	return snapshot


def publish_action_log_progress(log):
	if not getattr(log, "site", None):
		return None
	try:
		return publish_customer_site_progress(log.site)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "LensCloud Site Progress Realtime")
		return None
