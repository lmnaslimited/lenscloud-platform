import frappe
import frappe.sessions


no_cache = 1


def get_context(context):
	context.no_cache = 1
	context.boot = {}


	context.csrf_token = frappe.sessions.get_csrf_token()
	return context
