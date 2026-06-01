<script setup>
 import { computed, onMounted, reactive, ref, watch } from 'vue'
 import { useRoute, useRouter } from 'vue-router'
 import { Button, Badge } from 'frappe-ui'
 import { listDocs, getDoc, formatFieldValue, saveDoc } from '@/lib/api'
 import { getResourceByKey } from '@/lib/catalog'
 import { useSessionStore } from '@/lib/session'
 import PageHeader from '@/components/PageHeader.vue'
 import RecordList from '@/components/RecordList.vue'
 import RecordDetail from '@/components/RecordDetail.vue'
 import ActionPanel from '@/components/ActionPanel.vue'

 const props = defineProps({
 	resourceKey: {
 		type: String,
 		required: true,
 	},
 	mode: {
 		type: String,
 		default: 'list',
 	},
 	scope: {
 		type: String,
 		required: true,
 	},
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
 const saveState = ref('idle')
 const formState = reactive({})

 async function loadCustomerContext() {
	if (!resource.value?.customerScoped && props.scope !== 'customer') {
		return null
 	}

 	if (session.roles.length === 0 && session.isAuthenticated) {
 		// still continue; the UI remains role-aware but not hard blocked.
 	}

 	const customerRecords = await listDocs('Customer', {
 		fields: ['name', 'first_name', 'last_name', 'region', 'external_customer_id'],
 		limit: 1,
 		filters: [['user', '=', session.user]],
 	})

 	customerContext.value = customerRecords[0] || null
 	return customerContext.value
 }

 async function loadList() {
 	if (!resource.value) {
 		return
 	}

 	const filters = []
 	if (resource.value.customerScoped) {
 		const customer = await loadCustomerContext()
 		if (customer?.name) {
 			filters.push(['customer', '=', customer.name])
 		}
 	}

 	records.value = await listDocs(resource.value.doctype, {
 		fields: ['name', ...resource.value.summaryFields.map((field) => field.key), ...(resource.value.detailFields || []).map((field) => field.key)],
 		limit: 20,
 		filters: filters.length ? filters : undefined,
 	})
 }

 async function loadDetail() {
 	if (!resource.value) {
 		return
 	}

 	const name = route.params.name
 	record.value = await getDoc(resource.value.doctype, name)

 	if (resource.value.customerScoped && customerContext.value?.name && record.value?.customer && record.value.customer !== customerContext.value.name) {
 		record.value = null
 		throw new Error('This site is not linked to your customer record.')
 	}

 	related.value = await Promise.all((resource.value.relations || []).map(async (relation) => {
 		const filters = [[relation.field, '=', relation.useFieldAsFilter ? record.value[relation.useFieldAsFilter] : record.value.name]]
 		const items = await listDocs(relation.doctype, {
 			fields: ['name', ...relation.fields.map((field) => field)],
 			limit: 5,
 			filters,
 		})

 		return {
 			label: relation.label,
 			items,
 			previewFields: relation.fields.slice(0, 2),
 			route: relation.route,
 		}
 	}))
 }

 async function load() {
 	loading.value = true
 	error.value = null
 	related.value = []
 	try {
 		if (props.mode === 'detail') {
 			await loadDetail()
 		} else {
 			await loadList()
 		}
 	} catch (err) {
 		error.value = err?.message || 'Unable to load records.'
 	} finally {
 		loading.value = false
 	}
 }

 onMounted(load)
 watch(() => [props.mode, props.resourceKey, route.params.name, props.scope], load)

 const title = computed(() => resource.value?.label || 'Records')
 const subtitle = computed(() => resource.value?.listHelp || 'Native Frappe document surface.')

 function handleActionSubmit(payload) {
 	if (payload.action.backendSupported) {
 		return
 	}

 	// UI-only action surfaces intentionally stop here for this pass.
 	return payload
 }

 function editStateField(field, value) {
 	formState[field] = value
 }

 async function saveCurrentRecord() {
 	if (!record.value || !resource.value) {
 		return
 	}

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
 	<div class="stack">
 		<PageHeader
 			:kicker="scope === 'customer' ? 'Customer surface' : 'Platform console'"
 			:title="title"
 			:subtitle="subtitle"
 		>
 			<template #actions>
 				<Badge>{{ mode === 'detail' ? 'Detail view' : 'List view' }}</Badge>
 				<Button @click="load">Refresh</Button>
 			</template>
 		</PageHeader>

 		<div v-if="error" class="section-band" style="border-color: rgba(180, 35, 24, 0.3); background: rgba(180, 35, 24, 0.04)">
 			<p class="empty-title">Surface gap</p>
 			<p class="helper-text">{{ error }}</p>
 		</div>

 		<RecordList
 			v-if="mode === 'list'"
 			:resource="resource"
 			:records="records"
 			:loading="loading"
 			empty-title="No records yet"
 			empty-copy="This surface is ready, but the current user does not have any matching records yet."
 			@refresh="load"
 		/>

 		<div v-else class="stack">
 			<RecordDetail :resource="resource" :record="record" :related="related" :loading="loading">
 				<template #actions>
 					<Button v-if="resource.editable" @click="saveCurrentRecord">Save</Button>
 					<Button @click="load">Refresh</Button>
 				</template>
 			</RecordDetail>

 			<div v-if="resource.editable && record" class="form-panel">
 				<div class="section-head" style="margin-bottom: 6px">
 					<div>
 						<div class="section-title">Edit document</div>
 						<p class="section-subtitle">This form uses standard Frappe document save APIs. No backend business logic is added here.</p>
 					</div>
 				</div>

 				<div class="form-grid">
 					<div v-for="field in resource.detailFields" :key="field.key" class="form-control">
 						<label class="field">
 							<span>{{ field.label }}</span>
 							<textarea v-if="field.key === 'notes'" :value="record[field.key] || ''" @input="editStateField(field.key, $event.target.value)" />
 							<input v-else :value="record[field.key] || ''" @input="editStateField(field.key, $event.target.value)" />
 						</label>
 					</div>
 				</div>

 				<div class="form-actions">
 					<Badge v-if="saveState === 'saved'">Saved</Badge>
 					<Badge v-else-if="saveState === 'saving'">Saving…</Badge>
 					<Badge v-else-if="saveState === 'error'">Save failed</Badge>
 					<Button @click="saveCurrentRecord">Save changes</Button>
 				</div>
 			</div>

 			<ActionPanel v-if="resource.actions && resource.actions.length" :actions="resource.actions" :context-label="resource.label" @submit="handleActionSubmit" />
 		</div>
 	</div>
 </template>
