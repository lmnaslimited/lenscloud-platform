import frappe
from frappe import _
from frappe.model.document import Document


def default_site_control_profile(environment):
    return frappe.db.exists("Site Control Profile", {
        "environment": environment,
        "is_default": 1,
        "status": "Active",
        "docstatus": 1,
    })


class Landscape(Document):
    def validate(self):
        rows = self.get("environments") or []
        if len(rows) != int(self.tier_count or 0):
            frappe.throw(_("Tier Count must equal the number of Environment rows."))
        names = [row.environment for row in rows]
        if len(names) != len(set(names)):
            frappe.throw(_("Each Environment can appear only once in a Landscape."))
        sequences = [int(row.sequence or 0) for row in rows]
        if sequences != sorted(sequences) or len(sequences) != len(set(sequences)):
            frappe.throw(_("Landscape Environment sequence must be unique and ascending."))
        if not rows or rows[-1].environment != "Prod":
            frappe.throw(_("Every Landscape must end with Prod."))
        levels = {"Permissive": 0, "Test": 1, "Production-like": 2, "Restricted": 3}
        for row in rows:
            environment = frappe.get_doc("Environment", row.environment)
            if not row.site_control_profile:
                row.site_control_profile = default_site_control_profile(row.environment)
            if not row.site_control_profile:
                frappe.throw(_("Environment {0} has no default active submitted Site Control Profile.").format(row.environment))
            profile = frappe.get_doc("Site Control Profile", row.site_control_profile)
            if profile.docstatus != 1 or profile.status != "Active":
                frappe.throw(_("Landscape Environment {0} requires an active submitted Site Control Profile.").format(row.environment))
            if profile.environment != row.environment:
                frappe.throw(_("Site Control Profile {0} belongs to Environment {1}, not {2}.").format(profile.name, profile.environment, row.environment))
            if levels.get(profile.protection_level, -1) < levels.get(environment.protection_level, -1):
                frappe.throw(_("Site Control Profile {0} is less restrictive than Environment {1}.").format(profile.name, environment.name))
