# Copyright (c) 2026, LMNAs Cloud Solutions and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe
import requests


class Issue(Document):
	# def after_insert(self):
	# 	# Fetch settings from Platform Settings (Single DocType)
	# 	platform_settings = frappe.get_single("Platform Settings")
		
	# 	site2_url = platform_settings.get("support_system")
	# 	api_key = platform_settings.get("support_api_key")
		
	# 	# If support_api_secret is a Password field type, use get_password() to decrypt it
	# 	api_secret = platform_settings.get_password("support_api_secret")

	# 	# Safety check: ensure settings are configured
	# 	if not (site2_url and api_key and api_secret):
	# 		frappe.log_error(
	# 			title="Site Sync Configuration Missing",
	# 			message="Platform Settings is missing support_system, support_api_key, or support_api_secret."
	# 		)
	# 		return

	# 	# Ensure base URL doesn't have a trailing slash
	# 	site2_url = site2_url.rstrip("/")

	# 	# Build payload needed to be changed
	# 	payload = {
	# 		"customer": self.customer,
	# 		"subscription": self.subscription,
	# 		"site": getattr(self, "site", None),
	# 		"category": getattr(self, "category", "Technical"),
	# 		"summary": getattr(self, "summary", ""),
	# 		"description": getattr(self, "description", ""),
	# 		"severity": getattr(self, "severity", None),
	# 		"status": getattr(self, "status", "Open"),
	# 	}

	# 	# Headers & API Post
	# 	headers = {
	# 		"Authorization": f"token {api_key}:{api_secret}",
	# 		"Content-Type": "application/json",
	# 		"Accept": "application/json",
	# 	}

	# 	endpoint = f"{site2_url}/api/resource/Issue"

	# 	try:
	# 		response = requests.post(
	# 			endpoint, json=payload, headers=headers, timeout=10
	# 		)
	# 		response.raise_for_status()

	# 	except requests.exceptions.RequestException as e:
	# 		frappe.log_error(
	# 			title="Site 2 Sync Failed",
	# 			message=f"Failed to sync Issue {self.name} to {site2_url}.\nError: {str(e)}",
	# 		)
	pass