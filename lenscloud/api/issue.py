# Copyright (c) 2026, LMNAs Cloud Solutions and contributors
# For license information, please see license.txt

import frappe
import requests

@frappe.whitelist(methods=["POST"])
def create_orchestration_issue(site, subscription, orchestration_action_log=None, summary=None, message_params_json=None):
    """Auto-creates an Issue upon orchestration failure."""
    from lenscloud.api.customer_identity import customer_membership_for_user

    membership = customer_membership_for_user(frappe.session.user)
    customer = membership.customer if membership else getattr(frappe.get_doc("Site", site), "customer", None)

    issue_data = {
        "doctype": "Issue",
        "customer_member": membership.name,
        "customer": customer,
        "subscription": subscription,
        "site": site,
        "category": "Issue",
        "status": "Open",
        "summary": summary,
        "description": message_params_json or "No detailed logs available.",
        "severity": "Low"
    }
    
    # Store Action Log link if your Issue DocType has this custom field
    if orchestration_action_log:
        issue_exist = frappe.get_list("Issue", filters={"orchestration_action_log": orchestration_action_log}, limit=1)
        if issue_exist:
            return
        if frappe.get_meta("Issue").has_field("orchestration_action_log"):
            issue_data["orchestration_action_log"] = orchestration_action_log

    issue = frappe.get_doc(issue_data)
    issue.insert(ignore_permissions=True)
    frappe.db.commit()

    return {"status": "success", "issue": issue.name}

@frappe.whitelist()
def add_issue_comment(issue_id, content):
    """
    Whitelisted API to sync a comment from a local Issue to its corresponding remote Issue.
    
    Params:
        issue_id (str): The local Issue document name/ID.
        content (str): The comment text content.
    """
    if not issue_id or not content:
        frappe.throw(frappe._("Both 'issue_id' and 'content' are required parameters."))

    # 1. Fetch local Issue document
    issue_doc = frappe.get_doc("Issue", issue_id)

    # Fetch configuration settings
    platform_settings = frappe.get_single("Platform Settings")

    if not platform_settings.get("support_integration_enabled"):
        # frappe.throw(frappe._("Support Integration is disabled in Platform Settings."))
        lenscloud_comment = frappe.get_doc({"doctype":"Comment", 
        "comment_type": "Comment",
        "reference_doctype": "Issue",
        "reference_name": issue_doc.name,
        "comment_by": issue_doc.email,
        "content": content,
        })
        lenscloud_comment.insert()
        return lenscloud_comment
    
    if not issue_doc.helpdesk_ticket_id:
        frappe.throw(
            frappe._("Issue {0} does not have a synced 'helpdesk_ticket_id'.").format(issue_id)
        )

    site2_url = platform_settings.get("support_system")
    api_key = platform_settings.get("support_api_key")
    api_secret = platform_settings.get_password("support_api_secret")

    if not (site2_url and api_key and api_secret):
        frappe.throw(frappe._("Platform Settings configuration is incomplete."))

    # 2. Build payload for remote Comment creation
    payload = {
        "comment_type": "Comment",
        "reference_doctype": "Issue",
        "reference_name": issue_doc.helpdesk_ticket_id,
        "comment_by": issue_doc.email,
        "content": content,
    }

    headers = {
        "Authorization": f"token {api_key}:{api_secret}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    endpoint = f"{site2_url}/api/resource/Comment"

    # 3. Post the request
    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        frappe.log_error(
            title=f"Failed to post comment for Issue {issue_id}",
            message=f"Endpoint: {endpoint}\nPayload: {payload}\nError: {e}",
        )
        frappe.throw(frappe._("Failed to post comment to remote support system. Check Error Log."))

@frappe.whitelist()
def get_helpdesk_comments(issue_id):
    """
    Whitelisted API to fetch comments for a local Issue from the remote support system.
    
    Params:
        issue_id (str): The local Issue document name/ID.
    """
    if not issue_id:
        frappe.throw(frappe._("Parameter 'issue_id' is required."))

    # 1. Fetch local Issue document
    issue_doc = frappe.get_doc("Issue", issue_id)

    # Fetch configuration settings
    platform_settings = frappe.get_single("Platform Settings")

    if not platform_settings.get("support_integration_enabled"):
      
        lenscloud_comment = frappe.get_all(
            "Comment",
            fields=["name", "comment_email", "comment_by", "content", "creation"],
            filters={
                "reference_doctype": "Issue",
                "reference_name": issue_doc.name,
                "comment_type": "Comment"
            },
            order_by="creation asc"
        )
        return lenscloud_comment
    
    if not issue_doc.helpdesk_ticket_id:
        return []

    site2_url = platform_settings.get("support_system")
    api_key = platform_settings.get("support_api_key")
    api_secret = platform_settings.get_password("support_api_secret")

    if not (site2_url and api_key and api_secret):
        frappe.log_error(
            title="Helpdesk comments fetch failed",
            message="Platform Settings configuration is incomplete."
        )
        return []

    headers = {
        "Authorization": f"token {api_key}:{api_secret}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # Query params for remote Frappe REST API
    endpoint = f"{site2_url}/api/resource/Comment"
    params = {
        "fields": '["name", "comment_email", "comment_by", "content", "creation"]',
        "filters": f'[["reference_doctype", "=", "Issue"], ["reference_name", "=", "{issue_doc.helpdesk_ticket_id}"], ["comment_type", "=", "Comment"]]',
        "order_by": "creation asc",
        "limit_page_length": 0,
    }

    try:
        response = requests.get(endpoint, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        response_data = response.json()
        return response_data.get("data", [])
    except requests.exceptions.RequestException as e:
        frappe.log_error(
            title=f"Failed to fetch remote comments for Issue {issue_id}",
            message=f"Endpoint: {endpoint}\nError: {e}",
        )
        return []
    

@frappe.whitelist()
def syn_comment_webhook():
   
    # Read payload cleanly
    data = frappe.request.get_json() if (frappe.request and frappe.request.is_json) else frappe.form_dict

    issue_id = data.get("issue_id")
    comments = data.get("comments")

    if not issue_id or not comments:
        frappe.throw(f"Missing required fields. Received keys: {list(data.keys())}")

    # Emit Socket.io event to Vue
    frappe.publish_realtime(
        event="nectar_comments_updated",
        message={
            "issue_id": issue_id,
            "comments": comments
        },
        doctype="Issue",      # <--- Your DocType name
        docname=issue_id,     # <--- Document ID (e.g., ISS-2026-001)
        after_commit=False    # Immediate release (doesn't wait for DB transaction)
    )

    return {"status": "success", "issue_id": issue_id}