import frappe
from frappe import _
from frappe.utils import cint

from lenscloud.api.customer_identity import require_active_customer_membership
from lenscloud.api.orchestration import (
	latest_site_bootstrap_status,
	orchestrate_customer_site_bootstrap,
	orchestrate_customer_site_oauth,
	orchestrate_customer_site_setup,
	set_site_oauth_state,
	site_command_in_progress,
)


OPERATIONS = ("site_bootstrap.install_apps", "site_setup.complete", "site_setup.status", "oauth.configure", "oauth.status")


def require_customer_site(site):
	if frappe.session.user == "Guest":
		frappe.throw(_("Authentication is required."), frappe.PermissionError)
	membership = require_active_customer_membership(frappe.session.user)
	site_doc = frappe.get_doc("Site", site)
	if site_doc.customer != membership.customer:
		frappe.throw(_("You can access only your own Site setup."), frappe.PermissionError)
	return site_doc


def progress_snapshot(site_doc):
	rows = frappe.get_all(
		"Orchestration Action Log",
		filters={"site": site_doc.name, "operation": ["in", OPERATIONS]},
		fields=["name", "status", "operation", "modified", "message_id", "customer_message", "operator_message", "retryability", "resolution_owner"],
		order_by="modified desc",
		limit=20,
	)
	active = next((row for row in rows if row.status in {"Queued", "Running"}), None)
	failed = rows[0] if rows and rows[0].status == "Failed" else None
	bootstrap = next((row for row in rows if row.operation == "site_bootstrap.install_apps"), None)
	setup = getattr(site_doc, "setup_status", None) or "Not Checked"
	oauth = getattr(site_doc, "oauth_status", None) or "Not Checked"
	stage, status = "requested", "pending"
	if failed and not active:
		stage = {"Customer": "blocked_customer_input", "Platform": "blocked_platform_action", "Infra": "blocked_infra_action"}.get(failed.resolution_owner, "failed")
		status = "failed"
	elif active:
		stage = {"site_bootstrap.install_apps": "bootstrap_installing", "site_setup.complete": "setup_completing", "site_setup.status": "setup_verifying", "oauth.configure": "oauth_configuring", "oauth.status": "oauth_verifying"}[active.operation]
		status = "running"
	elif site_doc.route_status == "Ready" and site_doc.access_url and setup == "Complete" and oauth in {"Configured", "Enabled"}:
		stage, status = "ready", "succeeded"
	elif site_doc.route_status != "Ready":
		stage = "route_pending" if site_doc.access_url else "runtime_reconciling"
	elif not bootstrap or bootstrap.status != "Succeeded":
		stage = "bootstrap_installing"
	elif setup in {"Not Checked", "Pending", "Required", ""}:
		stage = "setup_completing"
	elif setup == "Running":
		stage = "setup_verifying"
	elif setup == "Blocked":
		stage, status = "blocked_customer_input", "blocked"
	elif oauth in {"Not Checked", "Required", "Pending", ""}:
		stage = "oauth_configuring"
	elif oauth == "Running":
		stage = "oauth_verifying"
	message = failed or active
	retryability = message.retryability if message else None
	return {
		"site": site_doc.name, "stage": stage, "stage_status": status,
		"active_operation": active.operation if active else None, "active_action_log": active.name if active else None,
		"can_retry": bool(message and retryability in {"Retryable", "Retry After Delay"}),
		"can_continue": not active and status not in {"failed", "blocked", "succeeded"},
		"message_id": message.message_id if message else None, "customer_message": message.customer_message if message else None,
		"operator_message": message.operator_message if message else None, "retryability": retryability,
		"resolution_owner": message.resolution_owner if message else None, "updated_at": str((active or failed or site_doc).modified),
	}


@frappe.whitelist()
def get_customer_site_progress(site):
	"""Read canonical provisioning truth without syncing runtime or enqueueing work."""
	return progress_snapshot(require_customer_site(site))


@frappe.whitelist(methods=["POST"])
def advance_customer_site_provisioning(site, force=False):
	"""Advance at most one provisioning operation."""
	site_doc = require_customer_site(site)
	if any(site_command_in_progress(site_doc, operation) for operation in OPERATIONS):
		return progress_snapshot(site_doc)
	if site_doc.route_status != "Ready" or not site_doc.access_url:
		return progress_snapshot(site_doc)
	bootstrap = latest_site_bootstrap_status(site_doc)
	if not bootstrap or bootstrap.status != "Succeeded":
		orchestrate_customer_site_bootstrap(site_doc)
		return progress_snapshot(site_doc)
	setup = getattr(site_doc, "setup_status", None) or "Not Checked"
	if setup == "Failed" and not cint(force):
		return progress_snapshot(site_doc)
	if setup in {"Not Checked", "Pending", "Required", "Failed", ""}:
		site_doc.setup_status = "Required"
		site_doc.setup_error = None
		site_doc.save(ignore_permissions=True)
		orchestrate_customer_site_setup(site_doc, force=cint(force))
		return progress_snapshot(site_doc)
	if setup == "Running":
		orchestrate_customer_site_setup(site_doc, force=cint(force))
		return progress_snapshot(site_doc)
	oauth = getattr(site_doc, "oauth_status", None) or "Not Checked"
	if setup == "Complete" and oauth in {"Not Checked", "Required", "Pending", ""}:
		set_site_oauth_state(site_doc, "Pending", None)
		orchestrate_customer_site_oauth(site_doc)
	elif setup == "Complete" and oauth == "Running":
		orchestrate_customer_site_oauth(site_doc)
	return progress_snapshot(site_doc)
