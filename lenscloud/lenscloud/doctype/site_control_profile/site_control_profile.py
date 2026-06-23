import re

import frappe
from frappe import _
from frappe.model.document import Document

SECRET_KEY = re.compile(r"(password|secret|token|private[_-]?key|credential|kubeconfig)", re.I)


class SiteControlProfile(Document):
    def validate(self):
        if self.version and self.version < 1:
            frappe.throw(_("Version must be at least 1."))
        if self.require_bench_test and not self.enable_bench_test:
            frappe.throw(_("Bench Test must be enabled before it can be required."))
        if self.require_latp and not self.enable_latp:
            frappe.throw(_("LATP must be enabled before it can be required."))
        if self.protection_level == "Restricted":
            if self.enable_developer_mode or self.allow_server_scripts:
                frappe.throw(_("Restricted profiles cannot enable developer mode or server scripts."))
            if self.enable_bench_test:
                frappe.throw(_("Restricted profiles cannot run Bench Test."))
            if self.enable_latp and self.latp_mode != "Non-destructive":
                frappe.throw(_("Restricted profiles permit non-destructive LATP only."))
        if self.cors_policy == "Allowlist" and not (self.cors_origins or "").strip():
            frappe.throw(_("CORS Allowlist requires at least one origin."))
        if self.cors_policy == "Disabled":
            self.cors_origins = None
        seen = set()
        for row in self.get("settings") or []:
            key = (row.setting_key or "").strip()
            if not key or SECRET_KEY.search(key):
                frappe.throw(_("Site Control settings cannot contain secret or credential keys."))
            if key in seen:
                frappe.throw(_("Duplicate Site Control setting: {0}.").format(key))
            seen.add(key)
