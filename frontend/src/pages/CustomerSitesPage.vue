<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { Alert, Badge, Button } from 'frappe-ui'
import { CheckCircle2, CircleHelp, CloudDownload, ExternalLink, Globe2, LifeBuoy, Lock, Pause, RefreshCcw, RotateCcw, SquareArrowOutUpRight } from 'lucide-vue-next'
import { listDocs, formatFieldValue } from '@/lib/api'
import { useSessionStore } from '@/lib/session'
import WorkspaceLayout from '@/components/WorkspaceLayout.vue'

const route = useRoute()
const session = useSessionStore()
const loading = ref(true)
const error = ref(null)
const customer = ref(null)
const sites = ref([])

const selectedName = computed(() => route.params.name || sites.value[0]?.name || '')
const selectedSite = computed(() => sites.value.find((site) => site.name === selectedName.value) || null)

const lockedActions = [
	{ label: 'Backup', icon: CloudDownload, status: 'Requires LensCloud qualification' },
	{ label: 'Restore', icon: RotateCcw, status: 'Requires LensCloud qualification' },
	{ label: 'Upgrade', icon: RefreshCcw, status: 'Requires LensCloud qualification' },
	{ label: 'Advanced DNS', icon: CircleHelp, status: 'Managed by platform team' },
	{ label: 'Suspend', icon: Pause, status: 'Managed by platform team' },
]

const stats = computed(() => [
	{ label: 'Sites', value: sites.value.length, note: 'Sites in your account' },
	{ label: 'Ready', value: sites.value.filter((site) => site.site_status === 'Ready' || site.site_status === 'Active').length, note: 'Ready to open' },
	{ label: 'Routes ready', value: sites.value.filter((site) => site.route_status === 'Ready').length, note: 'Access is ready' },
])

const assistantContext = computed(() => ({
	scope: 'customer',
	summary: selectedSite.value
		? `Guidance for site ${selectedSite.value.title || selectedSite.value.name}.`
		: 'Guidance for customer site management and support-first workflows.',
	badges: ['Sites', selectedSite.value ? 'site selected' : 'no site selected', 'advanced ops locked'],
	sections: [
		{ label: 'Customer record', value: customer.value?.name || 'No linked customer record' },
		{ label: 'Sites visible', value: `${sites.value.length} linked site(s)` },
		{ label: 'Selected site', value: selectedSite.value ? (selectedSite.value.title || selectedSite.value.name) : 'No site selected' },
		{ label: 'Standard action', value: 'Contact Support is the normal customer path for site help.' },
	],
	gaps: [
		'Live status sync requires restricted cluster access',
		'Advanced operations require qualification or platform-team handling',
	],
	nextSteps: sites.value.length
		? ['Open a site card for context.', 'Use Contact Support for standard requests.', 'Ask LensCloud about qualification before backup/restore/upgrade/DNS actions.']
		: ['Create the first Site.', 'LensCloud prepares the workspace and keeps progress visible.'],
}))

async function load() {
	loading.value = true
	error.value = null
	try {
		const customers = await listDocs('Customer', {
			fields: ['name', 'first_name', 'last_name', 'region', 'external_customer_id'],
			limit: 1,
			filters: [['user', '=', session.user]],
		})
		customer.value = customers[0] || null

		if (!customer.value) {
			sites.value = []
			return
		}

		sites.value = await listDocs('Site', {
			fields: ['name', 'title', 'domain', 'site_status', 'provisioning_status', 'hostname_reservation_status', 'route_status', 'tls_status', 'access_url', 'plan', 'subscription', 'environment', 'modified'],
			limit: 50,
			filters: [['customer', '=', customer.value.name]],
		})
	} catch (err) {
		error.value = err?.message || 'Unable to load customer sites.'
	} finally {
		loading.value = false
	}
}

onMounted(load)
</script>

<template>
	<WorkspaceLayout
		title="Sites"
		subtitle="Review Sites, follow setup progress, and open your ready workspace."
		inspector-kicker="Site context"
		:inspector-title="selectedSite ? (selectedSite.title || selectedSite.name) : 'No site selected'"
		inspector-subtitle="Customer-safe Site status and support actions."
		assistant-label="Assistant"
		assistant-hint="The assistant will help explain site status, support paths, billing context, and qualification requirements."
		:assistant-context="assistantContext"
	>
		<template #actions>
			<Button :as="RouterLink" to="/customer/plans">
				<SquareArrowOutUpRight class="size-4" />
				Choose Plan
			</Button>
			<Button variant="subtle" @click="load">Refresh</Button>
		</template>

		<template #main>
			<div class="h-full overflow-y-auto p-4">
				<Alert v-if="error" theme="red" title="Sites gap" :description="error" />

				<div v-if="loading" class="rounded border border-outline-gray-2 bg-surface-white p-5 text-sm text-ink-gray-5">
					Loading sites...
				</div>

				<template v-else>
					<section class="rounded border border-outline-gray-2 bg-surface-white p-4">
						<div class="flex flex-wrap items-center justify-between gap-3">
							<div>
								<p class="text-base font-semibold text-ink-gray-9">Manage sites</p>
								<p class="mt-1 text-sm leading-5 text-ink-gray-5">Open ready Sites, review setup progress, and use support when you need help.</p>
							</div>
							<Button :as="RouterLink" to="/customer/plans">
								<SquareArrowOutUpRight class="size-4" />
								Choose Plan
							</Button>
						</div>

						<div class="mt-4 grid gap-3 sm:grid-cols-3">
							<div v-for="stat in stats" :key="stat.label" class="rounded border border-outline-gray-2 bg-surface-gray-1 p-3">
								<p class="text-sm text-ink-gray-5">{{ stat.label }}</p>
								<p class="mt-1 text-2xl font-semibold text-ink-gray-9">{{ stat.value }}</p>
								<p class="mt-1 text-xs text-ink-gray-5">{{ stat.note }}</p>
							</div>
						</div>
					</section>

					<section v-if="!customer" class="mt-4 rounded border border-dashed border-outline-gray-2 bg-surface-gray-1 p-5">
						<p class="text-sm font-medium text-ink-gray-9">Customer record not linked</p>
						<p class="mt-1 text-sm leading-6 text-ink-gray-5">A Customer record tied to this Frappe user is required before sites can be listed.</p>
					</section>

					<section v-else-if="!sites.length" class="mt-4 rounded border border-outline-gray-2 bg-surface-white p-6 text-center">
						<div class="mx-auto grid size-10 place-items-center rounded bg-surface-gray-2 text-ink-gray-5">
							<Globe2 class="size-5" />
						</div>
						<p class="mt-3 text-base font-semibold text-ink-gray-9">Launch your first Site</p>
						<p class="mx-auto mt-1 max-w-md text-sm leading-6 text-ink-gray-5">Choose the Free Plan, confirm your ₹0 subscription, and LensCloud will prepare your first Site.</p>
						<Button class="mt-4" :as="RouterLink" to="/customer/plans">
							<SquareArrowOutUpRight class="size-4" />
							Choose Plan
						</Button>
					</section>

					<section v-else class="mt-4 grid gap-3 xl:grid-cols-2">
						<RouterLink
							v-for="site in sites"
							:key="site.name"
							:to="`/customer/sites/${encodeURIComponent(site.name)}`"
							class="rounded border border-outline-gray-2 bg-surface-white p-4 transition hover:bg-surface-gray-1"
						>
							<div class="flex items-start justify-between gap-3">
								<div class="min-w-0">
									<p class="truncate text-base font-semibold text-ink-gray-9">{{ site.title || site.name }}</p>
									<p class="mt-1 truncate text-xs text-ink-gray-5">{{ site.name }}</p>
								</div>
								<Badge :class="site.route_status === 'Ready' ? 'bg-emerald-50 text-emerald-700' : 'bg-surface-gray-2 text-ink-gray-6'">{{ site.route_status || site.site_status || 'Pending' }}</Badge>
							</div>

							<div class="mt-3 grid gap-2 sm:grid-cols-2">
								<div class="rounded bg-surface-gray-1 px-3 py-2">
									<p class="text-xs text-ink-gray-5">Setup progress</p>
									<p class="mt-1 truncate text-sm font-medium text-ink-gray-9">{{ site.provisioning_status || 'Pending' }}</p>
								</div>
								<div class="rounded bg-surface-gray-1 px-3 py-2">
									<p class="text-xs text-ink-gray-5">Access</p>
									<p class="mt-1 truncate text-sm font-medium text-ink-gray-9">{{ site.route_status === 'Ready' ? 'Ready' : 'Preparing' }}</p>
								</div>
							</div>

							<div class="mt-3 flex flex-wrap gap-2" @click.prevent>
								<Button v-if="site.access_url && ['Ready','Active'].includes(site.site_status)" size="sm" as="a" :href="site.access_url" target="_blank">
									<ExternalLink class="size-4" />
									Open Site
								</Button>
								<Button size="sm" variant="subtle"><LifeBuoy class="size-4" />Contact support</Button>
								<Badge class="bg-surface-gray-2 text-ink-gray-6">Access management coming soon</Badge>
							</div>
						</RouterLink>
					</section>
				</template>
			</div>
		</template>

		<template #inspector>
			<div class="space-y-3">
				<div class="rounded border border-outline-gray-2 bg-surface-gray-1 p-3">
					<div class="flex items-start justify-between gap-3">
						<div class="min-w-0">
							<p class="text-xs font-medium text-ink-gray-5">Selected site</p>
							<p class="mt-1 truncate text-sm font-medium text-ink-gray-9">{{ selectedSite ? (selectedSite.title || selectedSite.name) : 'No site selected' }}</p>
						</div>
						<Badge class="bg-surface-white text-ink-gray-7">Customer</Badge>
					</div>
				</div>

				<div v-if="selectedSite" class="rounded border border-outline-gray-2 bg-surface-white p-3">
					<div class="space-y-2 text-sm leading-6 text-ink-gray-6">
						<p><CheckCircle2 class="mr-1 inline size-4 text-ink-gray-4" /> Setup: {{ selectedSite.provisioning_status || 'Pending' }}</p>
						<p>Site status: {{ selectedSite.site_status || 'Pending' }}</p>
						<p>Access: {{ selectedSite.route_status === 'Ready' ? 'Ready' : 'Preparing' }}</p>
						<p v-if="selectedSite.access_url"><a class="text-ink-blue-3 hover:underline" :href="selectedSite.access_url" target="_blank" rel="noreferrer">Open site</a></p>
						<p>Updated: {{ formatFieldValue(selectedSite.modified) }}</p>
					</div>
				</div>

				<div class="rounded border border-outline-gray-2 bg-surface-white p-3">
					<div class="flex items-center gap-2">
						<Lock class="size-4 text-ink-gray-5" />
						<p class="text-sm font-medium text-ink-gray-9">Locked advanced operations</p>
					</div>
					<div class="mt-3 space-y-2">
						<div v-for="action in lockedActions" :key="action.label" class="flex items-center justify-between gap-3 rounded border border-outline-gray-2 bg-surface-gray-1 px-3 py-2">
							<div class="flex min-w-0 items-center gap-2">
								<component :is="action.icon" class="size-4 shrink-0 text-ink-gray-5" />
								<span class="truncate text-sm font-medium text-ink-gray-8">{{ action.label }}</span>
							</div>
							<Badge class="bg-surface-white text-ink-gray-7">{{ action.status }}</Badge>
						</div>
					</div>
				</div>
				<Alert theme="blue" title="Support first" description="Customers use support for standard requests. Backup, restore, upgrade, advanced DNS, suspend, and delete require LensCloud qualification or platform-team handling." />
			</div>
		</template>
	</WorkspaceLayout>
</template>
