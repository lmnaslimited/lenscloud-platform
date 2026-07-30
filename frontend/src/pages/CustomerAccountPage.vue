<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { Alert, Badge, Button, TextInput } from 'frappe-ui'
import { Building2, Headset, CreditCard, ExternalLink, LifeBuoy, LockKeyhole, MapPin, ShieldCheck, UserRound, UsersRound } from 'lucide-vue-next'
import { callMethod } from '@/lib/api'
import WorkspaceLayout from '@/components/WorkspaceLayout.vue'
import { useSessionStore } from '@/lib/session'

const route = useRoute()
const router = useRouter()
const session = useSessionStore()
const loading = ref(true)
const error = ref('')
const saveState = ref('idle')
const customer = ref(null)
const context = ref(null)
const formState = reactive({ first_name: '', last_name: '', region: '', external_customer_id: '' })
const passwordDialogOpen = ref(false)
const passwordState = ref('idle')
const passwordError = ref('')
const passwordSuccess = ref('')
const passwordForm = reactive({ old_password: '', new_password: '', confirm_password: '' })

const subscriptions = computed(() => context.value?.subscriptions || [])
const usage = computed(() => context.value?.usage || {})
const settings = computed(() => context.value?.settings || {})
const primarySubscription = computed(() => subscriptions.value[0] || null)
// const displayName = computed(() => [formState.first_name, formState.last_name].filter(Boolean).join(' ') || customer.value?.name || session.user)
const displayName = computed(() => {
  const name = [formState.first_name, formState.last_name].filter(Boolean).join(' ')
  return name || context.value?.user?.full_name || session.user
})
const accountInitial = computed(() => (displayName.value || 'L').slice(0, 1).toUpperCase())
const regionLabel = computed(() => formState.region || context.value?.customer?.region || 'Not selected')
const membership = computed(() => context.value?.membership || customer.value || {})
const membershipPending = computed(() => membership.value?.status === 'Pending' || membership.value?.membership_status === 'Pending')
const accountStatus = computed(() => membershipPending.value ? 'Waiting For Approval' : customer.value ? 'Linked And Ready' : 'Needs Customer Link')

async function load() {
	loading.value = true
	error.value = ''
	try {
		const portalResponse = await callMethod('lenscloud.api.orchestration.get_customer_portal_context')
		context.value = portalResponse.message || portalResponse
		customer.value = context.value?.customer || null
		// Extract user details directly from context
		const userData = context.value?.user || {}
		if (customer.value) {
			for (const key of Object.keys(formState)) formState[key] = customer.value[key] || ''
		}
		// Populate formState directly from User Doctype data
		formState.first_name = userData.first_name || ''
    	formState.last_name = userData.last_name || ''
	} catch (err) {
		error.value = err?.message || 'Unable to load account.'
	} finally {
		loading.value = false
	}
}

function resetPasswordForm() {
	passwordForm.old_password = ''
	passwordForm.new_password = ''
	passwordForm.confirm_password = ''
	passwordError.value = ''
	passwordSuccess.value = ''
	passwordState.value = 'idle'
}

function openPasswordDialog() {
	resetPasswordForm()
	passwordDialogOpen.value = true
}

function closePasswordDialog() {
	passwordDialogOpen.value = false
	const nextQuery = { ...route.query }
	delete nextQuery.changePassword
	if (route.query.changePassword) router.replace({ path: route.path, query: nextQuery })
}

async function submitPasswordChange() {
	passwordError.value = ''
	passwordSuccess.value = ''
	if (!passwordForm.old_password || !passwordForm.new_password || !passwordForm.confirm_password) {
		passwordError.value = 'Enter your current password, new password, and confirmation.'
		return
	}
	if (passwordForm.new_password !== passwordForm.confirm_password) {
		passwordError.value = 'New password and confirmation do not match.'
		return
	}
	passwordState.value = 'saving'
	try {
		await callMethod('frappe.core.doctype.user.user.update_password', {
			old_password: passwordForm.old_password,
			new_password: passwordForm.new_password,
			logout_all_sessions: 0,
		}, 'POST')
		passwordSuccess.value = 'Password updated. Your current session remains active.'
		passwordForm.old_password = ''
		passwordForm.new_password = ''
		passwordForm.confirm_password = ''
		passwordState.value = 'saved'
	} catch (err) {
		passwordState.value = 'error'
		passwordError.value = err?.message || 'Unable to update password. Check your current password and try again.'
	}
}

async function save() {
	if (!customer.value) return
	saveState.value = 'saving'
	error.value = ''
	try {
		const response = await callMethod('lenscloud.api.orchestration.update_customer_account', {
			first_name: formState.first_name,
			last_name: formState.last_name
		}, 'POST')
		customer.value = response.message || response
		saveState.value = 'saved'
		await load()
	} catch (err) {
		saveState.value = 'error'
		error.value = err?.message || 'Unable to save account details.'
	}
}

const trustCards = computed(() => [
	{ label: 'Signed In', value: session.user, icon: UserRound, tone: 'blue' },
	{ label: 'Customer Record', value: customer.value?.name || 'Not Linked', icon: Building2, tone: membershipPending.value ? 'amber' : customer.value ? 'green' : 'amber' },
	{ label: 'Default Region', value: regionLabel.value, icon: MapPin, tone: 'blue' },
	{ label: 'Subscriptions', value: usage.value.subscriptions || 0, icon: CreditCard, tone: 'blue', route: '/customer/subscriptions' },
])

const inspectorItems = computed(() => [
	{ label: 'Customer', value: customer.value?.name || 'No linked Customer' },
	{ label: 'Signed-In User', value: session.user },
	{ label: 'Membership', value: membership.value?.status || customer.value?.membership_status || 'Unknown' },
	{ label: 'Role', value: membership.value?.member_role || 'Customer' },
	{ label: 'Default Region', value: regionLabel.value },
	{ label: 'Active Subscriptions', value: usage.value.subscriptions || 0 },
	// { label: 'Support System', value: settings.value.support_system || 'Platform-managed' },
])

onMounted(load)
watch(() => route.query.changePassword, (value) => { if (value === '1') openPasswordDialog() }, { immediate: true })
</script>

<template>
	<WorkspaceLayout
		title="Account"
		subtitle="Identity, organization, and access for your LensCloud relationship."
		inspector-kicker="Identity Context"
		:inspector-title="customer ? 'Account Linked' : 'Account Needs Attention'"
		inspector-subtitle="Account is for identity and trust. Service progress stays in Subscriptions."
		mobile-inspector-label="Account Details"
	>
		<template #main>
			<div class="h-full overflow-y-auto bg-[#f7f9fb] p-4 lg:p-6">
				<Alert v-if="error" theme="red" title="Account unavailable" :description="error" class="mb-4" />
				<div v-if="loading" class="rounded-xl border border-[#EDEDED] bg-white p-6 text-sm text-[#64748B]">Loading your account...</div>

				<section v-else class="mx-auto max-w-6xl space-y-4">
					<Alert v-if="membershipPending" theme="amber" title="Approval needed before provisioning" description="Your email matches an existing LensCloud Customer domain. You can sign in, but a Customer admin or Platform operator must approve your membership before you can start subscriptions or Sites." />
					<div class="rounded-2xl border border-[#EDEDED] bg-white p-6 lg:p-8">
						<div class="grid gap-6 lg:grid-cols-[1fr_320px] lg:items-center">
							<div>
								<div class="inline-flex items-center gap-2 rounded-full border border-primary bg-surface-gray-4 px-3 py-1 text-xs font-semibold text-primary">
									<ShieldCheck class="size-3.5" />
									Your LensCloud Identity
								</div>
								<h2 class="mt-5 text-[28px] font-bold leading-9 text-[#191c1e] lg:text-[34px] lg:leading-[42px]">This is where your team learns to trust the platform.</h2>
								<p class="mt-4 max-w-2xl text-sm leading-6 text-[#505f76]">Account keeps identity, organization, and access clear. Dashboard stays focused on your service journey; Subscriptions carries setup progress.</p>
								<div class="mt-6 flex flex-wrap gap-3">
									<RouterLink to="/customer/subscriptions" class="inline-flex min-h-10 items-center justify-center gap-2 whitespace-nowrap rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-secondary"><span>View Subscriptions</span><ExternalLink class="size-4 shrink-0" /></RouterLink>
									<RouterLink to="/customer/plans" class="inline-flex min-h-10 items-center justify-center gap-2 whitespace-nowrap rounded-lg bg-[#f2f4f6] px-4 py-2 text-sm font-semibold text-[#434655] transition hover:bg-[#e8ecf1]"><span>Add New Subscription</span></RouterLink>
								</div>
							</div>
							<div class="rounded-xl border border-[#EDEDED] bg-[#f7f9fb] p-5 text-center">
								<div class="mx-auto grid size-16 place-items-center rounded-2xl bg-primary text-2xl font-bold text-white">{{ accountInitial }}</div>
								<h3 class="mt-4 text-lg font-semibold text-[#191c1e]">{{ displayName }}</h3>
								<p class="mt-1 break-all text-sm text-[#64748B]">{{ session.user }}</p>
								<Badge class="mt-4" :class="membershipPending ? 'bg-amber-50 text-amber-700' : customer ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'">{{ accountStatus }}</Badge>
							</div>
						</div>
					</div>

					<div class="grid gap-3 md:grid-cols-4">
						<component :is="card.route ? RouterLink : 'div'" v-for="card in trustCards" :key="card.label" :to="card.route" class="rounded-xl border border-[#EDEDED] bg-white p-4 transition" :class="card.route ? 'hover:border-primary hover:bg-[#f7f9fb]' : ''">
							<div class="flex items-center justify-between gap-3">
								<p class="text-xs font-semibold text-[#64748B]">{{ card.label }}</p>
								<component :is="card.icon" class="size-4" :class="card.tone === 'green' ? 'text-emerald-600' : card.tone === 'amber' ? 'text-amber-600' : 'text-primary'" />
							</div>
							<p class="mt-3 truncate text-sm font-semibold text-[#191c1e]">{{ card.value }}</p>
						</component>
					</div>

					<div class="grid gap-4 lg:grid-cols-[1fr_1fr]">
						<section class="rounded-2xl border border-[#EDEDED] bg-white p-5">
							<div class="flex items-start justify-between gap-3">
								<div><p class="text-xs font-semibold text-[#64748B]">Profile</p><h3 class="mt-2 text-lg font-semibold text-[#191c1e]">Your Account Details</h3>
									<!-- <p class="mt-1 text-sm leading-6 text-[#64748B]">Keep the basics right so every LensCloud handoff feels personal.</p> -->
								</div>
								<Badge v-if="saveState === 'saved'" class="bg-emerald-50 text-emerald-700">Saved</Badge>
								<Badge v-else-if="saveState === 'saving'" class="bg-blue-50 text-blue-700">Saving</Badge>
								<Badge v-else-if="saveState === 'error'" class="bg-red-50 text-red-700">Needs retry</Badge>
							</div>
							<!-- <div v-if="!customer" class="mt-5 rounded-lg border border-dashed border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-800">No Customer Record is linked to this signed-in user yet. Platform should link the Customer before subscriptions and access can feel complete.</div>
							<div v-else class="mt-5 grid gap-3 sm:grid-cols-2">
								<label class="space-y-1.5"><span class="text-xs font-semibold text-[#64748B]">First Name</span><TextInput v-model="formState.first_name" /></label>
								<label class="space-y-1.5"><span class="text-xs font-semibold text-[#64748B]">Last Name</span><TextInput v-model="formState.last_name" /></label>
								<label class="space-y-1.5"><span class="text-xs font-semibold text-[#64748B]">Default Region</span><TextInput v-model="formState.region" placeholder="Region" /></label>
								<label class="space-y-1.5"><span class="text-xs font-semibold text-[#64748B]">Customer Reference</span><TextInput v-model="formState.external_customer_id" placeholder="CRM or billing reference" /></label>
								<div class="sm:col-span-2"><Button :disabled="saveState === 'saving'" @click="save">{{ saveState === 'saving' ? 'Saving...' : 'Save account details' }}</Button></div>
							</div> -->
							<div class="mt-5 grid gap-3 sm:grid-cols-2">
								<label class="space-y-1.5"><span class="text-xs font-semibold text-[#64748B]">First Name</span><TextInput v-model="formState.first_name" /></label>
								<label class="space-y-1.5"><span class="text-xs font-semibold text-[#64748B]">Last Name</span><TextInput v-model="formState.last_name" /></label>
								<label class="space-y-1.5"><span class="text-xs font-semibold text-[#64748B]">Default Region</span><TextInput v-model="formState.region" placeholder="Region" :disabled="true" class="bg-gray-100 cursor-not-allowed" /></label>
								<label class="space-y-1.5"><span class="text-xs font-semibold text-[#64748B] hidden">Customer Reference</span><TextInput v-model="formState.external_customer_id" placeholder="Support or billing reference" :disabled="true" class="bg-gray-100 cursor-not-allowed hidden" /></label>
								<div class="sm:col-span-2"><Button :disabled="saveState === 'saving'" @click="save">{{ saveState === 'saving' ? 'Saving...' : 'Save account details' }}</Button></div>
							</div>
						</section>

						<section class="rounded-2xl border border-[#EDEDED] bg-white p-5">
							<p class="text-xs font-semibold text-[#64748B]">Access</p>
							<h3 class="mt-2 text-lg font-semibold text-[#191c1e]">Central User Access</h3>
							<p class="mt-2 text-sm leading-6 text-[#64748B]">LensCloud Platform will be the access home for your team. You will sign in here, invite users here, and reach Sites through platform-governed access.</p>
							<div class="mt-5 space-y-3">
								<div class="flex gap-3 rounded-lg border border-[#EDEDED] bg-[#f7f9fb] p-3"><LockKeyhole class="mt-0.5 size-4 text-primary" /><div><p class="text-sm font-semibold text-[#191c1e]">Site Access Is Platform-Managed</p><p class="text-xs leading-5 text-[#64748B]">Customers should not manage users independently inside each Site.</p></div></div>
								<div class="flex gap-3 rounded-lg border border-[#EDEDED] bg-[#f7f9fb] p-3"><UsersRound class="mt-0.5 size-4 text-primary" /><div><p class="text-sm font-semibold text-[#191c1e]">Team Invites</p><p class="text-xs leading-5 text-[#64748B]">Coming soon: invite users, assign customer roles, and audit access.</p></div></div>
								<div class="flex gap-3 rounded-lg border border-[#EDEDED] bg-[#f7f9fb] p-3"><LifeBuoy class="mt-0.5 size-4 text-primary" /><div><p class="text-sm font-semibold text-[#191c1e]">Support And Billing Contacts</p>
									<!-- <p class="text-xs leading-5 text-[#64748B]">{{ settings.support_system || 'Support' }} and {{ settings.billing_system || 'billing' }} details will connect here as external systems mature.</p> -->
									<a class="mt-4 inline-flex items-center gap-2 rounded-lg border border-[#EDEDED] bg-primary px-3 py-2 text-sm font-semibold text-white hover:bg-secondary" href="mailto:hello@lmnas.com">
									<Headset class="size-4" />Contact support</a>
								</div></div>
							</div>
						</section>
					</div>
				</section>
			</div>
		</template>

		<template #inspector>
			<div class="space-y-4">
				<div class="rounded-xl border border-[#EDEDED] bg-white p-4">
					<p class="text-xs font-semibold text-[#64748B]">Identity Context</p>
					<div class="mt-4 space-y-3">
						<div v-for="item in inspectorItems" :key="item.label" class="rounded-lg border border-[#EDEDED] bg-[#f7f9fb] px-3 py-2"><p class="text-xs text-[#64748B]">{{ item.label }}</p><p class="mt-1 truncate text-sm font-semibold text-[#191c1e]">{{ item.value }}</p></div>
					</div>
				</div>
				<!-- <div class="rounded-xl border border-[#EDEDED] bg-[#f7f9fb] p-4">
					<p class="text-sm font-semibold text-[#191c1e]">What Belongs Here</p>
					<ul class="mt-3 space-y-2 text-sm leading-6 text-[#64748B]"><li>Identity and organization truth.</li><li>Customer access model and future invites.</li><li>Support and billing contact context.</li></ul>
				</div> -->
				<!-- <div class="rounded-xl border border-[#EDEDED] bg-white p-4">
					<p class="text-sm font-semibold text-[#191c1e]">Service Work Stays In Subscriptions</p>
					<p class="mt-2 text-sm leading-6 text-[#64748B]">Provisioning, Plan changes, and Site progress belong in Subscriptions so Account stays calm and trustworthy.</p>
					<RouterLink to="/customer/subscriptions" class="mt-3 inline-flex min-h-10 items-center justify-center gap-2 whitespace-nowrap rounded-lg bg-[#f2f4f6] px-4 py-2 text-sm font-semibold text-[#434655] transition hover:bg-[#e8ecf1]"><span>Open Subscriptions</span></RouterLink>
				</div> -->
			</div>
		</template>
	</WorkspaceLayout>

	<div v-if="passwordDialogOpen" class="fixed inset-0 z-[1000] grid place-items-center bg-black/30 px-4 py-6" role="presentation" @mousedown.self="closePasswordDialog">
		<section role="dialog" aria-modal="true" aria-labelledby="customer-password-title" class="w-full max-w-md rounded-2xl border border-[#EDEDED] bg-white shadow-2xl">
			<form class="space-y-4 p-5" @submit.prevent="submitPasswordChange">
				<div>
					<h2 id="customer-password-title" class="text-base font-semibold text-[#191c1e]">Change Password</h2>
					<p class="mt-2 text-sm leading-6 text-[#64748B]">Update your LensCloud sign-in password without leaving Account. Your current session stays active after a successful change.</p>
				</div>
				<Alert v-if="passwordError" theme="red" title="Password not updated" :description="passwordError" />
				<Alert v-if="passwordSuccess" theme="green" title="Password updated" :description="passwordSuccess" />
				<label class="block space-y-1.5">
					<span class="text-xs font-semibold text-[#64748B]">Current Password</span>
					<input v-model="passwordForm.old_password" type="password" autocomplete="current-password" aria-label="Current Password" class="block h-9 w-full rounded-md border border-[#EDEDED] bg-white px-3 text-sm outline-none focus:border-[#1D4ED8] focus:ring-2 focus:ring-[#dce1ff]" />
				</label>
				<label class="block space-y-1.5">
					<span class="text-xs font-semibold text-[#64748B]">New Password</span>
					<input v-model="passwordForm.new_password" type="password" autocomplete="new-password" aria-label="New Password" class="block h-9 w-full rounded-md border border-[#EDEDED] bg-white px-3 text-sm outline-none focus:border-[#1D4ED8] focus:ring-2 focus:ring-[#dce1ff]" />
				</label>
				<label class="block space-y-1.5">
					<span class="text-xs font-semibold text-[#64748B]">Confirm New Password</span>
					<input v-model="passwordForm.confirm_password" type="password" autocomplete="new-password" aria-label="Confirm New Password" class="block h-9 w-full rounded-md border border-[#EDEDED] bg-white px-3 text-sm outline-none focus:border-[#1D4ED8] focus:ring-2 focus:ring-[#dce1ff]" />
				</label>
				<div class="flex flex-col-reverse gap-2 pt-2 sm:flex-row sm:justify-end">
					<Button variant="subtle" @click="closePasswordDialog">Cancel</Button>
					<Button type="submit" variant="solid" :disabled="passwordState === 'saving'">{{ passwordState === 'saving' ? 'Updating...' : 'Update Password' }}</Button>
				</div>
			</form>
		</section>
	</div>

</template>
