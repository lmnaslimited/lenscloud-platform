<script setup>
import { computed, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { Menu, PanelLeftClose } from 'lucide-vue-next'
import { customerNav, platformNav } from '@/lib/catalog'
import { useSessionStore } from '@/lib/session'
import { Button } from 'frappe-ui'

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
	<div class="app-frame">
		<aside class="sidebar">
			<div class="brand-mark">
				<div class="brand-badge">LC</div>
				<div class="brand-copy">
					<h1>LensCloud Platform</h1>
					<p>Frappe UI control plane</p>
				</div>
			</div>

			<div>
				<div class="nav-heading">Current scope</div>
				<div class="role-stack">
					<span class="role-chip platform">Platform</span>
					<span class="role-chip customer">Customer</span>
				</div>
			</div>

			<nav class="nav-group">
				<div v-for="group in navGroups" :key="group.heading">
					<div class="nav-heading">{{ group.heading }}</div>
					<RouterLink
						v-for="item in group.items"
						:key="item.key"
						:to="item.route"
						class="nav-link"
						:class="{ active: route.path === item.route || route.path.startsWith(`${item.route}/`) }"
						@click="closeMobileNav"
					>
						<component :is="item.icon" class="nav-icon" />
						<div class="nav-copy">
							<div class="nav-label">{{ item.label }}</div>
							<div class="nav-note">{{ item.note }}</div>
						</div>
					</RouterLink>
				</div>
			</nav>

			<div class="sidebar-footer">
				<div class="nav-heading">Session</div>
				<div class="note-row">
					<span class="chip">{{ session.status === 'loading' ? 'Loading session' : scopeLabel }}</span>
					<span class="chip" v-if="session.isPlatformUser">Platform role</span>
					<span class="chip" v-else-if="session.isCustomerUser">Customer role</span>
					<span class="chip" v-else>Authenticated</span>
				</div>
				<p class="detail-help">Native Frappe auth remains the source of truth for access and permissions.</p>
			</div>
		</aside>

		<div class="shell">
			<header class="shell-topbar">
				<div class="brand-mark">
					<div class="brand-badge">LC</div>
					<div class="brand-copy">
						<h1>LensCloud</h1>
						<p>{{ scopeLabel }}</p>
					</div>
				</div>
				<Button class="mobile-only" @click="mobileNavOpen = !mobileNavOpen">
					<component :is="mobileNavOpen ? PanelLeftClose : Menu" class="nav-icon" />
					{{ mobileNavOpen ? 'Close' : 'Menu' }}
				</Button>
			</header>

			<div v-if="mobileNavOpen" class="section-band mobile-only" style="margin: 12px 18px 0">
				<nav class="nav-group">
					<div v-for="group in navGroups" :key="group.heading">
						<div class="nav-heading">{{ group.heading }}</div>
						<RouterLink
							v-for="item in group.items"
							:key="item.key"
							:to="item.route"
							class="nav-link"
							:class="{ active: route.path === item.route || route.path.startsWith(`${item.route}/`) }"
							@click="closeMobileNav"
						>
								<component :is="item.icon" class="nav-icon" />
								<div class="nav-copy">
									<div class="nav-label">{{ item.label }}</div>
									<div class="nav-note">{{ item.note }}</div>
								</div>
							</RouterLink>
						</div>
				</nav>
			</div>

			<main class="shell-body">
				<slot />
			</main>
		</div>
	</div>
</template>
