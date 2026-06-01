<script setup>
import { onMounted, reactive, ref } from 'vue'
import { Button, Badge } from 'frappe-ui'
import { getDoc, saveDoc } from '@/lib/api'
import { platformSettings } from '@/lib/catalog'
import PageHeader from '@/components/PageHeader.vue'

const loading = ref(true)
const record = ref(null)
const saveState = ref('idle')
const error = ref(null)
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
	if (!record.value) {
		return
	}

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
	<div class="stack">
		<PageHeader
			kicker="Platform console"
			title="Platform Settings"
			subtitle="Native Frappe single-document configuration for root domain and external systems."
		>
			<template #actions>
				<Badge>Singleton</Badge>
				<Button @click="load">Refresh</Button>
			</template>
		</PageHeader>

		<div v-if="error" class="section-band" style="border-color: rgba(180, 35, 24, 0.3); background: rgba(180, 35, 24, 0.04)">
			<p class="empty-title">Settings gap</p>
			<p class="helper-text">{{ error }}</p>
		</div>

		<div v-if="loading" class="section-band">
			<div class="spinner" />
			<p class="empty-title" style="margin-top: 8px">Loading settings…</p>
		</div>

		<div v-else class="form-panel">
			<div class="section-head" style="margin-bottom: 6px">
				<div>
					<div class="section-title">Settings record</div>
					<p class="section-subtitle">This page uses standard Frappe document save APIs. No backend customization is required for the UI to render.</p>
				</div>
			</div>

			<div class="form-grid">
				<label class="field form-control">
					<span>Root domain</span>
					<input v-model="formState.root_domain" placeholder="example.com" />
				</label>
				<label class="field form-control">
					<span>CRM system</span>
					<input v-model="formState.crm_system" placeholder="CRM endpoint or identifier" />
				</label>
				<label class="field form-control">
					<span>Support system</span>
					<input v-model="formState.support_system" placeholder="Support endpoint or identifier" />
				</label>
				<label class="field form-control">
					<span>Billing system</span>
					<input v-model="formState.billing_system" placeholder="Billing endpoint or identifier" />
				</label>
			</div>

			<div class="form-actions">
				<Badge v-if="saveState === 'saved'">Saved</Badge>
				<Badge v-else-if="saveState === 'saving'">Saving…</Badge>
				<Badge v-else-if="saveState === 'error'">Save failed</Badge>
				<Button @click="save">Save settings</Button>
			</div>
		</div>
	</div>
</template>
