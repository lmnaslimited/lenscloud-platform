import frappe
from frappe import _
from frappe.model.document import Document


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
        for row in rows:
            environment = frappe.get_doc("Environment", row.environment)
            profile = frappe.get_doc("Site Control Profile", row.site_control_profile)
            levels = {"Permissive": 0, "Test": 1, "Production-like": 2, "Restricted": 3}
            if levels.get(profile.protection_level, -1) < levels.get(environment.protection_level, -1):
                frappe.throw(_("Site Control Profile {0} is less restrictive than Environment {1}.").format(profile.name, environment.name))
