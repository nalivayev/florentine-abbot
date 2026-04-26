<template>
  <div class="not-found">
    <p class="not-found-code">404</p>
    <h1 class="not-found-title">{{ t('not_found.title') }}</h1>
    <p class="not-found-path">{{ displayPath }}</p>
    <p class="not-found-hint">{{ t('not_found.hint') }}</p>
    <button type="button" class="btn" @click="goBack">{{ t('not_found.action') }}</button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const displayPath = computed(() => (
  typeof route.query.path === 'string' ? route.query.path : route.fullPath
))

function goBack() {
  router.back()
}
</script>

<style scoped>
.not-found {
  min-height: 60vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--sp-3);
  text-align: center;
}

.not-found-code {
  margin: 0;
  font-size: 3rem;
  font-weight: 700;
  line-height: 1;
  color: var(--text-heading);
}

.not-found-title {
  margin: 0;
  font-size: var(--fs-xl);
  color: var(--text-heading);
}

.not-found-path {
  margin: 0;
  font-family: monospace;
  font-size: var(--fs-sm);
  color: var(--text-muted);
}

.not-found-hint {
  margin: 0;
  max-width: 32rem;
  color: var(--text-muted);
}
</style>