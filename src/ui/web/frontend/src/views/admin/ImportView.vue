<template>
  <h1 class="page-title">{{ t('import.title') }}</h1>
  <p class="page-subtitle">{{ t('import.subtitle') }}</p>

  <div class="import-types">
    <RouterLink v-for="type in importTypes" :key="type.id" :to="type.route" class="import-type-card">
      <span class="import-type-label">{{ t(type.labelKey) }}</span>
      <span class="import-type-desc">{{ t(type.descKey) }}</span>
    </RouterLink>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const importTypes = [
  {
    id: 'scans',
    route: '/import/scan',
    labelKey: 'import.types.scans.label',
    descKey: 'import.types.scans.desc',
  },
]
</script>

<style scoped>
.import-types {
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
  max-width: 560px;
}
.import-type-card {
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
  padding: var(--sp-4) var(--sp-5);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: var(--surface);
  text-decoration: none;
  transition: border-color var(--motion-base), background var(--motion-base);
}
.import-type-card:hover {
  border-color: var(--accent);
  background: var(--surface-muted);
}
.import-type-label {
  font-size: var(--fs-base);
  font-weight: 600;
  color: var(--text-primary);
}
.import-type-desc {
  font-size: var(--fs-sm);
  color: var(--text-muted);
  line-height: 1.5;
}
</style>
