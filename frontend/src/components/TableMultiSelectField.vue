<script setup>
import { computed, ref } from 'vue'
import { Autocomplete } from 'frappe-ui'
import { X } from 'lucide-vue-next'

const props = defineProps({
	modelValue: { type: Array, default: () => [] },
	field: { type: Object, required: true },
	controlProps: { type: Function, required: true },
	disabled: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])
const query = ref('')
const childField = computed(() => props.field.columns?.[0] || {})
const childKey = computed(() => childField.value.key)
const options = computed(() => props.controlProps({}, childField.value)?.options || [])
const selected = computed(() => props.modelValue || [])

function add(value) {
	const selectedValue = value?.value || value || ''
	if (!selectedValue || selected.value.some((row) => row[childKey.value] === selectedValue)) return
	emit('update:modelValue', [...selected.value, { [childKey.value]: selectedValue }])
	query.value = ''
}
function remove(index) { emit('update:modelValue', selected.value.filter((_, rowIndex) => rowIndex !== index)) }
function labelFor(value) { return options.value.find((option) => option.value === value)?.label || value }
</script>

<template>
	<section class="rounded border border-outline-gray-2 bg-surface-white">
		<div class="border-b border-outline-gray-2 bg-surface-gray-1 px-3 py-2">
			<h3 class="text-sm font-medium text-ink-gray-9">{{ field.label }}</h3>
			<p v-if="field.description" class="mt-0.5 text-xs text-ink-gray-5">{{ field.description }}</p>
		</div>
		<div class="p-3">
			<div class="flex flex-wrap gap-2">
				<span v-for="(row, index) in selected" :key="row.name || row[childKey]" class="inline-flex items-center gap-1 rounded-full border border-outline-gray-2 bg-surface-gray-1 px-2.5 py-1 text-sm text-ink-gray-8">
					{{ labelFor(row[childKey]) }}
					<button type="button" :aria-label="`Remove ${labelFor(row[childKey])}`" class="rounded hover:bg-surface-gray-2" :disabled="disabled" @click="remove(index)"><X class="size-3.5" /></button>
				</span>
				<span v-if="!selected.length" class="text-sm text-ink-gray-5">No values selected.</span>
			</div>
			<Autocomplete class="mt-3 max-w-md" :model-value="query" :options="options" :placeholder="`Add ${childField.label || 'value'}`" :disabled="disabled" @change="add" />
		</div>
	</section>
</template>
