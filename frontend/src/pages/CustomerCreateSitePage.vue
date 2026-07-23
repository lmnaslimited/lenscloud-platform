<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { Alert, Badge, Button, TextInput, Textarea } from 'frappe-ui'
import { Check, ChevronRight, Globe2, MapPin, Package, Send, Settings2 } from 'lucide-vue-next'
import { callMethod } from '@/lib/api'
import WorkspaceLayout from '@/components/WorkspaceLayout.vue'

const loading = ref(true)
const submitted = ref(false)
const enrollment = ref(null)
const error = ref(null)
const customer = ref(null)
const regions = ref([])
const platformSettings = ref(null)
const selectedPlan = ref('')

const form = reactive({
	site_name: '',
	company_name: '',
	subdomain: '',
	region: '',
	notes: '',
})

const plans = ref([])

const selectedRegion = computed(() => regions.value.find((region) => region.name === form.region) || null)
const selectedPlanRecord = computed(() => plans.value.find((plan) => plan.name === selectedPlan.value) || null)
const rootDomain = computed(() => platformSettings.value?.root_domain || '')
const normalizedSubdomain = computed(() => form.subdomain.trim().toLowerCase().replace(/[^a-z0-9-]/g, '-').replace(/^-+|-+$/g, ''))
const domainPreview = computed(() => (normalizedSubdomain.value && rootDomain.value ? `${normalizedSubdomain.value}.${rootDomain.value}` : ''))
const rootDomainMissing = computed(() => !rootDomain.value)
const canSubmit = computed(() => form.site_name.trim() && form.company_name.trim() && form.region && selectedPlanRecord.value?.is_free && normalizedSubdomain.value && rootDomain.value)
const betaPlans = computed(() => plans.value.filter((plan) => plan.availability === 'Beta'))


const assistantContext = computed(() => {
	const gaps = []
	if (rootDomainMissing.value) gaps.push('Platform Settings root_domain is missing')
	if (!customer.value) gaps.push('Signed-in user has no linked Customer record')

	return {
		scope: 'customer',
		summary: submitted.value
			? 'Site was created in LensCloud and setup has started. Progress depends on available Free Plan capacity and Platform readiness.'
			: 'Guidance for creating a site with a preferred subdomain under the platform root domain.',
		badges: ['Create Site', rootDomainMissing.value ? 'root domain gap' : 'domain ready', submitted.value ? 'captured' : 'draft'],
		sections: [
			{ label: 'Domain preview', value: domainPreview.value || 'Root domain and subdomain are required' },
			{ label: 'Selected plan', value: selectedPlanRecord.value?.title || 'No plan selected' },
			{ label: 'Selected region', value: selectedRegion.value?.title || selectedRegion.value?.name || 'No region selected' },
			{ label: 'Submission state', value: canSubmit.value ? 'Ready to start Free Plan setup' : 'Waiting for required fields or root domain' },
		],
		gaps,
		nextSteps: submitted.value
			? ['View Dashboard or Sites to track customer-safe setup progress.', 'If setup is delayed, contact support instead of retrying repeatedly.']
			: ['Confirm the Free Plan, Site name, preferred subdomain, and Region.', 'Submit when the review is complete.', 'Use beta enrollment separately for multi-environment Plans.'],
	}
})

async function load() {
	loading.value = true
	error.value = null
	try {
		const response = await callMethod('lenscloud.api.orchestration.get_customer_portal_context')
		const context = response.message || response.data || response
		customer.value = context.customer || null
		platformSettings.value = context.settings || null
		regions.value = context.regions || []
		plans.value = context.plans || []

		if (!selectedPlan.value) {
			selectedPlan.value = plans.value.find((plan) => plan.is_default)?.name || plans.value.find((plan) => plan.is_free)?.name || plans.value[0]?.name || ''
		}

		if (!form.region) {
			const customerRegion = regions.value.find((region) => region.name === customer.value?.region)?.name
			form.region = customerRegion || regions.value[0]?.name || ''
		}
		posthog.capture('create_site_viewed', {
    plan: selectedPlan.value,
})
	} catch (err) {
		error.value = err?.message || 'Unable to load create site context.'
	} finally {
		loading.value = false
	}
}

async function submitRequest() {
	if (!canSubmit.value) return
	error.value = null
	try {
		posthog.capture('site_request_started', {
			plan: selectedPlan.value,
			region: form.region,
		})
		const response = await callMethod('lenscloud.api.orchestration.request_customer_subscription', {
			site_name: form.site_name,
			company_name: form.company_name,
			subdomain: normalizedSubdomain.value,
			region: form.region,
			plan: selectedPlan.value,
			notes: form.notes,
		}, 'POST')
		const result = response.message || response.data || response
		submitted.value = result
		posthog.capture('site_request_submitted', {
			plan: selectedPlan.value,
			region: form.region,
			hostname: result.hostname,
		})
	} catch (err) {
		error.value = err?.message || 'Unable to submit site request.'
	}
}

async function requestBeta(plan) {
	error.value = null
	try {
		const response = await callMethod('lenscloud.api.launch.request_beta_enrollment', { plan: plan.name, region: form.region }, 'POST')
		enrollment.value = response.message || response
	} catch (err) { error.value = err?.message || 'Unable to request beta enrollment.' }
}

onMounted(load)
</script>

<template>
	<WorkspaceLayout
		title="Free Plan setup"
		subtitle="Compatibility setup path. For the normal launch journey, browse Plans first."
		inspector-kicker="Request context"
		inspector-title="Site activation"
		inspector-subtitle="The Free Plan uses one production Site in your Region. LensCloud manages capacity and isolation."
		assistant-label="Assistant"
		assistant-hint="The assistant will help customers choose regions, plans, DNS settings, and next steps."
		:assistant-context="assistantContext"
	>
		<template #actions>
			<Badge class="bg-emerald-50 text-emerald-700">Free plan path</Badge>
			<Button variant="subtle" @click="load">Refresh</Button>
		</template>

		<template #main>
			<div class="h-full overflow-y-auto p-4">
				<Alert v-if="error" theme="red" title="Create site gap" :description="error" />

				<div v-if="loading" class="rounded border border-outline-gray-2 bg-surface-white p-5 text-sm text-ink-gray-5">
					Loading site request context...
				</div>

				<div v-else-if="submitted" class="rounded border border-outline-gray-2 bg-surface-white p-5">
					<div class="flex items-start gap-4">
						<div class="grid size-10 shrink-0 place-items-center rounded bg-emerald-50 text-emerald-700">
							<Check class="size-5" />
						</div>
						<div class="min-w-0 flex-1">
							<p class="text-base font-semibold text-ink-gray-9">Site request captured</p>
							<p class="mt-1 text-sm leading-6 text-ink-gray-5">{{ submitted.hostname || domainPreview || form.site_name }} was created as a LensCloud Site and setup has started.</p>
							<div class="mt-4 grid gap-2 sm:grid-cols-2">
								<div class="rounded border border-outline-gray-2 bg-surface-gray-1 p-3">
									<p class="text-xs text-ink-gray-5">Company</p>
									<p class="mt-1 text-sm font-medium text-ink-gray-9">{{ form.company_name }}</p>
								</div>
								<div class="rounded border border-outline-gray-2 bg-surface-gray-1 p-3">
									<p class="text-xs text-ink-gray-5">Region</p>
									<p class="mt-1 text-sm font-medium text-ink-gray-9">{{ selectedRegion?.title || selectedRegion?.name }}</p>
								</div>
								<div class="rounded border border-outline-gray-2 bg-surface-gray-1 p-3">
									<p class="text-xs text-ink-gray-5">Domain</p>
									<p class="mt-1 text-sm font-medium text-ink-gray-9">{{ submitted.hostname || domainPreview || 'Pending root domain' }}</p>
								</div>
							</div>
							<div class="mt-4 flex flex-wrap gap-2">
								<Button :as="RouterLink" to="/customer/dashboard"
								@click="posthog.capture('dashboard_opened_after_request')"
								>View dashboard</Button>
								<Button :as="RouterLink" to="/customer/sites" variant="subtle"
								@click="posthog.capture('sites_opened_after_request')"
								>View sites</Button>
								<Button variant="subtle" @click="submitted = false">Edit request</Button>
							</div>
						</div>
					</div>
				</div>

				<div v-else class="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
					<section class="rounded border border-outline-gray-2 bg-surface-white p-4">
						<div class="flex items-center gap-2">
							<Globe2 class="size-4 text-ink-gray-5" />
							<h2 class="text-base font-semibold text-ink-gray-9">Site basics</h2>
						</div>
						<div class="mt-4 grid gap-3 sm:grid-cols-2">
							<label class="space-y-1.5">
								<span class="text-xs font-medium text-ink-gray-5">Site name</span>
								<TextInput v-model="form.site_name" variant="subtle" placeholder="acme-production" />
							</label>
							<label class="space-y-1.5">
								<span class="text-xs font-medium text-ink-gray-5">Company or project</span>
								<TextInput v-model="form.company_name" variant="subtle" placeholder="Acme Incorporated" />
							</label>
							<label class="space-y-1.5 sm:col-span-2">
								<span class="text-xs font-medium text-ink-gray-5">Preferred subdomain</span>
								<TextInput v-model="form.subdomain" variant="subtle" placeholder="acme" />
							</label>
							<div class="sm:col-span-2 rounded border border-outline-gray-2 bg-surface-gray-1 px-3 py-2">
								<div class="flex items-center justify-between gap-3">
									<span class="text-xs font-medium text-ink-gray-5">Domain preview</span>
									<Badge :class="rootDomainMissing ? 'bg-red-50 text-red-700' : 'bg-surface-white text-ink-gray-7'">{{ rootDomainMissing ? 'Root domain missing' : rootDomain }}</Badge>
								</div>
								<p class="mt-1 truncate text-sm font-medium text-ink-gray-9">{{ domainPreview || 'Enter a subdomain after Platform Settings root domain is configured' }}</p>
							</div>
						</div>
					</section>

					<section class="rounded border border-outline-gray-2 bg-surface-white p-4">
						<div class="flex items-center gap-2"><Package class="size-4 text-ink-gray-5" /><h2 class="text-base font-semibold text-ink-gray-9">Your Plan</h2></div>
						<div v-if="selectedPlanRecord" class="mt-4 rounded border border-emerald-200 bg-emerald-50 p-3">
							<div class="flex items-center justify-between gap-3"><p class="text-sm font-semibold text-emerald-900">{{ selectedPlanRecord.title }}</p><Badge class="bg-white text-emerald-700">Single Tier · Public</Badge></div>
							<p class="mt-1 text-sm leading-5 text-emerald-800">{{ selectedPlanRecord.description || 'One production Site on shared LensCloud capacity, selected automatically for your Region.' }}</p>
						</div>
						<div v-if="betaPlans.length" class="mt-4 border-t border-outline-gray-2 pt-3">
							<p class="text-sm font-medium text-ink-gray-8">Explore beta Plans</p><p class="mt-1 text-xs text-ink-gray-5">Multi-environment Plans require capacity approval before provisioning.</p>
							<div class="mt-2 space-y-2"><div v-for="plan in betaPlans" :key="plan.name" class="flex items-center justify-between gap-3 rounded bg-surface-gray-1 px-3 py-2"><div><p class="text-sm font-medium text-ink-gray-8">{{ plan.title }}</p><p class="text-xs text-ink-gray-5">{{ plan.description || plan.landscape }}</p></div><Button size="sm" variant="subtle" :disabled="!form.region || enrollment"
							@click="
								posthog.capture('beta_access_requested', {
									plan: plan.name,
									region: form.region,
								});
								requestBeta(plan);
							"
							>{{ enrollment ? 'Requested' : 'Request access' }}</Button></div></div>
						</div>
					</section>

					<section class="rounded border border-outline-gray-2 bg-surface-white p-4">
						<div class="flex items-center gap-2">
							<MapPin class="size-4 text-ink-gray-5" />
							<h2 class="text-base font-semibold text-ink-gray-9">Region</h2>
						</div>
						<div class="mt-4 grid gap-2 sm:grid-cols-2">
							<button
								v-for="region in regions.filter((item) => !item.is_group).slice(0, 8)"
								:key="region.name"
								class="rounded border px-3 py-2 text-left transition hover:bg-surface-gray-1"
								:class="form.region === region.name ? 'border-ink-gray-8 bg-surface-gray-1' : 'border-outline-gray-2 bg-surface-white'"			
								@click="
									posthog.capture('region_selected', {
										region: region.name,
									});
									form.region = region.name;
								"
							>
								<p class="text-sm font-medium text-ink-gray-9">{{ region.title || region.name }}</p>
								<p class="mt-1 text-xs text-ink-gray-5">{{ region.cluster ? `Cluster: ${region.cluster}` : (region.parent_region || 'Cluster not mapped') }}</p>
							</button>
						</div>
					</section>

					<section class="rounded border border-outline-gray-2 bg-surface-white p-4">
						<h2 class="text-base font-semibold text-ink-gray-9">Review</h2>
						<div class="mt-3 space-y-2 text-sm leading-6 text-ink-gray-6">
							<p>Site: <span class="font-medium text-ink-gray-9">{{ form.site_name || 'Required' }}</span></p>
							<p>Domain: <span class="font-medium text-ink-gray-9">{{ domainPreview || 'Root domain/subdomain required' }}</span></p>
							<p>Company: <span class="font-medium text-ink-gray-9">{{ form.company_name || 'Required' }}</span></p>
							<p>Plan: <span class="font-medium text-ink-gray-9">{{ selectedPlanRecord?.title || 'Required' }}</span></p>
							<p>Region: <span class="font-medium text-ink-gray-9">{{ selectedRegion?.title || selectedRegion?.name || 'Required' }}</span></p>
						</div>
						<label class="mt-3 block space-y-1.5">
							<span class="text-xs font-medium text-ink-gray-5">Notes</span>
							<Textarea v-model="form.notes" variant="subtle" placeholder="Launch timing, DNS notes, migration context" />
						</label>
						<Button class="mt-4 !inline-flex !items-center gap-2" :disabled="!canSubmit" @click="submitRequest">
							<Send class="size-4" />
							<span>Submit site request </span>
						</Button>
					</section>
				</div>
			</div>
		</template>

		<template #inspector>
			<div class="space-y-3">
				<div class="rounded border border-outline-gray-2 bg-surface-gray-1 p-3">
					<p class="text-sm font-medium text-ink-gray-9">Activation path</p>
					<div class="mt-3 space-y-2">
						<div v-for="step in ['Basics', 'Plan', 'Region', 'Review', 'Pending activation']" :key="step" class="flex items-center gap-2 text-sm text-ink-gray-6">
							<ChevronRight class="size-4 text-ink-gray-4" />
							{{ step }}
						</div>
					</div>
				</div>
				<div class="rounded border border-outline-gray-2 bg-surface-white p-3">
					<div class="flex items-center gap-2">
						<Settings2 class="size-4 text-ink-gray-5" />
						<p class="text-sm font-medium text-ink-gray-9">Platform settings</p>
					</div>
					<div class="mt-3 space-y-2 text-sm leading-6 text-ink-gray-6">
						<p>Root domain: {{ rootDomain || 'Not configured' }}</p>
						<p>Billing: {{ platformSettings?.billing_system || 'Not configured' }}</p>
						<p>CRM: {{ platformSettings?.crm_system || 'Not configured' }}</p>
						<p>Support: {{ platformSettings?.support_system || 'Not configured' }}</p>
					</div>
				</div>
				<Alert theme="blue" title="Plan-first launch" description="This compatibility path uses the same Free Plan subscription API as the Plans page. Customers choose Plan, Region, and subdomain; LensCloud manages setup and access." />
			</div>
		</template>
	</WorkspaceLayout>
</template>
