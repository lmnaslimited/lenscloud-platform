import { createRouter, createWebHistory } from 'vue-router'
import { getHomeRoute } from '@/lib/catalog'
import { useSessionStore } from '@/lib/session'
import ShellLayout from '@/components/ShellLayout.vue'
import AccessGatePage from '@/pages/AccessGatePage.vue'
import DashboardPage from '@/pages/DashboardPage.vue'
import ResourcePage from '@/pages/ResourcePage.vue'
import CustomerAccountPage from '@/pages/CustomerAccountPage.vue'
import CustomerCreateSitePage from '@/pages/CustomerCreateSitePage.vue'
import CustomerPlansPage from '@/pages/CustomerPlansPage.vue'
import CustomerMembersPage from '@/pages/CustomerMembersPage.vue'
import CustomerSitesPage from '@/pages/CustomerSitesPage.vue'
import CustomerSubscriptionsPage from '@/pages/CustomerSubscriptionsPage.vue'
import CustomerMarketplacePage from '@/pages/CustomerMarketplacePage.vue'

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
			{ path: 'customer-members', name: 'platform-customer-members', component: ResourcePage, props: { scope: 'platform', resourceKey: 'customer-members', mode: 'list' }, meta: { scope: 'platform' } },
			{ path: 'customer-members/:name', name: 'platform-customer-member-detail', component: ResourcePage, props: { scope: 'platform', resourceKey: 'customer-members', mode: 'detail' }, meta: { scope: 'platform' } },
			{ path: 'release-groups', name: 'platform-release-groups', component: ResourcePage, props: { scope: 'platform', resourceKey: 'release-groups', mode: 'list' }, meta: { scope: 'platform' } },
			{ path: 'release-groups/:name', name: 'platform-release-group-detail', component: ResourcePage, props: { scope: 'platform', resourceKey: 'release-groups', mode: 'detail' }, meta: { scope: 'platform' } },
			{ path: 'apps', name: 'platform-apps', component: ResourcePage, props: { scope: 'platform', resourceKey: 'apps', mode: 'list' }, meta: { scope: 'platform' } },
			{ path: 'apps/:name', name: 'platform-app-detail', component: ResourcePage, props: { scope: 'platform', resourceKey: 'apps', mode: 'detail' }, meta: { scope: 'platform' } },
			{ path: 'tools', name: 'platform-tools', component: ResourcePage, props: { scope: 'platform', resourceKey: 'tools', mode: 'list' }, meta: { scope: 'platform' } },
			{ path: 'tools/:name', name: 'platform-tool-detail', component: ResourcePage, props: { scope: 'platform', resourceKey: 'tools', mode: 'detail' }, meta: { scope: 'platform' } },
			{ path: 'skills', name: 'platform-skills', component: ResourcePage, props: { scope: 'platform', resourceKey: 'skills', mode: 'list' }, meta: { scope: 'platform' } },
			{ path: 'skills/:name', name: 'platform-skill-detail', component: ResourcePage, props: { scope: 'platform', resourceKey: 'skills', mode: 'detail' }, meta: { scope: 'platform' } },
			{ path: 'capabilities', name: 'platform-capabilities', component: ResourcePage, props: { scope: 'platform', resourceKey: 'capabilities', mode: 'list' }, meta: { scope: 'platform' } },
			{ path: 'capabilities/:name', name: 'platform-capability-detail', component: ResourcePage, props: { scope: 'platform', resourceKey: 'capabilities', mode: 'detail' }, meta: { scope: 'platform' } },
			{ path: 'subscription-capabilities', name: 'platform-subscription-capabilities', component: ResourcePage, props: { scope: 'platform', resourceKey: 'subscription-capabilities', mode: 'list' }, meta: { scope: 'platform' } },
			{ path: 'subscription-capabilities/:name', name: 'platform-subscription-capability-detail', component: ResourcePage, props: { scope: 'platform', resourceKey: 'subscription-capabilities', mode: 'detail' }, meta: { scope: 'platform' } },
			{ path: 'capability-landscape-policies', name: 'platform-capability-landscape-policies', component: ResourcePage, props: { scope: 'platform', resourceKey: 'capability-landscape-policies', mode: 'list' }, meta: { scope: 'platform' } },
			{ path: 'capability-landscape-policies/:name', name: 'platform-capability-landscape-policy-detail', component: ResourcePage, props: { scope: 'platform', resourceKey: 'capability-landscape-policies', mode: 'detail' }, meta: { scope: 'platform' } },
			{ path: 'releases', name: 'platform-releases', component: ResourcePage, props: { scope: 'platform', resourceKey: 'releases', mode: 'list' }, meta: { scope: 'platform' } },
			{ path: 'releases/:name', name: 'platform-release-detail', component: ResourcePage, props: { scope: 'platform', resourceKey: 'releases', mode: 'detail' }, meta: { scope: 'platform' } },
			{ path: 'clusters', name: 'platform-clusters', component: ResourcePage, props: { scope: 'platform', resourceKey: 'clusters', mode: 'list' }, meta: { scope: 'platform' } },
			{ path: 'clusters/:name', name: 'platform-cluster-detail', component: ResourcePage, props: { scope: 'platform', resourceKey: 'clusters', mode: 'detail' }, meta: { scope: 'platform' } },
			{ path: 'runtime-namespaces', name: 'platform-runtime-namespaces', component: ResourcePage, props: { scope: 'platform', resourceKey: 'runtime-namespaces', mode: 'list' }, meta: { scope: 'platform' } },
			{ path: 'runtime-namespaces/:name', name: 'platform-runtime-namespace-detail', component: ResourcePage, props: { scope: 'platform', resourceKey: 'runtime-namespaces', mode: 'detail' }, meta: { scope: 'platform' } },
			{ path: 'database-servers', name: 'platform-database-servers', component: ResourcePage, props: { scope: 'platform', resourceKey: 'database-servers', mode: 'list' }, meta: { scope: 'platform' } },
			{ path: 'database-servers/:name', name: 'platform-database-server-detail', component: ResourcePage, props: { scope: 'platform', resourceKey: 'database-servers', mode: 'detail' }, meta: { scope: 'platform' } },
			{ path: 'benches', name: 'platform-benches', component: ResourcePage, props: { scope: 'platform', resourceKey: 'benches', mode: 'list' }, meta: { scope: 'platform' } },
			{ path: 'benches/:name', name: 'platform-bench-detail', component: ResourcePage, props: { scope: 'platform', resourceKey: 'benches', mode: 'detail' }, meta: { scope: 'platform' } },
			{ path: 'sites', name: 'platform-sites', component: ResourcePage, props: { scope: 'platform', resourceKey: 'sites', mode: 'list' }, meta: { scope: 'platform' } },
			{ path: 'sites/:name', name: 'platform-site-detail', component: ResourcePage, props: { scope: 'platform', resourceKey: 'sites', mode: 'detail' }, meta: { scope: 'platform' } },
			{ path: 'regions', name: 'platform-regions', component: ResourcePage, props: { scope: 'platform', resourceKey: 'regions', mode: 'list' }, meta: { scope: 'platform' } },
			{ path: 'regions/:name', name: 'platform-region-detail', component: ResourcePage, props: { scope: 'platform', resourceKey: 'regions', mode: 'detail' }, meta: { scope: 'platform' } },
			{ path: 'plans', name: 'platform-plans', component: ResourcePage, props: { scope: 'platform', resourceKey: 'plans', mode: 'list' }, meta: { scope: 'platform' } },
			{ path: 'plans/:name', name: 'platform-plan-detail', component: ResourcePage, props: { scope: 'platform', resourceKey: 'plans', mode: 'detail' }, meta: { scope: 'platform' } },
			{ path: 'subscriptions', name: 'platform-subscriptions', component: ResourcePage, props: { scope: 'platform', resourceKey: 'subscriptions', mode: 'list' }, meta: { scope: 'platform' } },
			{ path: 'subscriptions/:name', name: 'platform-subscription-detail', component: ResourcePage, props: { scope: 'platform', resourceKey: 'subscriptions', mode: 'detail' }, meta: { scope: 'platform' } },
			{ path: 'environments', name: 'platform-environments', component: ResourcePage, props: { scope: 'platform', resourceKey: 'environments', mode: 'list' }, meta: { scope: 'platform' } },
			{ path: 'environments/:name', name: 'platform-environment-detail', component: ResourcePage, props: { scope: 'platform', resourceKey: 'environments', mode: 'detail' }, meta: { scope: 'platform' } },
			{ path: 'landscapes', name: 'platform-landscapes', component: ResourcePage, props: { scope: 'platform', resourceKey: 'landscapes', mode: 'list' }, meta: { scope: 'platform' } },
			{ path: 'landscapes/:name', name: 'platform-landscape-detail', component: ResourcePage, props: { scope: 'platform', resourceKey: 'landscapes', mode: 'detail' }, meta: { scope: 'platform' } },
			{ path: 'site-control-profiles', name: 'platform-site-control-profiles', component: ResourcePage, props: { scope: 'platform', resourceKey: 'site-control-profiles', mode: 'list' }, meta: { scope: 'platform' } },
			{ path: 'site-control-profiles/:name', name: 'platform-site-control-profile-detail', component: ResourcePage, props: { scope: 'platform', resourceKey: 'site-control-profiles', mode: 'detail' }, meta: { scope: 'platform' } },
			{ path: 'privacy', name: 'platform-privacy', component: ResourcePage, props: { scope: 'platform', resourceKey: 'privacy', mode: 'list' }, meta: { scope: 'platform' } },
			{ path: 'privacy/:name', name: 'platform-privacy-detail', component: ResourcePage, props: { scope: 'platform', resourceKey: 'privacy', mode: 'detail' }, meta: { scope: 'platform' } },
			{ path: 'privacy-profiles', name: 'platform-privacy-profiles', component: ResourcePage, props: { scope: 'platform', resourceKey: 'privacy-profiles', mode: 'list' }, meta: { scope: 'platform' } },
			{ path: 'privacy-profiles/:name', name: 'platform-privacy-profile-detail', component: ResourcePage, props: { scope: 'platform', resourceKey: 'privacy-profiles', mode: 'detail' }, meta: { scope: 'platform' } },
			{ path: 'environment-test-runs', name: 'platform-environment-test-runs', component: ResourcePage, props: { scope: 'platform', resourceKey: 'environment-test-runs', mode: 'list' }, meta: { scope: 'platform' } },
			{ path: 'environment-test-runs/:name', name: 'platform-environment-test-run-detail', component: ResourcePage, props: { scope: 'platform', resourceKey: 'environment-test-runs', mode: 'detail' }, meta: { scope: 'platform' } },
			{ path: 'orchestration-logs', name: 'platform-orchestration-logs', component: ResourcePage, props: { scope: 'platform', resourceKey: 'orchestration-logs', mode: 'list' }, meta: { scope: 'platform' } },
			{ path: 'orchestration-logs/:name', name: 'platform-orchestration-log-detail', component: ResourcePage, props: { scope: 'platform', resourceKey: 'orchestration-logs', mode: 'detail' }, meta: { scope: 'platform' } },
			{ path: 'settings', name: 'platform-settings', component: ResourcePage, props: { scope: 'platform', resourceKey: 'settings', mode: 'detail' }, meta: { scope: 'platform' } },
			{ path: 'capability', name: 'platform-capability', component: ResourcePage, props: { scope: 'platform', resourceKey: 'capability', mode: 'list' }, meta: { scope: 'platform' } },
			{ path: 'capability/:name', name: 'platform-capability-detail', component: ResourcePage, props: { scope: 'platform', resourceKey: 'capability', mode: 'detail' }, meta: { scope: 'platform' } },
			{ path: 'capability-opted', name: 'platform-capability-opted', component: ResourcePage, props: { scope: 'platform', resourceKey: 'capability-opted', mode: 'list' }, meta: { scope: 'platform' } },
			{ path: 'capability-opted/:name', name: 'platform-capability-opted-detail', component: ResourcePage, props: { scope: 'platform', resourceKey: 'capability-opted', mode: 'detail' }, meta: { scope: 'platform' } },
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
			{ path: 'plans', name: 'customer-plans', component: CustomerPlansPage, meta: { scope: 'customer' } },
			{ path: 'subscriptions', name: 'customer-subscriptions', component: CustomerSubscriptionsPage, meta: { scope: 'customer' } },
			{ path: 'marketplace', name: 'customer-marketplace', component: CustomerMarketplacePage, meta: { scope: 'customer' } },
			{ path: 'members', name: 'customer-members', component: CustomerMembersPage, meta: { scope: 'customer' } },
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
