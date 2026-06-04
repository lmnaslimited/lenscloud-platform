# Copyright (c) 2026, LMNAs Cloud Solutions and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from lenscloud.api.orchestration import ensure_operator_fields, get_platform_settings, get_region_cluster, slugify


class Site(Document):
	def autoname(self):
		self.set_derived_identity()
		self.name = self.title

	def validate(self):
		self.set_derived_identity()
		if self.region:
			cluster = get_region_cluster(self.region)
			ensure_operator_fields(self, cluster)

	def set_derived_identity(self):
		if self.subdomain:
			self.subdomain = slugify(self.subdomain)

		if self.domain:
			self.domain = self.domain.strip().lower().strip('.')
			legacy_prefix = f'{self.subdomain}.'
			if self.subdomain and self.domain.startswith(legacy_prefix):
				self.domain = self.domain[len(legacy_prefix):]
		else:
			settings = get_platform_settings()
			root_domain = (settings.root_domain or '').strip().lower().strip('.')
			if not root_domain:
				frappe.throw(_('Platform Settings root_domain is required to derive Site domain.'))
			self.domain = root_domain

		if not self.subdomain:
			frappe.throw(_('Site requires a subdomain to derive the full hostname.'))
		if not self.domain:
			frappe.throw(_('Site requires a root or approved domain.'))

		self.title = f'{self.subdomain}.{self.domain}'
