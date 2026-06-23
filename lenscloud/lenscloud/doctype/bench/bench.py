# Copyright (c) 2026, LMNAs Cloud Solutions and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from lenscloud.api.orchestration import ensure_operator_fields, get_region_cluster, validate_database_server_placement_doc, validate_runtime_namespace_placement_doc
from lenscloud.api.policy import placement_keys


class Bench(Document):
	def validate(self):
		if self.subscription:
			subscription = frappe.get_doc("Subscription", self.subscription)
			if not self.environment:
				frappe.throw(_("Subscription Bench requires an Environment."))
			if self.region and self.region != subscription.region:
				frappe.throw(_("Bench Region must match Subscription Region."))
			self.region = subscription.region
			self.plan = subscription.plan
			self.release_group = subscription.release_group
			self.privacy = subscription.privacy_profile
			keys = placement_keys(subscription, self.environment, bench=self)
			self.bench_placement_key = keys["bench"]
			self.database_placement_key = keys["database"]
			if self.privacy != "Public":
				self.owner_customer = subscription.customer
				self.privacy_boundary = subscription.customer
		if not self.region:
			return
		cluster = get_region_cluster(self.region)
		ensure_operator_fields(self, cluster)
		validate_runtime_namespace_placement_doc(self, cluster)
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
		if self.plan and self.bench_status == "Ready" and frappe.db.get_value("Plan", self.plan, "is_free"):
			duplicate = frappe.db.exists("Bench", {"plan": self.plan, "region": self.region, "environment": "Prod", "bench_status": "Ready", "name": ["!=", self.name]})
			if duplicate:
				frappe.throw(_("Only one ready Free Plan Bench is allowed per Region."))

	def on_update(self):
		if self.database_server:
			from lenscloud.api.orchestration import update_database_server_count
			update_database_server_count(self.database_server)
