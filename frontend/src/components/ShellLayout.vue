<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { customerNav, platformNav } from '@/lib/catalog'
import { callMethod } from '@/lib/api'
import { useSessionStore } from '@/lib/session'
import { Badge, Button } from 'frappe-ui'
import { ChevronDown, ChevronRight, Circle, Menu, PanelLeftClose } from 'lucide-vue-next'

const route = useRoute()
const session = useSessionStore()
const mobileNavOpen = ref(false)
const remotePlatformNav = ref([])
const closedGroups = ref(new Set())
const currentScope = computed(() => route.meta.scope || 'platform')
const staticGroups = computed(() => currentScope.value === 'customer' ? customerNav : platformNav)
const iconByRoute = computed(() => new Map(platformNav.flatMap((group) => group.items).map((item) => [item.route, item.icon])))
const navGroups = computed(() => {
	if (currentScope.value !== 'platform' || !remotePlatformNav.value.length) return staticGroups.value
	return remotePlatformNav.value.map((group) => ({ ...group, items: group.items.map((item) => ({ ...item, icon: iconByRoute.value.get(item.route) || Circle })) }))
})
const primaryNavGroups = computed(() => navGroups.value.filter((group) => group.placement !== 'bottom'))
const bottomNavGroups = computed(() => navGroups.value.filter((group) => group.placement === 'bottom'))
const scopeLabel = computed(() => currentScope.value === 'customer' ? 'Customer portal' : 'Platform console')

function groupActive(group) { return group.items.some((item) => route.path === item.route || route.path.startsWith(`${item.route}/`)) }
function groupOpen(group) { return !group.collapsible || groupActive(group) || !closedGroups.value.has(group.heading) }
function toggleGroup(group) { const next = new Set(closedGroups.value); next.has(group.heading) ? next.delete(group.heading) : next.add(group.heading); closedGroups.value = next }
function initializeClosed() { closedGroups.value = new Set(navGroups.value.filter((group) => group.collapsible && group.keep_closed && !groupActive(group)).map((group) => group.heading)) }
async function loadNavigation() {
	if (currentScope.value !== 'platform') { remotePlatformNav.value = []; initializeClosed(); return }
	try { const response = await callMethod('lenscloud.api.launch.get_navigation', { scope: 'platform' }); remotePlatformNav.value = response.message || response || [] }
	catch { remotePlatformNav.value = [] }
	initializeClosed()
}
function closeMobileNav() { mobileNavOpen.value = false }
onMounted(loadNavigation)
watch(currentScope, loadNavigation)
</script>

<template>
	<div class="flex h-screen overflow-hidden bg-surface-white text-ink-gray-9">
		<aside class="hidden w-60 shrink-0 flex-col border-r border-outline-gray-2 bg-surface-menu-bar lg:flex">
			<div class="flex h-14 items-center gap-2 border-b border-outline-gray-2 px-3">
				<div class="grid size-7 place-items-center rounded bg-ink-gray-9 text-xs font-semibold text-white">LC</div>
				<div class="min-w-0"><div class="truncate text-sm font-semibold text-ink-gray-9">LensCloud</div><div class="text-xs text-ink-gray-5">{{ scopeLabel }}</div></div>
			</div>
			<div class="min-h-0 flex-1 overflow-y-auto px-2 py-2">
				<nav v-for="group in primaryNavGroups" :key="group.heading" class="mb-1">
					<button type="button" class="flex w-full items-center justify-between rounded px-2 py-1.5 text-left text-xs font-medium text-ink-gray-5 hover:bg-surface-gray-1" @click="group.collapsible && toggleGroup(group)">
						<span>{{ group.heading }}</span><component v-if="group.collapsible" :is="groupOpen(group) ? ChevronDown : ChevronRight" class="size-3.5" />
					</button>
					<div v-show="groupOpen(group)" class="mt-0.5 space-y-0.5">
						<RouterLink v-for="item in group.items" :key="item.key" :to="item.route" class="flex items-center gap-2 rounded px-2 py-1.5 text-sm text-ink-gray-7 hover:bg-surface-gray-1" :class="{ 'bg-surface-gray-2 font-medium text-ink-gray-9': route.path === item.route || route.path.startsWith(`${item.route}/`) }" @click="closeMobileNav">
							<component :is="item.icon || Circle" class="size-4 shrink-0 text-ink-gray-4" /><span class="truncate">{{ item.label }}</span>
						</RouterLink>
					</div>
				</nav>
			</div>
			<div class="border-t border-outline-gray-2 px-2 py-2">
				<nav v-for="group in bottomNavGroups" :key="group.heading" class="mb-1">
					<RouterLink v-for="item in group.items" :key="item.key" :to="item.route" class="flex items-center gap-2 rounded px-2 py-1.5 text-sm text-ink-gray-7 hover:bg-surface-gray-1" :class="{ 'bg-surface-gray-2 font-medium text-ink-gray-9': route.path === item.route || route.path.startsWith(`${item.route}/`) }" @click="closeMobileNav">
						<component :is="item.icon || Circle" class="size-4 shrink-0 text-ink-gray-4" /><span class="truncate">{{ item.label }}</span>
					</RouterLink>
				</nav>
				<div class="mt-2 flex items-center justify-between gap-2 px-1"><span class="truncate text-xs text-ink-gray-5">{{ session.user }}</span><Badge class="bg-surface-gray-2 text-ink-gray-6">{{ currentScope }}</Badge></div>
			</div>
		</aside>

		<div class="flex min-w-0 flex-1 flex-col overflow-hidden">
			<header class="flex h-11 shrink-0 items-center justify-between border-b border-outline-gray-2 px-3 lg:hidden"><button type="button" aria-label="Toggle navigation" class="grid size-8 place-items-center rounded hover:bg-surface-gray-1" @click="mobileNavOpen = !mobileNavOpen"><component :is="mobileNavOpen ? PanelLeftClose : Menu" class="size-4" /></button><span class="text-sm font-medium">LensCloud</span></header>
			<div v-if="mobileNavOpen" data-testid="mobile-navigation" class="max-h-[70vh] overflow-y-auto border-b border-outline-gray-2 bg-surface-menu-bar p-2 lg:hidden">
				<div v-for="group in primaryNavGroups" :key="group.heading" class="mb-2"><p class="px-2 py-1 text-xs font-medium text-ink-gray-5">{{ group.heading }}</p><RouterLink v-for="item in group.items" :key="item.key" :to="item.route" class="flex items-center gap-2 rounded px-2 py-2 text-sm hover:bg-surface-gray-1" @click="closeMobileNav"><component :is="item.icon || Circle" class="size-4 text-ink-gray-4" />{{ item.label }}</RouterLink></div>
				<div v-for="group in bottomNavGroups" :key="group.heading" class="mt-3 border-t border-outline-gray-2 pt-2"><p class="px-2 py-1 text-xs font-medium text-ink-gray-5">{{ group.heading }}</p><RouterLink v-for="item in group.items" :key="item.key" :to="item.route" class="flex items-center gap-2 rounded px-2 py-2 text-sm hover:bg-surface-gray-1" @click="closeMobileNav"><component :is="item.icon || Circle" class="size-4 text-ink-gray-4" />{{ item.label }}</RouterLink></div>
			</div>
			<main class="min-w-0 flex-1 overflow-hidden"><RouterView /></main>
		</div>
	</div>
</template>
