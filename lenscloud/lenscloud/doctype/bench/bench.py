# Copyright (c) 2026, LMNAs Cloud Solutions and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from lenscloud.api.orchestration import ensure_operator_fields, get_region_cluster, validate_database_server_placement_doc


class Bench(Document):
	def validate(self):
		if not self.region:
			return
		cluster = get_region_cluster(self.region)
		ensure_operator_fields(self, cluster)
		if self.current_release:
			release_group = frappe.db.get_value("Release", self.current_release, "release_group")
			if release_group and self.release_group != release_group:
				frappe.throw(_("Current Release must belong to the selected Release Group."))
		if self.next_release:
			next_group = frappe.db.get_value("Release", self.next_release, "release_group")
			if next_group and self.release_group != next_group:
				frappe.throw(_("Next Release must belong to the selected Release Group."))
		if self.database_server:
			database_server = frappe.get_doc("Database Server", self.database_server)
			validate_database_server_placement_doc(self, database_server, allow_pending=True)

	def on_update(self):
		if self.database_server:
			from lenscloud.api.orchestration import update_database_server_count
			update_database_server_count(self.database_server)
