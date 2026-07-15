<script setup>
import { computed, onMounted, ref } from 'vue'
import { Alert, Badge, Button } from 'frappe-ui'
import { Archive, CheckCircle2, Circle, Clock3, ExternalLink, FlaskConical, LayoutGrid, ListChecks, Lock, PencilLine, RefreshCcw, Sparkles, TestTube2 } from 'lucide-vue-next'
import { callMethod } from '@/lib/api'
import WorkspaceLayout from '@/components/WorkspaceLayout.vue'

const loading = ref(true)
const error = ref('')
const context = ref(null)
const selectedCode = ref('')

// Hydrated from get_marketplace_context on load (Phase 4), then kept in
// sync locally via optimistic updates from toggleOptIn (Phase 3).
const optedIn = ref({})
const togglingCode = ref('')

const capabilities = computed(() => context.value?.capabilities || [])
const hasCapabilities = computed(() => capabilities.value.length > 0)
const selectedCapability = computed(
	() => capabilities.value.find((item) => item.capability_code === selectedCode.value) || capabilities.value[0] || null
)

const STATUS_META = {
	Available: { class: 'bg-emerald-50 text-emerald-700', icon: Sparkles, iconColor: 'text-amber-500' },
	Planning: { class: 'bg-slate-50 text-slate-700', icon: PencilLine, iconColor: 'text-amber-500' },
	Beta: { class: 'bg-purple-50 text-purple-700', icon: TestTube2, iconColor: 'text-amber-500' },
	'Coming Soon': { class: 'bg-amber-50 text-amber-700', icon: Clock3, iconColor: 'text-amber-500' },
	Retired: { class: 'bg-rose-50 text-rose-700', icon: Archive, iconColor: 'text-amber-500' },
}

function statusClass(status) {
	return STATUS_META[status]?.class || 'bg-[#f2f4f6] text-[#64748B]'
}

function statusIcon(status) {
	return STATUS_META[status]?.icon || Circle
}

function statusIconColor(status) {
	return STATUS_META[status]?.iconColor || 'text-[#94A3B8]'
}

function isOptedIn(capability) {
	return Boolean(optedIn.value[capability.capability_code])
}

function isOptedInCode(code) {
	return Boolean(optedIn.value[code])
}

async function toggleOptIn(capability) {
	const code = capability.capability_code
	if (togglingCode.value === code) return // guard against double-clicks mid-request

	const previous = isOptedIn(capability)
	const next = !previous

	// Optimistic update so the toggle feels instant.
	optedIn.value[code] = next
	togglingCode.value = code
	error.value = ''

	try {
		const response = await callMethod('lenscloud.api.capability.toggle_opt_in', {
			capability_code: code,
			opted_in: next,
		})
		const result = response.message || response
		// Reconcile with the authoritative server state in case it differs.
		optedIn.value[code] = Boolean(result.opted_in)
	} catch (err) {
		// Roll back on failure.
		optedIn.value[code] = previous
		error.value = err?.message || `Unable to update opt-in for ${capability.capability_name}.`
	} finally {
		togglingCode.value = ''
	}
}

async function load() {
	loading.value = true
	error.value = ''
	try {
		const response = await callMethod('lenscloud.api.capability.get_marketplace_context')
		context.value = response.message || response
		if (!selectedCode.value && capabilities.value.length) {
			selectedCode.value = capabilities.value[0].capability_code
		}
		// Hydrate opt-in state from the backend rather than assuming none.
		const opted = context.value?.opted_capabilities || []
		optedIn.value = Object.fromEntries(opted.map((code) => [code, true]))
	} catch (err) {
		error.value = err?.message || 'Unable to load marketplace capabilities.'
	} finally {
		loading.value = false
	}
}

onMounted(load)
</script>

<template>
	<WorkspaceLayout
		title="Marketplace"
		subtitle="Explore LensCloud capabilities and opt in to the ones you need."
		inspector-kicker="Capability"
		:inspector-title="selectedCapability ? selectedCapability.capability_name : 'No Capability Selected'"
		inspector-subtitle="Details, category, and access."
	>
		<template #actions>
			<Button variant="subtle" class="!inline-flex !items-center !gap-2 whitespace-nowrap" @click="load">
				<RefreshCcw class="size-4 shrink-0" /><span>Refresh</span>
			</Button>
		</template>

		<template #main>
			<div class="h-full overflow-y-auto bg-[#f7f9fb] p-4 lg:p-6">
				<Alert v-if="error" theme="red" title="Marketplace unavailable" :description="error" class="mb-4" />

				<div v-if="loading" class="rounded-lg border border-[#EDEDED] bg-white p-6 text-sm text-[#64748B]">
					Loading capabilities...
				</div>

				<section v-else-if="!hasCapabilities" class="mx-auto grid min-h-[560px] max-w-4xl place-items-center rounded-xl border border-[#EDEDED] bg-white p-8 text-center">
					<div class="max-w-lg">
						<div class="mx-auto grid size-14 place-items-center rounded-xl bg-[#dce1ff] text-[#1D4ED8]">
							<LayoutGrid class="size-7" />
						</div>
						<h2 class="mt-5 text-2xl font-semibold text-[#191c1e]">No Capabilities Available</h2>
						<p class="mt-3 text-sm leading-6 text-[#64748B]">Check back soon — new capabilities are added regularly.</p>
					</div>
				</section>

				<section v-else class="mx-auto max-w-6xl">
					<div class="mb-5 flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
						<div>
							<p class="text-xs font-semibold text-[#64748B]">LensCloud Platform</p>
							<h2 class="mt-2 text-2xl font-semibold text-[#191c1e]">Marketplace</h2>
							<p class="mt-2 text-sm leading-6 text-[#64748B]">Opt in to the capabilities you want enabled for your account.</p>
						</div>
					</div>

					<div class="grid gap-4 lg:grid-cols-3">
						<article
							v-for="capability in capabilities"
							:key="capability.capability_code"
							class="cursor-pointer rounded-xl border bg-white p-5 transition hover:-translate-y-0.5 hover:shadow-sm"
							:class="selectedCapability?.capability_code === capability.capability_code ? 'border-[#1D4ED8] ring-2 ring-[#dce1ff]' : 'border-[#EDEDED]'"
							@click="selectedCode = capability.capability_code"
						>
							<div class="flex items-start justify-between gap-3">
								<div class="flex items-start gap-3">
									<div class="grid size-10 shrink-0 place-items-center overflow-hidden rounded-lg bg-[#f2f4f6]">
										<img v-if="capability.icon" :src="capability.icon" :alt="capability.capability_name" class="size-full object-cover" />
										<LayoutGrid v-else class="size-5 text-[#94A3B8]" />
									</div>
									<div>
										<p class="flex items-center gap-2 text-lg font-semibold text-[#191c1e]">
											{{ capability.capability_name }}
											<component :is="statusIcon(capability.status)" class="size-4" :class="statusIconColor(capability.status)" />
										</p>
										<p class="mt-1 text-xs text-[#64748B]">{{ capability.category_label || 'Uncategorized' }}</p>
									</div>
								</div>
								<Badge :class="statusClass(capability.status)">{{ capability.status }}</Badge>
							</div>

							<p class="mt-4 text-sm leading-6 text-[#434655]">{{ capability.short_description }}</p>

							<div class="mt-5 flex items-center justify-between">
								<a
									v-if="capability.docs_link"
									:href="capability.docs_link"
									target="_blank"
									class="inline-flex items-center gap-1 text-xs font-semibold text-[#1D4ED8]"
									@click.stop
								>
									Learn more <ExternalLink class="size-3" />
								</a>
								<span v-else class="text-xs text-[#64748B]">&nbsp;</span>

								<button
									type="button"
									class="relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition disabled:opacity-60"
									:class="isOptedIn(capability) ? 'bg-[#1D4ED8]' : 'bg-[#e2e5ea]'"
									:aria-pressed="isOptedIn(capability)"
									:disabled="togglingCode === capability.capability_code"
									@click.stop="toggleOptIn(capability)"
								>
									<span
										class="inline-block size-4 transform rounded-full bg-white transition"
										:class="isOptedIn(capability) ? 'translate-x-6' : 'translate-x-1'"
									/>
								</button>
							</div>
						</article>
					</div>
				</section>
			</div>
		</template>

		<template #inspector>
			<div v-if="selectedCapability" class="space-y-4">
				<div class="rounded-xl border border-[#EDEDED] bg-white p-4">
					<div class="flex items-start gap-3">
						<div class="grid size-12 shrink-0 place-items-center overflow-hidden rounded-lg bg-[#f2f4f6]">
							<img v-if="selectedCapability.icon" :src="selectedCapability.icon" :alt="selectedCapability.capability_name" class="size-full object-cover" />
							<LayoutGrid v-else class="size-6 text-[#94A3B8]" />
						</div>
						<div class="min-w-0 flex-1">
							<div class="flex items-start justify-between gap-2">
								<p class="text-xs font-semibold text-[#64748B]">{{ selectedCapability.category_label || 'Uncategorized' }}</p>
								<Badge :class="statusClass(selectedCapability.status)">{{ selectedCapability.status }}</Badge>
							</div>
							<h3 class="mt-2 flex items-center gap-2 text-base font-semibold text-[#191c1e]">
								{{ selectedCapability.capability_name }}
								<component :is="statusIcon(selectedCapability.status)" class="size-4" :class="statusIconColor(selectedCapability.status)" />
							</h3>
						</div>
					</div>
					<p v-if="selectedCapability.experimental" class="mt-3 inline-flex items-center gap-1 rounded-full bg-purple-50 px-2 py-0.5 text-xs font-semibold text-purple-700">
						<FlaskConical class="size-3.5" /> Experimental
					</p>

					<div class="mt-4 space-y-2 text-sm leading-6 text-[#505f76]">
						<p class="flex items-center gap-2">
							Opted in:
							<span class="inline-flex items-center gap-1 font-medium" :class="isOptedIn(selectedCapability) ? 'text-emerald-700' : 'text-[#191c1e]'">
								<CheckCircle2 v-if="isOptedIn(selectedCapability)" class="size-4" />
								{{ isOptedIn(selectedCapability) ? 'Yes' : 'No' }}
							</span>
						</p>
						<p class="flex items-center gap-2">
							Access:
							<span class="inline-flex items-center gap-1 font-medium text-[#191c1e]">
								<Lock v-if="selectedCapability.request_access_only" class="size-3.5" />
								{{ selectedCapability.request_access_only ? 'Request access required' : selectedCapability.allow_self_service ? 'Self-service opt-in' : 'Not self-service' }}
							</span>
						</p>
					</div>
				</div>

				<div class="rounded-xl border border-[#EDEDED] bg-white p-4">
					<p class="text-sm font-semibold text-[#191c1e]">Pricing</p>
					<div class="mt-3 space-y-2 text-sm leading-6 text-[#505f76]">
						<p>Pricing model: <span class="font-medium text-[#191c1e]">{{ selectedCapability.pricing_model_label || 'Not specified' }}</span></p>
						<p>Price: <span class="font-medium text-[#191c1e]">{{ selectedCapability.monthly_price || '0' }}</span></p>
						<p>Billing frequency: <span class="font-medium text-[#191c1e]">{{ selectedCapability.billing_frequency || 'Not specified' }}</span></p>
					</div>
				</div>

				<div v-if="selectedCapability.prerequisites?.length" class="rounded-xl border border-[#EDEDED] bg-white p-4">
					<p class="flex items-center gap-2 text-sm font-semibold text-[#191c1e]"><ListChecks class="size-4" /> Prerequisites</p>
					<div class="mt-3 space-y-2">
						<div v-for="prereq in selectedCapability.prerequisites" :key="prereq.capability_code" class="flex items-center justify-between gap-2 rounded-lg border border-[#EDEDED] bg-[#f7f9fb] px-3 py-2 text-sm">
							<span class="text-[#434655]">{{ prereq.capability_name }}</span>
							<span class="inline-flex items-center gap-1 text-xs font-medium" :class="isOptedInCode(prereq.capability_code) ? 'text-emerald-700' : 'text-[#94A3B8]'">
								<CheckCircle2 v-if="isOptedInCode(prereq.capability_code)" class="size-3.5" />
								{{ isOptedInCode(prereq.capability_code) ? 'Opted in' : 'Not opted in' }}
							</span>
						</div>
					</div>
				</div>

				<div v-if="selectedCapability.long_description" class="rounded-xl border border-[#EDEDED] bg-[#f7f9fb] p-4">
					<p class="text-sm font-semibold text-[#191c1e]">About this capability</p>
					<div class="mt-2 text-sm leading-6 text-[#64748B]" v-html="selectedCapability.long_description" />
				</div>

				<a
					v-if="selectedCapability.docs_link"
					:href="selectedCapability.docs_link"
					target="_blank"
					class="flex items-center justify-center gap-2 rounded-lg bg-[#f2f4f6] px-4 py-2 text-sm font-semibold text-[#434655] transition hover:bg-[#e8ecf1]"
				>
					Learn more <ExternalLink class="size-4" />
				</a>
			</div>
			<div v-else class="rounded-xl border border-[#EDEDED] bg-white p-4 text-sm leading-6 text-[#64748B]">
				Select a capability to see its details.
			</div>
		</template>
	</WorkspaceLayout>
</template>