<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { Alert, Badge, Button } from 'frappe-ui'
import { AlertTriangle, ArrowRight, CheckCircle2, Clock3, CreditCard, ExternalLink, Globe2, LifeBuoy, Package, Server, Sparkles, Users } from 'lucide-vue-next'
import { callMethod } from '@/lib/api'
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
	customerSites.value = customer.value?.sites || []
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
const customerUsage = computed(() => customer.value?.usage || {})
const onboardingStep = computed(() => customer.value?.onboarding_step || 'choose_plan')
const freePlan = computed(() => customerPlans.value.find((plan) => Number(plan.is_free)) || null)
const selectedSubscription = computed(() => (customer.value?.subscriptions || [])[0] || null)
const hasSubscription = computed(() => Boolean(selectedSubscription.value))
</script>

<template>
	<WorkspaceLayout
		title="Dashboard"
		:subtitle="scope === 'platform' ? 'Launch readiness, customer activity, capacity, and work requiring attention.' : 'Choose a Plan, track provisioning, and open your LensCloud Site.'"
		:inspector-kicker="scope === 'platform' ? 'Launch status' : 'Your service'"
		:inspector-title="scope === 'platform' ? (platform?.launch_ready ? 'Ready for customer onboarding' : 'Launch gates need attention') : (activeSite?.title || 'Free Plan onboarding')"
		:inspector-subtitle="scope === 'platform' ? 'All values come from authoritative aggregate APIs.' : 'Your Plan, Subscription, and Site progress stay here.'"
	>
		<template #actions>
			<Button variant="subtle" @click="load">Refresh</Button>
		</template>

		<template #main>
			<div class="h-full overflow-y-auto bg-[#f7f9fb] p-4">
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
					<section v-if="!hasSubscription" class="mx-auto grid min-h-[620px] max-w-5xl content-center rounded-2xl border border-[#EDEDED] bg-white p-6 text-[#191c1e] lg:p-10">
						<div class="grid gap-8 lg:grid-cols-[1fr_340px] lg:items-center">
							<div>
								<div class="mb-8 flex items-center gap-3">
									<div class="grid size-9 place-items-center rounded-lg bg-[#1D4ED8] text-white"><Sparkles class="size-4" /></div>
									<span class="text-lg font-bold text-[#1D4ED8]">LensCloud</span>
								</div>
								<div class="inline-flex items-center gap-2 rounded-full border border-[#cad3ff] bg-[#dce1ff] px-3 py-1 text-xs font-semibold text-[#0039b5]">
									<CheckCircle2 class="size-3.5" />
									Account ready
								</div>
								<h2 class="mt-5 max-w-2xl text-[28px] font-bold leading-[36px] text-[#191c1e] lg:text-[36px] lg:leading-[44px]">Launch your first LensCloud Site in a guided flow</h2>
								<p class="mt-4 max-w-xl text-base leading-6 text-[#505f76]">Choose the Free Plan, confirm your ₹0 subscription, and LensCloud will prepare your Site. You will always know the next step.</p>
								<div class="mt-7 flex flex-col gap-3 sm:flex-row">
									<RouterLink to="/customer/plans" class="inline-flex min-h-12 items-center justify-center gap-2 rounded-lg bg-[#1D4ED8] px-6 py-3 text-sm font-bold text-white shadow-sm transition hover:bg-[#0037b0] focus:outline-none focus:ring-2 focus:ring-[#b7c4ff] focus:ring-offset-2 active:scale-[0.99]">
										Choose a Plan
										<ArrowRight class="size-4" />
									</RouterLink>
								</div>
							</div>

							<aside class="rounded-xl border border-[#EDEDED] bg-[#f7f9fb] p-5">
								<p class="text-xs font-semibold text-[#64748B]">What happens next</p>
								<div class="mt-4 space-y-3">
									<div v-for="(item, index) in [
										{ label: 'Choose Free Plan', detail: 'Start with ₹0 due today' },
										{ label: 'Confirm subscription', detail: 'No payment method required' },
										{ label: 'Prepare Site', detail: 'Track setup progress here' },
										{ label: 'Open Site', detail: 'Access when ready' },
									]" :key="item.label" class="flex gap-3 rounded-lg border border-[#EDEDED] bg-white p-3">
										<div class="grid size-8 shrink-0 place-items-center rounded-full" :class="index === 0 ? 'bg-[#1D4ED8] text-white' : 'bg-[#dce1ff] text-[#0039b5]'">{{ index + 1 }}</div>
										<div><p class="text-sm font-semibold text-[#191c1e]">{{ item.label }}</p><p class="text-xs leading-5 text-[#64748B]">{{ item.detail }}</p></div>
									</div>
								</div>
							</aside>
						</div>
					</section>

					<template v-else>
						<section class="mx-auto max-w-5xl rounded-2xl border border-[#EDEDED] bg-white p-6 text-[#191c1e] lg:p-8">
							<div class="grid gap-6 lg:grid-cols-[1fr_320px] lg:items-start">
								<div>
									<Badge :class="onboardingStep === 'ready' ? 'bg-emerald-50 text-emerald-700' : onboardingStep === 'provisioning' ? 'bg-blue-50 text-blue-700' : 'bg-[#dce1ff] text-[#0039b5]'">{{ onboardingStep === 'ready' ? 'Ready to open' : onboardingStep === 'provisioning' ? 'Provisioning' : 'Subscription active' }}</Badge>
									<h2 class="mt-4 text-[24px] font-semibold leading-8 text-[#191c1e]">{{ activeSite ? 'Your LensCloud Site is on its way' : 'Your subscription is active' }}</h2>
									<p class="mt-3 max-w-xl text-sm leading-6 text-[#505f76]">{{ activeSite ? 'Follow setup progress and open your Site as soon as it is ready.' : 'Your service subscription is ready. Start or review your Site setup from here.' }}</p>
									<div class="mt-6 flex flex-col gap-3 sm:flex-row">
										<a v-if="activeSite && ['Ready','Active'].includes(activeSite.site_status) && activeSite.access_url" :href="activeSite.access_url" target="_blank" class="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-[#1D4ED8] px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-[#0037b0] focus:outline-none focus:ring-2 focus:ring-[#b7c4ff] focus:ring-offset-2">
											Open Site
											<ExternalLink class="size-4" />
										</a>
										<RouterLink v-else-if="activeSite" :to="`/customer/plans?site=${encodeURIComponent(activeSite.name)}&subscription=${encodeURIComponent(activeSite.subscription || '')}`" class="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-[#1D4ED8] px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-[#0037b0] focus:outline-none focus:ring-2 focus:ring-[#b7c4ff] focus:ring-offset-2">
											View provisioning progress
											<ArrowRight class="size-4" />
										</RouterLink>
										<RouterLink v-else to="/customer/subscriptions" class="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-[#1D4ED8] px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-[#0037b0] focus:outline-none focus:ring-2 focus:ring-[#b7c4ff] focus:ring-offset-2">
											Continue setup
											<ArrowRight class="size-4" />
										</RouterLink>
										<RouterLink to="/customer/plans" class="inline-flex min-h-11 items-center justify-center rounded-lg border border-[#EDEDED] bg-white px-5 py-3 text-sm font-semibold text-[#505f76] transition hover:bg-[#f2f4f6]">Add New Subscription</RouterLink>
									</div>
								</div>
								<div class="grid grid-cols-3 gap-2 text-center">
									<RouterLink to="/customer/subscriptions" class="rounded-lg border border-[#1D4ED8] bg-[#dce1ff] p-3 transition hover:bg-[#cad3ff]"><p class="text-xl font-semibold text-[#191c1e]">{{ customerUsage.subscriptions || 0 }}</p><p class="text-xs font-semibold text-[#0039b5]">Subscriptions</p></RouterLink>
									<div class="rounded-lg border border-[#EDEDED] bg-[#f7f9fb] p-3"><p class="text-xl font-semibold text-[#191c1e]">{{ customerUsage.sites || 0 }}</p><p class="text-xs text-[#64748B]">Sites</p></div>
									<div class="rounded-lg border border-[#EDEDED] bg-[#f7f9fb] p-3"><p class="text-xl font-semibold text-[#191c1e]">{{ customerUsage.ready_sites || 0 }}</p><p class="text-xs text-[#64748B]">Ready</p></div>
								</div>
							</div>
						</section>

						<section class="mx-auto mt-4 grid max-w-5xl gap-4 md:grid-cols-3">
							<div class="rounded-xl border border-[#EDEDED] bg-white p-4"><div class="flex items-center gap-2"><CreditCard class="size-4 text-[#1D4ED8]" /><p class="text-sm font-semibold text-[#191c1e]">{{ selectedSubscription?.plan || freePlan?.title || 'Subscription' }}</p></div><p class="mt-2 text-sm leading-6 text-[#64748B]">{{ selectedSubscription?.status || 'Active' }} service subscription.</p></div>
							<div class="rounded-xl border border-[#EDEDED] bg-white p-4"><div class="flex items-center gap-2"><Globe2 class="size-4 text-[#1D4ED8]" /><p class="text-sm font-semibold text-[#191c1e]">{{ activeSite?.title || activeSite?.name || 'Site setup' }}</p></div><p class="mt-2 text-sm leading-6 text-[#64748B]">{{ activeSite?.site_status || 'Preparing' }}</p></div>
							<div class="rounded-xl border border-[#EDEDED] bg-white p-4"><div class="flex items-center gap-2"><LifeBuoy class="size-4 text-[#1D4ED8]" /><p class="text-sm font-semibold text-[#191c1e]">Support</p></div><p class="mt-2 text-sm leading-6 text-[#64748B]">Contact support from any setup state.</p></div>
						</section>
					</template>
				</template>			</div>
		</template>

		<template #inspector>
			<div class="space-y-2 text-sm">
				<div v-if="scope === 'platform'" class="rounded bg-surface-gray-1 p-3"><p class="font-medium text-ink-gray-8">Truthful metrics</p><p class="mt-1 text-ink-gray-5">Counts are calculated server-side without list limits.</p></div>
				<div v-else class="rounded bg-surface-gray-1 p-3"><p class="font-medium text-ink-gray-8">Simple by design</p><p class="mt-1 text-ink-gray-5">Your Plan determines the supported environment and isolation policy.</p></div>
			</div>
		</template>
	</WorkspaceLayout>
</template>
