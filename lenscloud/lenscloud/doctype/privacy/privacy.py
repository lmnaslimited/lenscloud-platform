import frappe
from frappe import _
from frappe.model.document import Document


class Privacy(Document):
    def validate(self):
        if self.version and self.version < 1:
            frappe.throw(_("Version must be at least 1."))
        rows = self.get("environment_rules") or []
        names = [row.environment for row in rows]
        if len(names) != len(set(names)):
            frappe.throw(_("Privacy Profile can contain only one rule per Environment."))
        production = next((row for row in rows if row.environment == "Prod"), None)
        if production:
            for row in rows:
                if row.environment == "Prod":
                    continue
                same_boundary = row.database_boundary == production.database_boundary
                same_group = row.database_group == production.database_group
                if same_boundary and same_group:
                    frappe.throw(_("Prod Database policy cannot share a Database group with non-production Environments."))
