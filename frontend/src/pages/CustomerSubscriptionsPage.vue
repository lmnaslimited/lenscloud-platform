<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { Alert, Badge, Button } from 'frappe-ui'
import { ArrowRight, CheckCircle2, Clock3, CreditCard, ExternalLink, Globe2, Package, RefreshCcw } from 'lucide-vue-next'
import { callMethod } from '@/lib/api'
import WorkspaceLayout from '@/components/WorkspaceLayout.vue'

const route = useRoute()

const loading = ref(true)
const error = ref('')
const context = ref(null)
const selectedName = ref('')

const subscriptions = computed(() => context.value?.subscriptions || [])
const sites = computed(() => context.value?.sites || [])
const plans = computed(() => context.value?.plans || [])
const selectedSubscription = computed(() => subscriptions.value.find((item) => item.name === selectedName.value) || subscriptions.value[0] || null)
const selectedPlan = computed(() => plans.value.find((plan) => plan.name === selectedSubscription.value?.plan) || null)
const environmentSequence = computed(() => selectedSubscription.value?.landscape_summary?.environments || [])
const linkedSites = computed(() => sites.value.filter((site) => site.subscription === selectedSubscription.value?.name))
const readySite = computed(() => linkedSites.value.find((site) => ['Ready', 'Active'].includes(site.site_status) && site.route_status === 'Ready' && site.access_url) || environmentSequence.value.find((item) => ['Ready', 'Active'].includes(item.site_status) && item.route_status === 'Ready' && item.access_url) || null)
const hasSubscriptions = computed(() => subscriptions.value.length > 0)
const selectedProgressSite = computed(() => linkedSites.value[0] || environmentSequence.value.find((item) => item.site) || null)

function statusClass(status) {
	if (['Active', 'Approved'].includes(status)) return 'bg-emerald-50 text-emerald-700'
	if (['Pending Approval', 'Requested', 'Draft'].includes(status)) return 'bg-amber-50 text-amber-700'
	if (['Cancelled', 'Failed'].includes(status)) return 'bg-red-50 text-red-700'
	return 'bg-blue-50 text-blue-700'
}

function siteStatusText(site) {
	if (!site) return 'No Site yet'
	if (['Ready', 'Active'].includes(site.site_status)) return 'Ready to open'
	if (['Failed'].includes(site.site_status)) return 'Needs support'
	return site.provisioning_status || site.site_status || 'Preparing'
}

function environmentStatusText(item) {
	if (!item?.site) return 'Waiting for setup'
	if (['Ready', 'Active'].includes(item.site_status)) return 'Ready to open'
	if (['Failed'].includes(item.site_status)) return 'Needs support'
	return item.provisioning_status || item.site_status || 'Preparing'
}

function formatDate(value) {
	if (!value) return 'Not set'
	return new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium' }).format(new Date(value))
}

async function load() {
	loading.value = true
	error.value = ''
	try {
		const response = await callMethod('lenscloud.api.orchestration.get_customer_portal_context')
		context.value = response.message || response
		if (route.query.subscription && subscriptions.value.some((item) => item.name === route.query.subscription)) selectedName.value = route.query.subscription
		if (!selectedName.value && subscriptions.value.length) selectedName.value = subscriptions.value[0].name
	} catch (err) {
		error.value = err?.message || 'Unable to load subscriptions.'
	} finally {
		loading.value = false
	}
}

onMounted(load)
</script>

<template>
	<WorkspaceLayout
		title="Subscriptions"
		subtitle="Review your LensCloud service subscriptions and setup progress."
		inspector-kicker="Your Service"
		:inspector-title="selectedSubscription ? 'Subscription Details' : 'No Subscription Yet'"
		inspector-subtitle="Customer-safe Plan, payment, and Site progress."
	>
		<template #actions>
			<Button variant="subtle" class="!inline-flex !items-center !gap-2 whitespace-nowrap" @click="load"><RefreshCcw class="size-4 shrink-0" /><span>Refresh</span></Button>
		</template>

		<template #main>
			<div class="h-full overflow-y-auto bg-[#f7f9fb] p-4 lg:p-6">
				<Alert v-if="error" theme="red" title="Subscriptions unavailable" :description="error" class="mb-4" />

				<div v-if="loading" class="rounded-lg border border-[#EDEDED] bg-white p-6 text-sm text-[#64748B]">Loading subscriptions...</div>

				<section v-else-if="!hasSubscriptions" class="mx-auto grid min-h-[560px] max-w-4xl place-items-center rounded-xl border border-[#EDEDED] bg-white p-8 text-center">
					<div class="max-w-lg">
						<div class="mx-auto grid size-14 place-items-center rounded-xl bg-[#dce1ff] text-[#1D4ED8]"><CreditCard class="size-7" /></div>
						<h2 class="mt-5 text-2xl font-semibold text-[#191c1e]">No Subscription Yet</h2>
						<p class="mt-3 text-sm leading-6 text-[#64748B]">Choose a Plan to start your LensCloud service. The Free Plan has ₹0 due today and no payment method requirement.</p>
						<RouterLink to="/customer/plans" class="mt-6 inline-flex min-h-10 items-center justify-center gap-2 whitespace-nowrap rounded-lg bg-[#1D4ED8] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#0037b0]"><span>Choose a Plan</span><ArrowRight class="size-4 shrink-0" /></RouterLink>
					</div>
				</section>

				<section v-else class="mx-auto max-w-6xl">
					<div class="mb-5 flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
						<div>
							<p class="text-xs font-semibold text-[#64748B]">Your Service</p>
							<h2 class="mt-2 text-2xl font-semibold text-[#191c1e]">My Subscriptions</h2>
							<p class="mt-2 text-sm leading-6 text-[#64748B]">Small, clear cards for each service subscription. No infrastructure details here.</p>
						</div>
						<RouterLink to="/customer/plans" class="inline-flex min-h-10 items-center justify-center gap-2 whitespace-nowrap rounded-lg bg-[#f2f4f6] px-4 py-2 text-sm font-semibold text-[#434655] transition hover:bg-[#e8ecf1]"><span>Add New Subscription</span><ArrowRight class="size-4 shrink-0" /></RouterLink>
					</div>

					<div class="grid gap-4 lg:grid-cols-3">
						<article
							v-for="subscription in subscriptions"
							:key="subscription.name"
							class="cursor-pointer rounded-xl border bg-white p-5 transition hover:-translate-y-0.5 hover:shadow-sm"
							:class="selectedSubscription?.name === subscription.name ? 'border-[#1D4ED8] ring-2 ring-[#dce1ff]' : 'border-[#EDEDED]'"
							@click="selectedName = subscription.name"
						>
							<div class="flex items-start justify-between gap-3">
								<div>
									<p class="text-lg font-semibold text-[#191c1e]">{{ subscription.plan_title || plans.find((plan) => plan.name === subscription.plan)?.title || subscription.plan || 'Subscription' }}</p>
									<p class="mt-1 text-xs text-[#64748B]">{{ subscription.name }}</p>
								</div>
								<Badge :class="statusClass(subscription.status)">{{ subscription.status || 'Active' }}</Badge>
							</div>
							<div class="mt-5 space-y-3 text-sm text-[#434655]">
								<div class="flex items-center gap-2"><Globe2 class="size-4 text-[#64748B]" />Region: {{ subscription.region || 'Pending' }}</div>
								<div class="flex items-center gap-2"><Package class="size-4 text-[#64748B]" />Landscape: {{ subscription.landscape_summary?.landscape || 'Standard' }}</div>
								<div class="flex items-center gap-2"><CheckCircle2 class="size-4 text-emerald-600" />{{ subscription.landscape_summary?.environments?.length || 0 }} environment{{ Number(subscription.landscape_summary?.environments?.length || 0) === 1 ? '' : 's' }}</div>
							</div>
							<div class="mt-5">
								<a v-if="readySite && selectedSubscription?.name === subscription.name" :href="readySite.access_url" target="_blank" class="inline-flex items-center gap-2 rounded-lg bg-[#1D4ED8] px-4 py-2 text-sm font-semibold text-white hover:bg-[#0037b0]">Open Site <ExternalLink class="size-4" /></a>
								<Button v-else-if="selectedSubscription?.name === subscription.name" :as="RouterLink" :to="selectedProgressSite ? `/customer/plans?site=${encodeURIComponent(selectedProgressSite.site || selectedProgressSite.name)}&subscription=${encodeURIComponent(subscription.name)}` : `/customer/plans?subscription=${encodeURIComponent(subscription.name)}`" variant="subtle" @click.stop>View progress</Button>
								<span v-else class="text-sm font-medium text-[#1D4ED8]">View details</span>
							</div>
						</article>
					</div>
				</section>
			</div>
		</template>

		<template #inspector>
			<div v-if="selectedSubscription" class="space-y-4">
				<div class="rounded-xl border border-[#EDEDED] bg-white p-4">
					<p class="text-xs font-semibold text-[#64748B]">Subscription</p>
					<h3 class="mt-2 text-base font-semibold text-[#191c1e]">{{ selectedSubscription.plan_title || selectedPlan?.title || selectedSubscription.plan || selectedSubscription.name }}</h3>
					<div class="mt-4 space-y-2 text-sm leading-6 text-[#505f76]">
						<p>Status: <span class="font-medium text-[#191c1e]">{{ selectedSubscription.status || 'Active' }}</span></p>
						<p>Region: <span class="font-medium text-[#191c1e]">{{ selectedSubscription.region || 'Pending' }}</span></p>
						<p>Start: <span class="font-medium text-[#191c1e]">{{ formatDate(selectedSubscription.effective_from) }}</span></p>
						<p>End: <span class="font-medium text-[#191c1e]">{{ formatDate(selectedSubscription.effective_to) }}</span></p>
						<p>Frequency: <span class="font-medium text-[#191c1e]">{{ selectedSubscription.plan_frequency || selectedSubscription.payment?.frequency || 'Monthly' }}</span></p>
						<p>Next renewal: <span class="font-medium text-[#191c1e]">{{ formatDate(selectedSubscription.next_renewal_date) }}</span></p>
						<p>Payment: <span class="font-medium text-[#191c1e]">{{ selectedSubscription.payment?.amount_label || 'Pending' }}</span></p>
						<p>{{ selectedSubscription.payment?.payment_note || 'Payment or approval details are managed by LensCloud.' }}</p>
					</div>
				</div>
				<div class="rounded-xl border border-[#EDEDED] bg-[#f7f9fb] p-4">
					<p class="text-sm font-semibold text-[#191c1e]">Landscape Progress</p>
					<p class="mt-1 text-xs leading-5 text-[#64748B]">{{ selectedSubscription.landscape_summary?.landscape || 'Standard landscape' }}</p>
					<div v-if="environmentSequence.length" class="mt-4 space-y-3">
						<div v-for="item in environmentSequence" :key="item.environment" class="flex gap-3 rounded-lg border border-[#EDEDED] bg-white p-3">
							<div class="grid size-8 shrink-0 place-items-center rounded-full" :class="['Ready','Active'].includes(item.site_status) ? 'bg-emerald-50 text-emerald-700' : item.site ? 'bg-blue-50 text-[#1D4ED8]' : 'bg-[#f2f4f6] text-[#64748B]'">
								<CheckCircle2 v-if="['Ready','Active'].includes(item.site_status)" class="size-4" />
								<Clock3 v-else class="size-4" />
							</div>
							<div class="min-w-0 flex-1">
								<p class="text-sm font-medium text-[#191c1e]">{{ item.environment }}</p>
								<p class="mt-1 text-xs text-[#64748B]">{{ item.site_title || 'Site will be created as part of this landscape' }}</p>
								<p class="mt-1 text-xs text-[#64748B]">Status: {{ environmentStatusText(item) }}<span v-if="item.release"> · Version: {{ item.release }}</span></p>
								<a v-if="item.access_url && ['Ready','Active'].includes(item.site_status)" :href="item.access_url" target="_blank" class="mt-2 inline-flex items-center gap-1 text-xs font-semibold text-[#1D4ED8]">Open Site <ExternalLink class="size-3" /></a>
							</div>
						</div>
					</div>
					<p v-else class="mt-2 text-sm leading-6 text-[#64748B]">Landscape setup has not started yet.</p>
				</div>
			</div>
			<div v-else class="rounded-xl border border-[#EDEDED] bg-white p-4 text-sm leading-6 text-[#64748B]">Choose a Plan to create your first service subscription.</div>
		</template>
	</WorkspaceLayout>
</template>
