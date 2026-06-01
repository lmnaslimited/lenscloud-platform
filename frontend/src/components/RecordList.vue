<script setup>
import { computed, ref } from 'vue'
import { ChevronRight, Search } from 'lucide-vue-next'
import { Input, Button, Badge } from 'frappe-ui'
import { formatFieldValue } from '@/lib/api'

const props = defineProps({
	resource: {
		type: Object,
		required: true,
	},
	records: {
		type: Array,
		default: () => [],
	},
	loading: {
		type: Boolean,
		default: false,
	},
	emptyTitle: {
		type: String,
		default: 'No records yet',
	},
	emptyCopy: {
		type: String,
		default: 'Nothing to show here yet.',
	},
	hideSearch: {
		type: Boolean,
		default: false,
	},
})

const emit = defineEmits(['refresh'])
const searchText = ref('')

const filteredRecords = computed(() => {
	if (!searchText.value.trim()) {
		return props.records
	}

	const term = searchText.value.trim().toLowerCase()
	return props.records.filter((record) => {
		const values = [record.name, ...props.resource.summaryFields.map((field) => record[field.key])]
		return values.some((value) => String(formatFieldValue(value)).toLowerCase().includes(term))
	})
})

function recordTitle(record) {
	const titleField = props.resource.summaryFields.find((field) => ['title', 'first_name', 'name'].includes(field.key))
	if (titleField && record[titleField.key]) {
		return formatFieldValue(record[titleField.key])
	}

	if (record.title) {
		return record.title
	}

	if (record.first_name || record.last_name) {
		return [record.first_name, record.last_name].filter(Boolean).join(' ')
	}

	return record.name
}

function summaryValue(record, field) {
	return formatFieldValue(record[field.key])
}
</script>

<template>
	<div class="section-band">
		<div class="section-head">
			<div>
				<div class="section-title">{{ resource.label }}</div>
				<p class="section-subtitle">{{ resource.listHelp }}</p>
			</div>
			<div class="toolbar">
				<div class="search" v-if="!hideSearch">
					<Input v-model="searchText" placeholder="Search records" />
				</div>
				<Button @click="$emit('refresh')">
					<component :is="Search" class="nav-icon" />
					Refresh
				</Button>
			</div>
		</div>

		<div v-if="loading" class="empty-state">
			<div class="spinner" />
			<p class="empty-title">Loading {{ resource.label.toLowerCase() }}…</p>
			<p class="helper-text">Reading from standard Frappe document APIs.</p>
		</div>

		<div v-else-if="!filteredRecords.length" class="empty-state">
			<p class="empty-title">{{ emptyTitle }}</p>
			<p class="helper-text">{{ emptyCopy }}</p>
		</div>

		<div v-else class="table-list">
			<RouterLink
				v-for="record in filteredRecords"
				:key="record.name"
				class="table-row"
				:to="resource.detailRoute(record.name)"
			>
				<div class="table-main">
					<p class="table-title">{{ recordTitle(record) }}</p>
					<p class="helper-text mono">{{ record.name }}</p>
				</div>

				<div class="table-meta">
					<Badge v-for="field in resource.summaryFields.slice(0, 3)" :key="field.key">
						{{ field.label }}: {{ summaryValue(record, field) }}
					</Badge>
				</div>

				<div class="badge">
					<span>Open</span>
					<component :is="ChevronRight" class="nav-icon" />
				</div>
			</RouterLink>
		</div>
	</div>
</template>
