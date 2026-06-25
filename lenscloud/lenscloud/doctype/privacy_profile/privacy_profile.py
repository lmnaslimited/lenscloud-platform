import frappe
from frappe import _
from frappe.model.document import Document


def active_submitted_default(privacy, exclude=None):
    filters = {
        "privacy": privacy,
        "is_default": 1,
        "docstatus": 1,
    }
    if exclude:
        filters["name"] = ["!=", exclude]
    return frappe.db.exists("Privacy Profile", filters)


class PrivacyProfile(Document):
    def autoname(self):
        if not self.privacy:
            return
        prefix = f"PP-{self.privacy}-"
        existing = set(frappe.get_all("Privacy Profile", filters={"name": ["like", f"{prefix}%"]}, pluck="name"))
        index = 1
        while True:
            candidate = f"{prefix}{index:02d}"
            if candidate not in existing:
                self.name = candidate
                return
            index += 1

    def before_validate(self):
        if self.privacy and not self.title:
            self.title = _("{0} Privacy Profile").format(self.privacy)

    def validate(self):
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

    def before_submit(self):
        self._validate_default_profile()

    def on_update_after_submit(self):
        self._validate_default_profile()

    def _validate_default_profile(self):
        if not self.is_default:
            return
        duplicate = active_submitted_default(self.privacy, self.name)
        if duplicate:
            frappe.throw(_("Privacy Profile {0} is already the default submitted profile for Privacy {1}.").format(duplicate, self.privacy))
