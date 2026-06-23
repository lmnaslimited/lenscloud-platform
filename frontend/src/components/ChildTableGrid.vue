<script setup>
import { computed } from 'vue'
import { Button, FormControl } from 'frappe-ui'
import { Copy, GripVertical, Trash2 } from 'lucide-vue-next'

const props = defineProps({
	modelValue: { type: Array, default: () => [] },
	field: { type: Object, required: true },
	controlProps: { type: Function, required: true },
	disabled: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])
const rows = computed(() => props.modelValue || [])
const columns = computed(() => props.field.columns || [])
const tableWidth = computed(() => 52 + columns.value.reduce((total, column) => total + Number(column.width || 220), 0) + 150)

function commit(next) { emit('update:modelValue', next) }
function addRow() {
	const row = {}
	for (const column of columns.value) row[column.key] = column.default ?? (column.type === 'check' ? 0 : '')
	commit([...rows.value, row])
}
function updateCell(index, column, value) {
	const next = rows.value.map((row) => ({ ...row }))
	next[index][column.key] = column.type === 'link' ? (value || '') : value
	commit(next)
}
function removeRow(index) { commit(rows.value.filter((_, rowIndex) => rowIndex !== index)) }
function duplicateRow(index) {
	const copy = { ...rows.value[index] }
	delete copy.name
	commit([...rows.value.slice(0, index + 1), copy, ...rows.value.slice(index + 1)])
}
function moveRow(index, direction) {
	const target = index + direction
	if (target < 0 || target >= rows.value.length) return
	const next = rows.value.map((row) => ({ ...row }))
	const [row] = next.splice(index, 1)
	next.splice(target, 0, row)
	commit(next)
}
function rowKey(row, index) { return row.name || `new-child-${index}` }
function inputProps(row, column) {
	return { ...props.controlProps(row, column), label: column.label, disabled: props.disabled || column.readOnly }
}
</script>

<template>
	<section class="overflow-hidden rounded border border-outline-gray-2 bg-surface-white">
		<header class="flex flex-wrap items-center justify-between gap-3 border-b border-outline-gray-2 bg-surface-gray-1 px-3 py-2">
			<div>
				<h3 class="text-sm font-medium text-ink-gray-9">{{ field.label }}</h3>
				<p class="mt-0.5 text-xs text-ink-gray-5">{{ field.description || 'Edit child records, then save the parent document.' }}</p>
			</div>
			<Button size="sm" variant="subtle" :disabled="disabled" @click="addRow">Add row</Button>
		</header>

		<div v-if="!rows.length" class="px-4 py-6 text-center text-sm text-ink-gray-5">No rows yet. Add a row to configure this table.</div>
		<div v-else class="max-w-full overflow-x-auto" data-testid="child-table-scroll">
			<table class="border-separate border-spacing-0 text-left" :style="{ minWidth: `${tableWidth}px` }">
				<thead>
					<tr class="text-xs font-medium text-ink-gray-5">
						<th class="sticky left-0 top-0 z-30 w-[52px] border-b border-r border-outline-gray-2 bg-surface-gray-1 px-2 py-2 text-center">#</th>
						<th
							v-for="(column, columnIndex) in columns"
							:key="column.key"
							class="sticky top-0 z-20 border-b border-r border-outline-gray-2 bg-surface-gray-1 px-3 py-2"
							:class="columnIndex === 0 ? 'left-[52px] z-30 shadow-[2px_0_0_0_var(--outline-gray-2)]' : ''"
							:style="{ width: `${column.width || 220}px`, minWidth: `${column.width || 220}px` }"
						>{{ column.label }}<span v-if="column.required" class="text-red-500"> *</span></th>
						<th class="sticky right-0 top-0 z-30 w-[150px] border-b border-outline-gray-2 bg-surface-gray-1 px-3 py-2 text-right">Row actions</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="(row, rowIndex) in rows" :key="rowKey(row, rowIndex)" class="group align-top hover:bg-surface-gray-1">
						<td class="sticky left-0 z-20 border-b border-r border-outline-gray-2 bg-surface-white px-2 py-3 text-center text-xs text-ink-gray-5 group-hover:bg-surface-gray-1"><GripVertical class="mx-auto size-4 text-ink-gray-4" />{{ rowIndex + 1 }}</td>
						<td
							v-for="(column, columnIndex) in columns"
							:key="column.key"
							class="border-b border-r border-outline-gray-2 bg-surface-white px-2 py-2 group-hover:bg-surface-gray-1 [&_label]:sr-only"
							:class="columnIndex === 0 ? 'sticky left-[52px] z-20 shadow-[2px_0_0_0_var(--outline-gray-2)]' : ''"
							:style="{ width: `${column.width || 220}px`, minWidth: `${column.width || 220}px` }"
						>
							<FormControl v-if="['link', 'select', 'check'].includes(column.type)" v-bind="inputProps(row, column)" @update:modelValue="(value) => updateCell(rowIndex, column, value)" />
							<textarea v-else-if="column.type === 'textarea'" :aria-label="column.label" :value="row[column.key]" class="min-h-16 w-full rounded border border-outline-gray-2 bg-surface-gray-1 px-2 py-1.5 text-sm text-ink-gray-8 focus:border-blue-500 focus:outline-none" :disabled="disabled || column.readOnly" @input="updateCell(rowIndex, column, $event.target.value)"></textarea>
							<input v-else :type="column.type === 'number' ? 'number' : 'text'" :aria-label="column.label" :value="row[column.key]" class="h-8 w-full rounded border border-outline-gray-2 bg-surface-gray-1 px-2 text-sm text-ink-gray-8 focus:border-blue-500 focus:outline-none" :disabled="disabled || column.readOnly" @input="updateCell(rowIndex, column, $event.target.value)" />
						</td>
						<td class="sticky right-0 z-20 border-b border-outline-gray-2 bg-surface-white px-2 py-2 group-hover:bg-surface-gray-1">
							<div class="flex justify-end gap-1">
								<button type="button" aria-label="Move row up" class="grid size-7 place-items-center rounded hover:bg-surface-gray-2 disabled:opacity-40" :disabled="disabled || rowIndex === 0" @click="moveRow(rowIndex, -1)">↑</button>
								<button type="button" aria-label="Move row down" class="grid size-7 place-items-center rounded hover:bg-surface-gray-2 disabled:opacity-40" :disabled="disabled || rowIndex === rows.length - 1" @click="moveRow(rowIndex, 1)">↓</button>
								<button type="button" aria-label="Duplicate row" class="grid size-7 place-items-center rounded hover:bg-surface-gray-2 disabled:opacity-40" :disabled="disabled" @click="duplicateRow(rowIndex)"><Copy class="size-3.5" /></button>
								<button type="button" aria-label="Remove row" class="grid size-7 place-items-center rounded text-red-600 hover:bg-red-50 disabled:opacity-40" :disabled="disabled" @click="removeRow(rowIndex)"><Trash2 class="size-3.5" /></button>
							</div>
						</td>
					</tr>
				</tbody>
			</table>
		</div>
		<footer v-if="rows.length" class="flex items-center justify-between border-t border-outline-gray-2 bg-surface-gray-1 px-3 py-2 text-xs text-ink-gray-5">
			<span>{{ rows.length }} row{{ rows.length === 1 ? '' : 's' }}</span>
			<span>Fixed identity and action columns · Scroll horizontally for all fields</span>
		</footer>
	</section>
</template>
