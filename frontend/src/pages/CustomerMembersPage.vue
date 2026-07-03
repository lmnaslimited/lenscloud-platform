<script setup>
import { computed, onMounted, ref } from 'vue'
import { Alert, Badge, Button } from 'frappe-ui'
import { CheckCircle2, ShieldCheck, UserRound, UsersRound } from 'lucide-vue-next'
import { callMethod } from '@/lib/api'
import WorkspaceLayout from '@/components/WorkspaceLayout.vue'

const loading = ref(true)
const error = ref('')
const actionError = ref('')
const actionState = ref('idle')
const members = ref([])
const access = ref(null)

const pendingMembers = computed(() => members.value.filter((member) => member.status === 'Pending'))
const activeMembers = computed(() => members.value.filter((member) => member.status === 'Active'))
const canManage = computed(() => Boolean(access.value?.can_manage_members))

function statusTone(status) {
	if (status === 'Active') return 'bg-emerald-50 text-emerald-700'
	if (status === 'Pending') return 'bg-amber-50 text-amber-700'
	return 'bg-surface-gray-2 text-ink-gray-6'
}

async function load() {
	loading.value = true
	error.value = ''
	actionError.value = ''
	try {
		const accessResponse = await callMethod('lenscloud.api.customer_identity.get_customer_access_context')
		access.value = accessResponse.message || accessResponse
		if (access.value?.can_manage_members) {
			const response = await callMethod('lenscloud.api.customer_identity.list_customer_members')
			members.value = response.message || response || []
		} else {
			members.value = []
		}
	} catch (err) {
		error.value = err?.message || 'Unable to load customer members.'
	} finally {
		loading.value = false
	}
}

async function approve(member, role = 'Member') {
	actionState.value = member.name
	actionError.value = ''
	try {
		await callMethod('lenscloud.api.customer_identity.approve_customer_member', { member: member.name, member_role: role }, 'POST')
		await load()
	} catch (err) {
		actionError.value = err?.message || 'Unable to approve this member.'
	} finally {
		actionState.value = 'idle'
	}
}

onMounted(load)
</script>

<template>
	<WorkspaceLayout
		title="Members"
		subtitle="Approve customer team access using LensCloud roles and native permissions."
		inspector-kicker="Access"
		inspector-title="Customer Members"
		inspector-subtitle="Membership is scoped to your Customer. Platform still owns the broader CUA model."
		mobile-inspector-label="Member Details"
	>
		<template #main>
			<div class="h-full overflow-y-auto bg-[#f7f9fb] p-4 lg:p-6">
				<Alert v-if="error" theme="red" title="Members unavailable" :description="error" class="mb-4" />
				<Alert v-if="actionError" theme="red" title="Member action failed" :description="actionError" class="mb-4" />
				<div v-if="loading" class="rounded-xl border border-[#EDEDED] bg-white p-6 text-sm text-[#64748B]">Loading members...</div>

				<section v-else-if="!canManage" class="mx-auto grid min-h-[520px] max-w-3xl place-items-center rounded-2xl border border-[#EDEDED] bg-white p-8 text-center">
					<div>
						<div class="mx-auto grid size-14 place-items-center rounded-2xl bg-[#dce1ff] text-[#1D4ED8]"><ShieldCheck class="size-7" /></div>
						<h2 class="mt-5 text-2xl font-semibold text-[#191c1e]">Member approval is for Customer admins</h2>
						<p class="mt-3 max-w-xl text-sm leading-6 text-[#64748B]">Your current LensCloud role can use the customer portal, but it does not include access to approve members. A Customer admin or Platform operator can update your role if needed.</p>
					</div>
				</section>

				<section v-else class="mx-auto max-w-5xl space-y-5">
					<div class="rounded-2xl border border-[#EDEDED] bg-white p-6">
						<div class="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
							<div>
								<p class="text-xs font-semibold text-[#64748B]">Team Access</p>
								<h2 class="mt-2 text-2xl font-semibold text-[#191c1e]">Review Customer Members</h2>
								<p class="mt-2 text-sm leading-6 text-[#64748B]">Approve pending same-domain signups only when they belong to your organization.</p>
							</div>
							<Button variant="subtle" @click="load">Refresh</Button>
						</div>
					</div>

					<div class="grid gap-4 lg:grid-cols-[1fr_1fr]">
						<section class="rounded-2xl border border-[#EDEDED] bg-white p-5">
							<div class="flex items-center gap-2"><UsersRound class="size-5 text-[#1D4ED8]" /><h3 class="text-lg font-semibold text-[#191c1e]">Pending Approval</h3></div>
							<p v-if="!pendingMembers.length" class="mt-4 rounded-lg border border-dashed border-[#EDEDED] bg-[#f7f9fb] p-4 text-sm text-[#64748B]">No pending members right now.</p>
							<div v-else class="mt-4 space-y-3">
								<article v-for="member in pendingMembers" :key="member.name" class="rounded-xl border border-[#EDEDED] bg-[#f7f9fb] p-4">
									<div class="flex items-start justify-between gap-3">
										<div class="min-w-0"><p class="truncate text-sm font-semibold text-[#191c1e]">{{ member.user }}</p><p class="mt-1 text-xs text-[#64748B]">{{ member.source || 'Signup' }}</p></div>
										<Badge :class="statusTone(member.status)">{{ member.status }}</Badge>
									</div>
									<div class="mt-4 flex flex-wrap gap-2">
										<Button size="sm" :disabled="actionState === member.name" @click="approve(member, 'Member')">Approve Member</Button>
										<Button size="sm" variant="subtle" :disabled="actionState === member.name" @click="approve(member, 'Admin')">Approve Admin</Button>
									</div>
								</article>
							</div>
						</section>

						<section class="rounded-2xl border border-[#EDEDED] bg-white p-5">
							<div class="flex items-center gap-2"><CheckCircle2 class="size-5 text-emerald-600" /><h3 class="text-lg font-semibold text-[#191c1e]">Active Members</h3></div>
							<div class="mt-4 space-y-3">
								<article v-for="member in activeMembers" :key="member.name" class="rounded-xl border border-[#EDEDED] bg-[#f7f9fb] p-4">
									<div class="flex items-start justify-between gap-3"><div class="min-w-0"><p class="truncate text-sm font-semibold text-[#191c1e]">{{ member.user }}</p><p class="mt-1 text-xs text-[#64748B]">{{ member.member_role }}</p></div><Badge :class="statusTone(member.status)">{{ member.status }}</Badge></div>
								</article>
							</div>
						</section>
					</div>
				</section>
			</div>
		</template>

		<template #inspector>
			<div class="space-y-4">
				<div class="rounded-xl border border-[#EDEDED] bg-white p-4"><p class="text-sm font-semibold text-[#191c1e]">Native Permission Model</p><p class="mt-2 text-sm leading-6 text-[#64748B]">This page appears only when the current user can read Customer Member through Frappe permissions. Approval checks write permission again on the server.</p></div>
				<div class="rounded-xl border border-[#EDEDED] bg-[#f7f9fb] p-4"><p class="text-sm font-semibold text-[#191c1e]">Customer Scope Guardrail</p><p class="mt-2 text-sm leading-6 text-[#64748B]">Member rows are always filtered to the active Customer membership. If a Customer User Permission is missing, this membership scope still prevents cross-customer visibility.</p></div>
			</div>
		</template>
	</WorkspaceLayout>
</template>
