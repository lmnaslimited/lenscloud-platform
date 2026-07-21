<script setup>
import { computed, ref } from 'vue'
import { Sparkles, PanelRightOpen, PanelRightClose, X } from 'lucide-vue-next'
import { Badge, Button } from 'frappe-ui'

const props = defineProps({
	kicker: { type: String, default: '' },
	title: { type: String, required: true },
	subtitle: { type: String, default: '' },
	inspectorKicker: { type: String, default: 'Inspector' },
	inspectorTitle: { type: String, default: 'Context' },
	inspectorSubtitle: { type: String, default: '' },
	assistantLabel: { type: String, default: 'Assistant' },
	assistantHint: { type: String, default: 'Reserved for contextual AI guidance tied to the current workspace.' },
	assistantContext: { type: Object, default: () => ({}) },
	mobileInspectorLabel: { type: String, default: 'Details' },
})

const mobileInspectorOpen = ref(false)
const assistantOpen = ref(false)
const assistantIcon = computed(() => (assistantOpen.value ? PanelRightClose : PanelRightOpen))
const assistantSections = computed(() => props.assistantContext?.sections || [])
const assistantBadges = computed(() => props.assistantContext?.badges || [])
const assistantNextSteps = computed(() => props.assistantContext?.nextSteps || [])
const assistantGaps = computed(() => props.assistantContext?.gaps || [])
</script>

<template>
	<div class="flex h-full min-h-0 flex-col bg-surface-white">
		<header class="flex h-14 shrink-0 items-center justify-between gap-3 border-b border-outline-gray-2 px-5">
			<div class="flex min-w-0 items-center gap-3">
				<div class="min-w-0">
					<div class="flex items-center gap-2">
						<p v-if="kicker" class="shrink-0 text-xs font-medium text-ink-gray-5">{{ kicker }}</p>
						<span v-if="kicker" class="text-ink-gray-3">/</span>
						<h1 class="truncate text-lg font-semibold text-ink-gray-9">{{ title }}</h1>
					</div>
					<p v-if="subtitle" class="mt-2 truncate text-sm text-ink-gray-5">{{ subtitle }}</p>
				</div>
			</div>
			<div class="flex shrink-0 items-center gap-2">
				<slot name="actions" />
				<Button variant="subtle" :tooltip="assistantOpen ? 'Hide assistant' : assistantLabel" @click="assistantOpen = !assistantOpen"
				class="bg-violet-50 text-violet-700 hover:bg-violet-100 border border-violet-200">
					<span class="flex items-center gap-2">
						<!-- <component :is="assistantIcon" class="size-4" /> -->
						 <Sparkles class="size-4" />
						<span>lumi</span>
					</span>
					</Button>
			</div>
		</header>

		<div class="flex min-h-0 flex-1 overflow-hidden">
			<section class="relative min-w-0 flex-1 overflow-hidden bg-surface-white">
				<slot name="main" />
				<div class="pointer-events-none absolute inset-x-0 bottom-0 z-20 flex justify-center bg-gradient-to-t from-white via-white/85 to-transparent px-4 pb-4 pt-8 xl:hidden">
					<button
						type="button"
						class="pointer-events-auto inline-flex min-w-[220px] items-center justify-center gap-2 rounded-xl bg-[#1D4ED8] px-6 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-[#0037b0] focus:outline-none focus:ring-2 focus:ring-[#b7c4ff] focus:ring-offset-2"
						data-testid="mobile-inspector-trigger"
						@click="mobileInspectorOpen = true"
					>
						<PanelRightOpen class="size-4 shrink-0" />
						<span class="whitespace-nowrap leading-5">{{ mobileInspectorLabel }}</span>
					</button>
				</div>
			</section>

			<aside class="hidden w-[380px] shrink-0 flex-col border-l border-outline-gray-2 bg-surface-white xl:flex">
				<div class="flex h-14 shrink-0 items-center justify-between gap-3 border-b border-outline-gray-2 px-4">
					<div class="min-w-0">
						<p class="text-xs font-medium text-ink-gray-5">{{ inspectorKicker }}</p>
						<h2 class="truncate text-base font-semibold text-ink-gray-9 mt-2">{{ inspectorTitle }}</h2>
					</div>
					<!-- <Button variant="ghost" :tooltip="assistantOpen ? 'Hide assistant' : assistantLabel" @click="assistantOpen = !assistantOpen">
						<component :is="assistantIcon" class="size-4" />
					</Button> -->
				</div>

				<div class="min-h-0 flex-1 overflow-y-auto px-3 py-3">
					<p v-if="inspectorSubtitle" class="mb-3 text-sm leading-5 text-ink-gray-5">{{ inspectorSubtitle }}</p>
					<slot name="inspector">
						<div class="rounded border border-dashed border-outline-gray-2 bg-surface-gray-1 p-3">
							<p class="text-sm font-medium text-ink-gray-8">No record selected</p>
							<p class="mt-1 text-sm leading-5 text-ink-gray-5">Choose a record to inspect fields, status, and actions.</p>
						</div>
					</slot>
				</div>

				<div v-if="assistantOpen" class="max-h-[42%] shrink-0 overflow-y-auto border-t border-outline-gray-2 bg-surface-gray-1 p-3">
					<div class="flex items-start justify-between gap-3">
						<div class="min-w-0">
							<div class="flex items-center gap-2 text-sm font-medium text-ink-gray-8">
								<Sparkles class="size-4 text-ink-gray-5" />
								{{ assistantLabel }}
							</div>
							<p class="mt-1 text-sm leading-5 text-ink-gray-5">{{ assistantContext.summary || assistantHint }}</p>
						</div>
						<Badge v-if="assistantContext.scope" class="shrink-0 bg-surface-white text-ink-gray-7">{{ assistantContext.scope }}</Badge>
					</div>

					<div v-if="assistantBadges.length" class="mt-3 flex flex-wrap gap-2">
						<Badge v-for="badge in assistantBadges" :key="badge" class="bg-surface-white text-ink-gray-7">{{ badge }}</Badge>
					</div>

					<div v-if="assistantSections.length" class="mt-3 space-y-2">
						<div v-for="section in assistantSections" :key="section.label" class="rounded border border-outline-gray-2 bg-surface-white px-3 py-2">
							<p class="text-xs font-medium text-ink-gray-5">{{ section.label }}</p>
							<p class="mt-1 text-sm leading-5 text-ink-gray-8">{{ section.value }}</p>
						</div>
					</div>

					<div v-if="assistantGaps.length" class="mt-3 rounded border border-amber-200 bg-amber-50 px-3 py-2">
						<p class="text-xs font-medium text-amber-800">Gaps</p>
						<ul class="mt-1 space-y-1 text-sm leading-5 text-amber-800">
							<li v-for="gap in assistantGaps" :key="gap">{{ gap }}</li>
						</ul>
					</div>

					<div v-if="assistantNextSteps.length" class="mt-3 rounded border border-outline-gray-2 bg-surface-white px-3 py-2">
						<p class="text-xs font-medium text-ink-gray-5">Next steps</p>
						<ul class="mt-1 space-y-1 text-sm leading-5 text-ink-gray-7">
							<li v-for="step in assistantNextSteps" :key="step">{{ step }}</li>
						</ul>
					</div>
				</div>
			</aside>

			<Teleport to="body">
				<div v-if="mobileInspectorOpen" class="fixed inset-0 z-[300] xl:hidden" data-testid="mobile-inspector-drawer">
					<button type="button" class="absolute inset-0 bg-[#191c1e]/40" aria-label="Dismiss details backdrop" @click="mobileInspectorOpen = false" />
					<aside class="absolute inset-x-0 bottom-0 flex max-h-[86vh] flex-col rounded-t-2xl border border-[#EDEDED] bg-white shadow-2xl">
						<div class="mx-auto mt-2 h-1 w-10 rounded-full bg-[#c4c5d7]" aria-hidden="true" />
						<div class="flex shrink-0 items-center justify-between gap-3 border-b border-[#EDEDED] px-4 py-3">
							<div class="min-w-0">
								<p class="text-xs font-semibold text-[#64748B]">{{ inspectorKicker }}</p>
								<h2 class="truncate text-base font-semibold text-[#191c1e]">{{ inspectorTitle }}</h2>
							</div>
							<button type="button" aria-label="Close details" data-testid="mobile-inspector-close" class="grid size-8 place-items-center rounded-md text-[#64748B] hover:bg-[#f2f4f6] hover:text-[#191c1e]" @click="mobileInspectorOpen = false">
								<X class="size-4" />
							</button>
						</div>
						<div class="min-h-0 flex-1 overflow-y-auto px-4 py-4">
							<p v-if="inspectorSubtitle" class="mb-3 text-sm leading-5 text-[#64748B]">{{ inspectorSubtitle }}</p>
							<slot name="inspector">
								<div class="rounded border border-dashed border-[#EDEDED] bg-[#f7f9fb] p-3">
									<p class="text-sm font-medium text-[#191c1e]">No record selected</p>
									<p class="mt-1 text-sm leading-5 text-[#64748B]">Choose a record to inspect fields, status, and actions.</p>
								</div>
							</slot>
						</div>
					</aside>
				</div>
			</Teleport>
		</div>
	</div>
</template>
