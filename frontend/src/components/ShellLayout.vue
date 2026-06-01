<script setup>
import { computed, ref } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { customerNav, platformNav } from '@/lib/catalog'
import { useSessionStore } from '@/lib/session'
import { Button, Badge } from 'frappe-ui'
import { Menu, PanelLeftClose } from 'lucide-vue-next'

const route = useRoute()
const session = useSessionStore()
const mobileNavOpen = ref(false)

const currentScope = computed(() => route.meta.scope || 'platform')
const navGroups = computed(() => (currentScope.value === 'customer' ? customerNav : platformNav))
const scopeLabel = computed(() => (currentScope.value === 'customer' ? 'Customer portal' : 'Platform console'))

function closeMobileNav() {
	mobileNavOpen.value = false
}
</script>

<template>
	<div class="flex h-screen overflow-hidden bg-surface-white text-ink-gray-9">
		<aside class="hidden w-64 shrink-0 flex-col border-r border-outline-gray-2 bg-surface-menu-bar lg:flex">
			<div class="h-14 border-b border-outline-gray-2 px-4 py-3">
				<div class="flex items-center gap-3">
					<div class="grid size-8 place-items-center rounded bg-ink-gray-9 text-xs font-semibold text-white">
						LC
					</div>
					<div class="min-w-0">
						<div class="truncate text-sm font-semibold text-slate-900">LensCloud Platform</div>
						<div class="text-xs text-slate-500">Frappe UI control plane</div>
					</div>
				</div>
			</div>

			<div class="min-h-0 flex-1 space-y-4 overflow-y-auto px-2 py-3">
				<div class="space-y-2 px-2">
					<div class="text-[11px] font-medium uppercase tracking-[0.18em] text-slate-500">Current scope</div>
					<div class="flex flex-wrap gap-2">
						<Badge :class="currentScope === 'platform' ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-600'">Platform</Badge>
						<Badge :class="currentScope === 'customer' ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-600'">Customer</Badge>
					</div>
				</div>

				<nav v-for="group in navGroups" :key="group.heading" class="space-y-2">
					<div class="px-2 text-[11px] font-medium uppercase tracking-[0.18em] text-slate-500">{{ group.heading }}</div>
					<div class="space-y-1">
						<RouterLink
							v-for="item in group.items"
							:key="item.key"
							:to="item.route"
							class="group flex items-start gap-3 rounded px-2.5 py-2 transition hover:border-slate-200 hover:bg-slate-50"
							:class="{
								'border-slate-200 bg-slate-50 text-slate-950': route.path === item.route || route.path.startsWith(`${item.route}/`),
							}"
							@click="closeMobileNav"
						>
							<component :is="item.icon" class="mt-0.5 size-4 shrink-0 text-slate-400 transition group-hover:text-slate-700" />
							<div class="min-w-0">
								<div class="truncate text-sm font-medium text-slate-900">{{ item.label }}</div>
								<div class="mt-0.5 text-xs leading-5 text-slate-500">{{ item.note }}</div>
							</div>
						</RouterLink>
					</div>
				</nav>
			</div>

			<div class="border-t border-outline-gray-2 px-4 py-3">
				<div class="text-[11px] font-medium uppercase tracking-[0.18em] text-slate-500">Session</div>
				<div class="mt-3 flex flex-wrap gap-2">
					<Badge class="bg-slate-100 text-slate-600">{{ session.status === 'loading' ? 'Loading' : scopeLabel }}</Badge>
					<Badge v-if="session.isPlatformUser" class="bg-emerald-50 text-emerald-700">Platform role</Badge>
					<Badge v-else-if="session.isCustomerUser" class="bg-blue-50 text-blue-700">Customer role</Badge>
					<Badge v-else class="bg-slate-100 text-slate-600">Authenticated</Badge>
				</div>
				<p class="mt-3 text-xs leading-5 text-slate-500">Native Frappe auth remains the source of truth for access and permissions.</p>
			</div>
		</aside>

		<div class="flex min-w-0 flex-1 flex-col overflow-hidden">
			<header class="flex h-10.5 shrink-0 items-center justify-between border-b border-outline-gray-2 bg-surface-white px-4 lg:hidden">
				<Button variant="ghost" @click="mobileNavOpen = !mobileNavOpen">
					<component :is="mobileNavOpen ? PanelLeftClose : Menu" class="size-4" />
				</Button>
				<Badge class="bg-slate-100 text-slate-600">{{ scopeLabel }}</Badge>
			</header>

			<div v-if="mobileNavOpen" class="border-b border-slate-200 bg-white px-4 py-4 lg:hidden">
				<div class="space-y-4">
					<div v-for="group in navGroups" :key="group.heading" class="space-y-2">
						<div class="text-[11px] font-medium uppercase tracking-[0.18em] text-slate-500">{{ group.heading }}</div>
						<div class="space-y-1">
							<RouterLink
								v-for="item in group.items"
								:key="item.key"
								:to="item.route"
								class="flex items-start gap-3 rounded px-2.5 py-2 transition hover:border-slate-200 hover:bg-slate-50"
								:class="{
									'border-slate-200 bg-slate-50': route.path === item.route || route.path.startsWith(`${item.route}/`),
								}"
								@click="closeMobileNav"
							>
								<component :is="item.icon" class="mt-0.5 size-4 shrink-0 text-slate-400" />
								<div>
									<div class="text-sm font-medium text-slate-900">{{ item.label }}</div>
									<div class="text-xs leading-5 text-slate-500">{{ item.note }}</div>
								</div>
							</RouterLink>
						</div>
					</div>
				</div>
			</div>

			<main class="min-w-0 flex-1 overflow-hidden">
				<RouterView />
			</main>
		</div>
	</div>
</template>
