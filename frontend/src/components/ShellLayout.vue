<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { customerNav, platformNav } from '@/lib/catalog'
import { callMethod } from '@/lib/api'
import { useSessionStore } from '@/lib/session'
import { Alert, Badge, Button } from 'frappe-ui'
import { ChevronDown, ChevronRight, Circle, KeyRound, LogOut, Menu, PanelLeftClose, UserRound } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const session = useSessionStore()
const mobileNavOpen = ref(false)
const remotePlatformNav = ref([])
const closedGroups = ref(new Set())
const currentScope = computed(() => route.meta.scope || 'platform')
const staticGroups = computed(() => currentScope.value === 'customer' ? customerNav : platformNav)
const iconByRoute = computed(() => new Map(platformNav.flatMap((group) => group.items).map((item) => [item.route, item.icon])))
const navGroups = computed(() => {
	const groups = currentScope.value === 'platform' && remotePlatformNav.value.length
		? remotePlatformNav.value.map((group) => ({ ...group, items: group.items.map((item) => ({ ...item, icon: iconByRoute.value.get(item.route) || Circle })) }))
		: staticGroups.value
	if (currentScope.value !== 'customer') return groups
	return groups.map((group) => ({
		...group,
		items: group.items.filter((item) => !item.doctype || customerAccess.value?.doctype_permissions?.[item.doctype]?.read),
	})).filter((group) => group.items.length || group.placement === 'bottom')
})
const primaryNavGroups = computed(() => navGroups.value.filter((group) => group.placement !== 'bottom'))
const bottomNavGroups = computed(() => navGroups.value.filter((group) => group.placement === 'bottom'))
const bottomNavVisibleGroups = computed(() => bottomNavGroups.value.map((group) => ({ ...group, items: group.items.filter((item) => item.key !== 'customer-account') })).filter((group) => group.items.length))
const accountMenuOpen = ref(false)
const customerAccess = ref(null)
const passwordDialogOpen = ref(false)
const passwordState = ref('idle')
const passwordError = ref('')
const passwordSuccess = ref('')
const passwordForm = reactive({ old_password: '', new_password: '', confirm_password: '' })
const scopeLabel = computed(() => currentScope.value === 'customer' ? 'Customer portal' : 'Platform console')
const userProfile = reactive({ first_name: '', last_name: '', full_name: '' })

const accountName = computed(() => {
	// const raw = session.user
	// const local = raw.includes('@') ? raw.split('@')[0] : raw
	// const name = local.replace(/[._-]+/g, ' ').trim()
	// return name ? name.replace(/\b\w/g, (char) => char.toUpperCase()) : raw
	const firstName = userProfile.first_name || ''
	const lastName = userProfile.last_name || ''

	const fullName = [firstName, lastName].filter(Boolean).join(' ')
	if (fullName.trim()) return fullName.trim()
})
// const accountInitials = computed(() => accountName.value.split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]).join('').toUpperCase())
const accountInitials = computed(() => {
  const name = accountName.value || ''
  
  // Guard against undefined/null name before calling .split()
  if (!name) return ''

  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (!parts.length) return ''

  // Works for single name ("Falila" -> "F") and multi-word names ("Falila Khan" -> "FK")
  return parts.slice(0, 2).map((part) => part[0]).join('').toUpperCase()
})
const accountCaption = computed(() => {
	if (currentScope.value !== 'customer') return 'Platform Console'
	return customerAccess.value?.recent_plan || customerAccess.value?.membership?.member_role || 'Customer Portal'
})

function groupActive(group) { return group.items.some((item) => route.path === item.route || route.path.startsWith(`${item.route}/`)) }
function groupOpen(group) { return !group.collapsible || groupActive(group) || !closedGroups.value.has(group.heading) }
function toggleGroup(group) { const next = new Set(closedGroups.value); next.has(group.heading) ? next.delete(group.heading) : next.add(group.heading); closedGroups.value = next }
function initializeClosed() { closedGroups.value = new Set(navGroups.value.filter((group) => group.collapsible && group.keep_closed && !groupActive(group)).map((group) => group.heading)) }
async function loadNavigation() {
	if (currentScope.value !== 'platform') {
		remotePlatformNav.value = []
		try { const response = await callMethod('lenscloud.api.customer_identity.get_customer_access_context'); customerAccess.value = response.message || response || null }
		catch { customerAccess.value = null }
		initializeClosed()
		return
	}
	customerAccess.value = null
	try { const response = await callMethod('lenscloud.api.launch.get_navigation', { scope: 'platform' }); remotePlatformNav.value = response.message || response || [] }
	catch { remotePlatformNav.value = [] }
	initializeClosed()
}
async function loadUserProfile() {
  if (!session.user || session.user === 'Guest') return
  try {
    const res = await callMethod('frappe.client.get_value', {
      doctype: 'User',
      filters: { name: session.user },
      fieldname: ['first_name', 'last_name', 'full_name']
    })
    const data = res.message || res
    if (data) {
      userProfile.first_name = data.first_name || ''
	  userProfile.last_name = data.last_name || ''
	  userProfile.full_name = data.full_name || ''
    }
  } catch (err) {
    console.error('Failed to load user profile:', err)
  }
}
function closeMobileNav() { mobileNavOpen.value = false }

function accountRoute() { return currentScope.value === 'customer' ? '/customer/account' : '/platform/dashboard' }
async function signOut() {
	try { await callMethod('logout', {}, 'POST') }
	finally { session.reset(); window.location.href = '/login' }
}
function resetPasswordForm() {
	passwordForm.old_password = ''
	passwordForm.new_password = ''
	passwordForm.confirm_password = ''
	passwordError.value = ''
	passwordSuccess.value = ''
	passwordState.value = 'idle'
}
function openPasswordDialog() {
	accountMenuOpen.value = false
	mobileNavOpen.value = false
	if (currentScope.value === 'customer') {
		router.push({ path: '/customer/account', query: { changePassword: '1' } })
		return
	}
	resetPasswordForm()
	passwordDialogOpen.value = true
}
async function submitPasswordChange() {
	passwordError.value = ''
	passwordSuccess.value = ''
	if (!passwordForm.old_password || !passwordForm.new_password || !passwordForm.confirm_password) { passwordError.value = 'Enter your current password, new password, and confirmation.'; return }
	if (passwordForm.new_password !== passwordForm.confirm_password) { passwordError.value = 'New password and confirmation do not match.'; return }
	passwordState.value = 'saving'
	try {
		await callMethod('frappe.core.doctype.user.user.update_password', { old_password: passwordForm.old_password, new_password: passwordForm.new_password, logout_all_sessions: 0 }, 'POST')
		passwordSuccess.value = 'Password updated. Your current session remains active.'
		passwordForm.old_password = ''; passwordForm.new_password = ''; passwordForm.confirm_password = ''
		passwordState.value = 'saved'
	} catch (err) {
		passwordState.value = 'error'
		passwordError.value = err?.message || 'Unable to update password. Check your current password and try again.'
	}
}
onMounted(() => {
  loadNavigation()
  loadUserProfile()
})
watch(currentScope, loadNavigation)
watch(() => route.fullPath, () => {
	accountMenuOpen.value = false
	if (currentScope.value === 'customer') loadNavigation()
})
</script>

<template>
	<div class="flex h-screen overflow-hidden bg-surface-white text-ink-gray-9">
		<aside class="hidden w-64 shrink-0 flex-col border-r border-outline-gray-2 bg-surface-menu-bar lg:flex">
			<div class="flex h-14 items-center gap-2 border-b border-outline-gray-2 px-3">
				<!-- <div class="grid size-7 place-items-center rounded bg-ink-gray-9 text-xs font-semibold text-white">LC</div> -->
				<img
				src="/lenscloud.png"
				alt="LensCloud"
				class="h-10 w-10 shrink-0"
				/>
				<div class="min-w-0"><div class="truncate text-sm font-semibold text-ink-gray-9">LensCloud</div><div class="text-xs text-ink-gray-5 mt-2">{{ scopeLabel }}</div></div>
			</div>
			<div class="min-h-0 flex-1 overflow-y-auto px-2 py-2">
				<nav v-for="group in primaryNavGroups" :key="group.heading" class="mb-1">
					<button type="button" class="flex w-full items-center justify-between rounded px-2 py-1.5 text-left text-xs font-medium text-ink-gray-5 hover:bg-surface-gray-1" @click="group.collapsible && toggleGroup(group)">
						<span>{{ group.heading }}</span>
						<component v-if="group.collapsible" :is="groupOpen(group) ? ChevronDown : ChevronRight" class="size-3.5" />
					</button>
					<div v-show="groupOpen(group)" class="mt-2 space-y-1">
						<RouterLink v-for="item in group.items" :key="item.key" :to="item.route" class="flex items-center gap-2 rounded px-3 py-3 text-sm text-ink-gray-7" :class="{ 'bg-surface-gray-3 font-medium text-ink-gray-9': route.path === item.route || route.path.startsWith(`${item.route}/`) }" @click="closeMobileNav">
							<component :is="item.icon || Circle" class="size-4 shrink-0 text-primary" /><span class="truncate">{{ item.label }}</span>
						</RouterLink>
					</div>
				</nav>
			</div>
			<div class="relative border-t border-outline-gray-2 px-2 py-2">
				<nav v-for="group in bottomNavVisibleGroups" :key="group.heading" class="mb-1">
					<RouterLink v-for="item in group.items" :key="item.key" :to="item.route" class="flex items-center gap-2 rounded px-2 py-1.5 text-sm text-ink-gray-7 hover:bg-surface-gray-1" :class="{ 'bg-surface-gray-2 font-medium text-ink-gray-9': route.path === item.route || route.path.startsWith(`${item.route}/`) }" @click="closeMobileNav">
						<component :is="item.icon || Circle" class="size-4 shrink-0 text-ink-gray-4" /><span class="truncate">{{ item.label }}</span>
					</RouterLink>
				</nav>
				<div v-if="accountMenuOpen" data-testid="account-menu" class="absolute inset-x-2 bottom-full z-40 mb-2 overflow-hidden rounded-2xl border border-outline-gray-2 bg-white p-2 shadow-xl">
					<div class="flex items-center gap-3 border-b border-outline-gray-2 px-3 py-3">
						<div class="grid size-9 shrink-0 place-items-center rounded-full bg-primary text-sm font-semibold text-white">{{ accountInitials }}</div>
						<div class="min-w-0"><p class="truncate text-sm font-semibold text-ink-gray-9">{{ accountName }}</p><p class="truncate text-xs text-ink-gray-5">{{ session.user }}</p></div>
					</div>
					<RouterLink :to="accountRoute()" class="mt-2 flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-ink-gray-8 hover:bg-surface-gray-1" @click="accountMenuOpen = false"><UserRound class="size-4 shrink-0" /><span>Profile</span></RouterLink>
					<button type="button" class="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm font-medium text-ink-gray-8 hover:bg-surface-gray-1" @click="openPasswordDialog"><KeyRound class="size-4 shrink-0" /><span>Change Password</span></button>
					<button type="button" class="mt-2 flex w-full items-center gap-3 border-t border-outline-gray-2 px-3 py-3 text-left text-sm font-medium text-ink-gray-8 hover:bg-surface-gray-1" @click="signOut"><LogOut class="size-4 shrink-0" /><span>Sign Out</span></button>
				</div>
				<button type="button" data-testid="account-menu-trigger" class="mt-1 flex w-full items-center gap-3 rounded-xl bg-surface-gray-1 px-3 py-2.5 text-left transition hover:bg-surface-gray-2" @click="accountMenuOpen = !accountMenuOpen">
					<div class="grid size-9 shrink-0 place-items-center rounded-full bg-primary text-sm font-semibold text-white">{{ accountInitials }}</div>
					<div class="min-w-0 flex-1"><p class="truncate text-sm font-semibold text-ink-gray-9">{{ accountName }}</p><p class="truncate text-xs text-ink-gray-5">{{ accountCaption }}</p></div>
					<ChevronRight class="size-4 shrink-0 text-ink-gray-5" />
				</button>
			</div>
		</aside>

		<div class="flex min-w-0 flex-1 flex-col overflow-hidden">
			<header class="flex h-11 shrink-0 items-center justify-between border-b border-outline-gray-2 px-3 lg:hidden">
				<button type="button" aria-label="Toggle navigation" class="grid size-8 place-items-center rounded hover:bg-surface-gray-1" @click="mobileNavOpen = !mobileNavOpen">
					<component :is="mobileNavOpen ? PanelLeftClose : Menu" class="size-4" />
				</button>
				<span class="flex items-center gap-2 text-sm font-medium">
					<img
						src="/lenscloud.png"
						alt="LensCloud"
						class="h-7 w-7 shrink-0 object-contain"
					/>
					<span>LensCloud</span>
				</span>
			</header>
			<div v-if="mobileNavOpen" data-testid="mobile-navigation" class="max-h-[70vh] overflow-y-auto border-b border-outline-gray-2 bg-surface-menu-bar p-2 lg:hidden">
				<div v-for="group in primaryNavGroups" :key="group.heading" class="mb-2"><p class="px-2 py-1 text-xs font-medium text-ink-gray-5">{{ group.heading }}</p><RouterLink v-for="item in group.items" :key="item.key" :to="item.route" class="flex items-center gap-2 rounded px-2 py-2 text-sm hover:bg-surface-gray-1" @click="closeMobileNav"><component :is="item.icon || Circle" class="size-4 text-ink-gray-4" />{{ item.label }}</RouterLink></div>
				<div v-for="group in bottomNavVisibleGroups" :key="group.heading" class="mt-3 border-t border-outline-gray-2 pt-2"><p class="px-2 py-1 text-xs font-medium text-ink-gray-5">{{ group.heading }}</p><RouterLink v-for="item in group.items" :key="item.key" :to="item.route" class="flex items-center gap-2 rounded px-2 py-2 text-sm hover:bg-surface-gray-1" @click="closeMobileNav"><component :is="item.icon || Circle" class="size-4 text-ink-gray-4" />{{ item.label }}</RouterLink></div>
				<div class="mt-3 border-t border-outline-gray-2 pt-3">
					<button type="button" data-testid="mobile-account-menu-trigger" class="flex w-full items-center gap-3 rounded-xl bg-surface-gray-1 px-3 py-3 text-left" @click="accountMenuOpen = !accountMenuOpen">
						<div class="grid size-9 shrink-0 place-items-center rounded-full bg-primary text-sm font-semibold text-white">{{ accountInitials }}</div>
						<div class="min-w-0 flex-1"><p class="truncate text-sm font-semibold text-ink-gray-9">{{ accountName }}</p><p class="truncate text-xs text-ink-gray-5">{{ accountCaption }}</p></div>
						<ChevronRight class="size-4 shrink-0 text-ink-gray-5" />
					</button>
					<div v-if="accountMenuOpen" data-testid="mobile-account-menu" class="mt-2 rounded-xl border border-outline-gray-2 bg-white p-2">
						<RouterLink :to="accountRoute()" class="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium hover:bg-surface-gray-1" @click="closeMobileNav"><UserRound class="size-4" />Profile</RouterLink>
						<button type="button" class="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-sm font-medium hover:bg-surface-gray-1" @click="openPasswordDialog"><KeyRound class="size-4" />Change Password</button>
						<button type="button" class="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-sm font-medium hover:bg-surface-gray-1" @click="signOut"><LogOut class="size-4" />Sign Out</button>
					</div>
				</div>
			</div>
			<main class="min-w-0 flex-1 overflow-hidden"><RouterView /></main>
		</div>
		<div v-if="passwordDialogOpen" class="fixed inset-0 z-[1000] grid place-items-center bg-black/30 px-4 py-6" role="presentation" @mousedown.self="passwordDialogOpen = false">
			<section role="dialog" aria-modal="true" aria-labelledby="platform-password-title" class="w-full max-w-md rounded-2xl border border-outline-gray-2 bg-white shadow-2xl">
				<form class="space-y-4 p-5" @submit.prevent="submitPasswordChange">
					<div><h2 id="platform-password-title" class="text-base font-semibold text-ink-gray-9">Change Password</h2><p class="mt-2 text-sm leading-6 text-ink-gray-6">Update your Platform sign-in password without leaving the console.</p></div>
					<Alert v-if="passwordError" theme="red" title="Password not updated" :description="passwordError" />
					<Alert v-if="passwordSuccess" theme="green" title="Password updated" :description="passwordSuccess" />
					<label class="block space-y-1.5"><span class="text-xs font-semibold text-ink-gray-5">Current Password</span><input v-model="passwordForm.old_password" type="password" autocomplete="current-password" aria-label="Current Password" class="block h-9 w-full rounded-md border border-outline-gray-2 bg-white px-3 text-sm outline-none focus:border-[#1D4ED8] focus:ring-2 focus:ring-[#dce1ff]" /></label>
					<label class="block space-y-1.5"><span class="text-xs font-semibold text-ink-gray-5">New Password</span><input v-model="passwordForm.new_password" type="password" autocomplete="new-password" aria-label="New Password" class="block h-9 w-full rounded-md border border-outline-gray-2 bg-white px-3 text-sm outline-none focus:border-[#1D4ED8] focus:ring-2 focus:ring-[#dce1ff]" /></label>
					<label class="block space-y-1.5"><span class="text-xs font-semibold text-ink-gray-5">Confirm New Password</span><input v-model="passwordForm.confirm_password" type="password" autocomplete="new-password" aria-label="Confirm New Password" class="block h-9 w-full rounded-md border border-outline-gray-2 bg-white px-3 text-sm outline-none focus:border-[#1D4ED8] focus:ring-2 focus:ring-[#dce1ff]" /></label>
					<div class="flex flex-col-reverse gap-2 pt-2 sm:flex-row sm:justify-end"><Button variant="subtle" @click="passwordDialogOpen = false">Cancel</Button><Button type="submit" variant="solid" :disabled="passwordState === 'saving'">{{ passwordState === 'saving' ? 'Updating...' : 'Update Password' }}</Button></div>
				</form>
			</section>
		</div>
	</div>
</template>
