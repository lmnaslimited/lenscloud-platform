<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { Alert, Autocomplete, Badge, Button, Dropdown, FormControl, ListHeader, ListHeaderItem, ListRows, ListView, Popover, Tabs, TextInput } from 'frappe-ui'
import { listDocs, getDoc, saveDoc, createDoc, submitDoc, cancelDoc, callMethod, formatFieldValue } from '@/lib/api'
import { getResourceByDoctype, getResourceByKey, platformSettings } from '@/lib/catalog'
import { useSessionStore } from '@/lib/session'
import WorkspaceLayout from '@/components/WorkspaceLayout.vue'
import DocumentLayoutEditor from '@/components/DocumentLayoutEditor.vue'
import { ChevronDown, ChevronRight, CreditCard, Filter, FolderTree, LifeBuoy, List, Lock, MapPin, Maximize2, Minimize2, MoreHorizontal, Search, X } from 'lucide-vue-next'

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
const listFilters = ref({})
const draftFilterRows = ref([])
const sortState = reactive({ field: '', direction: 'asc' })
const inspectorTab = ref(0)
const displayMode = ref('list')
const expandedTreeNodes = ref(new Set())
const formState = reactive({})
const actionState = reactive({})
const createForm = reactive({})
const fieldOptions = reactive({})
const editorSchema = ref([])
const editorMeta = ref({})
const renameMode = ref(false)
const renameValue = ref('')
const renameState = ref('idle')
const isCreating = ref(false)
const editorHeight = ref(58)
const editorExpanded = ref(false)
const lifecycleState = ref('idle')
const actionExecutionState = ref('idle')
const actionResult = ref(null)
const actionRawResult = ref(null)
const actionFailure = ref(null)

const selectedName = computed(() => route.params.name || record.value?.name || '')
const isTreeResource = computed(() => Boolean(resource.value?.tree))

const listColumns = computed(() => {
	if (!resource.value) return []

	return [
		{ label: 'Name', key: 'name', width: '240px', type: 'text' },
		...resource.value.summaryFields.map((field) => ({
			...field,
			width: field.width || '180px',
		})),
	]
})

const allResourceFields = computed(() => {
	if (!resource.value) return []
	const fields = [
		{ key: 'name', label: 'Name', type: 'link', options: resource.value.doctype },
		...(resource.value.summaryFields || []),
		...(resource.value.detailFields || []),
		...(resource.value.lifecycleFields || []),
	]
	return fields.filter((field, index, source) => field.key && source.findIndex((item) => item.key === field.key) === index)
})

const filterDocFields = computed(() => allResourceFields.value.map((field) => ({
	fieldname: field.key,
	label: field.label || field.key,
	fieldtype: frappeFieldType(field),
	options: filterOptionsForField(field),
})))

const filterFieldOptions = computed(() => filterDocFields.value.map((field) => ({
	label: field.label,
	value: field.fieldname,
	description: field.fieldtype,
})))

const activeFilterEntries = computed(() => Object.entries(listFilters.value).filter(([field, [operator, value]]) => isFilterReady(field, operator, value)))
const appliedFilterCount = computed(() => activeFilterEntries.value.length)

function filterOptionsForField(field = {}) {
	if (Array.isArray(field.options)) return field.options.map((option) => (typeof option === 'object' ? option.value || option.label : option)).filter(Boolean).join('\n')
	return field.options || ''
}

function frappeFieldType(field = {}) {
	if (field.type === 'link') return 'Link'
	if (field.type === 'check') return 'Check'
	if (field.type === 'number') return 'Int'
	if (field.type === 'select' || Array.isArray(field.options)) return 'Select'
	return 'Data'
}

function rowTitle(row) {
	return row?.title || row?.first_name || row?.image_tag || row?.cluster_name || row?.plan_code || row?.name || ''
}

function setFilter(field, operator, value, source = '') {
	if (!field || value === undefined || value === null || value === '') return
	const nextFilters = { ...listFilters.value }
	nextFilters[field] = source ? [operator, value, source] : [operator, value]
	listFilters.value = nextFilters
	draftFilterRows.value = filtersToDraftRows(nextFilters)
}

function clearFilters() {
	listFilters.value = {}
	draftFilterRows.value = []
	searchQuery.value = ''
}

function clearAppliedFilter(field) {
	const nextFilters = { ...listFilters.value }
	delete nextFilters[field]
	listFilters.value = nextFilters
	draftFilterRows.value = filtersToDraftRows(nextFilters)
}

function filterChipLabel(field, operator, value) {
	const label = fieldMeta(field).label || field
	return `${label} ${operator} ${value}`
}


function operatorOptionsForField(fieldname) {
	const fieldtype = frappeFieldType(fieldMeta(fieldname))
	if (['Data', 'Long Text', 'Small Text', 'Text', 'Text Editor', 'JSON', 'Code', 'Link'].includes(fieldtype)) {
		return [
			{ label: 'Equals', value: '=' },
			{ label: 'Not Equals', value: '!=' },
			{ label: 'Like', value: 'like' },
			{ label: 'Not Like', value: 'not like' },
		]
	}
	if (['Int', 'Float'].includes(fieldtype)) {
		return [
			{ label: 'Equals', value: '=' },
			{ label: 'Not Equals', value: '!=' },
			{ label: '<', value: '<' },
			{ label: '>', value: '>' },
			{ label: '<=', value: '<=' },
			{ label: '>=', value: '>=' },
		]
	}
	return [
		{ label: 'Equals', value: '=' },
		{ label: 'Not Equals', value: '!=' },
	]
}

function defaultOperatorForField(fieldname) {
	const fieldtype = frappeFieldType(fieldMeta(fieldname))
	return ['Data', 'Long Text', 'Small Text', 'Text', 'Text Editor', 'JSON', 'Code'].includes(fieldtype) ? 'like' : '='
}

function defaultValueForField(fieldname) {
	const field = fieldMeta(fieldname)
	const fieldtype = frappeFieldType(field)
	if (fieldtype === 'Check') return 'Yes'
	if (fieldtype === 'Select') return filterValueOptions(fieldname)[0]?.value || ''
	return ''
}

function filterValueOptions(fieldname) {
	const field = fieldMeta(fieldname)
	const fieldtype = frappeFieldType(field)
	if (fieldname === 'name') {
		return records.value.map((row) => ({
			label: rowTitle(row) && rowTitle(row) !== row.name ? `${rowTitle(row)} · ${row.name}` : row.name,
			value: row.name,
		}))
	}
	if (fieldtype === 'Check') return [{ label: 'Yes', value: 'Yes' }, { label: 'No', value: 'No' }]
	if (fieldtype === 'Select') return filterOptionsForField(field).split('\n').filter(Boolean).map((option) => ({ label: option, value: option }))
	if (fieldtype === 'Link') return optionsForField(field)
	return []
}

function filtersToDraftRows(filters) {
	return Object.entries(filters).map(([field, [operator, value]]) => ({ field, operator, value }))
}

function addDraftFilter() {
	draftFilterRows.value = [...draftFilterRows.value, { field: '', operator: '=', value: '' }]
}

function removeDraftFilter(index) {
	draftFilterRows.value = draftFilterRows.value.filter((_, rowIndex) => rowIndex !== index)
}

function updateDraftField(row, selected) {
	const field = selected?.value || selected || ''
	row.field = field
	row.operator = defaultOperatorForField(field)
	row.value = defaultValueForField(field)
}

function updateDraftOperator(row, selected) {
	row.operator = selected?.value || selected || '='
	applyDraftFiltersIfReady()
}

function updateDraftValue(row, value) {
	row.value = value?.value ?? value ?? ''
	applyDraftFiltersIfReady()
}

function resetDraftFilters() {
	draftFilterRows.value = filtersToDraftRows(listFilters.value)
}

function appliedFiltersFromDraft() {
	const next = {}
	for (const row of draftFilterRows.value) {
		if (!isFilterReady(row.field, row.operator, row.value)) continue
		next[row.field] = [row.operator, row.value]
	}
	return next
}

function applyDraftFilters() {
	listFilters.value = appliedFiltersFromDraft()
}

function applyDraftFiltersIfReady() {
	listFilters.value = appliedFiltersFromDraft()
}

function normalizeValue(value) {
	return String(value ?? '').toLowerCase()
}

function fieldMeta(field) {
	return allResourceFields.value.find((item) => item.key === field) || {}
}

function isFilterReady(field, operator, value) {
	if (!field || !operator || value === undefined || value === null) return false
	const meta = fieldMeta(field)
	if (String(value) === '' && !['Check', 'Select'].includes(frappeFieldType(meta))) return false
	return true
}

function filterMatches(row, field, operator, value) {
	const raw = field === 'name' ? row.name : row[field]
	const left = normalizeValue(raw)
	const right = normalizeValue(value)
	const leftNumber = Number(raw)
	const rightNumber = Number(value)
	const canCompareNumber = !Number.isNaN(leftNumber) && !Number.isNaN(rightNumber)
	switch (operator) {
		case '=':
			return left === right
		case '!=':
			return left !== right
		case '<':
			return canCompareNumber ? leftNumber < rightNumber : left < right
		case '>':
			return canCompareNumber ? leftNumber > rightNumber : left > right
		case '<=':
			return canCompareNumber ? leftNumber <= rightNumber : left <= right
		case '>=':
			return canCompareNumber ? leftNumber >= rightNumber : left >= right
		case 'not like':
			return !left.includes(right.replaceAll('%', ''))
		case 'like':
		default:
			return left.includes(right.replaceAll('%', ''))
	}
}

function applyRecordFilters(rows) {
	const query = searchQuery.value.trim().toLowerCase()
	const keys = ['name', ...(resource.value?.summaryFields || []).map((field) => field.key)]
	const entries = Object.entries(listFilters.value).filter(([field, [operator, value]]) => isFilterReady(field, operator, value))
	return rows.filter((row) => {
		const queryMatch = !query || keys.some((key) => normalizeValue(key === 'name' ? rowTitle(row) || row.name : row[key]).includes(query))
		return queryMatch && entries.every(([field, [operator, value]]) => filterMatches(row, field, operator, value))
	})
}

function compareRows(a, b, field) {
	const av = field === 'name' ? rowTitle(a) || a.name : a[field]
	const bv = field === 'name' ? rowTitle(b) || b.name : b[field]
	const na = Number(av)
	const nb = Number(bv)
	if (!Number.isNaN(na) && !Number.isNaN(nb) && String(av).trim() !== '' && String(bv).trim() !== '') return na - nb
	return String(av || '').localeCompare(String(bv || ''))
}

const visibleRecords = computed(() => {
	let rows = applyRecordFilters(records.value)
	if (sortState.field) {
		rows = [...rows].sort((a, b) => compareRows(a, b, sortState.field) * (sortState.direction === 'desc' ? -1 : 1))
	}
	return rows
})

const treeRows = computed(() => {
	if (!isTreeResource.value) return []

	const tree = resource.value.tree
	const parentField = tree.parentField
	const query = searchQuery.value.trim().toLowerCase()
	let sourceRows = applyRecordFilters(records.value)

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

const catalogLifecycleFields = computed(() => resource.value?.lifecycleFields || (resource.value?.detailFields || []).filter((field) => !['name', 'docstatus', 'amended_from'].includes(field.key)))
const catalogFieldMap = computed(() => new Map(catalogLifecycleFields.value.map((field) => [field.key, field])))
const frappeTypeMap = {
	'Data': 'text', 'Small Text': 'textarea', 'Long Text': 'textarea', 'Text': 'textarea', 'Text Editor': 'textarea', 'Code': 'textarea',
	'Link': 'link', 'Select': 'select', 'Check': 'check', 'Int': 'number', 'Float': 'number', 'Currency': 'number',
	'Date': 'date', 'Datetime': 'datetime', 'Table': 'table', 'Table MultiSelect': 'table_multiselect',
	'Section Break': 'section_break', 'Column Break': 'column_break', 'Tab Break': 'tab_break',
}
function schemaFieldToUi(field, override = {}) {
	const type = frappeTypeMap[field.fieldtype] || 'text'
	const value = {
		key: field.fieldname, label: field.label || field.fieldname, type,
		required: Boolean(field.required), readOnly: Boolean(field.read_only), default: field.default,
		description: field.description || '', collapsible: Boolean(field.collapsible),
	}
	if (type === 'select') value.options = String(field.options || '').split('\n').filter(Boolean)
	else if (type === 'link') value.options = field.options
	if (['table', 'table_multiselect'].includes(type)) {
		value.options = field.options
		const overrideColumns = new Map((override.columns || []).map((column) => [column.key, column]))
		value.columns = (field.columns || []).map((column) => schemaFieldToUi(column, overrideColumns.get(column.fieldname) || {}))
	}
	return { ...value, ...override, columns: value.columns || override.columns }
}
const namingField = computed(() => editorMeta.value.naming_field || '')
const canRenameDocument = computed(() => Boolean(record.value && editorMeta.value.allow_rename && namingField.value))
const editorLayoutFields = computed(() => {
	if (!editorSchema.value.length) return catalogLifecycleFields.value
	return editorSchema.value.map((field) => schemaFieldToUi(field, catalogFieldMap.value.get(field.fieldname) || {}))
})
const existingEditorLayoutFields = computed(() => editorLayoutFields.value.filter((field) => field.key !== namingField.value))
const documentLifecycleFields = computed(() => editorLayoutFields.value.filter((field) => !['section_break', 'column_break', 'tab_break'].includes(field.type)))
const lifecycleFieldMap = computed(() => new Map(documentLifecycleFields.value.map((field) => [field.key, field])))
const canCreateDocument = computed(() => props.scope === 'platform' && Boolean(resource.value?.creatable))
const canEditDocument = computed(() => Boolean(resource.value?.editable) && (!resource.value?.submittable || Number(record.value?.docstatus || 0) === 0))
const canSubmitDocument = computed(() => Boolean(resource.value?.submittable && record.value && Number(record.value.docstatus || 0) === 0))
const canCancelDocument = computed(() => Boolean(resource.value?.submittable && record.value && Number(record.value.docstatus || 0) === 1))
const canAmendDocument = computed(() => Boolean(resource.value?.submittable && record.value && Number(record.value.docstatus || 0) === 2))
const documentStatusLabel = computed(() => {
	if (!resource.value?.submittable) return record.value ? 'Saved' : 'No document'
	const status = Number(record.value?.docstatus || 0)
	if (status === 1) return 'Submitted'
	if (status === 2) return 'Cancelled'
	return 'Draft'
})

function resetCreateForm(source = {}) {
	for (const key of Object.keys(createForm)) delete createForm[key]
	for (const field of documentLifecycleFields.value) {
		createForm[field.key] = cloneFieldValue(source[field.key] ?? field.default ?? (['table', 'table_multiselect'].includes(field.type) ? [] : ''))
	}
	if (source.amended_from) createForm.amended_from = source.amended_from
}

function startCreate(source = {}) {
	resetCreateForm(source)
	isCreating.value = true
	lifecycleState.value = 'idle'
	error.value = null
}

function stopCreate() {
	isCreating.value = false
	resetCreateForm()
}

function buildDocumentPayload(source, includeNamingField = true) {
	const payload = {}
	for (const field of documentLifecycleFields.value) {
		if (field.readOnly || (!includeNamingField && field.key === namingField.value)) continue
		if (field.type === 'check') {
			payload[field.key] = source[field.key] ? 1 : 0
		} else if (['table', 'table_multiselect'].includes(field.type)) {
			payload[field.key] = (source[field.key] || []).map((row) => {
				const child = row.name ? { name: row.name } : {}
				for (const column of field.columns || []) child[column.key] = column.type === 'check' ? (row[column.key] ? 1 : 0) : (row[column.key] ?? '')
				return child
			})
		} else {
			payload[field.key] = source[field.key] ?? ''
		}
	}
	if (source.amended_from) payload.amended_from = source.amended_from
	return payload
}


function editableField(field) {
	return { ...(lifecycleFieldMap.value.get(field.key) || {}), ...field }
}

function fieldOptionKey(field) {
	return `${field.type || 'text'}:${field.options || field.key}`
}

function optionModelContext() {
	return isCreating.value ? createForm : formState
}

function optionLabelForDoc(doc, field) {
	const labelFields = field.labelFields || ['title', 'first_name', 'last_name', 'image_tag', 'cluster_name', 'plan_code']
	const label = labelFields.map((key) => doc[key]).filter(Boolean).join(' ')
	return label && label !== doc.name ? `${label} · ${doc.name}` : doc.name
}

async function loadEditorSchema() {
	editorSchema.value = []
	editorMeta.value = {}
	if (props.scope !== 'platform' || !resource.value?.doctype) return
	const response = await callMethod('lenscloud.api.launch.get_doctype_editor_schema', { doctype: resource.value.doctype })
	const schema = response.message || response || {}
	editorMeta.value = schema
	editorSchema.value = schema.fields || []
}

async function loadFieldOptions() {
	const actionFields = (resource.value?.actions || []).flatMap((action) => action.fields || [])
	const childFields = documentLifecycleFields.value.flatMap((field) => ['table', 'table_multiselect'].includes(field.type) ? field.columns || [] : [])
	const linkFields = [...allResourceFields.value, ...documentLifecycleFields.value, ...childFields, ...actionFields].filter((field) => field.type === 'link' && field.options)
	await Promise.all(linkFields.map(async (field) => {
		const key = fieldOptionKey(field)
		if (fieldOptions[key]) return

		const fields = Array.from(new Set(['name', ...(field.labelFields || []), ...(field.optionFields || [])]))
		const rows = await listDocs(field.options, {
			fields,
			limit: field.limit || 100,
			orderBy: field.orderBy || 'modified desc',
			filters: field.filters,
		}).catch(() => [])

		fieldOptions[key] = rows.map((row) => ({
			label: optionLabelForDoc(row, field),
			value: row.name,
			doc: row,
		}))
	}))
}

function optionsForField(field, model = optionModelContext()) {
	const options = fieldOptions[fieldOptionKey(field)] || []
	if (typeof field.optionFilter !== 'function') return options
	return options.filter((option) => field.optionFilter(option.doc || {}, model, props.resourceKey))
}

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
		{ label: 'Action evidence', value: 'Orchestration Action Log' },
	]

	const byResource = {
		customers: [
			{ label: 'Customer', value: record.value?.name || 'No customer selected' },
			{ label: 'Subscription', value: 'Billing-system integration pending' },
			{ label: 'Support state', value: 'Support-system integration pending' },
		],
		'sites': [
			{ label: 'Site', value: record.value?.name || 'No site selected' },
			{ label: 'Site status', value: record.value?.site_status || 'Draft/status source pending' },
			{ label: 'Provisioning status', value: record.value?.provisioning_status || 'Operator status pending' },
			{ label: 'Hostname reservation', value: record.value?.hostname_reservation_status || 'Pending' },
			{ label: 'Route status', value: record.value?.route_status || 'Not Checked' },
			{ label: 'TLS status', value: record.value?.tls_status || 'Inherited from wildcard edge' },
			{ label: 'Access URL', value: record.value?.access_url || 'Pending' },
			{ label: 'Backup', value: record.value?.backup_state || 'Operator/request status pending' },
			{ label: 'Restore', value: record.value?.restore_state || 'Operator/request status pending' },
			{ label: 'Upgrade', value: record.value?.upgrade_state || 'Operator/request status pending' },
		],
		benches: [
			{ label: 'Bench', value: record.value?.name || 'No bench selected' },
			{ label: 'Release Group', value: record.value?.release_group || 'Not linked' },
			{ label: 'Current Release', value: record.value?.current_release || 'Not linked' },
			{ label: 'Next Release', value: record.value?.next_release || 'Not scheduled' },
			{ label: 'Bench status', value: record.value?.bench_status || 'Draft/status source pending' },
			{ label: 'Upgrade/SOP status', value: record.value?.upgrade_sop_status || 'Draft' },
			{ label: 'Region / Cluster', value: [record.value?.region, record.value?.cluster].filter(Boolean).join(' / ') || 'Placement pending' },
			{ label: 'Database Server', value: record.value?.database_server || 'Not attached' },
		],
		'database-servers': [
			{ label: 'Database Server', value: record.value?.name || 'No database selected' },
			{ label: 'Region / Cluster', value: [record.value?.region, record.value?.cluster].filter(Boolean).join(' / ') || 'Placement pending' },
			{ label: 'Privacy', value: record.value?.privacy || 'Not configured' },
			{ label: 'Runtime state', value: `${record.value?.database_status || 'Draft'} / ${record.value?.health_status || 'Unknown'}` },
			{ label: 'Bench capacity', value: `${record.value?.attached_bench_count || 0} / ${record.value?.maximum_bench_count || 'unlimited'}` },
		],
		'release-groups': [
			{ label: 'Release Group', value: record.value?.name || 'No release group selected' },
			{ label: 'Master data boundary', value: 'No deployable image tag is stored here' },
			{ label: 'Release family', value: record.value?.image_repository || record.value?.registry_url || 'Image family metadata pending' },
		],
		releases: [
			{ label: 'Release', value: record.value?.name || 'No release selected' },
			{ label: 'Release Group', value: record.value?.release_group || 'Not linked' },
			{ label: 'Image tag', value: record.value?.image_tag || 'Missing' },
			{ label: 'Build status', value: record.value?.build_status || 'Draft' },
			{ label: 'Release status', value: record.value?.release_status || 'Draft' },
			{ label: 'Rollout eligibility', value: record.value?.rollout_eligibility || 'Not Eligible' },
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
	if (props.resourceKey === 'sites') gaps.push('Backup, restore, and upgrade execution remain backend/operator gaps; standard DNS uses the shared wildcard edge')
	if (props.resourceKey === 'benches') gaps.push('Live FrappeBench apply requires a verified restricted Cluster kubeconfig and Kubernetes apply enablement')
	if (props.resourceKey === 'database-servers') gaps.push('Live MariaDB apply/status sync requires a verified restricted Cluster kubeconfig')
	if (props.resourceKey === 'releases') gaps.push('Build pipeline and promotion execution remain backend gaps')
	if (props.resourceKey === 'release-groups') gaps.push('Release Group is master data; create/promote Release flows are UI-only until backend support lands')
	if (props.resourceKey === 'customers') gaps.push('Subscription, billing, CRM, and support data are integration placeholders')

	return {
		scope: props.scope,
		summary: record.value
			? `Guidance for ${resource.value?.label || 'record'} ${record.value.title || record.value.first_name || record.value.name}.`
			: `Guidance for the ${resource.value?.label || 'records'} ${displayMode.value === 'tree' ? 'tree' : 'list'} surface.`,
		badges: [resource.value?.doctype, displayMode.value === 'tree' && isTreeResource.value ? 'tree' : props.mode, activeAction.value ? activeAction.value.label : 'no action selected'].filter(Boolean),
		sections: [
			{ label: 'Selected record', value: record.value ? (record.value.title || record.value.first_name || record.value.name) : 'No record selected' },
			{ label: 'Document status', value: documentStatusLabel.value },
			{ label: 'Current tab set', value: inspectorTabs.value.map((tab) => tab.label).join(', ') },
			{ label: 'Rows visible', value: `${visibleRowCount.value} of ${records.value.length}` },
			{ label: 'Infrastructure boundary', value: 'The platform reconciles operator resources only; cluster substrate remains owned by lenscloud-infra.' },
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

const listActions = computed(() => [
	{ label: 'Refresh', onClick: load },
	{ label: 'Clear filters and search', onClick: clearFilters },
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
		'docstatus',
		...resource.value.summaryFields.map((field) => field.key),
		...(resource.value.detailFields || []).map((field) => field.key),
		...(resource.value.lifecycleFields || []).map((field) => field.key),
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
		for (const field of documentLifecycleFields.value || []) {
			formState[field.key] = cloneFieldValue(record.value[field.key] ?? field.default ?? (['table', 'table_multiselect'].includes(field.type) ? [] : ''))
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

		return { label: relation.label, items, previewFields: relation.fields.slice(0, 2), route: relation.route, doctype: relation.doctype, linkField, sourceValue }
	}))
}

function applyRouteFilter() {
	const field = route.query.filter_field
	const value = route.query.filter_value
	if (!field || value === undefined) return
	listFilters.value = {}
	setFilter(String(field), String(route.query.filter_operator || '='), String(value), String(route.query.filter_source || 'Related'))
}

async function load() {
	loading.value = !records.value.length
	error.value = null
	related.value = []
	try {
		await loadEditorSchema()
		await Promise.all([loadList(), loadSettingsContext(), loadFieldOptions()])
		applyRouteFilter()
		const previewName = route.params.name || ''
		await loadDetail(previewName)
		if (!previewName) record.value = null
	} catch (err) {
		error.value = err?.message || 'Unable to load records.'
	} finally {
		loading.value = false
	}
}

onMounted(load)
watch(() => [props.mode, props.resourceKey, route.params.name, props.scope, route.query.filter_field, route.query.filter_value], load)
watch(isTreeResource, (enabled) => {
	displayMode.value = enabled ? 'tree' : 'list'
	expandedTreeNodes.value = new Set()
}, { immediate: true })

const title = computed(() => resource.value?.label || 'Records')
const subtitle = computed(() => resource.value?.listHelp || 'Native Frappe document surface.')
const activeAction = computed(() => (resource.value?.actions || []).find((action) => action.key === activeActionKey.value) || null)
const inspectorTabs = computed(() => {
	const tabs = [{ label: 'Overview' }]
	tabs.push({ label: `Actions${resource.value?.actions?.length ? ` (${resource.value.actions.length})` : ''}` })
	tabs.push({ label: `Related${related.value.length ? ` (${related.value.length})` : ''}` })
	tabs.push({ label: 'Diagnostics' })
	if (showExternalContext.value) tabs.push({ label: 'External' })
	return tabs
})

function selectAction(action) {
	activeActionKey.value = activeActionKey.value === action.key ? '' : action.key
	for (const key of Object.keys(actionState)) delete actionState[key]
	for (const field of action.fields || []) {
		actionState[field.key] = field.default ?? (field.type === 'check' ? false : '')
	}
	actionExecutionState.value = 'idle'
	actionResult.value = null
	actionRawResult.value = null
	actionFailure.value = null
}

function buildActionParams() {
	const params = { ...actionState }
	if (activeAction.value?.paramsFromRecord && record.value) {
		for (const [param, field] of Object.entries(activeAction.value.paramsFromRecord)) {
			params[param] = record.value[field]
		}
	}
	return params
}


function unwrapMethodResult(result) {
	if (result && typeof result === 'object' && Object.hasOwn(result, 'message')) {
		return result.message
	}
	return result
}

function formatActionResult(result) {
	if (!result) return ''
	return JSON.stringify(result, null, 2)
}

function actionLogFromError(message) {
	return String(message || '').match(/ORCH-\d{4}-\d+/)?.[0] || ''
}

function recoverySteps(action, message) {
	const text = String(message || '').toLowerCase()
	const steps = []

	if (text.includes('404') || text.includes('not found')) {
		steps.push('The runtime resource does not exist yet. Run the matching Reconcile action with Dry run switched off.')
	}
	if (text.includes('timed out') || text.includes('connection')) {
		steps.push('Confirm the host API authorization watcher is running, then run the Cluster permission preflight again.')
	}
	if (text.includes('secrets') && (text.includes('forbidden') || text.includes('403')) && text.includes('namespace')) {
		steps.push('Check the record Kubernetes namespace. New Platform-managed resources must use the Cluster runtime namespace exactly, for example lenscloud-runtime-eu.')
	}
	if (text.includes('permission') || text.includes('forbidden') || text.includes('403')) {
		steps.push('Run the Python Cluster permission preflight and stop if required access is denied.')
	}
	if (action?.key?.startsWith('sync-')) {
		steps.push('Confirm the preceding Reconcile action returned accepted rather than dry_run before syncing status.')
	}
	if (action?.key?.startsWith('reconcile-')) {
		steps.push('Confirm Kubernetes apply is enabled only for the controlled window and verify the Dry run switch before retrying.')
	}
	if (action?.key?.includes('delete')) {
		steps.push('Check dependent resources, exact confirmation text, ownership labels, and finalizer progress before retrying.')
	}
	steps.push('Open Platform > Orchestration Logs and inspect the latest action for this record.')
	return [...new Set(steps)]
}

function successGuidance(action, result) {
	if (!result || typeof result !== 'object') return null
	if (result.status === 'dry_run' || result.dry_run === true) {
		return {
			title: 'Dry run complete — no cluster resource was created',
			message: result.message || 'The manifest was generated and audited, but it was not applied to Kubernetes.',
			steps: result.next_actions || ['Enable apply for the controlled window.', 'Switch Dry run off.', 'Run Reconcile again and require status accepted before syncing.'],
		}
	}
	if (result.status === 'accepted') {
		return {
			title: 'Kubernetes accepted the resource',
			message: result.message || 'The owner resource was submitted successfully.',
			steps: result.next_actions || ['Run Sync runtime status until the resource is Ready.', 'Use Inspect runtime for conditions, finalizers, workloads, PVCs, Services, and Events.'],
		}
	}
	if (result.status === 'deleting') {
		return {
			title: 'Deletion accepted',
			message: result.message || 'The operator is processing normal finalizers.',
			steps: result.next_actions || ['Run Inspect runtime until the owner resource is absent and the Platform status is Deleted.', 'Use Retry delete only after correcting a reported blocker.'],
		}
	}
	return result.next_actions?.length ? { title: 'Action completed', message: result.message || 'Review the result below.', steps: result.next_actions } : null
}

const activeActionGuidance = computed(() => successGuidance(activeAction.value, actionResult.value))

async function executeActiveAction() {
	if (!activeAction.value?.method) return
	actionExecutionState.value = 'running'
	actionResult.value = null
	actionRawResult.value = null
	actionFailure.value = null
	error.value = null
	try {
		const result = await callMethod(activeAction.value.method, buildActionParams(), 'POST')
		actionRawResult.value = result
		actionResult.value = unwrapMethodResult(result)
		actionExecutionState.value = 'done'
		await load()
	} catch (err) {
		actionExecutionState.value = 'error'
		const message = err?.message || 'Unable to execute action.'
		actionFailure.value = {
			title: `${activeAction.value?.label || 'Action'} failed`,
			message,
			actionLog: actionLogFromError(message),
			steps: recoverySteps(activeAction.value, message),
		}
	}
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

const hasUnsavedChanges = computed(() => {
	if (!record.value || !resource.value?.editable || saveState.value === 'saving') return false
	return documentLifecycleFields.value.some((field) => !field.readOnly && JSON.stringify(formState[field.key] ?? (['table', 'table_multiselect'].includes(field.type) ? [] : '')) !== JSON.stringify(record.value[field.key] ?? field.default ?? (['table', 'table_multiselect'].includes(field.type) ? [] : '')))
})

function confirmRecordSwitch() {
	return !hasUnsavedChanges.value || window.confirm('You have unsaved edits in the inspector. Switch records and discard those local edits?')
}

async function selectRecord(row) {
	if (!resource.value?.detailRoute || !row?.name || row.name === selectedName.value) return
	if (!confirmRecordSwitch()) return
	error.value = null
	await router.push(resource.value.detailRoute(row.name))
	await loadDetail(row.name).catch((err) => {
		error.value = err?.message || 'Unable to load record.'
	})
}

function selectTreeRow(row) {
	selectRecord(row)
}

function toggleSort(field) {
	if (sortState.field === field) {
		sortState.direction = sortState.direction === 'asc' ? 'desc' : 'asc'
	} else {
		sortState.field = field
		sortState.direction = 'asc'
	}
}

function sortIndicator(field) {
	if (sortState.field !== field) return ''
	return sortState.direction === 'asc' ? '↑' : '↓'
}

function addCellFilter(field, value, source = '') {
	setFilter(field, '=', value, source)
}

function statusTone(value) {
	const normalized = String(value || '').toLowerCase()
	if (['ready', 'active', 'healthy', 'succeeded', 'verified', 'reserved'].some((item) => normalized.includes(item))) return 'green'
	if (['failed', 'blocked', 'conflict', 'degraded'].some((item) => normalized.includes(item))) return 'red'
	if (['running', 'provisioning', 'accepted', 'deleting', 'quiescing', 'pending'].some((item) => normalized.includes(item))) return 'amber'
	if (['deleted', 'retired', 'disabled', 'suspended'].some((item) => normalized.includes(item))) return 'muted'
	return 'gray'
}

function statusBadgeClass(value) {
	return {
		green: 'bg-emerald-50 text-emerald-700',
		red: 'bg-red-50 text-red-700',
		amber: 'bg-amber-50 text-amber-700',
		muted: 'bg-surface-gray-2 text-ink-gray-6',
		gray: 'bg-surface-white text-ink-gray-7',
	}[statusTone(value)]
}

function statusDotClass(value) {
	return {
		green: 'bg-emerald-500',
		red: 'bg-red-500',
		amber: 'bg-amber-500',
		muted: 'bg-ink-gray-4',
		gray: 'bg-ink-gray-3',
	}[statusTone(value)]
}

function isStatusField(field = {}) {
	return field.key?.includes('status') || field.key?.includes('state') || field.key === 'privacy' || field.key === 'health_status' || field.key === 'docstatus'
}

function isFilterableCell(field = {}) {
	return isStatusField(field) || field.type === 'link' || Boolean(field.linkPrefix) || ['region', 'cluster', 'customer', 'privacy', 'database_server', 'bench', 'release_group', 'current_release'].includes(field.key)
}

function cellValue(row, field) {
	return field.key === 'name' ? rowTitle(row) || row.name : row[field.key]
}

function cellSubtitle(row, field) {
	return field.key === 'name' && rowTitle(row) !== row.name ? row.name : ''
}

function relatedResourcePath(relation, item) {
	const target = getResourceByDoctype(relation.doctype)
	if (!target) return relation.route(item.name)
	return {
		path: target.route,
		query: { filter_field: 'name', filter_operator: '=', filter_value: item.name, filter_source: relation.label },
	}
}

function openRelatedFilter(relation, item) {
	if (relation.doctype === resource.value?.doctype) {
		setFilter('name', '=', item.name, relation.label)
		return
	}
	router.push(relatedResourcePath(relation, item))
}

function controlTypeForField(field) {
	if (field.type === 'check') return 'checkbox'
	if (field.type === 'textarea') return 'textarea'
	if (field.type === 'select') return 'select'
	if (field.type === 'link') return 'combobox'
	if (field.type === 'date') return 'date'
	if (field.type === 'datetime') return 'datetime-local'
	if (field.type === 'number') return 'number'
	return 'text'
}

function normalizedOptionsForField(field, model = optionModelContext()) {
	if (field.type === 'select') {
		const source = Array.isArray(field.options) ? field.options : String(field.options || '').split('\n')
		const options = source.map((option) => (typeof option === 'object' ? option : { label: option, value: option })).filter((option) => option.value !== '')
		return [{ label: 'None', value: '' }, ...options]
	}

	if (field.type === 'link') return [{ label: 'None', value: '' }, ...optionsForField(field, model)]
	return []
}

function controlValueForField(model, field) {
	return model[field.key]
}

function fieldControlProps(model, field) {
	const props = {
		type: controlTypeForField(field),
		label: field.label,
		required: field.required,
		modelValue: controlValueForField(model, field),
		variant: 'subtle',
		disabled: Boolean(field.readOnly),
	}

	if (field.type !== 'check') {
		props.placeholder = field.placeholder || field.label
	}

	if (field.type === 'select' || field.type === 'link') {
		props.options = normalizedOptionsForField(field, model)
	}

	if (field.type === 'link') {
		props.openOnFocus = true
		props.openOnClick = true
		props.allowCustomValue = Boolean(field.allowCreate)
	}

	return props
}

function canClearField(model, field) {
	return ['link', 'select'].includes(field.type) && Boolean(model[field.key])
}

function clearModelField(model, field) {
	model[field.key] = ''
}

function updateModelField(model, field, value) {
	if (field.type === 'link') {
		model[field.key] = value || ''
		return
	}
	model[field.key] = value
}

function cloneFieldValue(value) {
	if (value === null || value === undefined || typeof value !== 'object') return value
	return JSON.parse(JSON.stringify(value))
}

function addChildRow(model, field) {
	if (!Array.isArray(model[field.key])) model[field.key] = []
	const row = {}
	for (const column of field.columns || []) row[column.key] = column.default ?? (column.type === 'check' ? 0 : '')
	model[field.key].push(row)
}

function removeChildRow(model, field, index) {
	model[field.key].splice(index, 1)
}

function moveChildRow(model, field, index, direction) {
	const target = index + direction
	if (target < 0 || target >= model[field.key].length) return
	const rows = model[field.key]
	const [row] = rows.splice(index, 1)
	rows.splice(target, 0, row)
}

function childRowKey(row, index) {
	return row.name || `new-child-${index}`
}


async function createCurrentRecord() {
	if (!resource.value) return

	lifecycleState.value = 'creating'
	error.value = null
	try {
		const created = await createDoc(resource.value.doctype, buildDocumentPayload(createForm))
		isCreating.value = false
		await loadList()
		await router.push(resource.value.detailRoute(created.name))
		await loadDetail(created.name)
		lifecycleState.value = 'created'
	} catch (err) {
		lifecycleState.value = 'error'
		error.value = err?.message || 'Unable to create document.'
	}
}

async function submitCurrentRecord() {
	if (!record.value || !resource.value) return

	lifecycleState.value = 'submitting'
	error.value = null
	try {
		const submitted = await submitDoc(record.value)
		record.value = submitted
		await load()
		lifecycleState.value = 'submitted'
	} catch (err) {
		lifecycleState.value = 'error'
		error.value = err?.message || 'Unable to submit document.'
	}
}

async function cancelCurrentRecord() {
	if (!record.value || !resource.value) return

	lifecycleState.value = 'cancelling'
	error.value = null
	try {
		const cancelled = await cancelDoc(resource.value.doctype, record.value.name)
		record.value = cancelled
		await load()
		lifecycleState.value = 'cancelled'
	} catch (err) {
		lifecycleState.value = 'error'
		error.value = err?.message || 'Unable to cancel document.'
	}
}

function amendCurrentRecord() {
	if (!record.value || !resource.value) return
	startCreate({ ...record.value, amended_from: record.value.name })
}

async function saveCurrentRecord() {
	if (!record.value || !resource.value || !canEditDocument.value) return

	saveState.value = 'saving'
	try {
		const saved = await saveDoc(resource.value.doctype, record.value.name, buildDocumentPayload(formState, false))
		record.value = saved
		await load()
		saveState.value = 'saved'
	} catch (err) {
		saveState.value = 'error'
		error.value = err?.message || 'Unable to save record.'
	}
}

function startRenameDocument() {
	if (!canRenameDocument.value || hasUnsavedChanges.value) return
	renameValue.value = record.value.name
	renameState.value = 'idle'
	renameMode.value = true
}

async function renameCurrentDocument() {
	const nextName = renameValue.value.trim()
	if (!record.value || !nextName || nextName === record.value.name) return
	renameState.value = 'renaming'
	error.value = null
	try {
		const response = await callMethod('frappe.client.rename_doc', { doctype: resource.value.doctype, old_name: record.value.name, new_name: nextName, merge: 0 }, 'POST')
		const renamed = response.message || response
		renameMode.value = false
		renameState.value = 'renamed'
		await router.replace(resource.value.detailRoute(renamed))
		await load()
	} catch (err) {
		renameState.value = 'error'
		error.value = err?.message || 'Unable to rename document.'
	}
}

async function discardCurrentEdits() {
	if (!record.value) return
	await loadDetail(record.value.name)
	saveState.value = 'idle'
	error.value = null
}

async function closeCenterEditor() {
	if (!confirmRecordSwitch()) return
	editorExpanded.value = false
	record.value = null
	await router.push(resource.value.route)
}

function startEditorResize(event) {
	if (editorExpanded.value) return
	event.preventDefault()
	const container = event.currentTarget.closest('[data-resource-split]')
	if (!container) return
	const resize = (pointerEvent) => {
		const bounds = container.getBoundingClientRect()
		const next = ((bounds.bottom - pointerEvent.clientY) / bounds.height) * 100
		editorHeight.value = Math.min(75, Math.max(35, next))
	}
	const stop = () => {
		window.removeEventListener('pointermove', resize)
		window.removeEventListener('pointerup', stop)
	}
	window.addEventListener('pointermove', resize)
	window.addEventListener('pointerup', stop)
}

function resizeEditorByKeyboard(event) {
	if (event.key === 'ArrowUp') editorHeight.value = Math.min(75, editorHeight.value + 5)
	else if (event.key === 'ArrowDown') editorHeight.value = Math.max(35, editorHeight.value - 5)
	else return
	event.preventDefault()
}
</script>

<template>
	<WorkspaceLayout
		:title="title"
		:subtitle="subtitle"
		inspector-kicker="Selected record"
		:inspector-title="record ? `${resource.doctype}: ${record.title || record.first_name || record.name}` : `No ${resource.doctype} selected`"
		:inspector-subtitle="record ? 'Review status, related records, diagnostics, and actions for the selected record.' : 'Select a row from the list before editing or running actions.'"
		assistant-label="Assistant"
		assistant-hint="This drawer will eventually provide context-aware help for the selected doctype, record, and action path."
		:assistant-context="assistantContext"
	>
		<template #actions>
			<Button v-if="canCreateDocument" variant="subtle" @click="startCreate()">New {{ resource.label.replace(/s$/, '') }}</Button>
			<Badge class="bg-surface-gray-2 text-ink-gray-6">{{ displayMode === 'tree' && isTreeResource ? 'Tree view' : (mode === 'detail' ? 'Detail view' : 'List view') }}</Badge>
			<Button variant="subtle" @click="load">Refresh</Button>
		</template>

		<template #main>
			<div class="flex h-full min-h-0 flex-col p-4">
				<Alert v-if="error" theme="red" title="Unable to load or save this surface" :description="error" />

				<div v-if="isCreating" class="min-h-0 flex-1 overflow-auto rounded border border-outline-gray-2 bg-surface-white p-4">
					<div class="flex items-start justify-between gap-3 border-b border-outline-gray-2 pb-3">
						<div>
							<p class="text-sm font-medium text-ink-gray-9">New {{ resource.label.replace(/s$/, '') }}</p>
							<p class="mt-1 text-sm leading-5 text-ink-gray-5">Create this document with standard Frappe permissions and document APIs.</p>
						</div>
						<Badge v-if="createForm.amended_from" class="bg-amber-50 text-amber-700">Amending {{ createForm.amended_from }}</Badge>
					</div>

					<div class="mt-4"><DocumentLayoutEditor :fields="editorLayoutFields" :model="createForm" :control-props="fieldControlProps" /></div>

					<div class="mt-4 flex flex-wrap items-center gap-2 border-t border-outline-gray-2 pt-3">
						<Button :disabled="lifecycleState === 'creating'" @click="createCurrentRecord">{{ lifecycleState === 'creating' ? 'Creating...' : 'Create document' }}</Button>
						<Button variant="subtle" @click="stopCreate">Cancel</Button>
						<Badge v-if="lifecycleState === 'created'" class="bg-emerald-50 text-emerald-700">Created</Badge>
						<Badge v-else-if="lifecycleState === 'error'" class="bg-red-50 text-red-700">Failed</Badge>
					</div>
				</div>

				<div v-else class="relative flex min-h-0 flex-1 flex-col overflow-hidden rounded border border-outline-gray-2 bg-surface-white" data-resource-split>
				<div class="shrink-0 border-b border-outline-gray-2 bg-surface-gray-1 px-3 py-2">
					<div class="flex flex-wrap items-center justify-between gap-2">
						<div class="flex min-w-0 flex-1 flex-wrap items-center gap-2">
							<TextInput v-model="searchQuery" class="max-w-xs" variant="subtle" :placeholder="displayMode === 'tree' ? 'Search tree' : 'Search list'">
								<template #prefix><Search class="size-4 text-ink-gray-4" /></template>
							</TextInput>
							<Popover placement="bottom-start" popover-class="z-[200] w-[760px] rounded-lg border border-outline-gray-2 bg-surface-white p-3 shadow-xl" @open="resetDraftFilters">
								<template #target="{ togglePopover }">
									<Button variant="subtle" @click="togglePopover">
										<Filter class="size-4" />
										Filter
										<Badge v-if="appliedFilterCount" class="ml-1 bg-surface-gray-7 text-ink-white">{{ appliedFilterCount }}</Badge>
									</Button>
								</template>
								<template #body="{ close }">
									<div class="space-y-3">
										<div class="flex items-start justify-between gap-3">
											<div>
												<p class="text-sm font-medium text-ink-gray-9">Filters</p>
												<p class="mt-0.5 text-xs text-ink-gray-5">Add field, operator, and value, then apply the filter.</p>
											</div>
											<Button size="sm" variant="ghost" @click="close">Close</Button>
										</div>

										<div v-if="!draftFilterRows.length" class="rounded border border-dashed border-outline-gray-2 bg-surface-gray-1 px-3 py-2 text-sm text-ink-gray-5">No filters yet. Add a filter to start.</div>
										<div v-for="(filter, index) in draftFilterRows" :key="index" class="grid grid-cols-[64px_minmax(0,1fr)_160px_minmax(0,1fr)_32px] items-end gap-2">
											<div class="pb-1.5 text-right text-sm text-ink-gray-5">{{ index === 0 ? 'Where' : 'And' }}</div>
											<Autocomplete :model-value="filter.field" :options="filterFieldOptions" placeholder="Filter by..." @change="(value) => updateDraftField(filter, value)" />
											<FormControl type="select" :model-value="filter.operator" :options="operatorOptionsForField(filter.field)" placeholder="Operator" @update:modelValue="(value) => updateDraftOperator(filter, value)" />
											<Autocomplete v-if="['Link', 'Select', 'Check'].includes(frappeFieldType(fieldMeta(filter.field)))" :model-value="filter.value" :options="filterValueOptions(filter.field)" placeholder="Value" @change="(value) => updateDraftValue(filter, value)" />
											<FormControl v-else type="text" :model-value="filter.value" placeholder="Value" @update:modelValue="(value) => updateDraftValue(filter, value)" />
											<Button variant="ghost" icon="x" @click="removeDraftFilter(index)" />
										</div>

										<div class="flex items-center justify-between border-t border-outline-gray-2 pt-3">
											<Button variant="ghost" @click="addDraftFilter">Add filter</Button>
											<div class="flex items-center gap-2">
												<Button variant="ghost" @click="clearFilters(); close()">Clear filters</Button>
												<Button @click="applyDraftFilters(); close()">Apply filters</Button>
											</div>
										</div>
									</div>
								</template>
							</Popover>
							<div v-if="isTreeResource" class="flex shrink-0 rounded border border-outline-gray-2 bg-surface-white p-0.5">
								<Button size="sm" :variant="displayMode === 'list' ? 'subtle' : 'ghost'" class="h-7" @click="setDisplayMode('list')"><List class="size-4" />List</Button>
								<Button size="sm" :variant="displayMode === 'tree' ? 'subtle' : 'ghost'" class="h-7" @click="setDisplayMode('tree')"><FolderTree class="size-4" />Tree</Button>
							</div>
						</div>
						<div class="flex shrink-0 items-center gap-2">
							<Badge class="bg-surface-white text-ink-gray-7">{{ visibleRowCount }} / {{ records.length }}</Badge>
							<Dropdown :options="listActions"><Button variant="ghost" :icon="MoreHorizontal" /></Dropdown>
						</div>
					</div>
					<div v-if="activeFilterEntries.length" class="mt-2 flex flex-wrap items-center gap-2">
						<button v-for="([field, filter]) in activeFilterEntries" :key="field" type="button" class="rounded-full border border-outline-gray-2 bg-surface-white px-2.5 py-1 text-xs font-medium text-ink-gray-7 hover:bg-surface-gray-1" @click="clearAppliedFilter(field)">
							{{ filterChipLabel(field, filter[0], filter[1]) }} ×
						</button>
						<Button size="sm" variant="ghost" @click="clearFilters">Clear all</Button>
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
						getRowRoute: null,
						onRowClick: selectRecord,
						selectable: false,
						showTooltip: true,
						resizeColumn: true,
						enableActive: true,
						rowHeight: 52,
						emptyState: {
							title: 'No matching records',
							description: 'Adjust filters or refresh the list to see records.',
							button: { label: 'Clear filters', variant: 'subtle', onClick: clearFilters },
						},
					}"
				>
					<template #default>
						<ListHeader>
							<ListHeaderItem v-for="column in listColumns" :key="column.key" :item="column">
								<button type="button" class="flex min-w-0 items-center gap-1 truncate text-left text-sm text-ink-gray-5 hover:text-ink-gray-8" @click.stop="toggleSort(column.key)">
									<span class="truncate">{{ column.label }}</span>
									<span v-if="sortIndicator(column.key)" class="text-xs text-ink-gray-7">{{ sortIndicator(column.key) }}</span>
								</button>
							</ListHeaderItem>
						</ListHeader>
						<ListRows />
					</template>
					<template #cell="{ column, row }">
						<div class="flex min-w-0 items-start gap-2" :class="selectedName === row.name && column.key === 'name' ? 'border-l-2 border-blue-500 pl-2' : ''">
							<span v-if="column.key === 'name'" class="mt-1 size-2 shrink-0 rounded-full" :class="statusDotClass(row[resource.primaryStatusField] || row.status || row.site_status || row.bench_status || row.database_status || row.health_status)"></span>
							<div class="min-w-0 flex-1">
								<button
									v-if="isStatusField(column) || isFilterableCell(column)"
									type="button"
									class="block max-w-full truncate text-left hover:underline"
									:class="isStatusField(column) ? `rounded-full px-2 py-0.5 ${statusBadgeClass(cellValue(row, column))}` : 'text-ink-gray-8'"
									@click.stop="addCellFilter(column.key, cellValue(row, column), column.label)"
								>
									<span v-if="isStatusField(column)" class="mr-1 inline-block size-2 rounded-full" :class="statusDotClass(cellValue(row, column))"></span>{{ formatFieldValue(cellValue(row, column)) || '-' }}
								</button>
								<span v-else class="block truncate text-ink-gray-8">{{ formatFieldValue(cellValue(row, column)) || '-' }}</span>
								<div v-if="cellSubtitle(row, column)" class="truncate text-xs text-ink-gray-5">{{ cellSubtitle(row, column) }}</div>
								<Badge v-if="selectedName === row.name && column.key === 'name'" class="mt-1 bg-blue-100 text-blue-700">Selected</Badge>
							</div>
						</div>
					</template>
				</ListView>

				<section
					v-if="record && resource.editable"
					data-testid="center-document-editor"
					class="shrink-0 overflow-hidden border-t border-outline-gray-2 bg-surface-white max-lg:absolute max-lg:inset-0 max-lg:z-40 max-lg:!h-full max-lg:border-t-0"
					:class="editorExpanded ? 'absolute inset-0 z-40 h-full border-t-0' : ''"
					:style="editorExpanded ? {} : { height: `${editorHeight}%` }"
				>
					<div
						v-if="!editorExpanded"
						role="separator"
						tabindex="0"
						aria-label="Resize document editor"
						aria-orientation="horizontal"
						class="group flex h-2 cursor-row-resize items-center justify-center bg-surface-gray-1 hover:bg-blue-50 focus:bg-blue-50 focus:outline-none max-lg:hidden"
						@pointerdown="startEditorResize"
						@keydown="resizeEditorByKeyboard"
					><span class="h-0.5 w-10 rounded bg-ink-gray-3 group-hover:bg-blue-500"></span></div>

					<header class="flex h-14 items-center justify-between gap-3 border-b border-outline-gray-2 px-4">
						<div class="min-w-0"><div class="flex items-center gap-2"><p class="truncate text-sm font-semibold text-ink-gray-9">Editing {{ resource.doctype }}: {{ record.title || record.first_name || record.name }}</p><Badge v-if="hasUnsavedChanges" class="shrink-0 bg-amber-50 text-amber-700">Unsaved</Badge><Badge v-else class="shrink-0 bg-surface-gray-1 text-ink-gray-6">{{ documentStatusLabel }}</Badge></div><p class="mt-0.5 truncate text-xs text-ink-gray-5">Parent fields and child tables save together as one Frappe document.</p></div>
						<div class="flex shrink-0 items-center gap-2"><Button v-if="canRenameDocument" size="sm" variant="subtle" :disabled="hasUnsavedChanges" @click="startRenameDocument">Rename</Button><Button size="sm" variant="subtle" :disabled="!hasUnsavedChanges || saveState === 'saving'" @click="discardCurrentEdits">Discard</Button><Button size="sm" :disabled="!canEditDocument || saveState === 'saving'" @click="saveCurrentRecord">{{ saveState === 'saving' ? 'Saving...' : 'Save' }}</Button><button type="button" :aria-label="editorExpanded ? 'Restore split editor' : 'Expand editor'" class="grid size-8 place-items-center rounded hover:bg-surface-gray-1 focus:outline-none focus:ring-2 focus:ring-blue-500" @click="editorExpanded = !editorExpanded"><component :is="editorExpanded ? Minimize2 : Maximize2" class="size-4" /></button><button type="button" aria-label="Close editor" class="grid size-8 place-items-center rounded hover:bg-surface-gray-1 focus:outline-none focus:ring-2 focus:ring-blue-500" @click="closeCenterEditor"><X class="size-4" /></button></div>
					</header>

					<div v-if="renameMode" class="flex flex-wrap items-end gap-2 border-b border-blue-200 bg-blue-50 px-4 py-3"><TextInput v-model="renameValue" class="min-w-72" label="New document name" placeholder="New document name" /><Button size="sm" :disabled="renameState === 'renaming' || !renameValue.trim()" @click="renameCurrentDocument">{{ renameState === 'renaming' ? 'Renaming...' : 'Confirm rename' }}</Button><Button size="sm" variant="ghost" @click="renameMode = false">Cancel</Button><p class="w-full text-xs text-blue-700">Frappe updates links and the field-based document title through its rename workflow.</p></div>
					<div class="h-[calc(100%-3.5rem)] overflow-y-auto p-4">
						<DocumentLayoutEditor :fields="existingEditorLayoutFields" :model="formState" :control-props="fieldControlProps" :disabled="!canEditDocument" />
					</div>
				</section>
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
					<div v-if="tab.label.startsWith('Overview')" class="space-y-3">
						<div class="rounded border border-outline-gray-2 bg-surface-gray-1 p-3">
							<div class="flex items-start justify-between gap-3">
								<div class="min-w-0">
									<p class="text-xs font-medium text-ink-gray-5">Record</p>
									<p class="mt-1 truncate text-sm font-medium text-ink-gray-9">{{ record ? (record.title || record.first_name || record.name) : 'No record selected' }}</p>
								</div>
								<Badge :class="record ? 'bg-blue-50 text-blue-700' : 'bg-surface-white text-ink-gray-7'">{{ record ? 'Selected' : 'Pending' }}</Badge>
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


					<div v-else-if="tab.label.startsWith('Document')" class="space-y-3">
						<div class="rounded border border-outline-gray-2 bg-surface-gray-1 p-3">
							<div class="flex items-start justify-between gap-3">
								<div>
									<p class="text-sm font-medium text-ink-gray-9">Document lifecycle</p>
									<p class="mt-1 text-xs leading-5 text-ink-gray-5">Standard Frappe create, save, submit, cancel, and amend controls for document records.</p>
								</div>
								<Badge class="bg-surface-white text-ink-gray-7">{{ documentStatusLabel }}</Badge>
							</div>
						</div>

						<div class="grid gap-2">
							<div class="flex items-center justify-between rounded border border-outline-gray-2 bg-surface-white px-3 py-2">
								<span class="text-sm text-ink-gray-5">Create</span>
								<Badge :class="canCreateDocument ? 'bg-emerald-50 text-emerald-700' : 'bg-surface-gray-2 text-ink-gray-6'">{{ canCreateDocument ? 'Available' : 'Unavailable' }}</Badge>
							</div>
							<div class="flex items-center justify-between rounded border border-outline-gray-2 bg-surface-white px-3 py-2">
								<span class="text-sm text-ink-gray-5">Submit / Cancel</span>
								<Badge :class="resource.submittable ? 'bg-emerald-50 text-emerald-700' : 'bg-surface-gray-2 text-ink-gray-6'">{{ resource.submittable ? 'Submittable' : 'Not submittable' }}</Badge>
							</div>
							<div v-if="record?.amended_from" class="rounded border border-outline-gray-2 bg-surface-white px-3 py-2">
								<p class="text-sm text-ink-gray-5">Amended from</p>
								<p class="mt-1 truncate text-sm font-medium text-ink-gray-9">{{ record.amended_from }}</p>
							</div>
						</div>

						<div class="rounded border border-outline-gray-2 bg-surface-white p-3">
							<div class="flex flex-wrap items-center gap-2">
								<Button size="sm" variant="subtle" :disabled="!canCreateDocument" @click="startCreate()">New</Button>
								<Button size="sm" variant="subtle" :disabled="!canEditDocument || saveState === 'saving'" @click="saveCurrentRecord">Save</Button>
								<Button size="sm" variant="subtle" :disabled="!canSubmitDocument || lifecycleState === 'submitting'" @click="submitCurrentRecord">Submit</Button>
								<Button size="sm" variant="subtle" :disabled="!canCancelDocument || lifecycleState === 'cancelling'" @click="cancelCurrentRecord">Cancel</Button>
								<Button size="sm" variant="subtle" :disabled="!canAmendDocument" @click="amendCurrentRecord">Amend</Button>
							</div>
							<div class="mt-3 flex flex-wrap gap-2 border-t border-outline-gray-2 pt-3">
								<Badge v-if="lifecycleState === 'submitted'" class="bg-emerald-50 text-emerald-700">Submitted</Badge>
								<Badge v-else-if="lifecycleState === 'cancelled'" class="bg-amber-50 text-amber-700">Cancelled</Badge>
								<Badge v-else-if="lifecycleState === 'error'" class="bg-red-50 text-red-700">Lifecycle failed</Badge>
								<Badge v-else class="bg-surface-gray-2 text-ink-gray-6">{{ lifecycleState }}</Badge>
							</div>
						</div>
					</div>
					<div v-else-if="tab.label.startsWith('Diagnostics')" class="space-y-3">
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
									<div v-for="field in activeAction.fields || []" :key="field.key" class="flex items-end gap-2">
										<FormControl
											v-bind="fieldControlProps(actionState, field)"
											:class="field.type === 'check' ? '' : 'min-w-0 flex-1'"
											@update:modelValue="(value) => updateModelField(actionState, field, value)"
										/>
										<Button v-if="canClearField(actionState, field)" size="sm" variant="subtle" class="mb-0.5 shrink-0" @click="clearModelField(actionState, field)">Clear</Button>
									</div>
								</div>

								<div class="mt-3 flex flex-wrap items-center gap-2 border-t border-outline-gray-2 pt-3">
									<Button size="sm" variant="subtle" :disabled="!activeAction.backendSupported || !activeAction.method || actionExecutionState === 'running'" @click="executeActiveAction">{{ actionExecutionState === 'running' ? 'Running...' : (activeAction.method ? 'Run action' : 'Capture request') }}</Button>
									<Badge v-if="!activeAction.backendSupported" class="bg-amber-50 text-amber-700">Backend gap</Badge>
									<Badge v-else-if="actionExecutionState === 'done'" class="bg-emerald-50 text-emerald-700">Done</Badge>
									<Badge v-else-if="actionExecutionState === 'error'" class="bg-red-50 text-red-700">Failed</Badge>
								</div>

								<div v-if="actionFailure" class="mt-3 rounded border border-red-200 bg-red-50 p-3">
									<p class="text-sm font-semibold text-red-800">{{ actionFailure.title }}</p>
									<p class="mt-1 text-sm leading-5 text-red-700">{{ actionFailure.message }}</p>
									<RouterLink v-if="actionFailure.actionLog" class="mt-2 inline-block text-sm font-medium text-ink-blue-3 hover:underline" :to="`/platform/orchestration-logs/${encodeURIComponent(actionFailure.actionLog)}`">Open action log {{ actionFailure.actionLog }}</RouterLink>
									<div class="mt-3">
										<p class="text-xs font-semibold uppercase text-red-700">What to do next</p>
										<ol class="mt-1 list-decimal space-y-1 pl-5 text-sm text-red-700">
											<li v-for="step in actionFailure.steps" :key="step">{{ step }}</li>
										</ol>
									</div>
								</div>

								<div v-if="activeActionGuidance" class="mt-3 rounded border border-blue-200 bg-blue-50 p-3">
									<p class="text-sm font-semibold text-blue-800">{{ activeActionGuidance.title }}</p>
									<p class="mt-1 text-sm leading-5 text-blue-700">{{ activeActionGuidance.message }}</p>
									<ol class="mt-2 list-decimal space-y-1 pl-5 text-sm text-blue-700">
										<li v-for="step in activeActionGuidance.steps" :key="step">{{ step }}</li>
									</ol>
								</div>

								<div v-if="actionResult" class="mt-3 rounded border border-outline-gray-2 bg-surface-white p-3">
									<p class="text-xs font-medium uppercase text-ink-gray-5">Action result</p>
									<div class="mt-2 space-y-1 text-xs text-ink-gray-6">
										<p v-if="actionResult.status">Status: <span class="font-medium text-ink-gray-9">{{ actionResult.status }}</span></p>
										<p v-if="actionResult.dry_run !== undefined">Dry run: <span class="font-medium text-ink-gray-9">{{ actionResult.dry_run ? 'Yes' : 'No' }}</span></p>
										<p v-if="actionResult.cluster">Cluster: <span class="font-medium text-ink-gray-9">{{ actionResult.cluster }}</span></p>
										<p v-if="actionResult.action_log">Action log: <span class="font-medium text-ink-gray-9">{{ actionResult.action_log }}</span></p>
										<p v-if="actionResult.dns_record">DNS record: <span class="font-medium text-ink-gray-9">{{ actionResult.dns_record }}</span></p>
									</div>
									<pre v-if="actionResult.manifest" class="mt-3 max-h-72 overflow-auto rounded bg-surface-gray-1 p-3 text-xs text-ink-gray-8">{{ actionResult.manifest }}</pre>
									<pre v-else class="mt-3 max-h-72 overflow-auto rounded bg-surface-gray-1 p-3 text-xs text-ink-gray-8">{{ formatActionResult(actionResult) }}</pre>
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
								<button
									v-for="item in relation.items"
									v-else
									:key="item.name"
									type="button"
									class="block w-full rounded px-2 py-1.5 text-left text-sm transition hover:bg-surface-gray-1"
									@click="openRelatedFilter(relation, item)"
								>
									<div class="truncate font-medium text-ink-gray-9">{{ item.title || item.first_name || item.name }}</div>
									<div class="truncate text-xs text-ink-gray-5">Filter list by name = {{ item.name }}</div>
								</button>
							</div>
						</div>
					</div>
				</template>
			</Tabs>
		</template>
	</WorkspaceLayout>
</template>
