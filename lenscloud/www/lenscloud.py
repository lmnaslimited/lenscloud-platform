import frappe
import frappe.sessions
from frappe.utils import cint


no_cache = 1


def get_boot():
	site_name = getattr(frappe.local, "site", None)
	if not site_name:
		raise RuntimeError(
			"Frappe site context is unavailable; realtime cannot be initialized"
		)

	socketio_port = cint(frappe.conf.get("socketio_port") or 9000)
	if socketio_port <= 0:
		raise RuntimeError("socketio_port must be a positive integer")

	csrf_token = frappe.sessions.get_csrf_token()
	if not csrf_token:
		raise RuntimeError("Frappe did not provide a CSRF token")

	return frappe._dict(
		site_name=site_name,
		socketio_port=socketio_port,
		csrf_token=csrf_token,
	)


def get_context(context):
	context.no_cache = 1
	context.boot = get_boot()
	context.csrf_token = context.boot.csrf_token
	return context


@frappe.whitelist(methods=["GET"], allow_guest=True)
def get_context_for_dev():
	if not frappe.conf.developer_mode:
		frappe.throw(
			"This method is available only in developer mode",
			frappe.PermissionError,
		)

	return get_boot()