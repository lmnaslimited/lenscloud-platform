<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { X } from 'lucide-vue-next'
import { Badge, Button } from 'frappe-ui'

const props = defineProps({
	actions: {
		type: Array,
		default: () => [],
	},
	contextLabel: {
		type: String,
		default: 'record',
	},
	allowPrimaryAction: {
		type: Boolean,
		default: false,
	},
})

const emit = defineEmits(['submit'])
const openAction = ref(null)
const state = reactive({})

const activeAction = computed(() => props.actions.find((action) => action.key === openAction.value) || null)

function resetState(action) {
	state[action.key] = {}
	for (const field of action.fields || []) {
		state[action.key][field.key] = ''
	}
}

function open(action) {
	openAction.value = action.key
	if (!state[action.key]) {
		resetState(action)
	}
}

function close() {
	openAction.value = null
}

function submit(action) {
	emit('submit', {
		action,
		values: state[action.key] || {},
	})
	close()
}

watch(openAction, (value) => {
	if (!value) {
		return
	}
})
</script>

<template>
	<div class="panel" style="padding: 18px">
		<div class="section-head" style="margin-bottom: 12px">
			<div>
				<div class="section-title">Action entry points</div>
				<p class="section-subtitle">All interactions stay inside the UI. Backend support is surfaced explicitly when it is missing.</p>
			</div>
			<Badge v-if="!actions.length">No actions configured</Badge>
		</div>

		<div v-if="actions.length" class="stack">
			<div v-for="action in actions" :key="action.key" class="resource-card">
				<div class="resource-topline">
					<div>
						<p class="resource-title">{{ action.label }}</p>
						<p class="action-description">{{ action.description }}</p>
					</div>
					<Badge :class="action.backendSupported ? 'success' : 'warning'">{{ action.backendSupported ? 'Available' : 'UI-only / pending backend' }}</Badge>
				</div>
				<div class="button-row">
					<Button @click="open(action)">
						Open flow
					</Button>
				</div>
			</div>
		</div>

		<div v-if="activeAction" class="dialog-backdrop" @click.self="close">
			<div class="dialog-surface">
				<div class="dialog-header">
					<div>
						<p class="dialog-title">{{ activeAction.label }}</p>
						<p class="helper-text">{{ activeAction.description }}</p>
					</div>
					<Button @click="close">
						<component :is="X" class="nav-icon" />
						Close
					</Button>
				</div>

				<div class="notice-card" style="padding: 16px; background: var(--surface-2)">
					<p class="notice" style="color: var(--text); font-weight: 700; margin-bottom: 6px">This flow is built in the UI.</p>
					<p class="notice" style="color: var(--muted)">
						The primary interaction layer is ready, but the backend contract for {{ contextLabel }} {{ activeAction.label.toLowerCase() }} is still pending.
					</p>
				</div>

				<div class="dialog-fields">
					<div v-for="field in activeAction.fields || []" :key="field.key" class="dialog-field">
						<label>{{ field.label }}</label>
						<textarea v-if="field.type === 'textarea'" v-model="state[activeAction.key][field.key]" :placeholder="field.placeholder"></textarea>
						<input v-else v-model="state[activeAction.key][field.key]" :placeholder="field.placeholder" />
					</div>
				</div>

				<div class="form-actions">
					<Button v-if="!activeAction.backendSupported" disabled>Backend support pending</Button>
					<Button v-else @click="submit(activeAction)">Submit</Button>
				</div>
			</div>
		</div>
	</div>
</template>
