<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { Badge, Button, ListView } from 'frappe-ui'
import { Activity, Globe2, Server, Users } from 'lucide-vue-next'
import { listDocs, formatFieldValue, getDoc } from '@/lib/api'
import { platformResources, customerResources, platformSettings } from '@/lib/catalog'
import { useSessionStore } from '@/lib/session'
import WorkspaceLayout from '@/components/WorkspaceLayout.vue'

const props = defineProps({
	scope: { type: String, required: true },
})

const session = useSessionStore()
const loading = ref(true)
const data = reactive({
	platform: {},
	customerSites: [],
	platformSettings: null,
	customerAccount: null,
})

const resources = computed(() => (props.scope === 'customer' ? customerResources : platformResources))

async function loadPlatform() {
	const entries = await Promise.all(
		platformResources.map(async (resource) => {
			const items = await listDocs(resource.doctype, {
				fields: ['name', ...resource.summaryFields.map((field) => field.key)],
				limit: 4,
			})

			return { key: resource.key, items }
		}),
	)

	for (const entry of entries) {
		data.platform[entry.key] = entry.items
	}

	data.platformSettings = await getDoc(platformSettings.doctype, platformSettings.doctype).catch(() => null)
}

async function loadCustomer() {
	const customerRecords = await listDocs('Customer', {
		fields: ['name', 'first_name', 'last_name', 'region', 'external_customer_id'],
		limit: 1,
		filters: [['user', '=', session.user]],
	})

	data.customerAccount = customerRecords[0] || null

	if (data.customerAccount) {
		data.customerSites = await listDocs('Site', {
			fields: ['name', 'title', 'bench', 'customer', 'modified'],
			limit: 4,
			filters: [['customer', '=', data.customerAccount.name]],
		})
	}
}

async function load() {
	loading.value = true
	try {
		if (props.scope === 'customer') {
			await loadCustomer()
		} else {
			await loadPlatform()
		}
	} finally {
		loading.value = false
	}
}

onMounted(load)
watch(() => props.scope, load)

const platformSummary = computed(() => [
	{ label: 'Customers', route: '/platform/customers', count: (data.platform.customers || []).length, icon: Users, note: 'Identity records' },
	{ label: 'Sites', route: '/platform/sites', count: (data.platform.sites || []).length, icon: Globe2, note: 'Tenant instances' },
	{ label: 'Benches', route: '/platform/benches', count: (data.platform.benches || []).length, icon: Server, note: 'Runtime groups' },
	{ label: 'Regions', route: '/platform/regions', count: (data.platform.regions || []).length, icon: Activity, note: 'Placement map' },
])

const customerSummary = computed(() => [
	{ label: 'Sites', route: '/customer/sites', count: data.customerSites.length, icon: Globe2, note: 'Linked instances' },
	{ label: 'Account', route: '/customer/account', count: data.customerAccount ? 1 : 0, icon: Users, note: 'Customer identity' },
])

const dashboardMetrics = computed(() => (props.scope === 'customer' ? customerSummary.value : platformSummary.value))
const maxMetric = computed(() => Math.max(...dashboardMetrics.value.map((item) => item.count), 1))
const placementRows = computed(() => {
	const benches = data.platform.benches || []
	const sites = data.platform.sites || []
	const regions = data.platform.regions || []
	return [
		{ label: 'Sites per bench', value: sites.length, total: Math.max(benches.length, 1), hint: `${sites.length} sites / ${benches.length || 0} benches` },
		{ label: 'Benches per region', value: benches.length, total: Math.max(regions.length, 1), hint: `${benches.length || 0} benches / ${regions.length || 0} regions` },
		{ label: 'Release coverage', value: (data.platform['release-groups'] || []).length, total: Math.max(benches.length, 1), hint: `${(data.platform['release-groups'] || []).length} release groups` },
	]
})
</script>

<template>
	<WorkspaceLayout
		title="Dashboard"
		:subtitle="scope === 'customer'
			? 'Your authenticated surface for account visibility and customer lifecycle tracking.'
			: 'Operator-friendly surface for customers, release groups, benches, sites, regions, and settings.'"
		inspector-kicker="Scope inspector"
		inspector-title="Workspace context"
		:inspector-subtitle="scope === 'customer'
			? 'Customer-facing dashboard context, linked sites, and request entry points.'
			: 'Platform control-plane context, recent records, and session visibility.'"
		assistant-label="Assistant"
		assistant-hint="The assistant stays attached to the current dashboard context and can be expanded from the inspector."
	>
		<template #actions>
			<Badge v-if="scope === 'platform'" class="bg-surface-gray-2 text-ink-gray-6">Platform first</Badge>
			<Badge v-else class="bg-surface-gray-2 text-ink-gray-6">Customer facing</Badge>
			<Button variant="subtle" @click="load">Refresh</Button>
		</template>

		<template #main>
			<div class="h-full overflow-y-auto p-4">
			<div v-if="loading" class="rounded border border-outline-gray-2 bg-surface-white p-6">
				<div class="flex items-center gap-3">
					<LoadingIndicator />
					<div>
						<p class="text-sm font-medium text-ink-gray-8">Loading dashboard…</p>
						<p class="text-sm leading-6 text-ink-gray-5">Reading from native Frappe document APIs.</p>
					</div>
				</div>
			</div>

			<template v-else>
				<section class="rounded border border-outline-gray-2 bg-surface-white p-4">
					<div class="flex items-center justify-between gap-3">
						<div>
							<p class="text-[11px] font-medium uppercase tracking-[0.18em] text-ink-gray-5">Overview</p>
							<h2 class="mt-1 text-base font-semibold text-ink-gray-9">{{ scope === 'customer' ? 'Customer health' : 'Platform health' }}</h2>
						</div>
						<Badge class="bg-surface-gray-2 text-ink-gray-6">{{ loading ? 'Loading' : 'Live' }}</Badge>
					</div>

					<div class="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
						<RouterLink v-for="item in dashboardMetrics" :key="item.label" :to="item.route" class="rounded border border-outline-gray-2 bg-surface-gray-1 p-3 transition hover:bg-surface-gray-2">
							<div class="flex items-start justify-between gap-3">
								<div>
									<p class="text-sm font-medium text-ink-gray-7">{{ item.label }}</p>
									<p class="mt-1 text-2xl font-semibold text-ink-gray-9">{{ item.count }}</p>
									<p class="mt-1 text-xs text-ink-gray-5">{{ item.note }}</p>
								</div>
								<div class="grid size-8 place-items-center rounded bg-surface-white text-ink-gray-5">
									<component :is="item.icon" class="size-4" />
								</div>
							</div>
							<div class="mt-3 h-1.5 overflow-hidden rounded-full bg-surface-gray-3">
								<div class="h-full rounded-full bg-ink-gray-8" :style="{ width: `${Math.max(8, (item.count / maxMetric) * 100)}%` }" />
							</div>
						</RouterLink>
					</div>
				</section>

				<section v-if="scope === 'platform'" class="grid min-h-0 gap-3 xl:grid-cols-[1fr_1fr]">
					<div class="rounded border border-outline-gray-2 bg-surface-white p-4">
						<p class="text-[11px] font-medium uppercase tracking-[0.18em] text-ink-gray-5">Placement</p>
						<h2 class="mt-1 text-base font-semibold text-ink-gray-9">Capacity shape</h2>
						<div class="mt-4 space-y-3">
							<div v-for="row in placementRows" :key="row.label">
								<div class="flex items-center justify-between gap-3 text-sm">
									<span class="font-medium text-ink-gray-8">{{ row.label }}</span>
									<span class="text-ink-gray-5">{{ row.hint }}</span>
								</div>
								<div class="mt-2 h-2 overflow-hidden rounded-full bg-surface-gray-2">
									<div class="h-full rounded-full bg-surface-gray-7" :style="{ width: `${Math.min(100, Math.max(6, (row.value / row.total) * 45))}%` }" />
								</div>
							</div>
						</div>
					</div>

					<div class="rounded border border-outline-gray-2 bg-surface-white p-4">
						<p class="text-[11px] font-medium uppercase tracking-[0.18em] text-ink-gray-5">Recent activity</p>
						<h2 class="mt-1 text-base font-semibold text-ink-gray-9">Latest records</h2>
						<div class="mt-3 space-y-2">
							<template v-for="resource in resources.slice(0, 4)" :key="resource.key">
								<RouterLink v-for="record in (data.platform[resource.key] || []).slice(0, 1)" :key="record.name" :to="resource.detailRoute(record.name)" class="flex items-center justify-between rounded px-2 py-1.5 transition hover:bg-surface-gray-1">
									<div class="min-w-0">
										<p class="truncate text-sm font-medium text-ink-gray-9">{{ record.title || record.first_name || record.name }}</p>
										<p class="truncate text-xs text-ink-gray-5">{{ resource.label }}</p>
									</div>
									<Badge class="bg-surface-gray-2 text-ink-gray-6">Open</Badge>
								</RouterLink>
							</template>
							<p v-if="!resources.some((resource) => (data.platform[resource.key] || []).length)" class="text-sm text-ink-gray-5">No recent records yet.</p>
						</div>
					</div>
				</section>

				<section v-else class="rounded border border-outline-gray-2 bg-surface-white p-4">
					<p class="text-[11px] font-medium uppercase tracking-[0.18em] text-ink-gray-5">Customer surface</p>
					<h2 class="mt-1 text-base font-semibold text-ink-gray-9">Account and site status</h2>
					<div v-if="!data.customerAccount" class="mt-3 rounded border border-dashed border-outline-gray-2 bg-surface-gray-1 p-4">
						<p class="text-sm font-medium text-ink-gray-9">Customer record not linked</p>
						<p class="mt-1 text-sm leading-6 text-ink-gray-5">The frontend expects a Customer record tied to the signed-in user.</p>
					</div>
					<ListView
						v-else
						class="mt-3 h-[360px] rounded border border-outline-gray-2"
						:columns="[
							{ label: 'Site', key: 'name', width: 3, getLabel: ({ row }) => row.title || row.name },
							{ label: 'Bench', key: 'bench', width: '160px', getLabel: ({ row }) => formatFieldValue(row.bench) },
						]"
						:rows="data.customerSites"
						row-key="name"
						:options="{ selectable: false, showTooltip: true }"
					/>
				</section>
			</template>
			</div>
		</template>

		<template #inspector>
			<div class="space-y-3">
				<div class="rounded border border-outline-gray-2 bg-surface-gray-1 p-4">
					<div class="flex items-start justify-between gap-3">
						<div>
							<p class="text-xs font-medium uppercase tracking-[0.18em] text-ink-gray-5">Session</p>
							<p class="mt-1 text-sm font-medium text-ink-gray-9">{{ session.user || 'Guest' }}</p>
						</div>
						<Avatar :label="session.user || 'Guest'" size="sm" />
					</div>
					<div class="mt-3 flex flex-wrap gap-2">
						<Badge class="bg-white text-ink-gray-6">{{ session.isPlatformUser ? 'Platform' : 'Customer' }}</Badge>
						<Badge class="bg-white text-ink-gray-6">{{ scope }}</Badge>
					</div>
					<p class="mt-3 text-sm leading-6 text-ink-gray-5">Native Frappe auth remains the source of truth for access and permissions.</p>
				</div>

				<div class="rounded border border-outline-gray-2 bg-surface-white p-4">
					<div class="flex items-center justify-between gap-3">
						<div>
							<p class="text-sm font-medium text-ink-gray-9">Workspace status</p>
							<p class="mt-1 text-xs text-ink-gray-5">Current surface and record counts.</p>
						</div>
						<Badge class="bg-surface-gray-2 text-ink-gray-6">{{ loading ? 'Loading' : 'Ready' }}</Badge>
					</div>
					<div class="mt-3 space-y-2 text-sm leading-6 text-ink-gray-6">
						<p>Platform resources: {{ platformSummary.length }}</p>
						<p>Customer resources: {{ customerSummary.length }}</p>
						<p>Assistant drawer is reserved beneath the inspector header.</p>
					</div>
				</div>
			</div>
		</template>
	</WorkspaceLayout>
</template>
