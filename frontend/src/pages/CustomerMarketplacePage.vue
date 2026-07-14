<script setup>
import { computed, onMounted, ref } from 'vue'
import { Alert, Badge, Button } from 'frappe-ui'
import { CheckCircle2, ExternalLink, LayoutGrid, RefreshCcw, Sparkles } from 'lucide-vue-next'
import { callMethod } from '@/lib/api'
import WorkspaceLayout from '@/components/WorkspaceLayout.vue'

const loading = ref(true)
const error = ref('')
const context = ref(null)
const selectedCode = ref('')

// Local-only opt-in state for Phase 2 (visual only).
// Phase 3 replaces this with real persistence via toggle_opt_in,
// and Phase 4 hydrates it from the backend on load.
const optedIn = ref({})

const capabilities = computed(() => context.value?.capabilities || [])
const hasCapabilities = computed(() => capabilities.value.length > 0)
const selectedCapability = computed(
	() => capabilities.value.find((item) => item.capability_code === selectedCode.value) || capabilities.value[0] || null
)

function statusClass(status) {
	if (status === 'Active') return 'bg-emerald-50 text-emerald-700'
	if (status === 'Coming Soon') return 'bg-amber-50 text-amber-700'
	return 'bg-[#f2f4f6] text-[#64748B]'
}

function isOptedIn(capability) {
	return Boolean(optedIn.value[capability.capability_code])
}

function toggleOptIn(capability) {
	// Phase 2: local UI toggle only.
	// Phase 3 will call:
	//   await callMethod('lenscloud.api.capability.toggle_opt_in', {
	//     capability_code: capability.capability_code,
	//     opted_in: !isOptedIn(capability),
	//   })
	optedIn.value[capability.capability_code] = !isOptedIn(capability)
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
								<div>
									<p class="flex items-center gap-2 text-lg font-semibold text-[#191c1e]">
										{{ capability.capability_name }}
										<Sparkles v-if="capability.is_featured" class="size-4 text-amber-500" />
									</p>
									<p class="mt-1 text-xs text-[#64748B]">{{ capability.category || 'Uncategorized' }}</p>
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
									class="relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition"
									:class="isOptedIn(capability) ? 'bg-[#1D4ED8]' : 'bg-[#e2e5ea]'"
									:aria-pressed="isOptedIn(capability)"
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
					<p class="text-xs font-semibold text-[#64748B]">{{ selectedCapability.category || 'Uncategorized' }}</p>
					<h3 class="mt-2 text-base font-semibold text-[#191c1e]">{{ selectedCapability.capability_name }}</h3>
					<div class="mt-4 space-y-2 text-sm leading-6 text-[#505f76]">
						<p>Status: <span class="font-medium text-[#191c1e]">{{ selectedCapability.status }}</span></p>
						<p>Pricing: <span class="font-medium text-[#191c1e]">{{ selectedCapability.pricing_model || 'Not specified' }}</span></p>
						<p class="flex items-center gap-2">
							Opted in:
							<span class="inline-flex items-center gap-1 font-medium" :class="isOptedIn(selectedCapability) ? 'text-emerald-700' : 'text-[#191c1e]'">
								<CheckCircle2 v-if="isOptedIn(selectedCapability)" class="size-4" />
								{{ isOptedIn(selectedCapability) ? 'Yes' : 'No' }}
							</span>
						</p>
					</div>
				</div>
				<div v-if="selectedCapability.long_description" class="rounded-xl border border-[#EDEDED] bg-[#f7f9fb] p-4">
					<p class="text-sm font-semibold text-[#191c1e]">About this capability</p>
					<div class="mt-2 text-sm leading-6 text-[#64748B]" v-html="selectedCapability.long_description" />
				</div>
			</div>
			<div v-else class="rounded-xl border border-[#EDEDED] bg-white p-4 text-sm leading-6 text-[#64748B]">
				Select a capability to see its details.
			</div>
		</template>
	</WorkspaceLayout>
</template>