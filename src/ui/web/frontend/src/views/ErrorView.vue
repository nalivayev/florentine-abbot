<template>
  <div class="error-view">
    <p class="error-view-code">{{ displayCode }}</p>
    <h1 class="error-view-title">{{ title }}</h1>
    <p v-if="displayPath" class="error-view-path">{{ displayPath }}</p>
    <p class="error-view-hint">{{ hint }}</p>
    <div class="error-view-actions">
      <button v-if="displayPath" type="button" class="btn" @click="retry">{{ t('error_view.retry') }}</button>
      <button type="button" class="btn error-view-back" @click="goBack">{{ t('error_view.back') }}</button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const kind = computed(() => {
  const value = typeof route.query.kind === 'string' ? route.query.kind : ''
  if (['network', 'timeout', 'server', 'http'].includes(value)) return value
  return 'generic'
})

const displayPath = computed(() => (
  typeof route.query.path === 'string' ? route.query.path : ''
))

const displayCode = computed(() => {
  const status = typeof route.query.status === 'string' ? route.query.status : ''
  return status || 'ERR'
})

const title = computed(() => {
  if (kind.value === 'network') return t('error_view.network_title')
  if (kind.value === 'timeout') return t('error_view.timeout_title')
  if (kind.value === 'server') return t('error_view.server_title')
  if (kind.value === 'http') return t('error_view.http_title')
  return t('error_view.title')
})

const hint = computed(() => {
  if (kind.value === 'network') return t('error_view.network_hint')
  if (kind.value === 'timeout') return t('error_view.timeout_hint')
  if (kind.value === 'server') return t('error_view.server_hint')
  if (kind.value === 'http') return t('error_view.http_hint')
  return t('error_view.hint')
})

function retry() {
  if (displayPath.value) {
    router.replace(displayPath.value)
    return
  }

  router.back()
}

function goBack() {
  router.back()
}
</script>

<style scoped>
.error-view {
  min-height: 60vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--sp-3);
  text-align: center;
}

.error-view-code {
  margin: 0;
  font-size: 3rem;
  font-weight: 700;
  line-height: 1;
  color: var(--text-heading);
}

.error-view-title {
  margin: 0;
  font-size: var(--fs-xl);
  color: var(--text-heading);
}

.error-view-path {
  margin: 0;
  font-family: monospace;
  font-size: var(--fs-sm);
  color: var(--text-muted);
}

.error-view-hint {
  margin: 0;
  max-width: 32rem;
  color: var(--text-muted);
}

.error-view-actions {
  display: flex;
  gap: var(--sp-2);
}

.error-view-back {
  background: transparent;
  color: var(--text);
  border: 1px solid var(--border);
}
</style>