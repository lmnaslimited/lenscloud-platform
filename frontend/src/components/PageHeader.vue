<script setup>
defineProps({
	kicker: {
		type: String,
		default: '',
	},
	title: {
		type: String,
		required: true,
	},
	subtitle: {
		type: String,
		default: '',
	},
})
</script>

<template>
	<section class="page-header">
		<div class="header-copy">
			<p v-if="kicker" class="kicker">{{ kicker }}</p>
			<h1 class="page-title">{{ title }}</h1>
			<p v-if="subtitle" class="page-subtitle">{{ subtitle }}</p>
		</div>
		<div class="header-actions">
			<slot name="actions" />
		</div>
	</section>
</template>
