<script setup>
import { onMounted, reactive, ref } from 'vue'
import { Button, Badge } from 'frappe-ui'
import { listDocs, saveDoc } from '@/lib/api'
import PageHeader from '@/components/PageHeader.vue'
import ActionPanel from '@/components/ActionPanel.vue'
import { customerResources } from '@/lib/catalog'
import { useSessionStore } from '@/lib/session'

const session = useSessionStore()
const loading = ref(true)
const error = ref(null)
const saveState = ref('idle')
const customer = ref(null)
const sites = ref([])
const formState = reactive({
	first_name: '',
	last_name: '',
	region: '',
	external_customer_id: '',
})

async function load() {
	loading.value = true
	error.value = null
	try {
		const customers = await listDocs('Customer', {
			fields: ['name', 'first_name', 'last_name', 'region', 'external_customer_id'],
			limit: 1,
			filters: [['user', '=', session.user]],
		})

		customer.value = customers[0] || null
		if (customer.value) {
			for (const key of Object.keys(formState)) {
				formState[key] = customer.value[key] || ''
			}

			sites.value = await listDocs('Site', {
				fields: ['name', 'title', 'bench', 'customer', 'modified'],
				limit: 8,
				filters: [['customer', '=', customer.value.name]],
			})
		} else {
			sites.value = []
		}
	} catch (err) {
		error.value = err?.message || 'Unable to load account.'
	} finally {
		loading.value = false
	}
}

async function save() {
	if (!customer.value) {
		return
	}

	saveState.value = 'saving'
	try {
		const saved = await saveDoc('Customer', customer.value.name, formState)
		customer.value = saved
		saveState.value = 'saved'
		await load()
	} catch (err) {
		saveState.value = 'error'
		error.value = err?.message || 'Unable to save customer account.'
	}
}

onMounted(load)
</script>

<template>
	<div class="stack">
		<PageHeader
			kicker="Customer portal"
			title="Account"
			subtitle="Your customer identity, region placement, and linked site view."
		>
			<template #actions>
				<Badge v-if="customer">Linked</Badge>
				<Badge v-else>Gap: no customer record</Badge>
				<Button @click="load">Refresh</Button>
			</template>
		</PageHeader>

		<div v-if="error" class="section-band" style="border-color: rgba(180, 35, 24, 0.3); background: rgba(180, 35, 24, 0.04)">
			<p class="empty-title">Account gap</p>
			<p class="helper-text">{{ error }}</p>
		</div>

		<div v-if="loading" class="section-band">
			<div class="spinner" />
			<p class="empty-title" style="margin-top: 8px">Loading account…</p>
		</div>

		<template v-else>
			<div v-if="!customer" class="empty-state">
				<p class="empty-title">No linked customer record yet</p>
				<p class="helper-text">The UI expects a Customer document tied to the signed-in user. If that linkage is missing, this page surfaces the gap instead of inventing data.</p>
			</div>

			<div v-else class="stack">
				<div class="form-panel">
					<div class="section-head" style="margin-bottom: 6px">
						<div>
							<div class="section-title">Customer record</div>
							<p class="section-subtitle">Uses standard Frappe document save APIs. No backend flow customization is added here.</p>
						</div>
					</div>

					<div class="form-grid">
						<label class="field form-control">
							<span>First name</span>
							<input v-model="formState.first_name" />
						</label>
						<label class="field form-control">
							<span>Last name</span>
							<input v-model="formState.last_name" />
						</label>
						<label class="field form-control">
							<span>Primary region</span>
							<input v-model="formState.region" placeholder="Region name" />
						</label>
						<label class="field form-control">
							<span>External customer ID</span>
							<input v-model="formState.external_customer_id" placeholder="Billing or CRM identifier" />
						</label>
					</div>

					<div class="form-actions">
						<Badge v-if="saveState === 'saved'">Saved</Badge>
						<Badge v-else-if="saveState === 'saving'">Saving…</Badge>
						<Badge v-else-if="saveState === 'error'">Save failed</Badge>
						<Button @click="save">Save account</Button>
					</div>
				</div>

				<div class="section-band">
					<div class="section-head">
						<div>
							<div class="section-title">Linked sites</div>
							<p class="section-subtitle">Recent sites tied to your account.</p>
						</div>
						<Badge>{{ sites.length }}</Badge>
					</div>

					<div v-if="!sites.length" class="empty-state">
						<p class="empty-title">No sites linked yet</p>
						<p class="helper-text">The portal is ready for site lifecycle flows once the backend contract is available.</p>
					</div>

					<div v-else class="table-list">
						<div v-for="site in sites" :key="site.name" class="table-row">
							<div class="table-main">
								<p class="table-title">{{ site.title || site.name }}</p>
								<p class="helper-text mono">{{ site.name }}</p>
							</div>
							<div class="table-meta">
								<Badge>Bench: {{ site.bench || '—' }}</Badge>
								<Badge>Customer: {{ site.customer || '—' }}</Badge>
							</div>
							<div class="badge">UI-visible</div>
						</div>
					</div>
				</div>

				<ActionPanel :actions="customerResources[0].actions" context-label="customer account" />
			</div>
		</template>
	</div>
</template>
