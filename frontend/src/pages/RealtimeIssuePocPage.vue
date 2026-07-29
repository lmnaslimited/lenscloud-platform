<script>
import { createDocumentResource } from 'frappe-ui'
import { watchDocument } from '@/lib/realtime'

export default {
	name: 'RealtimeIssuePocPage',

	props: {
		name: {
			type: String,
			required: true,
		},
	},

	data() {
		return {
			issueResource: null,
			stopRealtime: null,
		}
	},

	created() {
		this.issueResource = createDocumentResource(
			{
				doctype: 'Issue',
				name: this.name,
				realtime: false,
			},
			this,
		)
	},

	mounted() {
		this.stopRealtime = watchDocument(this.$socket, {
			doctype: 'Issue',
			name: this.name,
			onUpdate: () => this.issueResource.reload(),
		})
	},

	beforeUnmount() {
		this.stopRealtime?.()
	},
}
</script>

<template>
	<div class="mx-auto max-w-3xl p-6">
		<h1 class="mb-6 text-xl font-semibold">Realtime Issue POC</h1>

		<div
			v-if="issueResource?.get?.loading && !issueResource?.doc"
			class="text-gray-500"
		>
			Loading issue…
		</div>

		<div
			v-else-if="issueResource?.doc"
			class="space-y-4 rounded-lg border bg-white p-6"
		>
			<div>
				<div class="text-sm text-gray-500">Name</div>
				<div>{{ issueResource.doc.name }}</div>
			</div>

			<div>
				<div class="text-sm text-gray-500">Subject</div>
				<div data-testid="issue-subject">
					{{ issueResource.doc.summary }}
				</div>
			</div>

			<div>
				<div class="text-sm text-gray-500">Status</div>
				<div data-testid="issue-status">
					{{ issueResource.doc.status }}
				</div>
			</div>

			<div>
				<div class="text-sm text-gray-500">Modified</div>
				<div data-testid="issue-modified">
					{{ issueResource.doc.modified }}
				</div>
			</div>
		</div>
	</div>
</template>