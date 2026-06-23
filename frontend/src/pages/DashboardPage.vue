<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { Alert, Badge, Button } from 'frappe-ui'
import { AlertTriangle, CheckCircle2, Clock3, Globe2, Server, SquareArrowOutUpRight, Users } from 'lucide-vue-next'
import { callMethod, listDocs } from '@/lib/api'
import { useSessionStore } from '@/lib/session'
import WorkspaceLayout from '@/components/WorkspaceLayout.vue'

const props = defineProps({ scope: { type: String, required: true } })
const session = useSessionStore()
const loading = ref(true)
const error = ref('')
const platform = ref(null)
const customer = ref(null)
const customerSites = ref([])

async function loadPlatform() {
	const response = await callMethod('lenscloud.api.launch.get_platform_dashboard')
	platform.value = response.message || response
}

async function loadCustomer() {
	const response = await callMethod('lenscloud.api.orchestration.get_customer_portal_context')
	customer.value = response.message || response
	if (customer.value?.customer?.name) {
		customerSites.value = await listDocs('Site', {
			fields: ['name', 'title', 'site_status', 'provisioning_status', 'route_status', 'access_url', 'modified'],
			filters: [['customer', '=', customer.value.customer.name]], limit: 8,
		})
	} else customerSites.value = []
}

async function load() {
	loading.value = true; error.value = ''
	try { await (props.scope === 'platform' ? loadPlatform() : loadCustomer()) }
	catch (err) { error.value = err?.message || 'Unable to load dashboard.' }
	finally { loading.value = false }
}

onMounted(load)
watch(() => props.scope, load)

const metrics = computed(() => platform.value?.metrics || {})
const actionItems = computed(() => {
	const source = platform.value?.action_required || {}
	return [
		{ label: 'Failed Sites', value: source.failed_sites || 0, route: '/platform/sites' },
		{ label: 'Pending approvals', value: source.pending_approvals || 0, route: '/platform/subscriptions' },
		{ label: 'Failed tests', value: source.failed_tests || 0, route: '/platform/environment-test-runs' },
		{ label: 'Failed actions', value: source.failed_actions || 0, route: '/platform/orchestration-logs' },
	]
})
const activeSite = computed(() => customerSites.value.find((site) => !['Deleted'].includes(site.site_status)) || null)
const customerPlans = computed(() => customer.value?.plans || [])
const freePlan = computed(() => customerPlans.value.find((plan) => Number(plan.is_free)) || null)
</script>

<template>
	<WorkspaceLayout
		title="Dashboard"
		:subtitle="scope === 'platform' ? 'Launch readiness, customer activity, capacity, and work requiring attention.' : 'Create your first Site and follow its activation progress.'"
		:inspector-kicker="scope === 'platform' ? 'Launch status' : 'Your service'"
		:inspector-title="scope === 'platform' ? (platform?.launch_ready ? 'Ready for customer onboarding' : 'Launch gates need attention') : (activeSite?.title || 'Free Plan onboarding')"
		:inspector-subtitle="scope === 'platform' ? 'All values come from authoritative aggregate APIs.' : 'Technical placement remains managed by LensCloud.'"
	>
		<template #actions>
			<Button v-if="scope === 'customer'" :as="RouterLink" to="/customer/create-site"><SquareArrowOutUpRight class="size-4" />Create Site</Button>
			<Button variant="subtle" @click="load">Refresh</Button>
		</template>

		<template #main>
			<div class="h-full overflow-y-auto p-4">
				<Alert v-if="error" theme="red" title="Dashboard unavailable" :description="error" />
				<div v-else-if="loading" class="rounded border border-outline-gray-2 bg-surface-white p-6 text-sm text-ink-gray-5">Loading current state...</div>

				<template v-else-if="scope === 'platform' && platform">
					<section class="rounded border border-outline-gray-2 bg-surface-white p-4">
						<div class="flex items-center justify-between gap-3">
							<div><p class="text-xs font-medium text-ink-gray-5">Launch readiness</p><h2 class="mt-1 text-base font-semibold text-ink-gray-9">Customer onboarding gates</h2></div>
							<Badge :class="platform.launch_ready ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'">{{ platform.launch_ready ? 'Ready' : 'Attention required' }}</Badge>
						</div>
						<div class="mt-3 grid gap-2 md:grid-cols-2 xl:grid-cols-3">
							<div v-for="gate in platform.gates" :key="gate.key" class="flex items-start gap-2 rounded bg-surface-gray-1 px-3 py-2">
								<CheckCircle2 v-if="gate.ready" class="mt-0.5 size-4 shrink-0 text-emerald-600" /><AlertTriangle v-else class="mt-0.5 size-4 shrink-0 text-amber-600" />
								<div class="min-w-0"><p class="text-sm font-medium text-ink-gray-8">{{ gate.label }}</p><p class="truncate text-xs text-ink-gray-5">{{ gate.message }}</p></div>
							</div>
						</div>
					</section>

					<section class="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
						<RouterLink v-for="item in [
							{ label: 'Customers', value: metrics.customers, route: '/platform/customers', icon: Users },
							{ label: 'Subscriptions', value: metrics.subscriptions, route: '/platform/subscriptions', icon: Clock3 },
							{ label: 'Provisioning Sites', value: metrics.provisioning_sites, route: '/platform/sites', icon: Server },
							{ label: 'Ready Sites', value: metrics.ready_sites, route: '/platform/sites', icon: Globe2 },
						]" :key="item.label" :to="item.route" class="rounded border border-outline-gray-2 bg-surface-white p-3 hover:bg-surface-gray-1">
							<div class="flex items-center justify-between"><p class="text-sm text-ink-gray-5">{{ item.label }}</p><component :is="item.icon" class="size-4 text-ink-gray-4" /></div>
							<p class="mt-2 text-2xl font-semibold text-ink-gray-9">{{ item.value || 0 }}</p>
						</RouterLink>
					</section>

					<section class="mt-3 grid gap-3 xl:grid-cols-2">
						<div class="rounded border border-outline-gray-2 bg-surface-white p-4">
							<h2 class="text-base font-semibold text-ink-gray-9">Action required</h2>
							<div class="mt-3 divide-y divide-outline-gray-1">
								<RouterLink v-for="item in actionItems" :key="item.label" :to="item.route" class="flex items-center justify-between py-2 text-sm hover:text-ink-gray-9"><span class="text-ink-gray-6">{{ item.label }}</span><Badge :class="item.value ? 'bg-red-50 text-red-700' : 'bg-surface-gray-1 text-ink-gray-6'">{{ item.value }}</Badge></RouterLink>
							</div>
						</div>
						<div class="rounded border border-outline-gray-2 bg-surface-white p-4">
							<h2 class="text-base font-semibold text-ink-gray-9">Regional capacity</h2>
							<div class="mt-3 space-y-2"><div v-for="row in platform.capacity" :key="row.name" class="rounded bg-surface-gray-1 px-3 py-2"><div class="flex justify-between text-sm"><span class="font-medium text-ink-gray-8">{{ row.title || row.name }}</span><span class="text-ink-gray-5">{{ row.cluster || 'No cluster' }}</span></div><p class="mt-1 text-xs text-ink-gray-5">Free {{ row.free_benches }} · Benches {{ row.ready_benches }} · Databases {{ row.ready_databases }} · Sites {{ row.ready_sites }}</p></div></div>
						</div>
					</section>
				</template>

				<template v-else-if="scope === 'customer'">
					<section class="rounded border border-outline-gray-2 bg-surface-white p-5">
						<div v-if="!activeSite" class="max-w-2xl">
							<Badge class="bg-emerald-50 text-emerald-700">{{ freePlan?.title || 'Free Plan' }}</Badge>
							<h2 class="mt-3 text-xl font-semibold text-ink-gray-9">Create your first LensCloud Site</h2>
							<p class="mt-2 text-sm leading-6 text-ink-gray-5">Choose your Region and subdomain. LensCloud assigns compatible shared capacity and keeps the infrastructure details out of your way.</p>
							<Button class="mt-4" :as="RouterLink" to="/customer/create-site">Start setup</Button>
						</div>
						<div v-else>
							<div class="flex items-start justify-between gap-3"><div><p class="text-sm text-ink-gray-5">Your Site</p><h2 class="mt-1 text-lg font-semibold text-ink-gray-9">{{ activeSite.title }}</h2></div><Badge :class="['Ready','Active'].includes(activeSite.site_status) ? 'bg-emerald-50 text-emerald-700' : 'bg-blue-50 text-blue-700'">{{ activeSite.site_status }}</Badge></div>
							<p class="mt-3 text-sm text-ink-gray-5">Provisioning: {{ activeSite.provisioning_status || 'Pending' }} · Route: {{ activeSite.route_status || 'Pending' }}</p>
							<div class="mt-4 flex gap-2"><Button :as="RouterLink" :to="`/customer/sites/${encodeURIComponent(activeSite.name)}`">View progress</Button><Button v-if="activeSite.access_url" as="a" :href="activeSite.access_url" target="_blank" variant="subtle">Open Site</Button></div>
						</div>
					</section>
				</template>
			</div>
		</template>

		<template #inspector>
			<div class="space-y-2 text-sm">
				<div v-if="scope === 'platform'" class="rounded bg-surface-gray-1 p-3"><p class="font-medium text-ink-gray-8">Truthful metrics</p><p class="mt-1 text-ink-gray-5">Counts are calculated server-side without list limits.</p></div>
				<div v-else class="rounded bg-surface-gray-1 p-3"><p class="font-medium text-ink-gray-8">Simple by design</p><p class="mt-1 text-ink-gray-5">Your Plan determines the supported environment and isolation policy.</p></div>
			</div>
		</template>
	</WorkspaceLayout>
</template>
