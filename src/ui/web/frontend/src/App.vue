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

      <div class="sidebar-footer">
        <div class="lang-switcher">
          <button
            v-for="lang in langs"
            :key="lang"
            class="lang-btn"
            :class="{ active: locale === lang }"
            @click="setLang(lang)"
          >{{ lang.toUpperCase() }}</button>
        </div>
        <div class="copyright">{{ t('footer.copyright', { year }) }}</div>
      </div>
    </aside>

    <main class="content" :class="{ 'content-full': !showSidebar }">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'

const { t, locale } = useI18n()
const route = useRoute()
const showSidebar = computed(() => !['/', '/login', '/setup'].includes(route.path))

const langs = ['ru', 'en']
const year = new Date().getFullYear()

function setLang(lang) {
  locale.value = lang
  localStorage.setItem('lang', lang)
}
</script>
