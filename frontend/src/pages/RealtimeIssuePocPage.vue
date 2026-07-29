<script>
import { createDocumentResource } from 'frappe-ui'
import { watchDocument } from '@/lib/realtime'

export default {
	name: 'RealtimeIssuePocPage',
	props: {
		name: { type: String, required: true },
	},
	data() {
		return { issueResource: null, stopRealtime: null, updateCount: 0 }
	},
	created() {
		this.issueResource = createDocumentResource(
			{ doctype: 'Issue', name: this.name, realtime: false, auto: true },
			this,
		)
	},
	mounted() {
		this.stopRealtime = watchDocument(this.$socket, {
			doctype: 'Issue',
			name: this.name,
			onUpdate: () => {
				this.updateCount += 1
				return this.issueResource.reload()
			},
		})
	},
	beforeUnmount() {
		this.stopRealtime?.()
	},
}
</script>

<template>
	<section class="mx-auto max-w-3xl space-y-5 p-6" aria-labelledby="issue-title">
		<header>
			<p class="text-sm text-gray-500">Customer support</p>
			<h1 id="issue-title" class="text-xl font-semibold">Realtime Issue POC</h1>
		</header>
		<LoadingIndicator v-if="issueResource?.get?.loading && !issueResource?.doc" />
		<ErrorMessage v-else-if="issueResource?.get?.error" :message="issueResource.get.error" />
		<div v-else-if="issueResource?.doc" class="space-y-4 rounded-lg border bg-white p-5">
			<div>
				<p class="text-sm text-gray-500">Issue</p>
				<p data-testid="issue-name">{{ issueResource.doc.name }}</p>
			</div>
			<div>
				<p class="text-sm text-gray-500">Summary</p>
				<p data-testid="issue-summary">{{ issueResource.doc.summary }}</p>
			</div>
			<div>
				<p class="text-sm text-gray-500">Status</p>
				<p data-testid="issue-status">{{ issueResource.doc.status }}</p>
			</div>
			<p class="text-xs text-gray-500" data-testid="issue-modified">
				Updated {{ issueResource.doc.modified }}
			</p>
			<span class="sr-only" data-testid="issue-update-count">{{ updateCount }}</span>
		</div>
	</section>
</template>
