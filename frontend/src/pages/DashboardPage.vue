<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { Badge, Button, ListView } from 'frappe-ui'
import { Activity, CreditCard, Globe2, LifeBuoy, Server, SquareArrowOutUpRight, Users } from 'lucide-vue-next'
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

	data.platformSettings = await getDoc(platformSettings.doctype, platformSettings.doctype).catch(() => null)

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
	{ label: 'Create Site', route: '/customer/create-site', count: data.customerSites.length ? 0 : 1, icon: SquareArrowOutUpRight, note: data.customerSites.length ? 'Start another site' : 'Recommended next step' },
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

const externalSystems = computed(() => [
	{
		label: 'Billing',
		icon: CreditCard,
		configured: Boolean(data.platformSettings?.billing_system),
		value: data.platformSettings?.billing_system || 'Not configured',
		customerNote: 'Invoices, plans, renewal, and finance status are read from the billing system.',
		platformNote: 'Platform agents see finance context and may use SSO to billing when configured.',
	},
	{
		label: 'CRM',
		icon: Users,
		configured: Boolean(data.platformSettings?.crm_system),
		value: data.platformSettings?.crm_system || 'Not configured',
		customerNote: 'Account relationship and onboarding status are read from CRM.',
		platformNote: 'Platform agents see CRM relationship context and may use SSO to CRM when configured.',
	},
	{
		label: 'Support',
		icon: LifeBuoy,
		configured: Boolean(data.platformSettings?.support_system),
		value: data.platformSettings?.support_system || 'Not configured',
		customerNote: 'Support ticket summaries and redirects use the configured support system.',
		platformNote: 'Platform agents see support state and may use SSO to the support system when configured.',
	},
])

const assistantContext = computed(() => {
	const missing = externalSystems.value.filter((system) => !system.configured).map((system) => `${system.label} system not configured`)
	return {
		scope: props.scope,
		summary: props.scope === 'customer'
			? 'Customer dashboard guidance focused on creating sites, reviewing commercial summaries, and finding support paths.'
			: 'Platform dashboard guidance focused on operational inventory, placement shape, and external-system readiness.',
		badges: [props.scope, loading.value ? 'loading' : 'ready'],
		sections: props.scope === 'customer'
			? [
				{ label: 'Customer account', value: data.customerAccount?.name || 'No linked customer record' },
				{ label: 'Sites', value: `${data.customerSites.length} linked site(s)` },
				{ label: 'Primary action', value: 'Create Site is the main conversion path.' },
			]
			: [
				{ label: 'Customers', value: `${(data.platform.customers || []).length} recent record(s)` },
				{ label: 'Sites', value: `${(data.platform.sites || []).length} recent record(s)` },
				{ label: 'External systems', value: externalSystems.value.map((system) => `${system.label}: ${system.configured ? 'configured' : 'missing'}`).join(', ') },
			],
		gaps: missing,
		nextSteps: props.scope === 'customer'
			? ['Create a site when root domain is configured.', 'Use Support for standard requests; advanced operations remain locked.']
			: ['Open Customers or Sites for External context.', 'Use Region tree/list to inspect placement hierarchy.'],
	}
})
</script>

<template>
	<WorkspaceLayout
		title="Dashboard"
		:subtitle="scope === 'customer'
			? 'Create and manage LensCloud sites from a customer-first workspace.'
			: 'Operator-friendly surface for customers, release groups, benches, sites, regions, and settings.'"
		inspector-kicker="Scope inspector"
		inspector-title="Workspace context"
		:inspector-subtitle="scope === 'customer'
			? 'Customer site status, activation path, and request context.'
			: 'Platform control-plane context, recent records, and session visibility.'"
		assistant-label="Assistant"
		assistant-hint="The assistant stays attached to the current dashboard context and can be expanded from the inspector."
		:assistant-context="assistantContext"
	>
		<template #actions>
			<Button v-if="scope === 'customer'" :as="RouterLink" to="/customer/create-site">
				<SquareArrowOutUpRight class="size-4" />
				Create Site
			</Button>
			<Badge v-if="scope === 'platform'" class="bg-surface-gray-2 text-ink-gray-6">Platform first</Badge>
			<Badge v-else class="bg-surface-gray-2 text-ink-gray-6">Site first</Badge>
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

				<section v-if="scope === 'customer'" class="grid gap-3 xl:grid-cols-3">
					<div v-for="system in externalSystems" :key="system.label" class="rounded border border-outline-gray-2 bg-surface-white p-4">
						<div class="flex items-start justify-between gap-3">
							<div class="flex items-center gap-2">
								<component :is="system.icon" class="size-4 text-ink-gray-5" />
								<p class="text-sm font-semibold text-ink-gray-9">{{ system.label }}</p>
							</div>
							<Badge :class="system.configured ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'">{{ system.configured ? 'Configured' : 'Gap' }}</Badge>
						</div>
						<p class="mt-3 truncate text-sm font-medium text-ink-gray-9">{{ system.value }}</p>
						<p class="mt-1 text-sm leading-5 text-ink-gray-5">{{ system.customerNote }}</p>
					</div>
				</section>

				<section v-if="scope === 'platform'" class="rounded border border-outline-gray-2 bg-surface-white p-4">
					<p class="text-[11px] font-medium uppercase tracking-[0.18em] text-ink-gray-5">External systems</p>
					<h2 class="mt-1 text-base font-semibold text-ink-gray-9">Billing, CRM, and support context</h2>
					<div class="mt-3 grid gap-3 xl:grid-cols-3">
						<div v-for="system in externalSystems" :key="system.label" class="rounded border border-outline-gray-2 bg-surface-gray-1 p-3">
							<div class="flex items-start justify-between gap-3">
								<div class="flex items-center gap-2">
									<component :is="system.icon" class="size-4 text-ink-gray-5" />
									<p class="text-sm font-semibold text-ink-gray-9">{{ system.label }}</p>
								</div>
								<Badge :class="system.configured ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'">{{ system.configured ? 'SSO ready' : 'Missing' }}</Badge>
							</div>
							<p class="mt-3 truncate text-sm font-medium text-ink-gray-9">{{ system.value }}</p>
							<p class="mt-1 text-sm leading-5 text-ink-gray-5">{{ system.platformNote }}</p>
						</div>
					</div>
				</section>

				<section v-else class="grid gap-3 xl:grid-cols-[1fr_1fr]">
					<div class="rounded border border-outline-gray-2 bg-surface-white p-4">
						<p class="text-[11px] font-medium uppercase tracking-[0.18em] text-ink-gray-5">Next step</p>
						<h2 class="mt-1 text-base font-semibold text-ink-gray-9">{{ data.customerSites.length ? 'Manage your sites' : 'Create your first site' }}</h2>
						<p class="mt-2 text-sm leading-6 text-ink-gray-5">{{ data.customerSites.length ? 'Open a site to review status and start lifecycle actions.' : 'Start a site request from the customer portal. Provisioning remains pending until backend orchestration is connected.' }}</p>
						<div class="mt-4 flex flex-wrap gap-2">
							<Button :as="RouterLink" to="/customer/create-site">
								<SquareArrowOutUpRight class="size-4" />
								Create Site
							</Button>
							<Button :as="RouterLink" to="/customer/sites" variant="subtle">View Sites</Button>
						</div>
					</div>

					<div class="rounded border border-outline-gray-2 bg-surface-white p-4">
						<p class="text-[11px] font-medium uppercase tracking-[0.18em] text-ink-gray-5">Sites</p>
						<h2 class="mt-1 text-base font-semibold text-ink-gray-9">Recent instances</h2>
						<div v-if="!data.customerAccount" class="mt-3 rounded border border-dashed border-outline-gray-2 bg-surface-gray-1 p-4">
							<p class="text-sm font-medium text-ink-gray-9">Customer record not linked</p>
							<p class="mt-1 text-sm leading-6 text-ink-gray-5">The frontend expects a Customer record tied to the signed-in user.</p>
						</div>
						<div v-else-if="!data.customerSites.length" class="mt-3 rounded border border-dashed border-outline-gray-2 bg-surface-gray-1 p-4">
							<p class="text-sm font-medium text-ink-gray-9">No sites yet</p>
							<p class="mt-1 text-sm leading-6 text-ink-gray-5">Create a site to start using LensCloud.</p>
						</div>
						<div v-else class="mt-3 space-y-2">
							<RouterLink v-for="site in data.customerSites" :key="site.name" :to="`/customer/sites/${encodeURIComponent(site.name)}`" class="flex items-center justify-between gap-3 rounded px-2 py-2 transition hover:bg-surface-gray-1">
								<div class="min-w-0">
									<p class="truncate text-sm font-medium text-ink-gray-9">{{ site.title || site.name }}</p>
									<p class="truncate text-xs text-ink-gray-5">{{ formatFieldValue(site.bench) }}</p>
								</div>
								<Badge class="bg-surface-gray-2 text-ink-gray-6">Open</Badge>
							</RouterLink>
						</div>
					</div>
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
						<p>Billing system: {{ data.platformSettings?.billing_system || 'Not configured' }}</p>
						<p>CRM system: {{ data.platformSettings?.crm_system || 'Not configured' }}</p>
						<p>Support system: {{ data.platformSettings?.support_system || 'Not configured' }}</p>
					</div>
				</div>
			</div>
		</template>
	</WorkspaceLayout>
</template>
