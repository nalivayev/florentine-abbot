import { createApp } from 'vue'
import { createI18n } from 'vue-i18n'
import './assets/theme.css'
import AppAdmin from './AppAdmin.vue'
import router from './router-admin.js'
import ru from './locales/ru.json'
import en from './locales/en.json'

const i18n = createI18n({
  legacy: false,
  locale: localStorage.getItem('lang') || navigator.language.slice(0, 2) || 'ru',
  fallbackLocale: 'en',
  messages: { ru, en },
})

createApp(AppAdmin).use(router).use(i18n).mount('#app')
