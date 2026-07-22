<script setup>
import { computed, ref } from 'vue'
import { Sparkles, PanelRightOpen, PanelRightClose, X, Send } from 'lucide-vue-next'
import { Badge, Button } from 'frappe-ui'

const props = defineProps({
	kicker: { type: String, default: '' },
	title: { type: String, required: true },
	subtitle: { type: String, default: '' },
	inspectorKicker: { type: String, default: 'Inspector' },
	inspectorTitle: { type: String, default: 'Context' },
	inspectorSubtitle: { type: String, default: '' },
	assistantLabel: { type: String, default: 'lumi' },
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

const userMessage = ref('')
function handleSendMessage() {
    if (!userMessage.value.trim()) return
    // Handle message dispatch logic here if connected to an API/store
    userMessage.value = ''
}

const inspectorWidth = ref(380) // Default width in px
const minWidth = 280
const maxWidth = 600
const isResizing = ref(false)

function startResize(direction, event) {
    isResizing.value = true
    const startX = event.clientX
    const startWidth = inspectorWidth.value

    const onMouseMove = (e) => {
        const deltaX = e.clientX - startX
        // Dragging left handle: moving left increases width, moving right decreases width
        const newWidth = direction === 'left' ? startWidth - deltaX : startWidth + deltaX
        inspectorWidth.value = Math.min(Math.max(newWidth, minWidth), maxWidth)
    }

    const stopResize = () => {
        isResizing.value = false
        window.removeEventListener('mousemove', onMouseMove)
        window.removeEventListener('mouseup', stopResize)
    }

    window.addEventListener('mousemove', onMouseMove)
    window.addEventListener('mouseup', stopResize)
}
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
						class="pointer-events-auto inline-flex min-w-[220px] items-center justify-center gap-2 rounded-xl bg-primary px-6 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-primary focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
						data-testid="mobile-inspector-trigger"
						@click="mobileInspectorOpen = true"
					>
						<PanelRightOpen class="size-4 shrink-0" />
						<span class="whitespace-nowrap leading-5">{{ mobileInspectorLabel }}</span>
					</button>
				</div>
			</section>

			<!-- <aside class="hidden w-[380px] shrink-0 flex-col border-l border-outline-gray-2 bg-surface-white xl:flex"> -->
			<aside 
                class="relative hidden shrink-0 flex-col border-l border-outline-gray-2 bg-surface-white xl:flex transition-none select-none"
                :style="{ width: `${inspectorWidth}px` }"
            >
                <!-- Left Resize Handle -->
                <div 
                    class="absolute inset-y-0 -left-1 w-1 cursor-col-resize hover:bg-gray-400/50 active:bg-gray-400/50 z-10"
                    @mousedown.prevent="startResize('left', $event)"
                />
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

				<!-- <div v-if="assistantOpen" class="max-h-[42%] shrink-0 overflow-y-auto border-t border-outline-gray-2 bg-surface-gray-1 p-3">
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
				</div> -->
			<!-- Right Resize Handle -->
			<div 
				class="absolute inset-y-0 -right-1 w-1 cursor-col-resize hover:bg-gray-400/50 active:bg-gray-400/50 z-10"
				@mousedown.prevent="startResize('right', $event)"
			/>
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
		<!-- Responsive Lumi Chat Assistant Drawer (Non-blocking) -->
		<Teleport to="body">
                <div v-if="assistantOpen" class="fixed right-0 top-0 z-[400] h-full w-full max-w-md pointer-events-none">
                    <!-- Inside the Lumi Chat Flyout Panel -->
					<aside class="pointer-events-auto flex h-full w-full flex-col bg-white shadow-2xl border-l border-outline-gray-2">
						<!-- Chat Header -->
						<div class="flex h-14 shrink-0 items-center justify-between border-b border-outline-gray-2 bg-violet-50/50 px-4">
							<div class="flex items-center gap-2.5 min-w-0">
								<div class="flex size-8 shrink-0 items-center justify-center rounded-lg bg-primary text-white shadow-sm">
									<Sparkles class="size-4" />
								</div>
								<div class="min-w-0">
									<div class="flex items-center gap-2">
										<h2 class="truncate text-sm font-semibold text-ink-gray-9">{{ assistantLabel }}</h2>
										<Badge v-if="assistantContext.scope" class="bg-blue-100 text-primary border-none text-[10px]">
											{{ assistantContext.scope }}
										</Badge>
									</div>
									<p class="text-xs text-ink-gray-5 mt-1">Active context assistant</p>
								</div>
							</div>
							<button 
								type="button" 
								class="grid size-8 place-items-center rounded-md text-ink-gray-5 hover:bg-violet-100 hover:text-ink-gray-9 transition"
								@click="assistantOpen = false"
							>
								<X class="size-4" />
							</button>
						</div>

						<!-- Main Container: Centered Content & Stream -->
						<div class="flex-1 overflow-y-auto p-4 bg-slate-50/50 flex flex-col justify-center">
							<div class="w-full max-w-lg mx-auto space-y-6">
								
								<!-- Assistant Summary / Header Context -->
								<div class="text-center space-y-2">
									<div class="inline-flex size-10 items-center justify-center rounded-xl bg-blue-100 text-primary shadow-xs">
										<Sparkles class="size-5" />
									</div>
									<h3 class="text-base font-semibold text-ink-gray-9">How can Lumi help you?</h3>
									<p class="text-xs leading-relaxed text-ink-gray-5 max-w-xs mx-auto">
										{{ assistantContext.summary || assistantHint }}
									</p>
								</div>

								<!-- CENTERED INPUT BOX (PostHog Style) -->
								<div class="rounded-2xl border border-outline-gray-2 bg-white p-2.5 shadow-md transition-all">
									<textarea 
										v-model="userMessage"
										rows="2"
										placeholder="Coming Soon..." 
										class="w-full resize-none border-none bg-transparent px-2 text-sm text-ink-gray-9 placeholder-ink-gray-4 focus:outline-none"
										@keydown.enter.prevent="handleSendMessage"
									/>
									<div class="flex items-center justify-between border-t border-outline-gray-1 pt-2 mt-1 px-1">
										<div class="flex items-center gap-1.5">
											<Badge v-for="badge in assistantBadges.slice(0, 2)" :key="badge" class="bg-surface-gray-2 text-ink-gray-7 text-[10px]">
												{{ badge }}
											</Badge>
										</div>
										<Button type="submit" variant="solid" class="!bg-primary hover:!bg-primary text-white shrink-0" @click="handleSendMessage">
											<template #icon>
												<Send class="size-4" />
											</template>
										</Button>
									</div>
								</div>

								<!-- CONTEXT & SUGGESTIONS BELOW INPUT -->
								<div class="space-y-3 pt-2">
									<!-- Detailed Sections -->
									<div v-if="assistantSections.length" class="space-y-1.5">
										<p class="text-[11px] font-medium text-ink-gray-5 uppercase tracking-wider">Context details</p>
										<div class="grid grid-cols-1 gap-1.5">
											<div 
												v-for="section in assistantSections" 
												:key="section.label" 
												class="rounded-xl border border-outline-gray-2 bg-white px-3 py-2 text-xs shadow-xs"
											>
												<p class="font-medium text-ink-gray-5 uppercase tracking-wider text-[10px]">{{ section.label }}</p>
												<p class="mt-0.5 font-normal text-ink-gray-8">{{ section.value }}</p>
											</div>
										</div>
									</div>

									<!-- Gaps Warning Card -->
									<div v-if="assistantGaps.length" class="rounded-xl border border-amber-200 bg-amber-50/80 p-3 text-xs text-amber-900">
										<p class="font-semibold text-amber-800">Gaps identified</p>
										<ul class="mt-1 list-disc pl-4 space-y-0.5">
											<li v-for="gap in assistantGaps" :key="gap">{{ gap }}</li>
										</ul>
									</div>

									<!-- Recommended Next Steps as Quick Action Chips -->
									<div v-if="assistantNextSteps.length" class="space-y-1.5">
										<p class="text-[11px] font-medium text-ink-gray-5 uppercase tracking-wider">Suggested actions</p>
										<div class="flex flex-col gap-1.5">
											<button 
												v-for="step in assistantNextSteps" 
												:key="step"
												type="button"
												class="flex items-center justify-between rounded-xl border border-outline-gray-2 bg-white p-2.5 text-left text-xs text-ink-gray-8 hover:border-violet-300 hover:bg-violet-50/50 transition shadow-xs"
												@click="userMessage = step"
											>
												<span>{{ step }}</span>
												<Sparkles class="size-3.5 text-violet-500 shrink-0" />
											</button>
										</div>
									</div>
								</div>

							</div>
						</div>
					</aside>
                </div>
            </Teleport>
	</div>
</template>
