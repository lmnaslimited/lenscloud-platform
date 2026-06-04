import { createRouter, createWebHistory } from 'vue-router'
import { getHomeRoute } from '@/lib/catalog'
import { useSessionStore } from '@/lib/session'
import ShellLayout from '@/components/ShellLayout.vue'
import AccessGatePage from '@/pages/AccessGatePage.vue'
import DashboardPage from '@/pages/DashboardPage.vue'
import ResourcePage from '@/pages/ResourcePage.vue'
import PlatformSettingsPage from '@/pages/PlatformSettingsPage.vue'
import CustomerAccountPage from '@/pages/CustomerAccountPage.vue'
import CustomerCreateSitePage from '@/pages/CustomerCreateSitePage.vue'
import CustomerSitesPage from '@/pages/CustomerSitesPage.vue'

const routes = [
	{
		path: '/access',
		name: 'access',
		component: AccessGatePage,
		meta: { public: true },
	},
	{
		path: '/',
		redirect: '/platform/dashboard',
	},
	{
		path: '/platform',
		component: ShellLayout,
		meta: { scope: 'platform' },
		children: [
			{ path: '', redirect: '/platform/dashboard' },
			{ path: 'dashboard', name: 'platform-dashboard', component: DashboardPage, props: { scope: 'platform' }, meta: { scope: 'platform' } },
			{ path: 'customers', name: 'platform-customers', component: ResourcePage, props: { scope: 'platform', resourceKey: 'customers', mode: 'list' }, meta: { scope: 'platform' } },
			{ path: 'customers/:name', name: 'platform-customer-detail', component: ResourcePage, props: { scope: 'platform', resourceKey: 'customers', mode: 'detail' }, meta: { scope: 'platform' } },
			{ path: 'release-groups', name: 'platform-release-groups', component: ResourcePage, props: { scope: 'platform', resourceKey: 'release-groups', mode: 'list' }, meta: { scope: 'platform' } },
			{ path: 'release-groups/:name', name: 'platform-release-group-detail', component: ResourcePage, props: { scope: 'platform', resourceKey: 'release-groups', mode: 'detail' }, meta: { scope: 'platform' } },
			{ path: 'apps', name: 'platform-apps', component: ResourcePage, props: { scope: 'platform', resourceKey: 'apps', mode: 'list' }, meta: { scope: 'platform' } },
			{ path: 'apps/:name', name: 'platform-app-detail', component: ResourcePage, props: { scope: 'platform', resourceKey: 'apps', mode: 'detail' }, meta: { scope: 'platform' } },
			{ path: 'releases', name: 'platform-releases', component: ResourcePage, props: { scope: 'platform', resourceKey: 'releases', mode: 'list' }, meta: { scope: 'platform' } },
			{ path: 'releases/:name', name: 'platform-release-detail', component: ResourcePage, props: { scope: 'platform', resourceKey: 'releases', mode: 'detail' }, meta: { scope: 'platform' } },
			{ path: 'clusters', name: 'platform-clusters', component: ResourcePage, props: { scope: 'platform', resourceKey: 'clusters', mode: 'list' }, meta: { scope: 'platform' } },
			{ path: 'clusters/:name', name: 'platform-cluster-detail', component: ResourcePage, props: { scope: 'platform', resourceKey: 'clusters', mode: 'detail' }, meta: { scope: 'platform' } },
			{ path: 'benches', name: 'platform-benches', component: ResourcePage, props: { scope: 'platform', resourceKey: 'benches', mode: 'list' }, meta: { scope: 'platform' } },
			{ path: 'benches/:name', name: 'platform-bench-detail', component: ResourcePage, props: { scope: 'platform', resourceKey: 'benches', mode: 'detail' }, meta: { scope: 'platform' } },
			{ path: 'sites', name: 'platform-sites', component: ResourcePage, props: { scope: 'platform', resourceKey: 'sites', mode: 'list' }, meta: { scope: 'platform' } },
			{ path: 'sites/:name', name: 'platform-site-detail', component: ResourcePage, props: { scope: 'platform', resourceKey: 'sites', mode: 'detail' }, meta: { scope: 'platform' } },
			{ path: 'regions', name: 'platform-regions', component: ResourcePage, props: { scope: 'platform', resourceKey: 'regions', mode: 'list' }, meta: { scope: 'platform' } },
			{ path: 'regions/:name', name: 'platform-region-detail', component: ResourcePage, props: { scope: 'platform', resourceKey: 'regions', mode: 'detail' }, meta: { scope: 'platform' } },
			{ path: 'plans', name: 'platform-plans', component: ResourcePage, props: { scope: 'platform', resourceKey: 'plans', mode: 'list' }, meta: { scope: 'platform' } },
			{ path: 'plans/:name', name: 'platform-plan-detail', component: ResourcePage, props: { scope: 'platform', resourceKey: 'plans', mode: 'detail' }, meta: { scope: 'platform' } },
			{ path: 'orchestration-logs', name: 'platform-orchestration-logs', component: ResourcePage, props: { scope: 'platform', resourceKey: 'orchestration-logs', mode: 'list' }, meta: { scope: 'platform' } },
			{ path: 'orchestration-logs/:name', name: 'platform-orchestration-log-detail', component: ResourcePage, props: { scope: 'platform', resourceKey: 'orchestration-logs', mode: 'detail' }, meta: { scope: 'platform' } },
			{ path: 'settings', name: 'platform-settings', component: PlatformSettingsPage, meta: { scope: 'platform' } },
		],
	},
	{
		path: '/customer',
		component: ShellLayout,
		meta: { scope: 'customer' },
		children: [
			{ path: '', redirect: '/customer/dashboard' },
			{ path: 'dashboard', name: 'customer-dashboard', component: DashboardPage, props: { scope: 'customer' }, meta: { scope: 'customer' } },
			{ path: 'sites', name: 'customer-sites', component: CustomerSitesPage, meta: { scope: 'customer' } },
			{ path: 'sites/:name', name: 'customer-site-detail', component: CustomerSitesPage, meta: { scope: 'customer' } },
			{ path: 'create-site', name: 'customer-create-site', component: CustomerCreateSitePage, meta: { scope: 'customer' } },
			{ path: 'account', name: 'customer-account', component: CustomerAccountPage, meta: { scope: 'customer' } },
		],
	},
]

const router = createRouter({
	history: createWebHistory('/lenscloud'),
	routes,
})

router.beforeEach(async (to) => {
	const session = useSessionStore()
	if (session.status !== 'ready') {
		await session.initialize()
	}

	if (to.meta.public) {
		return true
	}

	if (!session.isAuthenticated) {
		return { path: '/access', query: { 'redirect-to': to.fullPath } }
	}

	if (to.path === '/') {
		return getHomeRoute(session)
	}

	if (to.meta.scope === 'platform' && !session.canAccessPlatform) {
		return '/customer/dashboard'
	}

	if (to.meta.scope === 'customer' && !session.canAccessCustomer) {
		return '/access'
	}

	return true
})

export default router
