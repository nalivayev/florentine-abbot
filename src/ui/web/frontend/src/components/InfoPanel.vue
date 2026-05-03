<template>
  <aside ref="rootEl" class="viewer-panel viewer-panel-info" :class="{ open }">
    <p class="viewer-meta-title" :title="fileName">{{ fileName || '…' }}</p>

    <dl class="viewer-meta-grid">
      <div v-if="formattedPhotoDate" class="viewer-meta-row">
        <dt>{{ t('collections.date') }}</dt>
        <dd :title="formattedPhotoDate">{{ formattedPhotoDate }}</dd>
      </div>
      <div v-if="fileSource" class="viewer-meta-row">
        <dt>{{ t('collections.source') }}</dt>
        <dd :title="fileSource">{{ fileSource }}</dd>
      </div>
      <div v-if="fileCredit" class="viewer-meta-row">
        <dt>{{ t('collections.credit') }}</dt>
        <dd :title="fileCredit">{{ fileCredit }}</dd>
      </div>
    </dl>

    <section v-if="description" class="viewer-meta-section">
      <h2 class="viewer-section-title">{{ t('collections.description') }}</h2>
      <p class="viewer-meta-text" :title="description">{{ description }}</p>
    </section>

    <section v-if="creators.length > 0" class="viewer-meta-section">
      <h2 class="viewer-section-title">{{ t('collections.creators') }}</h2>
      <ul class="viewer-list">
        <li v-for="creator in creators" :key="creator" :title="creator">{{ creator }}</li>
      </ul>
    </section>

    <p v-if="!hasSemanticMetadata" class="viewer-meta-empty">{{ t('collections.no_metadata') }}</p>
  </aside>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

defineProps({
  open: { type: Boolean, default: false },
  fileName: { type: String, default: '' },
  formattedPhotoDate: { type: String, default: '' },
  fileSource: { type: String, default: '' },
  fileCredit: { type: String, default: '' },
  description: { type: String, default: '' },
  creators: { type: Array, default: () => [] },
  hasSemanticMetadata: { type: Boolean, default: false },
})

const { t } = useI18n()
const rootEl = ref(null)

defineExpose({ rootEl })
</script>

<style scoped>
.viewer-meta-title,
.viewer-meta-row dd,
.viewer-meta-text,
.viewer-list li {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.viewer-meta-grid,
.viewer-list {
  display: flex;
  flex-direction: column;
}

.viewer-meta-title {
  margin: 0 0 var(--sp-4);
  min-width: 0;
  font-size: 0.82rem;
  line-height: 1.35;
  font-weight: 400;
  color: var(--text);
}

.viewer-meta-grid {
  gap: var(--sp-2);
  margin: 0 0 var(--sp-4);
}

.viewer-meta-row {
  display: grid;
  grid-template-columns: 5.25rem minmax(0, 1fr);
  gap: var(--sp-2);
  align-items: start;
}

.viewer-meta-row dt {
  font-size: 0.78rem;
  line-height: 1.35;
  font-weight: 400;
  color: var(--text-muted);
  white-space: nowrap;
}

.viewer-meta-row dt::after {
  content: ':';
}

.viewer-meta-row dd {
  margin: 0;
  font-size: 0.78rem;
  line-height: 1.35;
  color: var(--text);
}

.viewer-meta-section {
  margin-top: var(--sp-3);
  padding-top: var(--sp-3);
  border-top: 1px solid var(--border);
}

.viewer-section-title {
  margin: 0 0 var(--sp-2);
  font-size: 0.74rem;
  font-weight: 400;
  color: var(--text-muted);
}

.viewer-meta-text {
  margin: 0;
  min-width: 0;
  line-height: 1.4;
}

.viewer-list {
  margin: 0;
  padding-left: 1.125rem;
  gap: var(--sp-1);
}

.viewer-list li {
  min-width: 0;
}

.viewer-meta-empty {
  margin: var(--sp-4) 0 0;
  font-size: var(--fs-xs);
  color: var(--text-muted);
}

:global(.viewer-stage.compact-layout) .viewer-meta-row {
  grid-template-columns: max-content minmax(0, 1fr);
  gap: var(--sp-2);
  align-items: baseline;
}
</style>