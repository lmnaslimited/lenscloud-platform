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
import posthog from "posthog-js"
import { initSocket } from './lib/socket.js'

setConfig('resourceFetcher', frappeRequest)

const app = createApp(App)
const pinia = createPinia()

posthog.init(import.meta.env.VITE_POSTHOG_PROJECT_TOKEN, {
	  api_host: import.meta.env.VITE_POSTHOG_HOST,
	  defaults: '2026-05-30',
	});

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

// Socket initialization
const socket = initSocket()

// 1. For Options API (this.$socket)
app.config.globalProperties.$socket = socket

// 2. For Composition API (inject('$socket'))
app.provide('$socket', socket)

app.mount('#app')
