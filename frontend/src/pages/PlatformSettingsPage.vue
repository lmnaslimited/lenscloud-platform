<script setup>
import { onMounted, reactive, ref } from 'vue'
import { Alert, Badge, Button, Tabs, TextInput } from 'frappe-ui'
import { getDoc, saveDoc } from '@/lib/api'
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
const formState = reactive({
	root_domain: '',
	crm_system: '',
	support_system: '',
	billing_system: '',
})

async function load() {
	loading.value = true
	error.value = null
	try {
		record.value = await getDoc(platformSettings.doctype, platformSettings.doctype)
		for (const key of Object.keys(formState)) {
			formState[key] = record.value?.[key] || ''
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
		const saved = await saveDoc(platformSettings.doctype, record.value.name || platformSettings.doctype, formState)
		record.value = saved
		saveState.value = 'saved'
	} catch (err) {
		saveState.value = 'error'
		error.value = err?.message || 'Unable to save platform settings.'
	}
}

onMounted(load)
</script>

<template>
	<WorkspaceLayout
		title="Platform Settings"
		subtitle="Native Frappe singleton configuration for root domain and external systems."
		inspector-kicker="Singleton inspector"
		inspector-title="Settings context"
		inspector-subtitle="Keep read-only status and editable singleton fields separate."
		assistant-label="Assistant"
		assistant-hint="The assistant will help explain integration settings, status, and change impact for platform engineers."
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
						<p class="mt-1 text-sm leading-6 text-ink-gray-5">This page uses standard Frappe document save APIs. No backend customization is required for the UI to render.</p>
					</div>

					<div class="grid gap-3 sm:grid-cols-2">
						<label class="space-y-1.5">
							<span class="text-xs font-medium uppercase tracking-[0.14em] text-ink-gray-5">Root domain</span>
							<TextInput v-model="formState.root_domain" placeholder="example.com" variant="subtle" class="w-full" />
						</label>
						<label class="space-y-1.5">
							<span class="text-xs font-medium uppercase tracking-[0.14em] text-ink-gray-5">CRM system</span>
							<TextInput v-model="formState.crm_system" placeholder="CRM endpoint or identifier" variant="subtle" class="w-full" />
						</label>
						<label class="space-y-1.5">
							<span class="text-xs font-medium uppercase tracking-[0.14em] text-ink-gray-5">Support system</span>
							<TextInput v-model="formState.support_system" placeholder="Support endpoint or identifier" variant="subtle" class="w-full" />
						</label>
						<label class="space-y-1.5">
							<span class="text-xs font-medium uppercase tracking-[0.14em] text-ink-gray-5">Billing system</span>
							<TextInput v-model="formState.billing_system" placeholder="Billing endpoint or identifier" variant="subtle" class="w-full" />
						</label>
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
