<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { Alert, Badge, Button, ListView } from 'frappe-ui'
import { CircleHelp, CloudDownload, Globe2, Pause, RefreshCcw, RotateCcw, Server, ShieldAlert, SquareArrowOutUpRight } from 'lucide-vue-next'
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

const siteActions = [
	{ label: 'Backup', icon: CloudDownload, status: 'Backend gap' },
	{ label: 'Restore', icon: RotateCcw, status: 'Backend gap' },
	{ label: 'Upgrade', icon: RefreshCcw, status: 'Backend gap' },
	{ label: 'DNS', icon: CircleHelp, status: 'Backend gap' },
	{ label: 'Suspend', icon: Pause, status: 'Backend gap' },
]

const stats = computed(() => [
	{ label: 'Sites', value: sites.value.length, note: 'Linked tenant instances' },
	{ label: 'Ready', value: sites.value.length, note: 'Status field pending' },
	{ label: 'Requests', value: 0, note: 'Request backend pending' },
])

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
			fields: ['name', 'title', 'bench', 'customer', 'modified'],
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
		subtitle="Create, review, and manage your LensCloud tenant instances."
		inspector-kicker="Site context"
		:inspector-title="selectedSite ? (selectedSite.title || selectedSite.name) : 'No site selected'"
		inspector-subtitle="Detailed lifecycle metadata and assistant guidance live here; primary customer actions stay in the main page."
		assistant-label="Assistant"
		assistant-hint="The assistant will help explain site status, DNS, backups, restores, and upgrade choices."
	>
		<template #actions>
			<Button :as="RouterLink" to="/customer/create-site">
				<SquareArrowOutUpRight class="size-4" />
				Create Site
			</Button>
			<Button variant="subtle" @click="load">Refresh</Button>
		</template>

		<template #main>
			<div class="h-full overflow-y-auto p-4">
				<Alert v-if="error" theme="red" title="Sites gap" :message="error" />

				<div v-if="loading" class="rounded border border-outline-gray-2 bg-surface-white p-5 text-sm text-ink-gray-5">
					Loading sites...
				</div>

				<template v-else>
					<section class="rounded border border-outline-gray-2 bg-surface-white p-4">
						<div class="flex flex-wrap items-center justify-between gap-3">
							<div>
								<p class="text-base font-semibold text-ink-gray-9">Manage sites</p>
								<p class="mt-1 text-sm leading-5 text-ink-gray-5">Create a site, review current instances, and start lifecycle actions from one place.</p>
							</div>
							<Button :as="RouterLink" to="/customer/create-site">
								<SquareArrowOutUpRight class="size-4" />
								Create Site
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
						<p class="mt-3 text-base font-semibold text-ink-gray-9">Create your first site</p>
						<p class="mx-auto mt-1 max-w-md text-sm leading-6 text-ink-gray-5">LensCloud is ready for the customer flow. Start a site request and the platform team can wire it to provisioning when backend support lands.</p>
						<Button class="mt-4" :as="RouterLink" to="/customer/create-site">
							<SquareArrowOutUpRight class="size-4" />
							Create Site
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
								<Badge class="bg-emerald-50 text-emerald-700">Visible</Badge>
							</div>

							<div class="mt-3 grid gap-2 sm:grid-cols-2">
								<div class="rounded bg-surface-gray-1 px-3 py-2">
									<p class="text-xs text-ink-gray-5">Bench</p>
									<p class="mt-1 truncate text-sm font-medium text-ink-gray-9">{{ formatFieldValue(site.bench) }}</p>
								</div>
								<div class="rounded bg-surface-gray-1 px-3 py-2">
									<p class="text-xs text-ink-gray-5">Updated</p>
									<p class="mt-1 truncate text-sm font-medium text-ink-gray-9">{{ formatFieldValue(site.modified) }}</p>
								</div>
							</div>

							<div class="mt-3 flex flex-wrap gap-2" @click.prevent>
								<Button v-for="action in siteActions.slice(0, 4)" :key="action.label" size="sm" variant="subtle" disabled>
									<component :is="action.icon" class="size-4" />
									{{ action.label }}
								</Button>
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
						<p><Server class="mr-1 inline size-4 text-ink-gray-4" /> Bench: {{ formatFieldValue(selectedSite.bench) }}</p>
						<p>Customer: {{ formatFieldValue(selectedSite.customer) }}</p>
						<p>Updated: {{ formatFieldValue(selectedSite.modified) }}</p>
					</div>
				</div>

				<Alert theme="yellow" title="Lifecycle backend gap" message="Customer lifecycle buttons are visible as product actions, but remain disabled until backend orchestration endpoints are connected." />
			</div>
		</template>
	</WorkspaceLayout>
</template>
