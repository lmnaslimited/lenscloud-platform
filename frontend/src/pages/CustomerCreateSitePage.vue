<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { Alert, Badge, Button, TextInput, Textarea } from 'frappe-ui'
import { Check, ChevronRight, Globe2, MapPin, Package, Send } from 'lucide-vue-next'
import { listDocs } from '@/lib/api'
import { useSessionStore } from '@/lib/session'
import WorkspaceLayout from '@/components/WorkspaceLayout.vue'

const session = useSessionStore()
const loading = ref(true)
const submitted = ref(false)
const error = ref(null)
const customer = ref(null)
const regions = ref([])
const selectedPlan = ref('starter')

const form = reactive({
	site_name: '',
	company_name: '',
	domain: '',
	region: '',
	notes: '',
})

const plans = [
	{ key: 'starter', label: 'Starter', note: 'Best for first production sites' },
	{ key: 'business', label: 'Business', note: 'For higher traffic and support needs' },
	{ key: 'custom', label: 'Custom', note: 'Platform team will confirm sizing' },
]

const selectedRegion = computed(() => regions.value.find((region) => region.name === form.region) || null)
const canSubmit = computed(() => form.site_name.trim() && form.company_name.trim() && form.region)

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

		regions.value = await listDocs('Region', {
			fields: ['name', 'title', 'parent_region', 'is_group', 'lft', 'rgt'],
			limit: 200,
			orderBy: 'lft asc',
		})

		if (!form.region) {
			form.region = customer.value?.region || regions.value.find((region) => !region.is_group)?.name || regions.value[0]?.name || ''
		}
	} catch (err) {
		error.value = err?.message || 'Unable to load create site context.'
	} finally {
		loading.value = false
	}
}

function submitRequest() {
	if (!canSubmit.value) return
	submitted.value = true
}

onMounted(load)
</script>

<template>
	<WorkspaceLayout
		title="Create Site"
		subtitle="Start a new LensCloud site request from a guided customer flow."
		inspector-kicker="Request context"
		inspector-title="Site activation"
		inspector-subtitle="The UI captures intent now. Backend provisioning and subscription wiring remain explicit gaps until connected."
		assistant-label="Assistant"
		assistant-hint="The assistant will help customers choose regions, plans, DNS settings, and next steps."
	>
		<template #actions>
			<Badge class="bg-amber-50 text-amber-700">Backend gap</Badge>
			<Button variant="subtle" @click="load">Refresh</Button>
		</template>

		<template #main>
			<div class="h-full overflow-y-auto p-4">
				<Alert v-if="error" theme="red" title="Create site gap" :message="error" />

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
							<p class="mt-1 text-sm leading-6 text-ink-gray-5">{{ form.site_name }} is ready to become a provisioning request once backend orchestration is connected.</p>
							<div class="mt-4 grid gap-2 sm:grid-cols-2">
								<div class="rounded border border-outline-gray-2 bg-surface-gray-1 p-3">
									<p class="text-xs text-ink-gray-5">Company</p>
									<p class="mt-1 text-sm font-medium text-ink-gray-9">{{ form.company_name }}</p>
								</div>
								<div class="rounded border border-outline-gray-2 bg-surface-gray-1 p-3">
									<p class="text-xs text-ink-gray-5">Region</p>
									<p class="mt-1 text-sm font-medium text-ink-gray-9">{{ selectedRegion?.title || selectedRegion?.name || form.region }}</p>
								</div>
							</div>
							<div class="mt-4 flex flex-wrap gap-2">
								<Button :as="RouterLink" to="/customer/sites">View sites</Button>
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
								<span class="text-xs font-medium text-ink-gray-5">Preferred domain</span>
								<TextInput v-model="form.domain" variant="subtle" placeholder="app.example.com" />
							</label>
						</div>
					</section>

					<section class="rounded border border-outline-gray-2 bg-surface-white p-4">
						<div class="flex items-center gap-2">
							<Package class="size-4 text-ink-gray-5" />
							<h2 class="text-base font-semibold text-ink-gray-9">Product plan</h2>
						</div>
						<div class="mt-4 grid gap-2">
							<button
								v-for="plan in plans"
								:key="plan.key"
								class="rounded border px-3 py-2 text-left transition hover:bg-surface-gray-1"
								:class="selectedPlan === plan.key ? 'border-ink-gray-8 bg-surface-gray-1' : 'border-outline-gray-2 bg-surface-white'"
								@click="selectedPlan = plan.key"
							>
								<div class="flex items-center justify-between gap-3">
									<p class="text-sm font-medium text-ink-gray-9">{{ plan.label }}</p>
									<Badge v-if="selectedPlan === plan.key" class="bg-ink-gray-8 text-white">Selected</Badge>
								</div>
								<p class="mt-1 text-xs leading-5 text-ink-gray-5">{{ plan.note }}</p>
							</button>
						</div>
						<Alert class="mt-3" theme="yellow" title="Subscription gap" message="Billing and subscription APIs are not wired in this frontend pass." />
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
								@click="form.region = region.name"
							>
								<p class="text-sm font-medium text-ink-gray-9">{{ region.title || region.name }}</p>
								<p class="mt-1 text-xs text-ink-gray-5">{{ region.parent_region || 'Primary region' }}</p>
							</button>
						</div>
					</section>

					<section class="rounded border border-outline-gray-2 bg-surface-white p-4">
						<h2 class="text-base font-semibold text-ink-gray-9">Review</h2>
						<div class="mt-3 space-y-2 text-sm leading-6 text-ink-gray-6">
							<p>Site: <span class="font-medium text-ink-gray-9">{{ form.site_name || 'Required' }}</span></p>
							<p>Company: <span class="font-medium text-ink-gray-9">{{ form.company_name || 'Required' }}</span></p>
							<p>Plan: <span class="font-medium text-ink-gray-9">{{ plans.find((plan) => plan.key === selectedPlan)?.label }}</span></p>
							<p>Region: <span class="font-medium text-ink-gray-9">{{ selectedRegion?.title || selectedRegion?.name || 'Required' }}</span></p>
						</div>
						<label class="mt-3 block space-y-1.5">
							<span class="text-xs font-medium text-ink-gray-5">Notes</span>
							<Textarea v-model="form.notes" variant="subtle" placeholder="Launch timing, DNS notes, migration context" />
						</label>
						<Button class="mt-4" :disabled="!canSubmit" @click="submitRequest">
							<Send class="size-4" />
							Submit site request
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
				<Alert theme="yellow" title="UI-only request" message="This pass does not create backend business logic. Submission is represented as a pending activation request until backend support is connected." />
			</div>
		</template>
	</WorkspaceLayout>
</template>
