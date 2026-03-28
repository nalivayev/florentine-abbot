<template>
  <div class="layout">

    <aside v-if="showSidebar" class="sidebar">
      <div class="sidebar-logo">Florentine Abbot</div>

      <RouterLink class="sidebar-link" to="/admin/config" active-class="active">{{ t('admin.nav.settings') }}</RouterLink>

      <hr class="divider">

      <div class="sidebar-section">{{ t('admin.nav.management') }}</div>
      <RouterLink class="sidebar-link" to="/admin/tasks/organizer" active-class="active">{{ t('admin.nav.organizer') }}</RouterLink>
      <RouterLink class="sidebar-link" to="/admin/tasks/processor" active-class="active">{{ t('admin.nav.processor') }}</RouterLink>
      <RouterLink class="sidebar-link" to="/admin/tasks/detector" active-class="active">{{ t('admin.nav.detector') }}</RouterLink>

      <hr class="divider">

      <a class="sidebar-link" href="#" @click.prevent="logout">{{ t('admin.nav.logout') }}</a>
    </aside>

    <div class="lang-switcher lang-switcher-top">
      <button class="lang-btn theme-btn" @click="toggle" :title="isDark ? 'Light' : 'Dark'">{{ isDark ? '☀' : '☽' }}</button>
      <span class="switcher-sep">|</span>
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
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { apiFetch } from './api.js'
import { useTheme } from './theme.js'

const { t, locale } = useI18n()
const { isDark, init, toggle } = useTheme()
onMounted(init)
const route = useRoute()
const router = useRouter()

const noSidebarPaths = ['/admin/login', '/admin/setup']

const showSidebar = computed(() => !noSidebarPaths.includes(route.path))

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
  router.push('/admin/login')
}
</script>

<style scoped>
.divider { margin: var(--sp-4) 0; }
.switcher-sep {
  color: var(--border);
  font-size: var(--fs-sm);
  user-select: none;
}
</style>
