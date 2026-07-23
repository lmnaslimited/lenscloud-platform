# import requests
# import frappe

# def sync_comment_to_target(doc, method):
#     """
#     Triggered whenever a Comment is added on Site 1.
#     If linked to an Issue, pushes the comment to the Target Site.
#     """
#     # Only process comments made on the Issue DocType
#     if doc.reference_doctype != "Issue":
#         return

#     # Fetch local Issue to get target_issue_id
#     issue = frappe.get_doc("Issue", doc.reference_name)
#     if not issue.target_issue_id:
#         return  # Issue hasn't been synced to target site yet

#     # Fetch Platform Settings for credentials
#     platform_settings = frappe.get_single("Platform Settings")
#     site2_url = platform_settings.get("support_system", "").rstrip("/")
#     api_key = platform_settings.get("support_api_key")
#     api_secret = platform_settings.get_password("support_api_secret")

#     if not (site2_url and api_key and api_secret):
#         return

#     # Post comment directly to Target Site using Frappe's standard Comment REST API
#     endpoint = f"{site2_url}/api/resource/Comment"
    
#     payload = {
#         "comment_type": "Comment",
#         "reference_doctype": "Issue",
#         "reference_name": issue.target_issue_id,
#         "content": doc.content,
#         "comment_email": frappe.session.user,
#         "comment_by": doc.created_by or frappe.session.user_fullname,
#     }

#     headers = {
#         "Authorization": f"token {api_key}:{api_secret}",
#         "Content-Type": "application/json",
#     }

#     try:
#         response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
#         response.raise_for_status()
#     except requests.exceptions.RequestException as e:
#         frappe.log_error(
#             title="Comment Sync to Target Failed",
#             message=f"Failed to push comment for Issue {issue.name} to Target Site.\nError: {str(e)}"
#         )

# @frappe.whitelist()
# def sync_from_support_system(self):
#     """
#     Pulls latest status and comments from the remote support system.
#     Usage: doc.sync_from_support_system() or via JS frm.call()
#     """
#     if not getattr(self, "remote_issue_id", None):
#         frappe.throw("This Issue is not linked to any Remote Issue ID.")

#     # 1. Get credentials from Platform Settings
#     platform_settings = frappe.get_single("Platform Settings")
#     support_url = platform_settings.get("support_system", "").rstrip("/")
#     api_key = platform_settings.get("support_api_key")
#     api_secret = platform_settings.get_password("support_api_secret")

#     if not (support_url and api_key and api_secret):
#         frappe.throw("Platform Settings credentials are incomplete.")

#     headers = {
#         "Authorization": f"token {api_key}:{api_secret}",
#         "Accept": "application/json",
#     }

#     # ----------------------------------------------------
#     # STEP 1: Sync Remote Status
#     # ----------------------------------------------------
#     endpoint = f"{support_url}/api/resource/Issue/{self.remote_issue_id}"
    
#     try:
#         res = requests.get(endpoint, headers=headers, timeout=10)
#         res.raise_for_status()
#         remote_doc = res.json().get("data", {})

#         remote_status = remote_doc.get("status")
#         if remote_status and remote_status != self.status:
#             self.status = remote_status
#             self.save(ignore_permissions=True)

#     except requests.exceptions.RequestException as e:
#         frappe.log_error(title="Failed to fetch Remote Issue", message=str(e))

#     # ----------------------------------------------------
#     # STEP 2: Sync Remote Comments
#     # ----------------------------------------------------
#     filters = [
#         ["reference_doctype", "=", "Issue"],
#         ["reference_name", "=", self.remote_issue_id],
#         ["comment_type", "=", "Comment"]
#     ]
    
#     comment_endpoint = f"{support_url}/api/resource/Comment?filters={frappe.as_json(filters)}&fields=[\"name\",\"content\",\"comment_by\"]"
    
#     try:
#         c_res = requests.get(comment_endpoint, headers=headers, timeout=10)
#         c_res.raise_for_status()
#         comments = c_res.json().get("data", [])

#         for comm in comments:
#             # Check for duplicates before creating
#             exists = frappe.db.exists("Comment", {
#                 "reference_doctype": "Issue",
#                 "reference_name": self.name,
#                 "content": comm.get("content")
#             })

#             if not exists:
#                 frappe.get_doc({
#                     "doctype": "Comment",
#                     "comment_type": "Comment",
#                     "reference_doctype": "Issue",
#                     "reference_name": self.name,
#                     "comment_by": comm.get("comment_by", "Support Team"),
#                     "content": comm.get("content")
#                 }).insert(ignore_permissions=True)

#         frappe.db.commit()

#     except requests.exceptions.RequestException as e:
#         frappe.log_error(title="Failed to fetch Remote Comments", message=str(e))

#     return {"status": "success", "message": "Synced from Support System successfully."}


# # ------------------------------------------------------------------
# # Incoming API Endpoints (For Push Updates from Support System)
# # ------------------------------------------------------------------

# @frappe.whitelist(allow_guest=False)
# def update_issue_status(remote_issue_id, status):
#     """
#     Endpoint for support system to push status updates in real-time.
#     """
#     if not remote_issue_id or not status:
#         frappe.throw("Both 'remote_issue_id' and 'status' are required.")

#     issue_name = frappe.db.get_value("Issue", {"remote_issue_id": remote_issue_id}, "name")
#     if not issue_name:
#         frappe.throw(f"No Issue found for Remote ID: {remote_issue_id}")

#     frappe.db.set_value("Issue", issue_name, "status", status)
#     frappe.db.commit()

#     return {"status": "success", "message": f"Updated {issue_name} status to {status}"}

# def sync_all_open_issues():
#     """
#     Scheduled background job task.
#     """
#     open_issues = frappe.get_all("Issue", filters={"status": ["!=", "Closed"], "remote_issue_id": ["is", "set"]})
#     for item in open_issues:
#         doc = frappe.get_doc("Issue", item.name)
#         doc.sync_from_support_system()


import frappe

@frappe.whitelist(methods=["POST"])
def create_orchestration_issue(site, subscription, action_log=None, summary=None, message_params_json=None):
    """Auto-creates an Issue upon orchestration failure."""
    from lenscloud.api.customer_identity import customer_membership_for_user

    membership = customer_membership_for_user(frappe.session.user)
    customer = membership.customer if membership else getattr(frappe.get_doc("Site", site), "customer", None)

    issue_data = {
        "doctype": "Issue",
        "customer": customer,
        "subscription": subscription,
        "site": site,
        "category": "Technical",
        "status": "Open",
        "summary": summary,
        "description": message_params_json or "No detailed logs available.",
        "severity": "S"
    }
    
    # Store Action Log link if your Issue DocType has this custom field
    if action_log and frappe.get_meta("Issue").has_field("orchestration_action_log"):
        issue_data["orchestration_action_log"] = action_log

    issue = frappe.get_doc(issue_data)
    issue.insert(ignore_permissions=True)
    frappe.db.commit()

    return {"status": "success", "issue": issue.name}