# Copyright (c) 2026, LMNAs Cloud Solutions and contributors
# For license information, please see license.txt

import frappe
import requests
from frappe.model.document import Document
from frappe.utils import now_datetime


class Issue(Document):
    def after_insert(self):
        platform_settings = frappe.get_single("Platform Settings")

        if not platform_settings.get("support_integration_enabled"):
            return

        support_url = platform_settings.get("support_system")
        api_key = platform_settings.get("support_api_key")
        api_secret = platform_settings.get_password("support_api_secret")

        if not (support_url and api_key and api_secret):
            frappe.log_error(
                title="Support sync: config missing",
                message=(
                    "Platform Settings is missing support_system, support_api_key, "
                    "or support_api_secret. support_integration_enabled is on but "
                    "credentials are incomplete."
                ),
            )
            return

        payload = {
            "customer": self.external_customer_id,
            "raised_by": self.email,
            "issue_type": self.category or "Issue",
            "subject": self.summary or "",
            "description": self.description or "",
            "priority": self.severity,
            "status": self.status or "Open",
        }

        headers = {
            "Authorization": f"token {api_key}:{api_secret}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        endpoint = f"{support_url.rstrip('/')}/api/resource/Issue"

        try:
            response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            response_data = response.json()
        except requests.exceptions.RequestException as e:
            frappe.log_error(
                title=f"Support sync failed: {self.name}",
                message=f"Failed to sync Issue {self.name} to {support_url}.\nError: {e}",
            )
            return
        # Extract the created ticket ID from Frappe's standard response format: {"data": {"name": "..."}}
        ticket_id = response_data.get("data", {}).get("name")
        if ticket_id:
            frappe.db.set_value(
                "Issue",
                self.name,
                {
                    "helpdesk_ticket_id": ticket_id,
                    "last_sync": now_datetime(),
                },
            )
        else:
            frappe.db.set_value("Issue", self.name, "last_sync", now_datetime())
            frappe.log_error(
                title=f"Support sync warning: {self.name}",
                message=f"Ticket created on remote site, but 'name' key was missing in response: {response_data}",
            )