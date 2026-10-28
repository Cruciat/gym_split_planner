import 'primeicons/primeicons.css'
import './styles.css'

import Aura from '@primeuix/themes/aura'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import { createApp } from 'vue'

import App from './App.vue'
import { router } from './router'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(PrimeVue, {
  theme: {
    preset: Aura,
    options: { darkModeSelector: 'system' },
  },
})

app.mount('#app')
