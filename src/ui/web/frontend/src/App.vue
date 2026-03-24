<template>
  <div class="layout">

    <aside v-if="showSidebar" class="sidebar">
      <div class="sidebar-logo">Florentine Abbot</div>

      <RouterLink class="sidebar-link" to="/admin/config" active-class="active">{{ t('nav.settings') }}</RouterLink>

      <hr class="divider" style="margin: 16px 0;">

      <div class="sidebar-section">{{ t('nav.management') }}</div>
      <RouterLink class="sidebar-link" to="/admin/tasks/organizer" active-class="active">{{ t('nav.organizer') }}</RouterLink>
      <RouterLink class="sidebar-link" to="/admin/tasks/processor" active-class="active">{{ t('nav.processor') }}</RouterLink>
      <RouterLink class="sidebar-link" to="/admin/tasks/detector" active-class="active">{{ t('nav.detector') }}</RouterLink>

      <hr class="divider" style="margin: 16px 0;">

      <a class="sidebar-link" href="#" @click.prevent="logout">{{ t('nav.logout') }}</a>

      <div class="sidebar-footer"></div>
    </aside>

    <div class="lang-switcher lang-switcher-top">
      <button
        v-for="lang in langs"
        :key="lang"
        class="lang-btn"
        :class="{ active: locale === lang }"
        @click="setLang(lang)"
      >{{ lang.toUpperCase() }}</button>
    </div>

    <main class="content" :class="{ 'content-full': !showSidebar }">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { apiFetch } from './api.js'

const { t, locale } = useI18n()
const route = useRoute()
const router = useRouter()
const showSidebar = computed(() => !['/', '/login', '/setup'].includes(route.path))

const langs = ['ru', 'en']

function setLang(lang) {
  locale.value = lang
  localStorage.setItem('lang', lang)
}

async function logout() {
  try {
    await apiFetch('/auth/logout', { method: 'POST' })
  } catch { /* ignore */ }
  localStorage.removeItem('token')
  router.push('/login')
}
</script>
