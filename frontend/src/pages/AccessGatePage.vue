<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Button } from 'frappe-ui'
import { ShieldAlert } from 'lucide-vue-next'

const route = useRoute()
const redirectTo = computed(() => route.query['redirect-to'] || '/platform/dashboard')
</script>

<template>
	<div class="flex min-h-screen items-center justify-center bg-slate-50 p-4">
		<div class="w-full max-w-lg rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
			<div class="flex items-start justify-between gap-4">
				<div>
					<p class="text-[11px] font-medium uppercase tracking-[0.18em] text-slate-500">LensCloud access</p>
					<h1 class="mt-1 text-2xl font-semibold tracking-tight text-slate-950">Sign in to continue</h1>
					<p class="mt-2 text-sm leading-6 text-slate-500">The frontend uses native Frappe authentication. Once you are signed in, the product surface will route you to the right console.</p>
				</div>
				<ShieldAlert class="size-10 text-amber-500" />
			</div>

			<div class="mt-5 rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-4">
				<p class="text-sm font-medium text-slate-950">Session required</p>
				<p class="mt-1 text-sm leading-6 text-slate-500">This page is intentionally thin. All meaningful product interactions happen after login.</p>
			</div>

			<div class="mt-5 flex flex-wrap gap-2">
				<Button tag="a" :href="`/login?redirect-to=${encodeURIComponent(redirectTo)}`">Go to login</Button>
				<Button tag="a" href="/" variant="subtle">Back to root</Button>
			</div>
		</div>
	</div>
</template>
