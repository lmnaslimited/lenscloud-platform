<script setup>
import { computed, ref } from 'vue'
import { Sparkles, PanelRightOpen, PanelRightClose } from 'lucide-vue-next'
import { Button } from 'frappe-ui'

const props = defineProps({
	kicker: { type: String, default: '' },
	title: { type: String, required: true },
	subtitle: { type: String, default: '' },
	inspectorKicker: { type: String, default: 'Inspector' },
	inspectorTitle: { type: String, default: 'Context' },
	inspectorSubtitle: { type: String, default: '' },
	assistantLabel: { type: String, default: 'Assistant' },
	assistantHint: { type: String, default: 'Reserved for contextual AI guidance tied to the current workspace.' },
})

const assistantOpen = ref(false)
const assistantIcon = computed(() => (assistantOpen.value ? PanelRightClose : PanelRightOpen))
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
					<p v-if="subtitle" class="mt-0.5 truncate text-sm text-ink-gray-5">{{ subtitle }}</p>
				</div>
			</div>
			<div class="flex shrink-0 items-center gap-2">
				<slot name="actions" />
			</div>
		</header>

		<div class="flex min-h-0 flex-1 overflow-hidden">
			<section class="min-w-0 flex-1 overflow-hidden bg-surface-white">
				<slot name="main" />
			</section>

			<aside class="hidden w-[380px] shrink-0 flex-col border-l border-outline-gray-2 bg-surface-white xl:flex">
				<div class="flex h-14 shrink-0 items-center justify-between gap-3 border-b border-outline-gray-2 px-4">
					<div class="min-w-0">
						<p class="text-xs font-medium text-ink-gray-5">{{ inspectorKicker }}</p>
						<h2 class="truncate text-base font-semibold text-ink-gray-9">{{ inspectorTitle }}</h2>
					</div>
					<Button variant="ghost" :tooltip="assistantOpen ? 'Hide assistant' : assistantLabel" @click="assistantOpen = !assistantOpen">
						<component :is="assistantIcon" class="size-4" />
					</Button>
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

				<div v-if="assistantOpen" class="shrink-0 border-t border-outline-gray-2 bg-surface-gray-1 p-3">
					<div class="flex items-center gap-2 text-sm font-medium text-ink-gray-8">
						<Sparkles class="size-4 text-ink-gray-5" />
						{{ assistantLabel }}
					</div>
					<p class="mt-1 text-sm leading-5 text-ink-gray-5">{{ assistantHint }}</p>
				</div>
			</aside>
		</div>
	</div>
</template>
