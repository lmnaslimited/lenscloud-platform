<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Button } from 'frappe-ui'
import { ShieldAlert } from 'lucide-vue-next'

const route = useRoute()
const redirectTo = computed(() => route.query['redirect-to'] || '/platform/dashboard')
</script>

<template>
	<div class="section-band" style="min-height: calc(100vh - 56px); display: grid; place-items: center">
		<div class="notice-card" style="max-width: 720px; width: 100%; padding: 24px; display: grid; gap: 16px">
			<div class="resource-topline">
				<div>
					<p class="kicker">LensCloud access</p>
					<h1 class="page-title" style="font-size: 1.6rem">Sign in to continue</h1>
					<p class="page-subtitle">The frontend uses native Frappe authentication. Once you are signed in, the product surface will route you to the right console.</p>
				</div>
				<ShieldAlert class="nav-icon" style="width: 42px; height: 42px; color: var(--warning)" />
			</div>

			<div class="empty-state" style="padding: 20px">
				<p class="empty-title">Session required</p>
				<p class="helper-text">This page is intentionally thin. All meaningful product interactions happen after login.</p>
			</div>

			<div class="button-row">
				<Button tag="a" :href="`/login?redirect-to=${encodeURIComponent(redirectTo)}`">Go to login</Button>
				<Button tag="a" href="/">Back to root</Button>
			</div>
		</div>
	</div>
</template>
