<template>
	<FrappeUIProvider>
		<router-view />
	</FrappeUIProvider>
</template>

<script setup>
import { FrappeUIProvider, setConfig, useTheme } from 'frappe-ui'

const { setTheme } = useTheme()

if (!localStorage.getItem('theme')) {
	setTheme('light')
}

setConfig('systemTimezone', window.timezone?.system || null)
setConfig('localTimezone', window.timezone?.user || null)
setConfig('translatedMessages', window.translated_messages || {})
</script>
