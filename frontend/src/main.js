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

setConfig('resourceFetcher', frappeRequest)

const app = createApp(App)
const pinia = createPinia()

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

app.mount('#app')
