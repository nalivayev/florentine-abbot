<template>
  <div class="layout">

    <aside v-if="showSidebar" class="sidebar" :class="{ collapsed }">
      <div class="sidebar-top">
        <button class="sidebar-toggle sidebar-utility-btn" @click="toggleSidebar" :title="collapsed ? t('nav.expand') : t('nav.collapse')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="3" y1="6" x2="21" y2="6"/>
            <line x1="3" y1="12" x2="21" y2="12"/>
            <line x1="3" y1="18" x2="21" y2="18"/>
          </svg>
        </button>
        <div class="sidebar-logo" v-show="!collapsed">Florentine Abbot</div>
      </div>

      <div class="sidebar-nav">

      <RouterLink class="sidebar-link" to="/photos" active-class="active" :title="collapsed ? t('nav.photos') : ''">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
        <span>{{ t('nav.photos') }}</span>
      </RouterLink>
      <RouterLink class="sidebar-link" to="/map" active-class="active" :title="collapsed ? t('nav.map') : ''">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"/><line x1="8" y1="2" x2="8" y2="18"/><line x1="16" y1="6" x2="16" y2="22"/></svg>
        <span>{{ t('nav.map') }}</span>
      </RouterLink>
      <RouterLink class="sidebar-link" to="/collections" active-class="active" :title="collapsed ? t('nav.collections') : ''">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
        <span>{{ t('nav.collections') }}</span>
      </RouterLink>
      <RouterLink v-if="isAdmin" class="sidebar-link" to="/people" active-class="active" :title="collapsed ? t('nav.people') : ''">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
        <span>{{ t('nav.people') }}</span>
      </RouterLink>
      <RouterLink class="sidebar-link" to="/genealogy" active-class="active" :title="collapsed ? t('nav.genealogy') : ''">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><line x1="12" y1="2" x2="12" y2="8"/><path d="M5 20a2 2 0 1 0 0-4 2 2 0 0 0 0 4z"/><path d="M12 8a2 2 0 1 0 0-4 2 2 0 0 0 0 4z"/><path d="M19 20a2 2 0 1 0 0-4 2 2 0 0 0 0 4z"/><path d="M5 16v-2a4 4 0 0 1 4-4h6a4 4 0 0 1 4 4v2"/></svg>
        <span>{{ t('nav.genealogy') }}</span>
      </RouterLink>
      <RouterLink class="sidebar-link" to="/timeline" active-class="active" :title="collapsed ? t('nav.timeline') : ''">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><line x1="12" y1="2" x2="12" y2="22"/><polyline points="17 7 12 2 7 7"/><line x1="5" y1="9" x2="12" y2="9"/><line x1="19" y1="13" x2="12" y2="13"/><polyline points="7 17 12 22 17 17"/></svg>
        <span>{{ t('nav.timeline') }}</span>
      </RouterLink>
      <RouterLink class="sidebar-link" to="/stats" active-class="active" :title="collapsed ? t('nav.stats') : ''">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
        <span>{{ t('nav.stats') }}</span>
      </RouterLink>

      <template v-if="isAdmin">
        <hr class="divider">
        <RouterLink class="sidebar-link" to="/import" active-class="active" :title="collapsed ? t('nav.import') : ''">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><polyline points="16 16 12 12 8 16"/><line x1="12" y1="12" x2="12" y2="21"/><path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"/></svg>
          <span>{{ t('nav.import') }}</span>
        </RouterLink>
        <RouterLink class="sidebar-link" to="/settings" active-class="active" :title="collapsed ? t('nav.settings') : ''">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
          <span>{{ t('nav.settings') }}</span>
        </RouterLink>
        <RouterLink class="sidebar-link" to="/services" active-class="active" :title="collapsed ? t('nav.services') : ''">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></svg>
          <span>{{ t('nav.services') }}</span>
        </RouterLink>
        <RouterLink class="sidebar-link" to="/file-manager" active-class="active" :title="collapsed ? t('nav.file_manager') : ''">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
          <span>{{ t('nav.file_manager') }}</span>
        </RouterLink>
        <RouterLink class="sidebar-link" to="/tasks" active-class="active" :title="collapsed ? t('nav.tasks') : ''">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
          <span>{{ t('nav.tasks') }}</span>
        </RouterLink>
        <RouterLink class="sidebar-link" to="/users" active-class="active" :title="collapsed ? t('nav.users') : ''">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
          <span>{{ t('nav.users') }}</span>
        </RouterLink>
      </template>

      <hr class="divider">
      <a class="sidebar-link" href="#" @click.prevent="logout" :title="collapsed ? t('nav.logout') : ''">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
        <span>{{ t('nav.logout') }}</span>
      </a>

      </div>

      <div class="sidebar-bottom">
        <div class="sidebar-switcher" :class="{ collapsed }">
          <button class="lang-btn theme-btn sidebar-utility-btn" @click="toggle" :title="isDark ? 'Light' : 'Dark'">{{ isDark ? '☀' : '☽' }}</button>
          <button
            v-if="collapsed"
            class="lang-btn sidebar-utility-btn"
            @click="toggleCollapsedLang"
          >{{ collapsedLangLabel }}</button>
          <template v-else>
            <button
              v-for="lang in langs"
              :key="lang"
              class="lang-btn sidebar-utility-btn"
              :class="{ active: locale === lang }"
              @click="setLang(lang)"
            >{{ lang.toUpperCase() }}</button>
          </template>
        </div>
      </div>
    </aside>

    <main class="content" :class="{ 'content-full': !showSidebar, 'content-viewer': route.meta.viewer, 'content-collapsed': showSidebar && collapsed }">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { apiFetch } from './api.js'
import { useTheme } from './theme.js'

const { t, locale } = useI18n()
const { isDark, init, toggle } = useTheme()
onMounted(init)
const route = useRoute()
const router = useRouter()

const noSidebarPaths = ['/login']
const showSidebar = computed(() => !noSidebarPaths.includes(route.path))

const langs = ['ru', 'en']
const activeLang = computed(() => (langs.includes(locale.value) ? locale.value : langs[0]))
const collapsedLangLabel = computed(() => activeLang.value.toUpperCase())
const userRole = ref(null)
const isAdmin = computed(() => userRole.value === 'admin')

const collapsed = ref(localStorage.getItem('sidebar-collapsed') === 'true')
function toggleSidebar() {
  collapsed.value = !collapsed.value
  localStorage.setItem('sidebar-collapsed', collapsed.value)
}

async function fetchRole() {
  try {
    const res = await apiFetch('/auth/me')
    if (res.ok) userRole.value = (await res.json()).role
    else userRole.value = null
  } catch { userRole.value = null }
}

onMounted(fetchRole)

watch(() => route.path, (path, prev) => {
  if (prev === '/login' && path !== '/login') fetchRole()
})

function setLang(lang) {
  locale.value = lang
  localStorage.setItem('lang', lang)
}

function toggleCollapsedLang() {
  const currentIndex = langs.indexOf(activeLang.value)
  const nextLang = langs[(currentIndex + 1) % langs.length]
  setLang(nextLang)
}

async function logout() {
  try {
    await apiFetch('/auth/logout', { method: 'POST' })
  } catch { /* ignore */ }
  localStorage.removeItem('token')
  userRole.value = null
  router.push('/login')
}
</script>

<style scoped>
.divider { margin: var(--sp-4) 0; }
</style>
