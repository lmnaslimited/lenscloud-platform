import re

import frappe
from frappe import _
from frappe.model.document import Document

SECRET_KEY = re.compile(r"(password|secret|token|private[_-]?key|credential|kubeconfig)", re.I)


def active_submitted_default(environment, exclude=None):
    filters = {
        "environment": environment,
        "is_default": 1,
        "status": "Active",
        "docstatus": 1,
    }
    if exclude:
        filters["name"] = ["!=", exclude]
    return frappe.db.exists("Site Control Profile", filters)


class SiteControlProfile(Document):
    def validate(self):
        self.profile_code = (self.profile_code or self.title or "").strip()
        if self.version and self.version < 1:
            frappe.throw(_("Version must be at least 1."))
        if self.require_bench_test and not self.enable_bench_test:
            frappe.throw(_("Bench Test must be enabled before it can be required."))
        if self.require_latp and not self.enable_latp:
            frappe.throw(_("LATP must be enabled before it can be required."))
        if self.environment:
            environment = frappe.get_doc("Environment", self.environment)
            levels = {"Permissive": 0, "Test": 1, "Production-like": 2, "Restricted": 3}
            if levels.get(self.protection_level, -1) < levels.get(environment.protection_level, -1):
                frappe.throw(_("Site Control Profile {0} is less restrictive than Environment {1}.").format(self.name or self.title, environment.name))
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

    def before_submit(self):
        if self.status != "Active":
            frappe.throw(_("Only Active Site Control Profile versions can be submitted."))
        self._validate_default_version()

    def on_update_after_submit(self):
        self._validate_default_version()

    def _validate_default_version(self):
        if not self.is_default or self.status != "Active":
            return
        duplicate = active_submitted_default(self.environment, self.name)
        if duplicate:
            frappe.throw(_("Site Control Profile {0} is already the default active submitted profile for Environment {1}.").format(duplicate, self.environment))
