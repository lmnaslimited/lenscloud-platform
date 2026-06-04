# Copyright (c) 2026, LMNAs Cloud Solutions and contributors
# For license information, please see license.txt

from frappe.model.document import Document

from lenscloud.api.orchestration import ensure_operator_fields, get_region_cluster


class Bench(Document):
	def validate(self):
		if self.region:
			cluster = get_region_cluster(self.region)
			ensure_operator_fields(self, cluster)
