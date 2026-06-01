import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { Button, Input, Badge, FrappeUI, setConfig, frappeRequest } from 'frappe-ui'
import App from './App.vue'
import router from './router'

setConfig('resourceFetcher', frappeRequest)

const app = createApp(App)
const pinia = createPinia()

app.use(FrappeUI)
app.use(pinia)
app.use(router)

app.component('Button', Button)
app.component('Input', Input)
app.component('Badge', Badge)

app.mount('#app')
