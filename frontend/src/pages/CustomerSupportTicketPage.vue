<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { Alert, Badge, Button } from 'frappe-ui'
import { 
    AlertCircle, Clock3, Headset, Plus, RefreshCcw, X, 
    Send, User, Bot, MessageSquare, Maximize2, Minimize2,
    Edit3, Save
} from 'lucide-vue-next'
import { callMethod } from '@/lib/api'
import WorkspaceLayout from '@/components/WorkspaceLayout.vue'
import posthog from 'posthog-js'
import { useSessionStore } from '@/lib/session'


const session = useSessionStore()

const route = useRoute()
const loading = ref(true)
const error = ref('')
const context = ref(null)
const tickets = ref([])
const selectedName = ref('')

// Modal & Creation State
const showCreateModal = ref(false)
const creating = ref(false)
const createError = ref('')

const drawerMode = ref('short')
const isEditingDrawer = ref(false)
const savingDrawer = ref(false)
const drawerError = ref('')

// Form state for inline editing in the drawer
const editForm = ref({
    status: '',
    severity: ''
})

const form = ref({
    subject: '',
    site: '',
    subscription: '',
    category: 'Technical',
    severity: 'Low',
    description: '',
})

const selectedTicket = computed(() => tickets.value.find((item) => item.name === selectedName.value) || tickets.value[0] || null)
const hasTickets = computed(() => tickets.value.length > 0)

const hasSubscriptions = computed(() => {
    return (context.value?.subscriptions || []).length > 0
})

const fieldOptions = ref({
  status: [],
  severity: [],
  category: []
})

function statusClass(status) {
    if (['Resolved', 'Closed'].includes(status)) return 'bg-emerald-50 text-emerald-700 border-emerald-200'
    if (['Open'].includes(status)) return 'bg-amber-50 text-amber-700 border-amber-200'
    if (['Cancelled'].includes(status)) return 'bg-red-50 text-red-700 border-red-200'
    return 'bg-blue-50 text-blue-700 border-blue-200'
}

function severityClass(severity) {
    if (['High'].includes(severity)) return 'bg-red-50 text-red-700 font-medium'
    if (severity === 'Medium') return 'bg-amber-50 text-amber-700 font-medium'
    return 'bg-[#f2f4f6] text-[#64748B]'
}

// Parse newline-separated string from Frappe field options (e.g. "Open\nResolved\nClosed")
function parseOptions(optionsString) {
  if (!optionsString) return []
  return optionsString
    .split('\n')
    .map(opt => opt.trim())
    .filter(Boolean)
}

// Fetch field metadata dynamically from Frappe
async function fetchIssueFieldOptions() {
  try {
    // If using standard Frappe client library:
    const docMeta = await callMethod('frappe.desk.form.load.getdoctype', {
      doctype: 'Issue'
    })

    const fields = docMeta?.docs?.[0]?.fields || []

    const statusField = fields.find(f => f.fieldname === 'status')
    const severityField = fields.find(f => f.fieldname === 'severity')
    const categoryField = fields.find(f => f.fieldname === 'category')

    fieldOptions.value.status = parseOptions(statusField?.options)
    fieldOptions.value.severity = parseOptions(severityField?.options)
    fieldOptions.value.category = parseOptions(categoryField?.options)

  } catch (err) {
    console.error('Failed to load Issue metadata options:', err)
    // Fallback options in case metadata fetch fails
    fieldOptions.value.status = ['Open', 'Reopened', 'Resolved', 'Closed', 'Cancelled']
    fieldOptions.value.severity = ['Low', 'Medium', 'High']
  }
}

function formatDate(value) {
    if (!value) return 'Not set'
    return new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

function initEditForm() {
    if (selectedTicket.value) {
        editForm.value = {
            status: selectedTicket.value.status || 'Open',
            severity: selectedTicket.value.severity || 'Low'
        }
    }
    isEditingDrawer.value = false
    drawerError.value = ''
}

async function handleSaveDrawerDetails() {
    if (!selectedTicket.value) return
    savingDrawer.value = true
    drawerError.value = ''
    try {
        await callMethod('frappe.client.set_value', {
            doctype: 'Issue',
            name: selectedTicket.value.name,
            fieldname: {
                status: editForm.value.status,
                severity: editForm.value.severity
            }
        }, 'POST')
        
        // Update local ticket state directly
        selectedTicket.value.status = editForm.value.status
        selectedTicket.value.severity = editForm.value.severity
        
        isEditingDrawer.value = false
    } catch (err) {
        drawerError.value = err?.message || 'Failed to update ticket details.'
    } finally {
        savingDrawer.value = false
    }
}

async function load() {
    loading.value = true
    error.value = ''
    try {
        const response = await callMethod('lenscloud.api.orchestration.get_customer_portal_context')
        context.value = response.message || response
        
        const siteNames = (context.value?.sites || []).map((s) => s.name)
        
        if (siteNames.length > 0) {
            const ticketResponse = await callMethod('frappe.client.get_list', {
                doctype: 'Issue',
                fields: ['*'],
                filters: [['site', 'in', siteNames]],
                order_by: 'creation desc',
                limit_page_length: 0,
            }, 'GET')
            tickets.value = ticketResponse.message || ticketResponse || []
            if (route.query.ticket && tickets.value.some((item) => item.name === route.query.ticket)) {
                selectedName.value = route.query.ticket
            }
            if (!selectedName.value && tickets.value.length) {
                selectedName.value = tickets.value[0].name
            }
            if (selectedName.value) { 
                loadComments(selectedName.value)
                initEditForm()
            }
        } else {
            tickets.value = []
        }
    } catch (err) {
        error.value = err?.message || 'Unable to load support tickets.'
    } finally {
        loading.value = false
    }
}

// onMounted(load)
onMounted(() => {
    load()
  fetchIssueFieldOptions()
})

const siteOptions = computed(() => {
    const sites = context.value?.sites || []
    return [
        ...sites.map((s) => ({
            label: s.site_name || s.name,
            value: s.name,
        })),
    ]
})

const subscriptionOptions = computed(() => {
    const subs = context.value?.subscriptions || []
    return [
        ...subs.map((sub) => ({
            label: sub.plan_name ? `${sub.name} (${sub.plan_name})` : sub.name,
            value: sub.name,
        })),
    ]
})

function resetForm() {
    form.value = {
        subject: '',
        site: '',
        subscription: '',
        category: 'Technical',
        severity: 'Low',
        description: '',
    }
    createError.value = ''
}

function openCreateModal() {
    if (!hasSubscriptions.value) return
    resetForm()
    showCreateModal.value = true
    
    if (context.value?.sites?.length === 1) {
        form.value.site = context.value.sites[0].name
    }
    
    if (context.value?.subscriptions?.length === 1) {
        form.value.subscription = context.value.subscriptions[0].name
    }
}

async function handleCreateTicket() {
    if (!form.value.subject) {
        createError.value = 'Please provide a subject.'
        return
    }
    creating.value = true
    createError.value = ''
    try {
        const res = await callMethod('frappe.client.insert', {
            doc: {
                doctype: 'Issue',
                summary: form.value.subject,
                category: form.value.category,
                severity: form.value.severity,
                site: form.value.site || undefined,
                subscription: form.value.subscription || undefined,
                customer_member: context.value?.membership?.name || undefined,
                description: form.value.description,
            },
        }, 'POST')

        const createdDoc = res.message || res
        posthog.capture('support_ticket_created', {
            ticket: createdDoc.name,
            category: createdDoc.category,
            severity: createdDoc.severity,
        })
        showCreateModal.value = false
        resetForm()
        await load()
        if (createdDoc?.name) {
            selectedName.value = createdDoc.name
        }
    } catch (err) {
        console.error("Full error:", err)
        createError.value = err?.message || 'Failed to create ticket. Please try again.'
    } finally {
        creating.value = false
    }
}

// State for Ticket Comments
const comments = ref([])
const loadingComments = ref(false)
const newCommentText = ref('')
const postingComment = ref(false)
const commentError = ref('')

async function loadComments(ticketName) {
    if (!ticketName) {
        comments.value = []
        return
    }
    loadingComments.value = true
    commentError.value = ''
    try {
        const response = await callMethod('lenscloud.api.issue.get_helpdesk_comments', {
            issue_id: ticketName
        }, 'GET')
        
        comments.value = response.message || response || []
    } catch (err) {
        commentError.value = err?.message || 'Failed to load comments from helpdesk.'
    } finally {
        loadingComments.value = false
    }
}

async function handleAddComment() {
    if (!newCommentText.value.trim() || !selectedTicket.value) return
    postingComment.value = true
    commentError.value = ''
    try {
        await callMethod('lenscloud.api.issue.add_issue_comment', {
            issue_id: selectedTicket.value.name,
            content: newCommentText.value
        })
        newCommentText.value = ''
        await loadComments(selectedTicket.value.name)
    } catch (err) {
        commentError.value = err?.message || 'Failed to post comment.'
    } finally {
        postingComment.value = false
    }
}

function isUserComment(comment) {
    const userEmail = session.user || ''

    return (
        comment.comment_by === userEmail || 
        comment.comment_email === userEmail || 
        comment.user === userEmail
    )
}

function selectTicket(ticket) {
    posthog.capture('support_ticket_selected', {
        ticket: ticket.name,
        status: ticket.status,
        category: ticket.category,
    })
    selectedName.value = ticket.name
}

watch(selectedName, (newName) => {
    if (newName) {
        loadComments(newName)
        initEditForm()
        drawerMode.value = 'short'
    }
})
</script>

<template>
    <WorkspaceLayout
        title="Support Tickets"
        subtitle="Review issues you've raised with LensCloud support."
        inspector-kicker="Comment Space"
        :inspector-title="selectedTicket ? selectedTicket.name : ''"
        :inspector-subtitle="''"
    >
        <template #actions>
            <div class="flex items-center gap-2">
                <Button variant="subtle" class="!inline-flex !items-center !gap-2 whitespace-nowrap" @click="load">
                    <span class="flex items-center gap-2">
                        <RefreshCcw class="size-4" />
                        <span>Refresh</span>
                    </span>
                </Button>
                <Button 
                    v-if="hasSubscriptions" 
                    variant="outline" 
                    class="!inline-flex !items-center !gap-2 whitespace-nowrap !text-primary" 
                    @click="openCreateModal"
                >
                    <span class="flex items-center gap-2">
                        <Plus class="size-4 text-primary" />
                        <span>New Ticket</span>
                    </span>
                </Button>
            </div>
        </template>

        <!-- MAIN AREA: TICKET LIST GRID + INTEGRATED BOTTOM DRAWER -->
        <template #main>
            <div class="relative flex flex-col h-full bg-[#f7f9fb] overflow-hidden">
                
                <!-- TOP PORTION: TICKETS GRID -->
                <div v-show="drawerMode !== 'full'" class="flex-1 overflow-y-auto p-4 lg:p-6">
                    <Alert v-if="error" theme="red" title="Support tickets unavailable" :description="error" class="mb-4" />
                    <Alert 
                        v-if="!loading && !hasSubscriptions" 
                        theme="blue" 
                        title="Subscription Required" 
                        class="mb-4"
                    >
                        <template #description>
                            <p>
                                You currently do not have an active subscription. Please 
                                <RouterLink to="/customer/subscriptions" class="font-medium underline">subscribe to a plan</RouterLink> 
                                to raise support tickets.
                            </p>
                        </template>
                    </Alert>

                    <div v-if="loading" class="rounded-lg border border-[#EDEDED] bg-white p-6 text-sm text-[#64748B]">
                        Loading support tickets...
                    </div>

                    <section v-else-if="!hasTickets" class="mx-auto grid min-h-[400px] max-w-4xl place-items-center rounded-xl border border-[#EDEDED] bg-white p-8 text-center">
                        <div class="max-w-lg">
                            <div class="mx-auto grid size-14 place-items-center rounded-xl bg-blue-200 text-primary">
                                <Headset class="size-7" />
                            </div>
                            <h2 class="mt-5 text-2xl font-semibold text-[#191c1e]">No Support Tickets Yet</h2>
                            <p class="mt-3 text-sm leading-6 text-[#64748B]">When you raise an issue with LensCloud support, it will show up here with its status and history.</p>
                            
                            <div class="mt-6 flex justify-center">
                                <Button v-if="hasSubscriptions" variant="outline" @click="openCreateModal" class="!bg-primary">
                                    <span class="flex items-center gap-2 text-white">
                                        <Plus class="size-4 text-white" />
                                        <span>Raise a Ticket</span>
                                    </span>
                                </Button>
                                <RouterLink v-else to="/customer/subscriptions">
                                    <Button variant="solid" class="!bg-primary">Subscribe to a Plan</Button>
                                </RouterLink>
                            </div>
                        </div>
                    </section>

                    <section v-else class="mx-auto max-w-6xl">
                        <div class="mb-4">
                            <p class="text-xs font-semibold text-[#64748B]">Your Service</p>
                            <h2 class="mt-1 text-xl font-semibold text-[#191c1e]">My Support Tickets</h2>
                        </div>

                        <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                            <article
                                v-for="ticket in tickets"
                                :key="ticket.name"
                                class="cursor-pointer rounded-xl border bg-white p-4 transition hover:-translate-y-0.5 hover:shadow-xs"
                                :class="selectedTicket?.name === ticket.name ? 'border-primary ring-2 ring-primary/10' : 'border-[#EDEDED]'"
                                @click="selectTicket(ticket)"
                            >
                                <div class="flex items-start justify-between gap-2">
                                    <div>
                                        <p class="text-base font-semibold text-[#191c1e]">{{ ticket.name }}</p>
                                        <p class="mt-0.5 text-xs text-[#64748B] line-clamp-1">{{ ticket.summary || ticket.subject || ticket.name }}</p>
                                    </div>
                                    <Badge :class="statusClass(ticket.status)">{{ ticket.status || 'Open' }}</Badge>
                                </div>
                                <div class="mt-4 space-y-2 text-xs text-[#434655]">
                                    <div class="flex items-center gap-1.5"><AlertCircle class="size-3.5 text-[#64748B]" />{{ ticket.category || 'Not set' }}</div>
                                    <div class="flex items-center gap-1.5"><Clock3 class="size-3.5 text-[#64748B]" />{{ formatDate(ticket.creation) }}</div>
                                    <div class="flex items-center justify-between pt-1">
                                        <Badge :class="severityClass(ticket.severity)">{{ ticket.severity }}</Badge>
                                        <!-- <span class="text-[11px] text-primary font-medium flex items-center gap-1">
                                            <MessageSquare class="size-3" /> Select
                                        </span> -->
                                    </div>
                                </div>
                            </article>
                        </div>
                    </section>
                </div>

            <!-- BOTTOM DRAWER (WITH EDITABLE STATUS, SUMMARY, DESCRIPTION) -->
            <div 
                v-if="selectedTicket"
                class="bg-white border-t border-gray-200 shadow-lg transition-[height] duration-300 ease-in-out flex flex-col shrink-0"
                :class="{
                    /* Below 'lg': stays at h-72 even if collapsed state is active. On 'lg' and up: collapses to h-11 */
                    'h-72 lg:h-11': drawerMode === 'collapsed',
                    'h-72': drawerMode === 'short',
                    'absolute inset-0 z-20 h-full max-h-[100dvh]': drawerMode === 'full'
                }"
            >
                <!-- Drawer Header Bar -->
                <div 
                class="px-3 sm:px-5 py-2.5 bg-slate-50 border-b border-gray-200 flex items-center justify-between shrink-0 select-none"
                @click="drawerMode = drawerMode === 'full' ? 'short' : 'full'"
                >
                <!-- Left Side: Title & Status Dropdown -->
                <div class="flex items-center gap-1.5 sm:gap-3 min-w-0 pr-1">
                    <!-- Truncated Name -->
                    <span class="text-xs font-semibold text-gray-900 truncate max-w-[100px] xs:max-w-[140px] sm:max-w-none">
                    {{ selectedTicket.name }}
                    </span>
                    
                    <!-- EDITABLE STATUS BADGE -->
                    <div @click.stop class="shrink-0">
                    <select 
                        v-if="isEditingDrawer"
                        v-model="editForm.status"
                        class="text-xs font-medium text-gray-800 bg-white border border-gray-300 rounded-md pl-2 pr-6 py-1 leading-none shadow-2xs focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none cursor-pointer transition"
                    >
                    <option 
                        v-for="opt in fieldOptions.status" 
                        :key="opt" 
                        :value="opt"
                    >
                        {{ opt }}
                    </option>
                    </select>
                    <Badge v-else :class="statusClass(selectedTicket.status)">
                        {{ selectedTicket.status || 'Open' }}
                    </Badge>
                    </div>
                </div>

                <!-- Right Side: Action Controls -->
                <div class="flex items-center gap-1 sm:gap-2 shrink-0" @click.stop>
                    <template v-if="isEditingDrawer">
                    <!-- CANCEL BUTTON: Text on Desktop, Icon + Tooltip on Mobile -->
                    <button 
                        type="button"
                        class="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-gray-600 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition shadow-2xs disabled:opacity-50"
                        :disabled="savingDrawer"
                        title="Cancel"
                        @click="initEditForm"
                    >
                        <X class="size-3 text-gray-500" />
                        <span class="hidden xs:inline">Cancel</span>
                    </button>

                    <!-- SAVE BUTTON -->
                    <button 
                        type="button"
                        class="inline-flex items-center gap-1 px-2.5 sm:px-3 py-1 text-xs font-medium text-white bg-primary rounded-md hover:bg-primary/90 transition shadow-2xs disabled:opacity-50"
                        :disabled="savingDrawer"
                        @click="handleSaveDrawerDetails"
                    >
                        <Save class="size-3 text-white" />
                        <span>{{ savingDrawer ? 'Saving...' : 'Save' }}</span>
                    </button>
                    </template>

                    <button 
                    v-else
                    type="button"
                    class="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-gray-700 bg-white border border-gray-200 rounded-md hover:bg-gray-50 transition shadow-2xs"
                    @click="isEditingDrawer = true"
                    >
                    <Edit3 class="size-3 text-gray-500" /> Edit
                    </button>

                    <span class="text-gray-300 hidden xs:inline">|</span>

                    <!-- Expand / Shorten Button -->
                    <button
                    type="button"
                    class="p-1 rounded-md text-gray-500 hover:bg-gray-200 hover:text-gray-800 transition"
                    :title="drawerMode === 'full' ? 'Shorten Drawer' : 'Expand to Full Height'"
                    @click="drawerMode = drawerMode === 'full' ? 'short' : 'full'"
                    >
                    <Minimize2 v-if="drawerMode === 'full'" class="size-4" />
                    <Maximize2 v-else class="size-4" />
                    </button>
                </div>
                </div>

                <!-- Drawer Inner Body Content -->
                <!-- Replaced v-show with class binding so body ONLY hides when collapsed on desktop (lg:hidden) -->
                <div 
                    class="p-3 sm:p-4 flex-1 overflow-y-auto space-y-4 text-xs text-gray-800 pb-16 sm:pb-4"
                    :class="{ 'hidden lg:block': drawerMode === 'collapsed' }"
                >
                    <Alert v-if="drawerError" theme="red" :description="drawerError" class="mb-2" />

                    <!-- GROUPED SECTION: SUMMARY & DESCRIPTION -->
                    <div class="rounded-xl border border-gray-200/80 bg-slate-50/70 p-3.5 sm:p-4 shadow-2xs space-y-3">
                        <div>
                            <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide block mb-1">Summary</label>
                            <p class="text-base font-semibold text-gray-900 leading-snug">
                                {{ selectedTicket.summary || selectedTicket.subject || 'No summary provided.' }}
                            </p>
                        </div>
                        
                        <hr class="border-gray-200/60" />

                        <div>
                            <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide block mb-1.5">Description</label>
                            <div class="text-base max-w-none font-normal text-gray-700" v-html="selectedTicket.description || '<p>No description provided.</p>'" />
                        </div>
                    </div>

                    <!-- METADATA ROW -->
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 pt-2 pb-4 border-t border-gray-100 items-start">
                        <!-- SEVERITY -->
                        <div>
                            <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide block mb-1.5">Severity</label>
                            <select 
                                v-if="isEditingDrawer"
                                v-model="editForm.severity"
                                class="w-full text-xs font-medium rounded-md border border-gray-300 bg-white px-2 py-1 focus:border-primary focus:outline-none shadow-2xs"
                            >
                            <option 
                                v-for="opt in fieldOptions.severity" 
                                :key="opt" 
                                :value="opt"
                            >
                                {{ opt }}
                            </option>
                            </select>
                            <Badge v-else :class="severityClass(selectedTicket.severity)">
                                {{ selectedTicket.severity }}
                            </Badge>
                        </div>

                        <!-- CATEGORY -->
                        <div>
                            <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide block mb-1.5">Category</label>
                            <span class="text-sm font-medium text-gray-900 block truncate">{{ selectedTicket.category || 'Not set' }}</span>
                        </div>

                        <!-- SITE -->
                        <div>
                            <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide block mb-1.5">Site</label>
                            <span class="text-sm font-medium text-secondary block truncate">{{ selectedTicket.site || 'Not linked' }}</span>
                        </div>

                        <!-- SUBSCRIPTION -->
                        <div>
                            <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide block mb-1.5">Subscription</label>
                            <span class="text-sm font-medium text-secondary block truncate">{{ selectedTicket.subscription || 'Not linked' }}</span>
                        </div>
                    </div>
                </div>
            </div>
            </div>
        </template>

        <!-- INSPECTOR: COMPACT CHAT FEED (INPUT TOP, SMALLER BUBBLES) -->
        <template #inspector>
        <div v-if="selectedTicket" class="flex flex-col h-full bg-white rounded-xl border border-gray-200 overflow-hidden">
            
            <!-- LOADING STATE -->
            <div v-if="loadingComments" class="flex-1 flex items-center justify-center p-4 text-xs text-gray-400">
            Loading updates...
            </div>

            <!-- 1. NO COMMENTS STATE: CENTERED INPUT AREA -->
            <div 
            v-else-if="comments.length === 0" 
            class="flex-1 flex flex-col items-center justify-center p-4 text-center my-auto"
            >
            <div class="size-10 rounded-full bg-slate-100 flex items-center justify-center text-gray-400 mb-3">
                <MessageSquare class="size-5" />
            </div>
            <p class="text-base font-medium text-gray-700 mb-1">No comments yet</p>
            <p class="text-xs text-gray-400 mb-4 max-w-xs">Start the conversation by sending a reply below.</p>

            <Alert v-if="commentError" theme="red" :description="commentError" class="w-full max-w-md mb-2" />

            <!-- Centered Input Box -->
            <div class="w-full max-w-md space-y-2">
                <textarea
                v-model="newCommentText"
                rows="3"
                placeholder="Write a comment..."
                class="w-full text-base p-3 rounded-lg border border-gray-200 bg-white text-gray-800 placeholder-gray-400 shadow-2xs focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary transition resize-none"
                ></textarea>
                
                <div class="flex justify-end">
                <Button
                    variant="solid"
                    class="!bg-primary !text-white !rounded-md"
                    size="sm"
                    :loading="postingComment"
                    :disabled="!newCommentText.trim()"
                    @click="handleAddComment"
                >
                    <span class="flex items-center gap-1.5 text-xs font-medium">
                    <span>Send</span>
                    <Send class="size-3" />
                    </span>
                </Button>
                </div>
            </div>
            </div>

            <!-- 2. COMMENTS PRESENT: CHAT FEED + STICKY BOTTOM INPUT -->
            <div v-else class="flex flex-col h-full min-h-0">
            
            <!-- CHAT BUBBLES FEED (SCROLLABLE) -->
            <div class="flex-1 overflow-y-auto p-3 space-y-3 bg-gray-50">
                <div
                v-for="comment in comments"
                :key="comment.name"
                class="flex gap-2 max-w-[88%]"
                :class="isUserComment(comment) ? 'mr-auto' : 'ml-auto flex-row-reverse'"
                >
                <!-- User / Support Avatar -->
                <div 
                    class="size-6 rounded-full flex items-center justify-center shrink-0 text-xs font-semibold mt-0.5"
                    :class="isUserComment(comment) ? 'bg-primary text-white' : 'bg-white text-slate-800'"
                >
                    <User v-if="isUserComment(comment)" class="size-3.5 text-white" />
                    <Headset v-else class="size-3.5" />
                </div>

                <div class="flex flex-col">
                    <!-- Author & Creation Date -->
                    <div 
                    class="flex items-center gap-1.5 mb-1" 
                    :class="isUserComment(comment) ? '' : 'justify-end'"
                    >
                    <span class="text-xs font-semibold text-gray-600">
                        {{ isUserComment(comment) ? 'You' : (comment.comment_by || 'Support') }}
                    </span>
                    <span class="text-[10px] text-gray-500">{{ formatDate(comment.creation) }}</span>
                    </div>

                    <!-- Chat Bubble -->
                    <div
                    class="rounded-xl px-3 py-2 text-base shadow-2xs"
                    :class="isUserComment(comment) 
                        ? 'bg-primary text-white rounded-tl-none' 
                        : 'bg-white border border-gray-100 text-gray-800 rounded-tr-none'"
                    >
                    <div class="max-w-none break-words" v-html="comment.content" />
                    </div>
                </div>
                </div>
            </div>

            <!-- STICKY BOTTOM INPUT AREA -->
            <div class="p-3 border-t border-gray-100 bg-white shrink-0">
                <Alert v-if="commentError" theme="red" :description="commentError" class="mb-2" />

                <div class="flex items-center gap-2">
                <textarea
                    v-model="newCommentText"
                    rows="1"
                    placeholder="Write a comment..."
                    class="flex-1 text-base p-2 rounded-lg border border-gray-200 bg-white text-gray-800 placeholder-gray-400 shadow-2xs focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary transition resize-none"
                    @keydown.enter.exact.prevent="handleAddComment"
                ></textarea>
                
                <Button
                    variant="solid"
                    class="!bg-primary !text-white !rounded-md shrink-0"
                    size="sm"
                    :loading="postingComment"
                    :disabled="!newCommentText.trim()"
                    @click="handleAddComment"
                >
                    <Send class="size-3.5" />
                </Button>
                </div>
            </div>

            </div>

        </div>

        <div v-else class="rounded-xl border border-[#EDEDED] bg-white p-4 text-center text-xs text-[#64748B]">
            Select a ticket to interact with support.
        </div>
        </template>
    </WorkspaceLayout>

    <!-- CREATE TICKET MODAL OVERLAY -->
    <div
        v-if="showCreateModal"
        class="fixed inset-0 z-[1000] grid place-items-center bg-black/40 px-4 py-6 overflow-y-auto"
        role="presentation"
        @mousedown.self="showCreateModal = false"
    >
        <form
            class="w-full max-w-2xl rounded-xl bg-white p-6 shadow-xl border border-gray-100 relative"
            @submit.prevent="handleCreateTicket"
        >
            <div class="flex items-start justify-between gap-4 border-b border-gray-100 pb-4">
                <div>
                    <h3 class="text-lg font-semibold text-gray-900">Raise a Support Ticket</h3>
                    <p class="mt-1 text-xs text-gray-500">Provide ticket details and any relevant attachments.</p>
                </div>
                <button
                    type="button"
                    class="rounded-md p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition"
                    @click="showCreateModal = false"
                >
                    <X class="size-5" />
                </button>
            </div>

            <Alert v-if="createError" theme="red" :description="createError" class="mt-4" />

            <div class="mt-4 space-y-4">
                <div>
                    <label class="block text-xs font-semibold text-gray-700 mb-1">
                        Subject <span class="text-red-500">*</span>
                    </label>
                    <input
                        v-model="form.subject"
                        type="text"
                        required
                        placeholder="Brief summary of the issue"
                        class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    />
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-xs font-semibold text-gray-700 mb-1">Site</label>
                        <select
                            v-model="form.site"
                            class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                        >
                            <option v-for="opt in siteOptions" :key="opt.value" :value="opt.value">
                                {{ opt.label }}
                            </option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-gray-700 mb-1">Subscription</label>
                        <select
                            v-model="form.subscription"
                            class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                        >
                            <option v-for="opt in subscriptionOptions" :key="opt.value" :value="opt.value">
                                {{ opt.label }}
                            </option>
                        </select>
                    </div>
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-xs font-semibold text-gray-700 mb-1">Category</label>
                        <select
                            v-model="form.category"
                            class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                        >
                        <option 
                            v-for="opt in fieldOptions.category" 
                            :key="opt" 
                            :value="opt"
                        >
                            {{ opt }}
                        </option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-gray-700 mb-1">Severity</label>
                        <select
                            v-model="form.severity"
                            class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                        >
                        <option 
                            v-for="opt in fieldOptions.severity" 
                            :key="opt" 
                            :value="opt"
                        >
                            {{ opt }}
                        </option>
                        </select>
                    </div>
                </div>

                <div>
                    <label class="block text-xs font-semibold text-gray-700 mb-1">Description</label>
                    <textarea
                        v-model="form.description"
                        rows="5"
                        placeholder="Detailed explanation of what went wrong..."
                        class="w-full rounded-md border border-gray-300 bg-white p-3 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    ></textarea>
                </div>
            </div>

            <div class="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end border-t border-gray-100 pt-4">
                <Button variant="subtle" type="button" @click="showCreateModal = false">Cancel</Button>
                <Button variant="solid" class="!bg-primary" type="submit" :loading="creating">Submit Ticket</Button>
            </div>
        </form>
    </div>
</template>