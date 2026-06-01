<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { Button, Badge } from 'frappe-ui'
import { listDocs, formatFieldValue, getDoc } from '@/lib/api'
import { platformResources, customerResources, platformSettings } from '@/lib/catalog'
import { useSessionStore } from '@/lib/session'
import PageHeader from '@/components/PageHeader.vue'

const props = defineProps({
	scope: {
		type: String,
		required: true,
	},
})

const session = useSessionStore()
const loading = ref(true)
const data = reactive({
	platform: {},
	customerSites: [],
	platformSettings: null,
	customerAccount: null,
})

const resources = computed(() => (props.scope === 'customer' ? customerResources : platformResources))

async function loadPlatform() {
	const entries = await Promise.all(
		platformResources.map(async (resource) => {
			const items = await listDocs(resource.doctype, {
				fields: ['name', ...resource.summaryFields.map((field) => field.key)],
				limit: 4,
			})

			return { key: resource.key, items }
		}),
	)

	for (const entry of entries) {
		data.platform[entry.key] = entry.items
	}

	data.platformSettings = await getDoc(platformSettings.doctype, platformSettings.doctype).catch(() => null)
}

async function loadCustomer() {
	const customerRecords = await listDocs('Customer', {
		fields: ['name', 'first_name', 'last_name', 'region', 'external_customer_id'],
		limit: 1,
		filters: [['user', '=', session.user]],
	})

	data.customerAccount = customerRecords[0] || null

	if (data.customerAccount) {
		data.customerSites = await listDocs('Site', {
			fields: ['name', 'title', 'bench', 'customer', 'modified'],
			limit: 4,
			filters: [['customer', '=', data.customerAccount.name]],
		})
	}
}

async function load() {
	loading.value = true
	try {
		if (props.scope === 'customer') {
			await loadCustomer()
		} else {
			await loadPlatform()
		}
	} finally {
		loading.value = false
	}
}

onMounted(load)
watch(() => props.scope, load)

const platformSummary = computed(() => [
	{ label: 'Customers', route: '/platform/customers', count: (data.platform.customers || []).length },
	{ label: 'Release groups', route: '/platform/release-groups', count: (data.platform['release-groups'] || []).length },
	{ label: 'Benches', route: '/platform/benches', count: (data.platform.benches || []).length },
	{ label: 'Sites', route: '/platform/sites', count: (data.platform.sites || []).length },
	{ label: 'Regions', route: '/platform/regions', count: (data.platform.regions || []).length },
])

const customerSummary = computed(() => [
	{ label: 'Sites', route: '/customer/sites', count: data.customerSites.length },
	{ label: 'Account', route: '/customer/account', count: data.customerAccount ? 1 : 0 },
])
</script>

<template>
	<div class="stack">
		<PageHeader
			:kicker="scope === 'customer' ? 'Customer portal' : 'Platform console'"
			title="LensCloud Dashboard"
			:subtitle="scope === 'customer'
				? 'Your authenticated surface for account visibility and customer lifecycle tracking.'
				: 'Operator-friendly surface for customers, release groups, benches, sites, regions, and settings.'"
		>
			<template #actions>
				<Badge v-if="scope === 'platform'">Platform first</Badge>
				<Badge v-else>Customer facing</Badge>
				<Button @click="load">Refresh</Button>
			</template>
		</PageHeader>

		<div v-if="loading" class="section-band">
			<div class="spinner" />
			<p class="empty-title" style="margin-top: 8px">Loading dashboard…</p>
			<p class="helper-text">Reading from native Frappe document APIs.</p>
		</div>

		<template v-else>
			<section class="section-band">
				<div class="section-head">
					<div>
						<div class="section-title">{{ scope === 'customer' ? 'Your account surface' : 'Operational surface' }}</div>
						<p class="section-subtitle">{{ scope === 'customer' ? 'Identity, linked sites, and pending request entry points.' : 'Current records and shortcuts into the platform console.' }}</p>
					</div>
				</div>

				<div :class="scope === 'customer' ? 'grid-2' : 'grid-4'">
					<div v-for="item in scope === 'customer' ? customerSummary : platformSummary" :key="item.label" class="stat-card" style="padding: 16px">
						<div class="resource-topline">
							<div>
								<p class="resource-title">{{ item.label }}</p>
								<p class="helper-text">Current count or visibility marker.</p>
							</div>
							<div class="badge">{{ item.count }}</div>
						</div>
						<div class="button-row" style="margin-top: 8px">
							<Button :to="item.route" tag="RouterLink">Open</Button>
						</div>
					</div>
				</div>
			</section>

			<section v-if="scope === 'platform'" class="section-band">
				<div class="section-head">
					<div>
						<div class="section-title">Platform shortcuts</div>
						<p class="section-subtitle">Recent records and their related list surfaces.</p>
					</div>
				</div>

				<div class="grid-2">
					<div v-for="resource in resources" :key="resource.key" class="resource-card">
						<div class="resource-topline">
							<div>
								<p class="resource-title">{{ resource.label }}</p>
								<p class="helper-text">{{ resource.listHelp }}</p>
							</div>
							<Badge>{{ (data.platform[resource.key] || []).length }} recent</Badge>
						</div>
						<div class="table-list">
							<RouterLink v-for="record in data.platform[resource.key] || []" :key="record.name" :to="resource.detailRoute(record.name)" class="table-row">
								<div class="table-main">
									<p class="table-title">{{ record.title || record.first_name || record.name }}</p>
									<p class="helper-text mono">{{ record.name }}</p>
								</div>
								<div class="table-meta">
									<Badge v-for="field in resource.summaryFields.slice(0, 2)" :key="field.key">{{ field.label }}: {{ formatFieldValue(record[field.key]) }}</Badge>
								</div>
								<div class="badge">Open</div>
							</RouterLink>
						</div>
					</div>
				</div>
			</section>

			<section v-else class="section-band">
				<div class="section-head">
					<div>
						<div class="section-title">Customer surface</div>
						<p class="section-subtitle">Your current customer record and linked sites.</p>
					</div>
				</div>

				<div v-if="!data.customerAccount" class="empty-state">
					<p class="empty-title">Customer record not linked</p>
					<p class="helper-text">The frontend expects a Customer record linked to the signed-in user. If the backend does not yet provide that linkage, this is surfaced here as a gap.</p>
				</div>

				<div v-else class="grid-2">
					<div class="resource-card">
						<div class="resource-topline">
							<div>
								<p class="resource-title">{{ data.customerAccount.first_name || data.customerAccount.name }}</p>
								<p class="helper-text mono">{{ data.customerAccount.name }}</p>
							</div>
							<Badge>{{ data.customerSites.length }} sites</Badge>
						</div>
						<div class="field-grid">
							<div class="field">
								<label>Primary region</label>
								<div class="value">{{ data.customerAccount.region || '—' }}</div>
							</div>
							<div class="field">
								<label>External ID</label>
								<div class="value">{{ data.customerAccount.external_customer_id || '—' }}</div>
							</div>
						</div>
						<div class="button-row">
							<Button :to="'/customer/account'" tag="RouterLink">Open account</Button>
							<Button :to="'/customer/sites'" tag="RouterLink">View sites</Button>
						</div>
					</div>

					<div class="resource-card">
						<div class="resource-topline">
							<div>
								<p class="resource-title">Linked sites</p>
								<p class="helper-text">Recent sites tied to your customer record.</p>
							</div>
							<Badge>{{ data.customerSites.length }}</Badge>
						</div>
						<div class="table-list">
							<RouterLink v-for="site in data.customerSites" :key="site.name" :to="`/customer/sites/${encodeURIComponent(site.name)}`" class="table-row">
								<div class="table-main">
									<p class="table-title">{{ site.title || site.name }}</p>
									<p class="helper-text mono">{{ site.name }}</p>
								</div>
								<div class="table-meta">
									<Badge>Bench: {{ site.bench || '—' }}</Badge>
									<Badge>Customer: {{ site.customer || '—' }}</Badge>
								</div>
								<div class="badge">Open</div>
							</RouterLink>
						</div>
					</div>
				</div>
			</section>
		</template>
	</div>
</template>
