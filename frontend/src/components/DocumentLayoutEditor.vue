<script setup>
import { computed, ref, watch } from 'vue'
import { FormControl } from 'frappe-ui'
import ChildTableGrid from '@/components/ChildTableGrid.vue'
import TableMultiSelectField from '@/components/TableMultiSelectField.vue'

const props = defineProps({
	fields: { type: Array, default: () => [] },
	model: { type: Object, required: true },
	controlProps: { type: Function, required: true },
	disabled: { type: Boolean, default: false },
})
const emit = defineEmits(['update:field'])
const activeTab = ref(0)

function emptySection(label = '') { return { label, collapsible: false, columns: [[]] } }
const tabs = computed(() => {
	const result = []
	let tab = { label: 'Details', sections: [] }
	let section = emptySection()
	let column = section.columns[0]
	const ensureTab = () => { if (!result.includes(tab)) result.push(tab) }
	const ensureSection = () => { ensureTab(); if (!tab.sections.includes(section)) tab.sections.push(section) }

	for (const field of props.fields) {
		if (field.type === 'tab_break') {
			tab = { label: field.label || 'Details', sections: [] }
			section = emptySection()
			column = section.columns[0]
			result.push(tab)
		} else if (field.type === 'section_break') {
			ensureTab()
			section = emptySection(field.label || '')
			section.collapsible = Boolean(field.collapsible)
			tab.sections.push(section)
			column = section.columns[0]
		} else if (field.type === 'column_break') {
			ensureSection()
			column = []
			section.columns.push(column)
		} else {
			ensureSection()
			column.push(field)
		}
	}
	if (!result.length) result.push(tab)
	return result.filter((item) => item.sections.some((itemSection) => itemSection.columns.some((items) => items.length)))
})
watch(tabs, () => { if (activeTab.value >= tabs.value.length) activeTab.value = 0 })

function update(field, value) {
	props.model[field.key] = value
	emit('update:field', { field: field.key, value })
}
function isWide(field) { return ['table', 'table_multiselect', 'textarea'].includes(field.type) }
</script>

<template>
	<div>
		<div v-if="tabs.length > 1" class="mb-4 flex gap-1 overflow-x-auto border-b border-outline-gray-2">
			<button v-for="(tab, index) in tabs" :key="tab.label + index" type="button" class="shrink-0 border-b-2 px-3 py-2 text-sm font-medium" :class="activeTab === index ? 'border-blue-500 text-ink-gray-9' : 'border-transparent text-ink-gray-5 hover:text-ink-gray-8'" @click="activeTab = index">{{ tab.label }}</button>
		</div>
		<div v-for="(tab, tabIndex) in tabs" v-show="activeTab === tabIndex" :key="tab.label + tabIndex" class="space-y-4">
			<section v-for="(section, sectionIndex) in tab.sections" :key="section.label + sectionIndex" class="rounded border border-outline-gray-2 bg-surface-white">
				<header v-if="section.label" class="border-b border-outline-gray-2 bg-surface-gray-1 px-3 py-2"><h3 class="text-sm font-medium text-ink-gray-9">{{ section.label }}</h3></header>
				<div class="grid grid-cols-1 gap-4 p-3 md:[grid-template-columns:var(--editor-columns)]" :style="{ '--editor-columns': `repeat(${section.columns.length}, minmax(0, 1fr))` }">
					<div v-for="(column, columnIndex) in section.columns" :key="columnIndex" class="min-w-0 space-y-3">
						<template v-for="field in column" :key="field.key">
							<ChildTableGrid v-if="field.type === 'table'" :field="field" :model-value="model[field.key] || []" :control-props="controlProps" :disabled="disabled || field.readOnly" @update:modelValue="(value) => update(field, value)" />
							<TableMultiSelectField v-else-if="field.type === 'table_multiselect'" :field="field" :model-value="model[field.key] || []" :control-props="controlProps" :disabled="disabled || field.readOnly" @update:modelValue="(value) => update(field, value)" />
							<div v-else class="min-w-0" :class="isWide(field) ? 'col-span-full' : ''">
								<FormControl v-bind="controlProps(model, field)" :disabled="disabled || field.readOnly" @update:modelValue="(value) => update(field, value)" />
								<p v-if="field.description" class="mt-1 text-xs leading-5 text-ink-gray-5">{{ field.description }}</p>
							</div>
						</template>
					</div>
				</div>
			</section>
		</div>
	</div>
</template>
