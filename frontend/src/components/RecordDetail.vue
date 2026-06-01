<script setup>
import { computed } from 'vue'
import { ArrowLeft, ExternalLink } from 'lucide-vue-next'
import { Badge, Button } from 'frappe-ui'
import { formatFieldValue } from '@/lib/api'

const props = defineProps({
	resource: {
		type: Object,
		required: true,
	},
	record: {
		type: Object,
		default: null,
	},
	related: {
		type: Array,
		default: () => [],
	},
	loading: {
		type: Boolean,
		default: false,
	},
})

const displayFields = computed(() => props.resource.detailFields || props.resource.summaryFields || [])

function fieldValue(field) {
	if (!props.record) {
		return '—'
	}

	return formatFieldValue(props.record[field.key])
}

function linkForField(field) {
	if (!props.record || !field.linkPrefix) {
		return null
	}

	const value = props.record[field.key]
	if (!value) {
		return null
	}

	return `${field.linkPrefix}${encodeURIComponent(value)}`
}
</script>

<template>
	<div class="section-band">
		<div class="section-head">
			<div>
				<div class="section-title">{{ resource.label }}</div>
				<p class="section-subtitle">{{ resource.listHelp }}</p>
			</div>
			<div class="page-actions">
				<Button :to="resource.route" tag="RouterLink">
					<component :is="ArrowLeft" class="nav-icon" />
					Back to list
				</Button>
				<slot name="actions" />
			</div>
		</div>

		<div v-if="loading" class="empty-state">
			<div class="spinner" />
			<p class="empty-title">Loading record…</p>
			<p class="helper-text">Reading the document from Frappe.</p>
		</div>

		<div v-else-if="!record" class="empty-state">
			<p class="empty-title">Record not found</p>
			<p class="helper-text">The current user may not have access or the record does not exist.</p>
		</div>

		<div v-else class="detail-grid">
			<div class="section-band" style="box-shadow: none; padding: 0; border: 0; background: transparent">
				<div class="resource-topline">
					<div>
						<h2 class="resource-title">{{ record.title || record.first_name || record.name }}</h2>
						<p class="resource-subtitle mono">{{ record.name }}</p>
					</div>
					<div class="table-meta">
						<Badge v-for="field in resource.summaryFields.slice(0, 3)" :key="field.key">{{ field.label }}: {{ fieldValue(field) }}</Badge>
					</div>
				</div>
			</div>

			<div class="panel" style="padding: 18px">
				<div class="section-head" style="margin-bottom: 12px">
					<div>
						<div class="section-title">Record fields</div>
						<p class="section-subtitle">Native Frappe document data exposed in the product UI.</p>
					</div>
				</div>

				<div class="field-grid">
					<div v-for="field in displayFields" :key="field.key" class="field">
						<label>{{ field.label }}</label>
						<div class="value">
							<RouterLink v-if="linkForField(field)" :to="linkForField(field)">{{ fieldValue(field) }}</RouterLink>
							<span v-else>{{ fieldValue(field) }}</span>
						</div>
					</div>
				</div>
			</div>

			<div class="panel" style="padding: 18px" v-if="related.length">
				<div class="section-head" style="margin-bottom: 12px">
					<div>
						<div class="section-title">Related records</div>
						<p class="section-subtitle">Linked records pulled from standard doctype queries.</p>
					</div>
				</div>

				<div class="stack">
					<div v-for="block in related" :key="block.label" class="resource-card">
						<div class="resource-topline">
							<div>
								<p class="resource-title">{{ block.label }}</p>
								<p class="resource-subtitle">{{ block.items.length ? `${block.items.length} records shown` : 'No linked records found yet.' }}</p>
							</div>
						</div>

						<div v-if="block.items.length" class="table-list">
							<RouterLink v-for="item in block.items" :key="item.name" class="table-row" :to="block.route(item.name)">
								<div class="table-main">
									<p class="table-title">{{ item.title || item.first_name || item.name }}</p>
									<p class="helper-text mono">{{ item.name }}</p>
								</div>
								<div class="table-meta">
									<Badge v-for="key in block.previewFields.slice(0, 2)" :key="key">{{ key }}: {{ formatFieldValue(item[key]) }}</Badge>
								</div>
								<div class="badge">
									<component :is="ExternalLink" class="nav-icon" />
								</div>
							</RouterLink>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>
