import './index.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import {
	Alert,
	Avatar,
	Badge,
	Button,
	Dialog,
	Dropdown,
	ErrorMessage,
	FrappeUI,
	FormControl,
	ListView,
	LoadingIndicator,
	Tabs,
	TextInput,
	Textarea,
	frappeRequest,
	setConfig,
} from 'frappe-ui'
import App from './App.vue'
import router from './router'
import posthog from 'posthog-js'
import { initSocket } from './socket'

setConfig('resourceFetcher', frappeRequest)

const app = createApp(App)
const pinia = createPinia()

const posthogToken = import.meta.env.VITE_POSTHOG_PROJECT_TOKEN
if (posthogToken) {
	posthog.init(posthogToken, {
		api_host: import.meta.env.VITE_POSTHOG_HOST,
		defaults: '2026-05-30',
	})
}

app.use(FrappeUI)
app.use(pinia)
app.use(router)

app.component('Alert', Alert)
app.component('Avatar', Avatar)
app.component('Badge', Badge)
app.component('Button', Button)
app.component('Dialog', Dialog)
app.component('Dropdown', Dropdown)
app.component('ErrorMessage', ErrorMessage)
app.component('FormControl', FormControl)
app.component('ListView', ListView)
app.component('LoadingIndicator', LoadingIndicator)
app.component('Tabs', Tabs)
app.component('TextInput', TextInput)
app.component('Textarea', Textarea)

async function startApplication() {
	if (import.meta.env.DEV) {
		const boot = await frappeRequest({
			url: '/api/method/lenscloud.www.lenscloud.get_context_for_dev',
			method: 'GET',
		})

		Object.assign(window, boot)
		window.frappe = window.frappe || {}
		window.frappe.csrf_token = window.csrf_token
	}

	const socket = initSocket()
	app.config.globalProperties.$socket = socket
	app.provide('socket', socket)
	app.mount('#app')
}

startApplication().catch((error) => {
	console.error('LensCloud startup failed', error)
})
