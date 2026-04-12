<template>
  <div class="wip">
    <p class="wip-icon">🚧</p>
    <h2 class="wip-title">{{ t('wip.title') }}</h2>
    <p class="wip-hint">{{ t('wip.hint') }}</p>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
</script>

<style scoped>
.wip {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 60vh;
  text-align: center;
  color: var(--text-muted);
}
.wip-icon { font-size: 2.5rem; margin-bottom: 1rem; }
.wip-title { font-size: 1.1rem; font-weight: 600; color: var(--text); margin-bottom: 0.5rem; }
.wip-hint { font-size: 0.88rem; }
</style>
