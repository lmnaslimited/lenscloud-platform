<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { Alert, Badge, Button, ListView, Tabs, TextInput } from 'frappe-ui'
import { listDocs, saveDoc } from '@/lib/api'
import { customerResources } from '@/lib/catalog'
import WorkspaceLayout from '@/components/WorkspaceLayout.vue'
import { useSessionStore } from '@/lib/session'

const session = useSessionStore()
const loading = ref(true)
const error = ref(null)
const saveState = ref('idle')
const customer = ref(null)
const sites = ref([])
const inspectorTab = ref(0)
const inspectorTabs = [
	{ label: 'Summary' },
	{ label: 'Sites' },
	{ label: 'Requests' },
]
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
				fields: ['name', 'title', 'domain', 'site_status', 'provisioning_status', 'route_status', 'access_url', 'plan', 'subscription', 'environment', 'modified'],
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
	if (!customer.value) return

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

const assistantContext = computed(() => ({
	scope: 'customer',
	summary: customer.value ? 'Guidance for customer account details and linked site context.' : 'Customer account linkage is missing for this signed-in user.',
	badges: ['Account', customer.value ? 'linked' : 'gap', `${sites.value.length} site(s)`],
	sections: [
		{ label: 'Customer record', value: customer.value?.name || 'No linked Customer record' },
		{ label: 'Region', value: formState.region || 'No region selected' },
		{ label: 'External customer ID', value: formState.external_customer_id || 'Not configured' },
	],
	gaps: customer.value ? [] : ['Signed-in user has no linked Customer record'],
	nextSteps: customer.value
		? ['Keep profile fields current.', 'Use Plans to start or request subscriptions.', 'Use Sites for progress and access.']
		: ['Create or link a Customer record to this Frappe user before customer flows can show account data.'],
}))

onMounted(load)
</script>

<template>
	<WorkspaceLayout
		title="Account"
		subtitle="Your customer profile, linked Sites, and future access management."
		inspector-kicker="Customer inspector"
		inspector-title="Account context"
		inspector-subtitle="LensCloud Platform is the access home for customer users and Sites."
		assistant-label="Assistant"
		assistant-hint="The assistant will help explain customer-facing lifecycle actions, account status, and request flow context."
		:assistant-context="assistantContext"
	>
		<template #actions>
			<Badge v-if="customer" class="bg-surface-gray-2 text-ink-gray-6">Linked</Badge>
			<Badge v-else class="bg-surface-gray-2 text-ink-gray-6">Gap: no customer record</Badge>
			<Button variant="subtle" @click="load">Refresh</Button>
		</template>

		<template #main>
			<div class="h-full overflow-y-auto p-4">
			<Alert v-if="error" theme="red" title="Account gap" :description="error" />

			<div class="rounded border border-outline-gray-2 bg-surface-white p-4">
				<div v-if="loading" class="flex items-center gap-3">
					<LoadingIndicator />
					<div>
						<p class="text-sm font-medium text-ink-gray-9">Loading account…</p>
						<p class="text-sm leading-6 text-ink-gray-5">Reading the linked customer record.</p>
					</div>
				</div>

				<div v-else-if="!customer" class="rounded border border-dashed border-outline-gray-2 bg-surface-gray-1 p-4">
					<p class="text-sm font-medium text-ink-gray-9">No linked customer record yet</p>
					<p class="mt-1 text-sm leading-6 text-ink-gray-5">The UI expects a Customer document tied to the signed-in user. If that linkage is missing, the gap is surfaced instead of invented data.</p>
				</div>

				<div v-else class="space-y-4">
					<div>
						<p class="text-[11px] font-medium uppercase tracking-[0.18em] text-ink-gray-5">Customer record</p>
						<p class="mt-1 text-sm leading-6 text-ink-gray-5">Keep your profile current. User invites and fine-grained access management are coming in the CUA pass.</p>
					</div>

					<div class="grid gap-3 sm:grid-cols-2">
						<label class="space-y-1.5">
							<span class="text-xs font-medium uppercase tracking-[0.14em] text-ink-gray-5">First name</span>
							<TextInput v-model="formState.first_name" variant="subtle" class="w-full" />
						</label>
						<label class="space-y-1.5">
							<span class="text-xs font-medium uppercase tracking-[0.14em] text-ink-gray-5">Last name</span>
							<TextInput v-model="formState.last_name" variant="subtle" class="w-full" />
						</label>
						<label class="space-y-1.5">
							<span class="text-xs font-medium uppercase tracking-[0.14em] text-ink-gray-5">Primary region</span>
							<TextInput v-model="formState.region" placeholder="Region name" variant="subtle" class="w-full" />
						</label>
						<label class="space-y-1.5">
							<span class="text-xs font-medium uppercase tracking-[0.14em] text-ink-gray-5">External customer ID</span>
							<TextInput v-model="formState.external_customer_id" placeholder="Billing or CRM identifier" variant="subtle" class="w-full" />
						</label>
					</div>

					<div class="flex flex-wrap items-center gap-2">
						<Badge v-if="saveState === 'saved'" class="bg-emerald-50 text-emerald-700">Saved</Badge>
						<Badge v-else-if="saveState === 'saving'" class="bg-surface-gray-2 text-ink-gray-6">Saving…</Badge>
						<Badge v-else-if="saveState === 'error'" class="bg-red-50 text-red-700">Save failed</Badge>
						<Button @click="save">Save account</Button>
					</div>
				</div>
			</div>

			<div class="mt-3 rounded border border-outline-gray-2 bg-surface-white p-4">
				<div class="flex items-center justify-between gap-3">
					<div>
						<p class="text-sm font-medium text-ink-gray-9">Linked sites</p>
						<p class="mt-1 text-xs text-ink-gray-5">Recent sites tied to your account.</p>
					</div>
					<Badge class="bg-surface-gray-2 text-ink-gray-6">{{ sites.length }}</Badge>
				</div>

				<div v-if="!sites.length" class="mt-3 rounded border border-dashed border-outline-gray-2 bg-surface-gray-1 p-4">
					<p class="text-sm font-medium text-ink-gray-9">No sites linked yet</p>
					<p class="mt-1 text-sm leading-6 text-ink-gray-5">Choose a Plan to start your first Free Site setup.</p>
				</div>

				<div v-else class="mt-3 overflow-hidden rounded border border-outline-gray-2">
					<ListView
						class="h-[360px]"
						:columns="[
							{ label: 'Name', key: 'name', width: 3, getLabel: ({ row }) => row.title || row.name },
							{ label: 'Status', key: 'site_status', width: '140px', getLabel: ({ row }) => row.site_status || 'Pending' },
							{ label: 'Access', key: 'route_status', width: '140px', getLabel: ({ row }) => row.route_status === 'Ready' ? 'Ready' : 'Preparing' },
						]"
						:rows="sites"
						row-key="name"
						:options="{ selectable: false, showTooltip: true }"
					/>
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
								<div class="min-w-0">
									<p class="text-xs font-medium text-ink-gray-5">Customer</p>
									<p class="mt-1 truncate text-sm font-medium text-ink-gray-9">{{ customer ? (customer.first_name || customer.name) : 'No customer record' }}</p>
								</div>
								<Avatar :label="customer ? (customer.first_name || customer.name) : 'Gap'" size="sm" />
							</div>
						</div>
						<div v-if="customer" class="grid gap-2">
							<div v-for="item in customerResources[0].detailFields.slice(0, 4)" :key="item.key" class="rounded border border-outline-gray-2 bg-surface-white px-3 py-2">
								<p class="text-sm text-ink-gray-5">{{ item.label }}</p>
								<p class="mt-1 truncate text-sm font-medium text-ink-gray-9">{{ customer[item.key] || '-' }}</p>
							</div>
						</div>
						<p v-else class="text-sm leading-5 text-ink-gray-5">A Customer record linked to the signed-in user has not been found yet.</p>
					</div>
					<div v-else-if="tab.label === 'Sites'" class="space-y-2">
						<div class="flex items-center justify-between rounded border border-outline-gray-2 bg-surface-white px-3 py-2">
							<span class="text-sm text-ink-gray-5">Linked sites</span>
							<span class="text-sm font-medium text-ink-gray-9">{{ sites.length }}</span>
						</div>
						<p v-if="!sites.length" class="text-sm leading-5 text-ink-gray-5">No linked sites yet.</p>
						<div v-for="site in sites" v-else :key="site.name" class="rounded px-2 py-1.5 text-sm hover:bg-surface-gray-1">
							<p class="truncate font-medium text-ink-gray-9">{{ site.title || site.name }}</p>
							<p class="truncate text-xs text-ink-gray-5">{{ site.route_status === 'Ready' ? 'Ready to open' : (site.provisioning_status || 'Preparing') }}</p>
						</div>
					</div>
					<div v-else class="space-y-3">
						<p class="text-sm leading-5 text-ink-gray-5">Customer user invitations, role profiles, and Site access grants are planned in the Central User Access pass. For now, use Plans and Sites for launch flow.</p>
						<Button :to="'/customer/sites'" tag="RouterLink" variant="subtle">Open Sites</Button>
					</div>
				</template>
			</Tabs>
		</template>
	</WorkspaceLayout>
</template>
