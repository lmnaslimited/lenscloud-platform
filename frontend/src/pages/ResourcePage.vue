<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { Alert, Badge, Button, Dropdown, ListView, Tabs, TextInput, Textarea } from 'frappe-ui'
import { listDocs, getDoc, saveDoc, formatFieldValue } from '@/lib/api'
import { getResourceByKey, platformSettings } from '@/lib/catalog'
import { useSessionStore } from '@/lib/session'
import WorkspaceLayout from '@/components/WorkspaceLayout.vue'
import { ChevronDown, ChevronRight, CreditCard, Filter, FolderTree, LifeBuoy, List, Lock, MapPin, MoreHorizontal, Search, Users } from 'lucide-vue-next'

const props = defineProps({
	resourceKey: { type: String, required: true },
	mode: { type: String, default: 'list' },
	scope: { type: String, required: true },
})

const route = useRoute()
const router = useRouter()
const session = useSessionStore()
const resource = computed(() => getResourceByKey(props.resourceKey))
const loading = ref(true)
const records = ref([])
const record = ref(null)
const related = ref([])
const error = ref(null)
const customerContext = ref(null)
const settingsContext = ref(null)
const saveState = ref('idle')
const activeActionKey = ref('')
const searchQuery = ref('')
const filterMode = ref('all')
const inspectorTab = ref(0)
const displayMode = ref('list')
const expandedTreeNodes = ref(new Set())
const formState = reactive({})
const actionState = reactive({})

const selectedName = computed(() => route.params.name || records.value[0]?.name || '')
const isTreeResource = computed(() => Boolean(resource.value?.tree))

const listColumns = computed(() => {
	if (!resource.value) return []

	return [
		{
			label: 'Name',
			key: 'name',
			width: 3,
			getLabel: ({ row }) => row.title || row.first_name || row.name,
		},
		...resource.value.summaryFields.map((field) => ({
			label: field.label,
			key: field.key,
			width: field.width || '180px',
			getLabel: ({ row }) => formatFieldValue(row[field.key]),
		})),
	]
})

const visibleRecords = computed(() => {
	const query = searchQuery.value.trim().toLowerCase()
	let rows = records.value

	if (filterMode.value === 'linked') {
		rows = rows.filter((row) => resource.value?.summaryFields?.some((field) => row[field.key]))
	} else if (filterMode.value === 'gaps') {
		rows = rows.filter((row) => resource.value?.summaryFields?.some((field) => !row[field.key]))
	}

	if (!query) return rows

	const keys = ['name', ...(resource.value?.summaryFields || []).map((field) => field.key)]
	return rows.filter((row) => keys.some((key) => String(row[key] || '').toLowerCase().includes(query)))
})

const treeRows = computed(() => {
	if (!isTreeResource.value) return []

	const tree = resource.value.tree
	const parentField = tree.parentField
	const query = searchQuery.value.trim().toLowerCase()
	let sourceRows = records.value

	if (filterMode.value === 'linked') {
		sourceRows = sourceRows.filter((row) => resource.value?.summaryFields?.some((field) => row[field.key]))
	} else if (filterMode.value === 'gaps') {
		sourceRows = sourceRows.filter((row) => resource.value?.summaryFields?.some((field) => !row[field.key]))
	}

	const rowByName = new Map(sourceRows.map((row) => [row.name, row]))
	const keys = ['name', ...(resource.value?.summaryFields || []).map((field) => field.key)]
	const included = new Set()

	function includeWithParents(row) {
		if (!row?.name || included.has(row.name)) return
		included.add(row.name)
		const parent = rowByName.get(row[parentField])
		if (parent) includeWithParents(parent)
	}

	if (query) {
		sourceRows.forEach((row) => {
			if (keys.some((key) => String(row[key] || '').toLowerCase().includes(query))) {
				includeWithParents(row)
			}
		})
	} else {
		sourceRows.forEach((row) => included.add(row.name))
	}

	const childrenByParent = new Map()
	sourceRows.forEach((row) => {
		if (!included.has(row.name)) return
		const parent = row[parentField] || ''
		if (!childrenByParent.has(parent)) childrenByParent.set(parent, [])
		childrenByParent.get(parent).push(row)
	})

	const sortRows = (rows) => rows.sort((a, b) => {
		const leftA = Number(a.lft || 0)
		const leftB = Number(b.lft || 0)
		if (leftA || leftB) return leftA - leftB
		return String(a.title || a.name).localeCompare(String(b.title || b.name))
	})

	const result = []
	function walk(parent, depth = 0) {
		sortRows(childrenByParent.get(parent) || []).forEach((row) => {
			const childCount = (childrenByParent.get(row.name) || []).length
			result.push({ row, depth, childCount })
			if (expandedTreeNodes.value.has(row.name) || query) walk(row.name, depth + 1)
		})
	}

	walk('')

	if (!result.length) {
		sourceRows
			.filter((row) => included.has(row.name))
			.forEach((row) => result.push({ row, depth: 0, childCount: 0 }))
	}

	return result
})

const visibleRowCount = computed(() => (displayMode.value === 'tree' && isTreeResource.value ? treeRows.value.length : visibleRecords.value.length))

const showExternalContext = computed(() => props.scope === 'platform' && ['customers', 'sites'].includes(props.resourceKey))
const externalSystems = computed(() => [
	{
		label: 'Billing',
		icon: CreditCard,
		configured: Boolean(settingsContext.value?.billing_system),
		value: settingsContext.value?.billing_system || 'Not configured',
		button: 'Open Billing',
		description: 'Invoice status, payment state, plan, renewal, and finance notes are sourced from the billing system.',
		customerPlaceholder: 'Billing account, invoice status, balance, and renewal are pending integration data.',
	},
	{
		label: 'CRM',
		icon: Users,
		configured: Boolean(settingsContext.value?.crm_system),
		value: settingsContext.value?.crm_system || 'Not configured',
		button: 'Open CRM',
		description: 'Relationship owner, onboarding status, lifecycle stage, and contacts are sourced from CRM.',
		customerPlaceholder: 'CRM stage, onboarding state, contacts, and account notes are pending integration data.',
	},
	{
		label: 'Support',
		icon: LifeBuoy,
		configured: Boolean(settingsContext.value?.support_system),
		value: settingsContext.value?.support_system || 'Not configured',
		button: 'Open Support',
		description: 'Tickets, SLA state, escalations, and support handoff are sourced from the support system.',
		customerPlaceholder: 'Open tickets, last ticket state, SLA, and escalation status are pending integration data.',
	},
])
const lockedOperatorActions = computed(() => [
	{ label: 'Backup', value: props.resourceKey === 'sites' ? 'Qualified customer or platform-managed' : 'Site-level only' },
	{ label: 'Restore', value: props.resourceKey === 'sites' ? 'Qualified customer or platform-managed' : 'Site-level only' },
	{ label: 'Upgrade', value: props.resourceKey === 'sites' ? 'Qualified customer or platform-managed' : 'Site-level only' },
	{ label: 'Advanced DNS', value: props.resourceKey === 'sites' ? 'Qualified customer or platform-managed' : 'Site-level only' },
])

const stateModelRows = computed(() => {
	const common = [
		{ label: 'Approval state', value: 'Backend status source pending' },
		{ label: 'Provisioning state', value: 'Backend status source pending' },
		{ label: 'Audit trail', value: 'Event source pending' },
	]

	const byResource = {
		customers: [
			{ label: 'Customer', value: record.value?.name || 'No customer selected' },
			{ label: 'Subscription', value: 'Billing-system integration pending' },
			{ label: 'Support state', value: 'Support-system integration pending' },
		],
		'sites': [
			{ label: 'Site', value: record.value?.name || 'No site selected' },
			{ label: 'DNS Record', value: 'DNS lifecycle source pending' },
			{ label: 'Backup', value: 'Operator/request status pending' },
			{ label: 'Restore', value: 'Operator/request status pending' },
			{ label: 'Upgrade', value: 'Operator/request status pending' },
		],
		benches: [
			{ label: 'Bench', value: record.value?.name || 'No bench selected' },
			{ label: 'Release Group', value: record.value?.release_group || 'Not linked' },
			{ label: 'Tenant placement', value: record.value?.region || 'Placement source pending' },
		],
		'release-groups': [
			{ label: 'Release Group', value: record.value?.name || 'No release group selected' },
			{ label: 'Bench image management', value: 'Promotion/backend status pending' },
		],
		regions: [
			{ label: 'Region', value: record.value?.name || 'No region selected' },
			{ label: 'Tenant placement', value: record.value?.is_group ? 'Placement group' : 'Placement leaf' },
		],
	}

	return [...(byResource[props.resourceKey] || []), ...common]
})

const recentActivityRows = computed(() => [
	{ label: 'Last document update', value: record.value?.modified || 'Not available from current fields' },
	{ label: 'Last UI refresh', value: loading.value ? 'Loading' : 'Current session' },
	{ label: 'Infrastructure boundary', value: 'No infra mutation from this UI pass' },
])

const assistantContext = computed(() => {
	const gaps = []
	if (showExternalContext.value) {
		externalSystems.value.filter((system) => !system.configured).forEach((system) => gaps.push(`${system.label} system not configured`))
		gaps.push('SSO links are placeholders until configured outside LensCloud')
	}
	if (activeAction.value && !activeAction.value.backendSupported) gaps.push(`${activeAction.value.label} backend support is not wired`)
	if (props.resourceKey === 'sites') gaps.push('Provisioning, DNS, backup, restore, and upgrade status sources are pending')
	if (props.resourceKey === 'customers') gaps.push('Subscription, billing, CRM, and support data are integration placeholders')

	return {
		scope: props.scope,
		summary: record.value
			? `Guidance for ${resource.value?.label || 'record'} ${record.value.title || record.value.first_name || record.value.name}.`
			: `Guidance for the ${resource.value?.label || 'records'} ${displayMode.value === 'tree' ? 'tree' : 'list'} surface.`,
		badges: [resource.value?.doctype, displayMode.value === 'tree' && isTreeResource.value ? 'tree' : props.mode, activeAction.value ? activeAction.value.label : 'no action selected'].filter(Boolean),
		sections: [
			{ label: 'Selected record', value: record.value ? (record.value.title || record.value.first_name || record.value.name) : 'No record selected' },
			{ label: 'Current tab set', value: inspectorTabs.value.map((tab) => tab.label).join(', ') },
			{ label: 'Rows visible', value: `${visibleRowCount.value} of ${records.value.length}` },
			{ label: 'Infrastructure boundary', value: 'This frontend surfaces control-plane intent only; it does not mutate infrastructure.' },
		],
		gaps,
		nextSteps: activeAction.value
			? [
				activeAction.value.backendSupported ? 'Review action fields before capture.' : 'Treat this action as UI-only until backend support is connected.',
				'Use Status and External tabs to confirm lifecycle and commercial gaps.',
			]
			: [
				'Review Summary and Status before taking action.',
				showExternalContext.value ? 'Use External tab for Billing, CRM, and Support context.' : 'Open a record to inspect detailed context.',
			],
	}
})

const filterOptions = computed(() => [
	{ label: 'All records', onClick: () => { filterMode.value = 'all' } },
	{ label: 'Linked records', onClick: () => { filterMode.value = 'linked' } },
	{ label: 'Records with gaps', onClick: () => { filterMode.value = 'gaps' } },
])

const listActions = computed(() => [
	{ label: 'Refresh', onClick: load },
	{ label: 'Clear search', onClick: () => { searchQuery.value = ''; filterMode.value = 'all' } },
])

async function loadCustomerContext() {
	if (!resource.value?.customerScoped && props.scope !== 'customer') return null

	const customerRecords = await listDocs('Customer', {
		fields: ['name', 'first_name', 'last_name', 'region', 'external_customer_id'],
		limit: 1,
		filters: [['user', '=', session.user]],
	})

	customerContext.value = customerRecords[0] || null
	return customerContext.value
}

async function loadSettingsContext() {
	if (!showExternalContext.value) {
		settingsContext.value = null
		return
	}

	settingsContext.value = await getDoc(platformSettings.doctype, platformSettings.doctype).catch(() => null)
}

async function loadList() {
	if (!resource.value) return

	const filters = []
	if (resource.value.customerScoped) {
		const customer = await loadCustomerContext()
		if (customer?.name) filters.push(['customer', '=', customer.name])
	}

	const fieldKeys = new Set([
		'name',
		...resource.value.summaryFields.map((field) => field.key),
		...(resource.value.detailFields || []).map((field) => field.key),
		...(resource.value.tree?.extraFields || []),
	])

	records.value = await listDocs(resource.value.doctype, {
		fields: [...fieldKeys],
		limit: resource.value.listLimit || 20,
		filters: filters.length ? filters : undefined,
		orderBy: resource.value.tree?.orderBy,
	})

	if (resource.value.tree && !expandedTreeNodes.value.size) {
		const roots = records.value.filter((row) => !row[resource.value.tree.parentField]).map((row) => row.name)
		expandedTreeNodes.value = new Set(roots)
	}
}

async function loadDetail(name) {
	if (!resource.value || !name) {
		record.value = null
		related.value = []
		return
	}

	record.value = await getDoc(resource.value.doctype, name)
	related.value = []

	if (record.value && resource.value.editable) {
		for (const key of Object.keys(formState)) delete formState[key]
		for (const field of resource.value.detailFields || []) {
			formState[field.key] = record.value[field.key] ?? ''
		}
	}

	if (resource.value.customerScoped && customerContext.value?.name && record.value?.customer && record.value.customer !== customerContext.value.name) {
		record.value = null
		throw new Error('This site is not linked to your customer record.')
	}

	related.value = await Promise.all((resource.value.relations || []).map(async (relation) => {
		const linkField = relation.linkField || relation.field || 'name'
		const sourceField = relation.sourceField || relation.useFieldAsFilter || 'name'
		const sourceValue = sourceField === 'name' ? record.value.name : record.value[sourceField] || record.value.name
		const items = await listDocs(relation.doctype, {
			fields: ['name', ...relation.fields],
			limit: 5,
			filters: [[linkField, '=', sourceValue]],
		})

		return { label: relation.label, items, previewFields: relation.fields.slice(0, 2), route: relation.route }
	}))
}

async function load() {
	loading.value = !records.value.length
	error.value = null
	related.value = []
	try {
		await Promise.all([loadList(), loadSettingsContext()])
		const previewName = route.params.name || (props.mode === 'list' ? records.value[0]?.name : '')
		await loadDetail(previewName)
	} catch (err) {
		error.value = err?.message || 'Unable to load records.'
	} finally {
		loading.value = false
	}
}

onMounted(load)
watch(() => [props.mode, props.resourceKey, route.params.name, props.scope], load)
watch(isTreeResource, (enabled) => {
	displayMode.value = enabled ? 'tree' : 'list'
	expandedTreeNodes.value = new Set()
}, { immediate: true })

const title = computed(() => resource.value?.label || 'Records')
const subtitle = computed(() => resource.value?.listHelp || 'Native Frappe document surface.')
const activeAction = computed(() => (resource.value?.actions || []).find((action) => action.key === activeActionKey.value) || null)
const inspectorTabs = computed(() => {
	const tabs = [
		{ label: 'Summary' },
		{ label: 'Fields' },
		{ label: 'Status' },
	]

	if (showExternalContext.value) tabs.push({ label: 'External' })

	tabs.push(
		{ label: `Actions${resource.value?.actions?.length ? ` (${resource.value.actions.length})` : ''}` },
		{ label: `Related${related.value.length ? ` (${related.value.length})` : ''}` },
	)

	return tabs
})

function selectAction(action) {
	activeActionKey.value = activeActionKey.value === action.key ? '' : action.key
	for (const key of Object.keys(actionState)) delete actionState[key]
}

function setDisplayMode(mode) {
	displayMode.value = mode
}

function toggleTreeNode(name) {
	const next = new Set(expandedTreeNodes.value)
	if (next.has(name)) next.delete(name)
	else next.add(name)
	expandedTreeNodes.value = next
}

function selectTreeRow(row) {
	if (!resource.value?.detailRoute) return
	router.push(resource.value.detailRoute(row.name))
	loadDetail(row.name).catch((err) => {
		error.value = err?.message || 'Unable to load region.'
	})
}

function assignActionField(field, value) {
	actionState[field] = value
}

async function saveCurrentRecord() {
	if (!record.value || !resource.value) return

	saveState.value = 'saving'
	try {
		const saved = await saveDoc(resource.value.doctype, record.value.name, formState)
		record.value = saved
		await load()
		saveState.value = 'saved'
	} catch (err) {
		saveState.value = 'error'
		error.value = err?.message || 'Unable to save record.'
	}
}
</script>

<template>
	<WorkspaceLayout
		:title="title"
		:subtitle="subtitle"
		inspector-kicker="Doctype inspector"
		:inspector-title="record ? (record.title || record.first_name || record.name || resource.label) : resource.label"
		:inspector-subtitle="mode === 'detail' && record ? 'Update fields, review related records, and surface request entry points from this rail.' : 'Open a record to inspect editable fields and related data.'"
		assistant-label="Assistant"
		assistant-hint="This drawer will eventually provide context-aware help for the selected doctype, record, and action path."
		:assistant-context="assistantContext"
	>
		<template #actions>
			<Badge class="bg-surface-gray-2 text-ink-gray-6">{{ displayMode === 'tree' && isTreeResource ? 'Tree view' : (mode === 'detail' ? 'Detail view' : 'List view') }}</Badge>
			<Button variant="subtle" @click="load">Refresh</Button>
		</template>

		<template #main>
			<div class="flex h-full min-h-0 flex-col p-4">
				<Alert v-if="error" theme="red" title="Surface gap" :message="error" />

				<div class="flex min-h-0 flex-1 flex-col overflow-hidden rounded border border-outline-gray-2 bg-surface-white">
				<div class="flex shrink-0 items-center justify-between gap-2 border-b border-outline-gray-2 bg-surface-gray-1 px-3 py-2">
					<div class="flex min-w-0 flex-1 items-center gap-2">
						<TextInput v-model="searchQuery" class="max-w-xs" variant="subtle" :placeholder="displayMode === 'tree' ? 'Search tree' : 'Search list'">
							<template #prefix><Search class="size-4 text-ink-gray-4" /></template>
						</TextInput>
						<div v-if="isTreeResource" class="flex shrink-0 rounded border border-outline-gray-2 bg-surface-white p-0.5">
							<Button size="sm" :variant="displayMode === 'list' ? 'subtle' : 'ghost'" class="h-7" @click="setDisplayMode('list')">
								<List class="size-4" />
								List
							</Button>
							<Button size="sm" :variant="displayMode === 'tree' ? 'subtle' : 'ghost'" class="h-7" @click="setDisplayMode('tree')">
								<FolderTree class="size-4" />
								Tree
							</Button>
						</div>
						<Badge v-if="filterMode !== 'all'" class="bg-surface-gray-2 text-ink-gray-6">{{ filterMode }}</Badge>
					</div>
					<div class="flex shrink-0 items-center gap-2">
						<Badge class="bg-surface-white text-ink-gray-7">{{ visibleRowCount }} / {{ records.length }}</Badge>
						<Dropdown :options="filterOptions"><Button variant="subtle" :icon="Filter">Filter</Button></Dropdown>
						<Dropdown :options="listActions"><Button variant="ghost" :icon="MoreHorizontal" /></Dropdown>
					</div>
				</div>

				<div v-if="loading" class="px-4 py-3 text-sm text-ink-gray-5">Loading records...</div>

				<div v-else-if="displayMode === 'tree' && isTreeResource" class="min-h-0 flex-1 overflow-auto">
					<div v-if="!treeRows.length" class="flex h-full flex-col items-center justify-center px-4 text-center">
						<div class="grid size-9 place-items-center rounded bg-surface-gray-2 text-ink-gray-5">
							<FolderTree class="size-4" />
						</div>
						<p class="mt-3 text-sm font-medium text-ink-gray-9">No regions yet</p>
						<p class="mt-1 max-w-sm text-sm leading-5 text-ink-gray-5">Region is a tree doctype. Once records exist, parent regions and child regions will appear here.</p>
						<Button class="mt-3" variant="subtle" @click="load">Refresh</Button>
					</div>

					<div v-else class="divide-y divide-outline-gray-1">
						<div
							v-for="item in treeRows"
							:key="item.row.name"
							class="flex min-h-10 cursor-pointer items-center gap-2 px-3 py-2 transition hover:bg-surface-gray-1"
							:class="{ 'bg-surface-gray-1': selectedName === item.row.name }"
							:style="{ paddingLeft: `${12 + item.depth * 24}px` }"
							@click="selectTreeRow(item.row)"
						>
							<Button
								variant="ghost"
								size="sm"
								class="size-6 shrink-0"
								:disabled="!item.childCount"
								@click.stop="toggleTreeNode(item.row.name)"
							>
								<component :is="expandedTreeNodes.has(item.row.name) || searchQuery ? ChevronDown : ChevronRight" class="size-4" :class="!item.childCount ? 'text-transparent' : 'text-ink-gray-5'" />
							</Button>
							<MapPin class="size-4 shrink-0 text-ink-gray-5" />
							<div class="min-w-0 flex-1">
								<div class="truncate text-sm font-medium text-ink-gray-9">{{ item.row.title || item.row.name }}</div>
								<div class="truncate text-xs text-ink-gray-5">{{ item.row.name }}</div>
							</div>
							<Badge v-if="item.row.is_group" class="bg-surface-gray-2 text-ink-gray-6">Group</Badge>
							<Badge v-if="item.childCount" class="bg-surface-white text-ink-gray-7">{{ item.childCount }}</Badge>
						</div>
					</div>
				</div>

				<ListView
					v-else
					class="min-h-0 flex-1"
					:columns="listColumns"
					:rows="visibleRecords"
					row-key="name"
					:options="{
						getRowRoute: (row) => resource.detailRoute(row.name),
						selectable: true,
						showTooltip: true,
						resizeColumn: true,
						emptyState: {
							title: mode === 'detail' ? 'No related records yet' : 'No records yet',
							description: mode === 'detail'
								? 'Open a different record or refresh the list to see related context.'
								: 'This surface is ready, but the current user does not have any matching records yet.',
							button: { label: 'Refresh', variant: 'subtle', onClick: load },
						},
					}"
				/>
				</div>
			</div>
		</template>

		<template #inspector>
			<Tabs
				v-model="inspectorTab"
				as="div"
				:tabs="inspectorTabs"
				class="h-full [&_[role='tab']]:py-2 [&_[role='tab']]:text-sm [&_[role='tablist']]:gap-4 [&_[role='tablist']]:px-1 [&_[role='tabpanel']]:px-1 [&_[role='tabpanel']]:py-3"
			>
				<template #tab-panel="{ tab }">
					<div v-if="tab.label.startsWith('Summary')" class="space-y-3">
						<div class="rounded border border-outline-gray-2 bg-surface-gray-1 p-3">
							<div class="flex items-start justify-between gap-3">
								<div class="min-w-0">
									<p class="text-xs font-medium text-ink-gray-5">Record</p>
									<p class="mt-1 truncate text-sm font-medium text-ink-gray-9">{{ record ? (record.title || record.first_name || record.name) : 'No record selected' }}</p>
								</div>
								<Badge class="bg-surface-white text-ink-gray-7">{{ record ? 'Loaded' : 'Pending' }}</Badge>
							</div>
						</div>

						<div class="grid gap-2">
							<div class="flex items-center justify-between rounded border border-outline-gray-2 bg-surface-white px-3 py-2">
								<span class="text-sm text-ink-gray-5">Doctype</span>
								<span class="truncate text-sm font-medium text-ink-gray-9">{{ resource.doctype }}</span>
							</div>
							<div class="flex items-center justify-between rounded border border-outline-gray-2 bg-surface-white px-3 py-2">
								<span class="text-sm text-ink-gray-5">Mode</span>
								<span class="text-sm font-medium text-ink-gray-9">{{ displayMode === 'tree' && isTreeResource ? 'tree' : mode }}</span>
							</div>
							<div class="flex items-center justify-between rounded border border-outline-gray-2 bg-surface-white px-3 py-2">
								<span class="text-sm text-ink-gray-5">Rows</span>
								<span class="text-sm font-medium text-ink-gray-9">{{ visibleRowCount }} / {{ records.length }}</span>
							</div>
							<div class="rounded border border-outline-gray-2 bg-surface-white px-3 py-2">
								<p class="text-sm text-ink-gray-5">Selected row</p>
								<p class="mt-1 truncate text-sm font-medium text-ink-gray-9">{{ selectedName || '-' }}</p>
							</div>
						</div>
					</div>

					<div v-else-if="tab.label.startsWith('Fields')" class="space-y-3">
						<div v-if="!record" class="rounded border border-dashed border-outline-gray-2 bg-surface-gray-1 p-3">
							<p class="text-sm font-medium text-ink-gray-8">No record selected</p>
							<p class="mt-1 text-sm leading-5 text-ink-gray-5">Choose a row to inspect fields here.</p>
						</div>

						<template v-else>
							<div class="flex items-center justify-between gap-2">
								<div>
									<p class="text-sm font-medium text-ink-gray-9">Fields</p>
									<p class="text-xs text-ink-gray-5">{{ resource.editable ? 'Editable via standard Frappe document save.' : 'Read-only for this first pass.' }}</p>
								</div>
								<Badge class="bg-surface-gray-2 text-ink-gray-6">{{ resource.editable ? 'Editable' : 'Read only' }}</Badge>
							</div>

							<div class="space-y-2">
								<div v-for="field in resource.detailFields || []" :key="field.key" class="space-y-1">
									<label class="text-xs font-medium text-ink-gray-5">{{ field.label }}</label>
									<TextInput
										v-if="resource.editable && field.key !== 'notes'"
										v-model="formState[field.key]"
										:placeholder="field.label"
										variant="subtle"
										class="w-full"
									/>
									<Textarea
										v-else-if="resource.editable"
										v-model="formState[field.key]"
										:placeholder="field.label"
										variant="subtle"
										class="w-full"
									/>
									<div v-else class="truncate rounded bg-surface-gray-1 px-2.5 py-1.5 text-sm text-ink-gray-7">
										{{ formatFieldValue(record[field.key]) }}
									</div>
								</div>
							</div>

							<div v-if="resource.editable" class="flex flex-wrap items-center gap-2 border-t border-outline-gray-2 pt-3">
								<Button size="sm" :label="saveState === 'saving' ? 'Saving...' : 'Save'" :disabled="saveState === 'saving'" @click="saveCurrentRecord" />
								<Badge v-if="saveState === 'saved'" class="bg-emerald-50 text-emerald-700">Saved</Badge>
								<Badge v-else-if="saveState === 'error'" class="bg-red-50 text-red-700">Failed</Badge>
							</div>
						</template>
					</div>

					<div v-else-if="tab.label.startsWith('Status')" class="space-y-3">
						<div class="rounded border border-outline-gray-2 bg-surface-gray-1 p-3">
							<div class="flex items-start justify-between gap-3">
								<div>
									<p class="text-sm font-medium text-ink-gray-9">State model alignment</p>
									<p class="mt-1 text-xs leading-5 text-ink-gray-5">This tab exposes documented lifecycle vocabulary without inventing backend state or infrastructure behavior.</p>
								</div>
								<Badge class="bg-surface-white text-ink-gray-7">Read only</Badge>
							</div>
						</div>

						<div class="rounded border border-outline-gray-2 bg-surface-white">
							<div class="border-b border-outline-gray-2 bg-surface-gray-1 px-3 py-2">
								<p class="text-sm font-medium text-ink-gray-9">Lifecycle state</p>
							</div>
							<div class="p-2">
								<div v-for="row in stateModelRows" :key="row.label" class="flex items-center justify-between gap-3 rounded px-2 py-1.5">
									<span class="text-sm text-ink-gray-5">{{ row.label }}</span>
									<span class="truncate text-sm font-medium text-ink-gray-9">{{ row.value }}</span>
								</div>
							</div>
						</div>

						<div class="rounded border border-outline-gray-2 bg-surface-white">
							<div class="border-b border-outline-gray-2 bg-surface-gray-1 px-3 py-2">
								<p class="text-sm font-medium text-ink-gray-9">Recent activity</p>
							</div>
							<div class="p-2">
								<div v-for="row in recentActivityRows" :key="row.label" class="flex items-center justify-between gap-3 rounded px-2 py-1.5">
									<span class="text-sm text-ink-gray-5">{{ row.label }}</span>
									<span class="truncate text-sm font-medium text-ink-gray-9">{{ row.value }}</span>
								</div>
							</div>
						</div>
					</div>

					<div v-else-if="tab.label.startsWith('External')" class="space-y-3">
						<div class="rounded border border-outline-gray-2 bg-surface-gray-1 p-3">
							<div class="flex items-start justify-between gap-3">
								<div>
									<p class="text-sm font-medium text-ink-gray-9">Platform agent context</p>
									<p class="mt-1 text-xs leading-5 text-ink-gray-5">Billing, CRM, and Support summaries are sourced from configured external systems. SSO setup is external to this frontend.</p>
								</div>
								<Badge class="bg-surface-white text-ink-gray-7">Platform only</Badge>
							</div>
						</div>

						<div v-for="system in externalSystems" :key="system.label" class="rounded border border-outline-gray-2 bg-surface-white p-3">
							<div class="flex items-start justify-between gap-3">
								<div class="flex min-w-0 items-start gap-2">
									<component :is="system.icon" class="mt-0.5 size-4 shrink-0 text-ink-gray-5" />
									<div class="min-w-0">
										<p class="text-sm font-medium text-ink-gray-9">{{ system.label }}</p>
										<p class="mt-1 truncate text-xs text-ink-gray-5">{{ system.value }}</p>
									</div>
								</div>
								<Badge :class="system.configured ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'">{{ system.configured ? 'Configured' : 'Missing' }}</Badge>
							</div>
							<p class="mt-2 text-xs leading-5 text-ink-gray-5">{{ system.description }}</p>
							<div class="mt-3 rounded border border-dashed border-outline-gray-2 bg-surface-gray-1 px-3 py-2">
								<p class="text-xs leading-5 text-ink-gray-5">{{ system.customerPlaceholder }}</p>
							</div>
							<div class="mt-3 flex flex-wrap items-center gap-2 border-t border-outline-gray-2 pt-3">
								<Button size="sm" variant="subtle" disabled>{{ system.button }}</Button>
								<Badge class="bg-surface-gray-2 text-ink-gray-6">SSO pending</Badge>
							</div>
						</div>

						<div v-if="props.resourceKey === 'sites'" class="rounded border border-outline-gray-2 bg-surface-white p-3">
							<div class="flex items-center gap-2">
								<Lock class="size-4 text-ink-gray-5" />
								<p class="text-sm font-medium text-ink-gray-9">Customer qualification</p>
							</div>
							<div class="mt-3 space-y-2">
								<div v-for="item in lockedOperatorActions" :key="item.label" class="flex items-center justify-between gap-3 rounded border border-outline-gray-2 bg-surface-gray-1 px-3 py-2">
									<span class="text-sm text-ink-gray-7">{{ item.label }}</span>
									<Badge class="bg-surface-white text-ink-gray-7">{{ item.value }}</Badge>
								</div>
							</div>
						</div>
					</div>

					<div v-else-if="tab.label.startsWith('Actions')" class="space-y-3">
						<div v-if="!(resource.actions || []).length" class="rounded border border-dashed border-outline-gray-2 bg-surface-gray-1 p-3">
							<p class="text-sm font-medium text-ink-gray-8">No action entry points</p>
							<p class="mt-1 text-sm leading-5 text-ink-gray-5">This doctype has no lifecycle actions in the first pass.</p>
						</div>

						<template v-else>
							<div class="grid gap-2">
								<Button
									v-for="action in resource.actions || []"
									:key="action.key"
									variant="subtle"
									class="h-7 justify-start"
									@click="selectAction(action)"
								>
									{{ action.label }}
								</Button>
							</div>

							<div v-if="activeAction" class="rounded border border-outline-gray-2 bg-surface-gray-1 p-3">
								<div class="flex items-start justify-between gap-2">
									<div>
										<p class="text-sm font-medium text-ink-gray-9">{{ activeAction.label }}</p>
										<p class="mt-1 text-xs leading-5 text-ink-gray-5">{{ activeAction.description }}</p>
									</div>
									<Badge class="bg-surface-white text-ink-gray-7">{{ activeAction.backendSupported ? 'Ready' : 'UI only' }}</Badge>
								</div>

								<div class="mt-3 space-y-2">
									<div v-for="field in activeAction.fields || []" :key="field.key" class="space-y-1">
										<label class="text-xs font-medium text-ink-gray-5">{{ field.label }}</label>
										<TextInput
											v-if="field.type !== 'textarea'"
											v-model="actionState[field.key]"
											:placeholder="field.placeholder"
											variant="subtle"
											class="w-full"
										/>
										<Textarea
											v-else
											v-model="actionState[field.key]"
											:placeholder="field.placeholder"
											variant="subtle"
											class="w-full"
										/>
									</div>
								</div>

								<div class="mt-3 flex flex-wrap items-center gap-2 border-t border-outline-gray-2 pt-3">
									<Button size="sm" variant="subtle" :disabled="!activeAction.backendSupported">Capture request</Button>
									<Badge v-if="!activeAction.backendSupported" class="bg-amber-50 text-amber-700">Backend gap</Badge>
								</div>
							</div>
						</template>
					</div>

					<div v-else class="space-y-3">
						<div v-if="!related.length" class="rounded border border-dashed border-outline-gray-2 bg-surface-gray-1 p-3">
							<p class="text-sm font-medium text-ink-gray-8">No related records</p>
							<p class="mt-1 text-sm leading-5 text-ink-gray-5">Related records will appear here when the selected document has linked context.</p>
						</div>

						<div v-for="relation in related" v-else :key="relation.label" class="rounded border border-outline-gray-2 bg-surface-white">
							<div class="flex items-center justify-between gap-2 border-b border-outline-gray-2 bg-surface-gray-1 px-3 py-2">
								<p class="text-sm font-medium text-ink-gray-9">{{ relation.label }}</p>
								<Badge class="bg-surface-white text-ink-gray-7">{{ relation.items.length }}</Badge>
							</div>
							<div class="p-2">
								<p v-if="!relation.items.length" class="px-1 py-2 text-sm leading-5 text-ink-gray-5">No related records found.</p>
								<RouterLink
									v-for="item in relation.items"
									v-else
									:key="item.name"
									:to="relation.route(item.name)"
									class="block rounded px-2 py-1.5 text-sm transition hover:bg-surface-gray-1"
								>
									<div class="truncate font-medium text-ink-gray-9">{{ item.title || item.first_name || item.name }}</div>
									<div class="truncate text-xs text-ink-gray-5">{{ item.name }}</div>
								</RouterLink>
							</div>
						</div>
					</div>
				</template>
			</Tabs>
		</template>
	</WorkspaceLayout>
</template>
