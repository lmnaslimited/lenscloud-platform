<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { Alert, Badge, Button, FormControl, Tabs } from 'frappe-ui'
import { getDoc, listDocs, saveDoc } from '@/lib/api'
import { platformSettings } from '@/lib/catalog'
import WorkspaceLayout from '@/components/WorkspaceLayout.vue'

const loading = ref(true)
const record = ref(null)
const saveState = ref('idle')
const error = ref(null)
const inspectorTab = ref(0)
const inspectorTabs = [
	{ label: 'Summary' },
	{ label: 'Fields' },
]
const formState = reactive(Object.fromEntries(platformSettings.detailFields.map((field) => [field.key, ''])))
const fieldOptions = reactive({})

function fieldOptionKey(field) {
	return `${field.type || 'text'}:${field.options || field.key}`
}

function optionLabelForDoc(doc, field) {
	const labelFields = field.labelFields || ['title', 'plan_code']
	const label = labelFields.map((key) => doc[key]).filter(Boolean).join(' ')
	return label && label !== doc.name ? `${label} · ${doc.name}` : doc.name
}

async function loadFieldOptions() {
	const linkFields = platformSettings.detailFields.filter((field) => field.type === 'link' && field.options)
	await Promise.all(linkFields.map(async (field) => {
		const key = fieldOptionKey(field)
		if (fieldOptions[key]) return
		const fields = Array.from(new Set(['name', ...(field.labelFields || ['title', 'plan_code'])]))
		const rows = await listDocs(field.options, { fields, limit: 100 }).catch(() => [])
		fieldOptions[key] = rows.map((row) => ({ label: optionLabelForDoc(row, field), value: row.name }))
	}))
}

function optionsForField(field) {
	return fieldOptions[fieldOptionKey(field)] || []
}


function controlTypeForField(field) {
	if (field.type === 'check') return 'checkbox'
	if (field.type === 'textarea') return 'textarea'
	if (field.type === 'select') return 'select'
	if (field.type === 'link') return 'combobox'
	return 'text'
}

function normalizedOptionsForField(field) {
	if (field.type === 'select') {
		const source = Array.isArray(field.options) ? field.options : String(field.options || '').split('\n')
		const options = source.map((option) => (typeof option === 'object' ? option : { label: option, value: option })).filter((option) => option.value !== '')
		return [{ label: 'None', value: '' }, ...options]
	}
	if (field.type === 'link') return [{ label: 'None', value: '' }, ...optionsForField(field)]
	return []
}

function controlValueForField(field) {
	return formState[field.key]
}

function fieldControlProps(field) {
	const props = {
		type: controlTypeForField(field),
		label: field.label,
		required: field.required,
		modelValue: controlValueForField(field),
		variant: 'subtle',
		disabled: Boolean(field.readOnly),
	}
	if (field.type !== 'check') props.placeholder = field.placeholder || field.label
	if (field.type === 'select' || field.type === 'link') props.options = normalizedOptionsForField(field)
	if (field.type === 'link') {
		props.openOnFocus = true
		props.openOnClick = true
		props.allowCustomValue = Boolean(field.allowCreate)
	}
	return props
}

function canClearField(field) {
	return ['link', 'select'].includes(field.type) && Boolean(formState[field.key])
}

function clearModelField(field) {
	formState[field.key] = ''
}

function updateModelField(field, value) {
	if (field.type === 'link') {
		formState[field.key] = value || ''
		return
	}
	formState[field.key] = value
}

async function load() {
	loading.value = true
	error.value = null
	try {
		await loadFieldOptions()
		record.value = await getDoc(platformSettings.doctype, platformSettings.doctype)
		for (const key of Object.keys(formState)) {
			formState[key] = platformSettings.detailFields.find((field) => field.key === key)?.type === 'check' ? Boolean(record.value?.[key]) : (record.value?.[key] || '')
		}
	} catch (err) {
		error.value = err?.message || 'Unable to load platform settings.'
	} finally {
		loading.value = false
	}
}

async function save() {
	if (!record.value) return

	saveState.value = 'saving'
	try {
		const payload = Object.fromEntries(platformSettings.detailFields.filter((field) => !field.readOnly).map((field) => [field.key, field.type === 'check' ? (formState[field.key] ? 1 : 0) : formState[field.key]]))
		const saved = await saveDoc(platformSettings.doctype, record.value.name || platformSettings.doctype, payload)
		record.value = saved
		saveState.value = 'saved'
	} catch (err) {
		saveState.value = 'error'
		error.value = err?.message || 'Unable to save platform settings.'
	}
}

const assistantContext = computed(() => {
	const gaps = []
	if (!formState.operator_namespace) gaps.push('Global operator namespace fallback is not configured')
	if (!formState.default_storage_class) gaps.push('Global storage-class fallback is not configured')
	if (!formState.root_domain) gaps.push('Wildcard root domain is required for standard Site hostnames')
	if (formState.wildcard_dns_status !== 'Ready') gaps.push('Wildcard DNS readiness is not confirmed')
	if (formState.wildcard_tls_status !== 'Ready') gaps.push('Wildcard TLS readiness is not confirmed')
	if (formState.ingress_status !== 'Ready') gaps.push('Shared ingress readiness is not confirmed')
	if (!formState.billing_system) gaps.push('Billing system is not configured')
	if (!formState.crm_system) gaps.push('CRM system is not configured')
	if (!formState.support_system) gaps.push('Support system is not configured')

	return {
		scope: 'platform',
		summary: 'Global defaults and shared wildcard-edge readiness. Region selects the active Cluster for each Bench and Site.',
		badges: ['Platform Settings', record.value ? 'loaded' : 'pending', saveState.value],
		sections: [
			{ label: 'Placement model', value: 'Region -> Cluster; no single active cluster' },
			{ label: 'Operator namespace fallback', value: formState.operator_namespace || 'Not configured' },
			{ label: 'Storage-class fallback', value: formState.default_storage_class || 'Not configured' },
			{ label: 'Root domain', value: formState.root_domain || 'Not configured' },
			{ label: 'Wildcard edge', value: `${formState.wildcard_dns_status || 'Unknown'} DNS / ${formState.wildcard_tls_status || 'Unknown'} TLS / ${formState.ingress_status || 'Unknown'} ingress` },
			{ label: 'Billing system', value: formState.billing_system || 'Not configured' },
			{ label: 'CRM system', value: formState.crm_system || 'Not configured' },
			{ label: 'Support system', value: formState.support_system || 'Not configured' },
		],
		gaps,
		nextSteps: ['Register each runtime Cluster and map deployable Regions to it.', 'Keep Kubernetes credentials on Cluster records as mounted server-side references.', 'Use shared wildcard DNS/TLS for standard Sites; per-Site Route53 records are not part of this flow.', 'SSO setup remains external to this frontend.'],
	}
})

onMounted(load)
</script>

<template>
	<WorkspaceLayout
		title="Platform Settings"
		subtitle="Global fallbacks, wildcard edge readiness, and external systems. Runtime placement is owned by Region and Cluster."
		inspector-kicker="Singleton inspector"
		inspector-title="Settings context"
		inspector-subtitle="Keep read-only status and editable singleton fields separate."
		assistant-label="Assistant"
		assistant-hint="The assistant will help explain integration settings, status, and change impact for platform engineers."
		:assistant-context="assistantContext"
	>
		<template #actions>
			<Badge class="bg-surface-gray-2 text-ink-gray-6">Singleton</Badge>
			<Button variant="subtle" @click="load">Refresh</Button>
		</template>

		<template #main>
			<div class="h-full overflow-y-auto p-4">
			<Alert v-if="error" theme="red" title="Settings gap" :message="error" />

			<div class="rounded border border-outline-gray-2 bg-surface-white p-4">
				<div v-if="loading" class="flex items-center gap-3">
					<LoadingIndicator />
					<div>
						<p class="text-sm font-medium text-ink-gray-9">Loading settings…</p>
						<p class="text-sm leading-6 text-ink-gray-5">Reading the singleton document.</p>
					</div>
				</div>

				<div v-else class="space-y-4">
					<div>
						<p class="text-[11px] font-medium uppercase tracking-[0.18em] text-ink-gray-5">Settings record</p>
						<p class="mt-1 text-sm leading-6 text-ink-gray-5">This page uses standard Frappe document save APIs. Cluster-specific runtime access stays on Cluster records; these settings provide only global fallbacks and shared edge state.</p>
					</div>

					<div class="grid gap-3 sm:grid-cols-2">
						<div v-for="field in platformSettings.detailFields" :key="field.key" class="flex items-end gap-2">
							<FormControl
								v-bind="fieldControlProps(field)"
								:class="field.type === 'check' ? '' : 'min-w-0 flex-1'"
								@update:modelValue="(value) => updateModelField(field, value)"
							/>
							<Button v-if="canClearField(field)" size="sm" variant="subtle" class="mb-0.5 shrink-0" @click="clearModelField(field)">Clear</Button>
						</div>
					</div>

					<div class="flex flex-wrap items-center gap-2">
						<Badge v-if="saveState === 'saved'" class="bg-emerald-50 text-emerald-700">Saved</Badge>
						<Badge v-else-if="saveState === 'saving'" class="bg-surface-gray-2 text-ink-gray-6">Saving…</Badge>
						<Badge v-else-if="saveState === 'error'" class="bg-red-50 text-red-700">Save failed</Badge>
						<Button @click="save">Save settings</Button>
					</div>
				</div>
			</div>
			</div>
		</template>

		<template #inspector>
			<Tabs v-model="inspectorTab" as="div" :tabs="inspectorTabs" class="h-full [&_[role='tab']]:py-2 [&_[role='tab']]:text-sm [&_[role='tablist']]:gap-4 [&_[role='tablist']]:px-1 [&_[role='tabpanel']]:px-1 [&_[role='tabpanel']]:py-3">
				<template #tab-panel="{ tab }">
					<div v-if="tab.label === 'Summary'" class="space-y-3">
						<div class="rounded border border-outline-gray-2 bg-surface-gray-1 p-3">
							<div class="flex items-start justify-between gap-3">
								<div>
									<p class="text-xs font-medium text-ink-gray-5">Singleton</p>
									<p class="mt-1 text-sm font-medium text-ink-gray-9">Platform Settings</p>
								</div>
								<Badge class="bg-surface-white text-ink-gray-7">{{ record ? 'Loaded' : 'Pending' }}</Badge>
							</div>
						</div>
						<div class="grid gap-2">
							<div v-for="item in platformSettings.summaryFields" :key="item.key" class="rounded border border-outline-gray-2 bg-surface-white px-3 py-2">
								<p class="text-sm text-ink-gray-5">{{ item.label }}</p>
								<p class="mt-1 truncate text-sm font-medium text-ink-gray-9">{{ record?.[item.key] || '-' }}</p>
							</div>
						</div>
					</div>
					<div v-else class="space-y-3">
						<p class="text-sm leading-5 text-ink-gray-5">Edit settings in the main workspace. This rail stays focused on review and change awareness.</p>
						<Badge v-if="saveState === 'saved'" class="bg-emerald-50 text-emerald-700">Saved</Badge>
						<Badge v-else-if="saveState === 'saving'" class="bg-surface-gray-2 text-ink-gray-6">Saving</Badge>
						<Badge v-else-if="saveState === 'error'" class="bg-red-50 text-red-700">Save failed</Badge>
					</div>
				</template>
			</Tabs>
		</template>
	</WorkspaceLayout>
</template>
