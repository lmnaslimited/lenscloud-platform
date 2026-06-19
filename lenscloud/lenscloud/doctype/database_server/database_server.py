# Copyright (c) 2026, LMNAs Cloud Solutions and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from lenscloud.api.orchestration import get_region_cluster, slugify, validate_runtime_namespace_placement_doc


class DatabaseServer(Document):
	def validate(self):
		cluster = get_region_cluster(self.region)
		self.cluster = cluster.name
		self.operator_resource_name = slugify(self.operator_resource_name or self.title)
		runtime_namespace = cluster.default_runtime_namespace or "default"
		self.kubernetes_namespace = self.kubernetes_namespace or runtime_namespace
		if self.provisioning_type == "Operator Managed":
			validate_runtime_namespace_placement_doc(self, cluster)
		self.storage_class = self.storage_class or cluster.default_storage_class or "local-path"
		self.data_retention_policy = self.data_retention_policy or "Retain"
		self.attached_bench_count = frappe.db.count("Bench", {"database_server": self.name}) if not self.is_new() else 0
		if self.data_retention_policy not in {"Retain", "Delete"}:
			frappe.throw(_("Data Retention Policy must be Retain or Delete."))
		if self.privacy in {"Private", "Private Shared"} and not (self.owner_customer or self.privacy_boundary):
			frappe.throw(_("{0} Database Server requires an Owner Customer or Privacy Boundary.").format(self.privacy))
		if self.privacy == "Public":
			self.owner_customer = None
			self.privacy_boundary = None
		if self.replica_count and self.replica_count < 1:
			frappe.throw(_("Replica Count must be at least 1."))

	def on_update(self):
		count = frappe.db.count("Bench", {"database_server": self.name})
		if self.attached_bench_count != count:
			frappe.db.set_value("Database Server", self.name, "attached_bench_count", count, update_modified=False)
