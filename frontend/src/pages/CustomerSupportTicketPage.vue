<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { Alert, Badge, Button, Dialog, FormControl, Input, Select, Textarea } from 'frappe-ui'
import { AlertCircle, Clock3, Headset, Plus, RefreshCcw } from 'lucide-vue-next'
import { callMethod } from '@/lib/api'
import WorkspaceLayout from '@/components/WorkspaceLayout.vue'
import posthog from 'posthog-js'

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
const form = ref({
    subject: '',
    site: '',
    subscription: '',
    category: 'Technical',
    severity: 'M',
    description: '',
})

const selectedTicket = computed(() => tickets.value.find((item) => item.name === selectedName.value) || tickets.value[0] || null)
const hasTickets = computed(() => tickets.value.length > 0)

// Check if user has active subscriptions in context
const hasSubscriptions = computed(() => {
    return (context.value?.subscriptions || []).length > 0
})

function statusClass(status) {
    if (['Resolved', 'Closed'].includes(status)) return 'bg-emerald-50 text-emerald-700'
    if (['Open', 'Reopened'].includes(status)) return 'bg-amber-50 text-amber-700'
    if (['Cancelled'].includes(status)) return 'bg-red-50 text-red-700'
    return 'bg-blue-50 text-blue-700'
}

function severityClass(severity) {
    if (['XL', 'L'].includes(severity)) return 'bg-red-50 text-red-700'
    if (severity === 'M') return 'bg-amber-50 text-amber-700'
    return 'bg-[#f2f4f6] text-[#64748B]'
}

function severityLabel(severity) {
    return { XS: 'Extra Small', S: 'Small', M: 'Medium', L: 'Large', XL: 'Extra Large' }[severity] || 'Not set'
}

function formatDate(value) {
    if (!value) return 'Not set'
    return new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
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
            if (route.query.ticket && tickets.value.some((item) => item.name === route.query.ticket)) selectedName.value = route.query.ticket
            if (!selectedName.value && tickets.value.length) selectedName.value = tickets.value[0].name
            if (selectedName.value) { loadComments(selectedName.value)}
        } else {
            tickets.value = []
        }
    } catch (err) {
        error.value = err?.message || 'Unable to load support tickets.'
    } finally {
        loading.value = false
    }
}

onMounted(load)

// Computed options derived from portal context
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
        severity: 'M',
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
                customer: context.value?.customer?.name || undefined,
                description: form.value.description,
            },
        },
    'POST'
)

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
        console.dir(err)

        createError.value = err?.message || 'Failed to create ticket. Please try again.'
    } finally {
        creating.value = false
    }
}

// Add these new reactive refs for file upload
const attachments = ref([])
const uploadingFile = ref(false)

// Upload file using callMethod
async function handleFileUpload(event) {
    const file = event.target.files[0]
    if (!file) return

    uploadingFile.value = true
    createError.value = ''

    const formData = new FormData()
    formData.append('file', file)
    formData.append('is_private', 1)

    try {
        // Using callMethod for file upload
        const response = await callMethod('upload_file', formData)
        const fileDoc = response.message || response
        if (fileDoc) {
            attachments.value.push(fileDoc)
        }
    } catch (err) {
        createError.value = err?.message || 'Failed to upload attachment.'
    } finally {
        uploadingFile.value = false
        event.target.value = '' // Reset file input
    }
}

function removeAttachment(index) {
    attachments.value.splice(index, 1)
}

// State for Ticket Comments
const comments = ref([])
const loadingComments = ref(false)
const newCommentText = ref('')
const postingComment = ref(false)
const commentError = ref('')

// Load comments whenever a selected ticket changes
async function loadComments(ticketName) {
    if (!ticketName) {
        comments.value = []
        return
    }
    loadingComments.value = true
    commentError.value = ''
    try {
        const response = await callMethod('frappe.client.get_list', {
            doctype: 'Comment',
            fields: ['name', 'comment_email', 'comment_by', 'content', 'creation'],
            filters: [
                ['reference_doctype', '=', 'Issue'],
                ['reference_name', '=', ticketName],
                ['comment_type', '=', 'Comment'],
            ],
            order_by: 'creation asc',
        })
        comments.value = response.message || response || []
    } catch (err) {
        commentError.value = 'Failed to load comments.'
    } finally {
        loadingComments.value = false
    }
}

// Post a new comment using callMethod
async function handleAddComment() {
    if (!newCommentText.value.trim() || !selectedTicket.value) return

    postingComment.value = true
    commentError.value = ''

    try {
        await callMethod('frappe.desk.form.utils.add_comment', {
            reference_doctype: 'Issue',
            reference_name: selectedTicket.value.name,
            content: newCommentText.value,
            comment_email: context.value?.customer?.email || undefined,
            comment_by: context.value?.customer?.customer_name || 'Customer',
        })

        newCommentText.value = ''
        // Reload comments list to display the newly added comment
        await loadComments(selectedTicket.value.name)
    } catch (err) {
        commentError.value = err?.message || 'Failed to post comment.'
    } finally {
        postingComment.value = false
    }
}

// Automatically reload comments when the selected ticket changes
watch(selectedName, (newName) => {
    if (newName) {
        loadComments(newName)
    }
})

</script>

<template>
    <WorkspaceLayout
        title="Support Tickets"
        subtitle="Review issues you've raised with LensCloud support."
        inspector-kicker="Your Ticket"
        :inspector-title="selectedTicket ? 'Ticket Details' : 'No Ticket Yet'"
        inspector-subtitle="Full status, severity, and description for the selected ticket."
    >
        <template #actions>
            <div class="flex items-center gap-2">
                <Button variant="subtle" class="!inline-flex !items-center !gap-2 whitespace-nowrap" @click="load">
                    <span class="flex items-center gap-2">
                        <RefreshCcw class="size-4" />
                        <span>Refresh</span>
                    </span>
                </Button>
                <!-- Only show New Ticket button if user has subscriptions -->
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

        <template #main>
            <div class="h-full overflow-y-auto bg-[#f7f9fb] p-4 lg:p-6">
                <Alert v-if="error" theme="red" title="Support tickets unavailable" :description="error" class="mb-4" />

                <!-- Alert banner shown if the user has no active subscriptions -->
                <Alert 
                    v-if="!loading && !hasSubscriptions" 
                    theme="blue" 
                    title="Subscription Required" 
                    class="mb-4"
                >
                    <template #description>
                        <p>
                        You currently do not have an active subscription. Please <RouterLink to="/customer/subscriptions" class="font-medium underline">subscribe to a plan</RouterLink> to raise support tickets.
                        </p>
                    </template>
                </Alert>

                <div v-if="loading" class="rounded-lg border border-[#EDEDED] bg-white p-6 text-sm text-[#64748B]">Loading support tickets...</div>

                <section v-else-if="!hasTickets" class="mx-auto grid min-h-[560px] max-w-4xl place-items-center rounded-xl border border-[#EDEDED] bg-white p-8 text-center">
                    <div class="max-w-lg">
                        <div class="mx-auto grid size-14 place-items-center rounded-xl bg-blue-200 text-primary"><Headset class="size-7" /></div>
                        <h2 class="mt-5 text-2xl font-semibold text-[#191c1e]">No Support Tickets Yet</h2>
                        <p class="mt-3 text-sm leading-6 text-[#64748B]">When you raise an issue with LensCloud support, it will show up here with its status and history.</p>
                        
                        <!-- CTA inside empty state -->
                        <div class="mt-6 flex justify-center">
                            <Button v-if="hasSubscriptions" variant="outline" @click="openCreateModal" class="!text-primary">
                                <span class="flex items-center gap-2 text-white">
                                    <Plus class="size-4 text-primary" />
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
                    <div class="mb-5">
                        <p class="text-xs font-semibold text-[#64748B]">Your Service</p>
                        <h2 class="mt-2 text-2xl font-semibold text-[#191c1e]">My Support Tickets</h2>
                        <p class="mt-2 text-sm leading-6 text-[#64748B]">Select a ticket to see its full details.</p>
                    </div>

                    <div class="grid gap-4 lg:grid-cols-3">
                        <article
                            v-for="ticket in tickets"
                            :key="ticket.name"
                            class="cursor-pointer rounded-xl border bg-white p-5 transition hover:-translate-y-0.5 hover:shadow-sm"
                            :class="selectedTicket?.name === ticket.name ? 'border-secondary' : 'border-[#EDEDED]'"
                            @click="
                                posthog.capture('support_ticket_selected', {
                                    ticket: ticket.name,
                                    status: ticket.status,
                                    category: ticket.category,
                                });
                                selectedName = ticket.name
                            "
                        >
                            <div class="flex items-start justify-between gap-3">
                                <div>
                                    <p class="text-lg font-semibold text-[#191c1e]"> {{ ticket.name }} </p>
                                    <p class="mt-1 text-xs text-[#64748B]"> {{ ticket.summary || ticket.subject || ticket.name }} </p>
                                </div>
                                <Badge :class="statusClass(ticket.status)">{{ ticket.status || 'Open' }}</Badge>
                            </div>
                            <div class="mt-5 space-y-3 text-sm text-[#434655]">
                                <div class="flex items-center gap-2"><AlertCircle class="size-4 text-[#64748B]" />Category: {{ ticket.category || 'Not set' }}</div>
                                <div class="flex items-center gap-2"><Clock3 class="size-4 text-[#64748B]" />Raised: {{ formatDate(ticket.creation) }}</div>
                                <div class="flex items-center gap-2">
                                    <Badge :class="severityClass(ticket.severity)">{{ severityLabel(ticket.severity) }}</Badge>
                                </div>
                            </div>
                        </article>
                    </div>
                </section>
            </div>
        </template>

        <template #inspector>
            <div v-if="selectedTicket" class="space-y-4">
                <div class="rounded-xl border border-[#EDEDED] bg-white p-4">
                    <p class="text-xs font-semibold text-[#64748B]">Ticket</p>
                    <h3 class="mt-2 text-base font-semibold text-[#191c1e]">{{ selectedTicket.summary || selectedTicket.subject || selectedTicket.name }}</h3>
                    <div class="mt-4 space-y-2 text-sm leading-6 text-[#505f76]">
                        <p>Ticket ID: <span class="font-medium text-[#191c1e]">{{ selectedTicket.name }}</span></p>
                        <p>Status: <span class="font-medium text-[#191c1e]">{{ selectedTicket.status || 'Open' }}</span></p>
                        <p>Severity: <span class="font-medium text-[#191c1e]">{{ severityLabel(selectedTicket.severity) }}</span></p>
                        <p>Category: <span class="font-medium text-[#191c1e]">{{ selectedTicket.category || 'Not set' }}</span></p>
                        <p>Source: <span class="font-medium text-[#191c1e]">{{ selectedTicket.source || 'Customer' }}</span></p>
                        <p>
                            Subscription:
                            <RouterLink v-if="selectedTicket.subscription" to="/customer/subscriptions" class="font-medium text-[#1D4ED8]">{{ selectedTicket.subscription }}</RouterLink>
                            <span v-else class="font-medium text-[#191c1e]">Not linked</span>
                        </p>
                        <p>
                            Site:
                            <RouterLink v-if="selectedTicket.site" :to="`/customer/sites/${encodeURIComponent(selectedTicket.site)}`" class="font-medium text-[#1D4ED8]">{{ selectedTicket.site }}</RouterLink>
                            <span v-else class="font-medium text-[#191c1e]">Not linked</span>
                        </p>
                        <p>Raised on: <span class="font-medium text-[#191c1e]">{{ formatDate(selectedTicket.creation) }}</span></p>
                        <p>Last synced: <span class="font-medium text-[#191c1e]">{{ formatDate(selectedTicket.last_sync) }}</span></p>
                    </div>
                </div>

                <div class="rounded-xl border border-[#EDEDED] bg-[#f7f9fb] p-4">
                    <p class="text-sm font-semibold text-[#191c1e]">Summary</p>
                    <p class="mt-2 text-sm leading-6 text-[#64748B]">{{ selectedTicket.summary || selectedTicket.subject || 'No summary provided.' }}</p>
                </div>

                <div class="rounded-xl border border-[#EDEDED] bg-[#f7f9fb] p-4">
                    <p class="text-sm font-semibold text-[#191c1e]">Description</p>
                    <div class="prose prose-sm mt-2 max-w-none text-[#64748B]" v-html="selectedTicket.description || '<p>No description provided.</p>'" />
                </div>
                <!-- COMMENTS SECTION -->
        <div class="rounded-xl border border-[#EDEDED] bg-white p-4">
            <h4 class="text-sm font-semibold text-[#191c1e] mb-3">Activity & Comments</h4>

            <Alert v-if="commentError" theme="red" :description="commentError" class="mb-3" />

            <!-- Comments Timeline List -->
            <div v-if="loadingComments" class="text-xs text-gray-500 py-2">Loading activity...</div>

            <div v-else-if="comments.length === 0" class="text-xs text-gray-400 py-2">
                No comments yet. Start the conversation below.
            </div>

            <div v-else class="space-y-3 max-h-80 overflow-y-auto pr-1 mb-4">
                <div
                    v-for="comment in comments"
                    :key="comment.name"
                    class="rounded-lg bg-gray-50 p-3 text-xs border border-gray-100"
                >
                    <div class="flex items-center justify-between text-gray-500 mb-1">
                        <span class="font-semibold text-gray-800">{{ comment.comment_by || comment.comment_email || 'User' }}</span>
                        <span>{{ formatDate(comment.creation) }}</span>
                    </div>
                    <div class="text-gray-700 leading-relaxed prose prose-xs max-w-none" v-html="comment.content" />
                </div>
            </div>

            <!-- Add Comment Form -->
            <div class="mt-3 pt-3 border-t border-gray-100">
                <textarea
                    v-model="newCommentText"
                    rows="3"
                    placeholder="Write a reply or add a comment..."
                    class="w-full rounded-lg border border-gray-300 p-2.5 text-xs text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                ></textarea>
                <div class="mt-2 flex justify-end">
                    <Button
                        variant="solid"
                        class="!bg-secondary"
                        size="sm"
                        :loading="postingComment"
                        :disabled="!newCommentText.trim()"
                        @click="handleAddComment"
                    >
                        Send Comment
                    </Button>
                </div>
            </div>
        </div>
            </div>
            <div v-else class="rounded-xl border border-[#EDEDED] bg-white p-4 text-sm leading-6 text-[#64748B]">Select a ticket to view its details.</div>
        </template>
    </WorkspaceLayout>

   <!-- Custom Ticket Modal Overlay -->
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
            <!-- Header -->
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

            <!-- Error Alert -->
            <Alert v-if="createError" theme="red" :description="createError" class="mt-4" />

            <!-- Body Fields -->
            <div class="mt-4 space-y-4">
                <!-- Subject -->
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

                <!-- Site & Subscription Select -->
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

                <!-- Category & Severity Select -->
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-xs font-semibold text-gray-700 mb-1">Category</label>
                        <select
                            v-model="form.category"
                            class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                        >
                            <option value="Technical">Technical</option>
                            <option value="Miscellaneous">Miscellaneous</option>
                            <option value="Others">Others</option>
                        </select>
                    </div>

                    <div>
                        <label class="block text-xs font-semibold text-gray-700 mb-1">Severity</label>
                        <select
                            v-model="form.severity"
                            class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                        >
                            <option value="XS">Extra Small (XS)</option>
                            <option value="S">Small (S)</option>
                            <option value="M">Medium (M)</option>
                            <option value="L">Large (L)</option>
                            <option value="XL">Extra Large (XL)</option>
                        </select>
                    </div>
                </div>

                <!-- Description (Multiline Long Text Area) -->
                <div>
                    <label class="block text-xs font-semibold text-gray-700 mb-1">Description</label>
                    <textarea
                        v-model="form.description"
                        rows="5"
                        placeholder="Detailed explanation of what went wrong..."
                        class="w-full rounded-md border border-gray-300 bg-white p-3 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    ></textarea>
                </div>

                <!-- Attachments Field -->
                <!-- <div>
                    <label class="block text-xs font-semibold text-gray-700 mb-1">Attachments</label>
                    <div class="flex items-center gap-3">
                        <input
                            type="file"
                            id="custom-file-upload"
                            class="hidden"
                            @change="handleFileUpload"
                        />
                        <label
                            for="custom-file-upload"
                            class="cursor-pointer inline-flex items-center gap-2 rounded-md border border-gray-300 bg-white px-3 py-2 text-xs font-medium text-gray-700 hover:bg-gray-50 transition"
                        >
                            <Paperclip class="size-4 text-gray-500" />
                            <span>{{ uploadingFile ? 'Uploading...' : 'Attach File' }}</span>
                        </label>
                    </div> -->

                    <!-- Attached Files List -->
                    <!-- <div v-if="attachments.length" class="mt-3 flex flex-wrap gap-2">
                        <div
                            v-for="(file, idx) in attachments"
                            :key="file.file_url || idx"
                            class="inline-flex items-center gap-2 rounded-md bg-gray-100 px-3 py-1 text-xs text-gray-800 border border-gray-200"
                        >
                            <span class="truncate max-w-[200px]">{{ file.file_name }}</span>
                            <button
                                type="button"
                                class="text-red-500 hover:text-red-700"
                                @click="removeAttachment(idx)"
                            >
                                <X class="size-3.5" />
                            </button>
                        </div>
                    </div> -->
                <!-- </div> -->
            </div>

            <!-- Footer Actions -->
            <div class="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end border-t border-gray-100 pt-4">
                <Button variant="subtle" type="button" @click="showCreateModal = false">Cancel</Button>
                <Button variant="solid" class="!bg-primary" type="submit" :loading="creating || uploadingFile">Submit Ticket</Button>
            </div>
        </form>
    </div>

</template>