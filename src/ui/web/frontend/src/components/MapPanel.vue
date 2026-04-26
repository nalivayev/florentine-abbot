<template>
  <MapSurface
    v-if="showEngine"
    class="viewer-map-surface"
    :engine-factory="engineFactory"
    :model="model"
    @ready="$emit('ready', $event)"
    @viewport-change="$emit('viewport-change', $event)"
    @marker-click="$emit('marker-click', $event)"
    @hover="$emit('hover', $event)"
  />

  <div v-else class="viewer-map-placeholder">
    <div class="viewer-map-icon">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
        <path d="M12 20.25C16 15.68 18.25 12.47 18.25 9.75C18.25 6.3 15.45 3.5 12 3.5C8.55 3.5 5.75 6.3 5.75 9.75C5.75 12.47 8 15.68 12 20.25Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
        <circle cx="12" cy="9.75" r="2.25" stroke="currentColor" stroke-width="1.5"/>
      </svg>
    </div>
    <p class="viewer-map-text">{{ emptyText }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import MapSurface from './MapSurface.vue'

const props = defineProps({
  model: { type: Object, default: null },
  engineFactory: { type: Function, default: null },
  emptyText: { type: String, required: true },
})

defineEmits(['ready', 'viewport-change', 'marker-click', 'hover'])

const showEngine = computed(() => typeof props.engineFactory === 'function' && props.model !== null)
</script>

<style scoped>
.viewer-map-surface {
  min-height: 100%;
}

.viewer-map-placeholder {
  min-height: 100%;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: flex-start;
  gap: var(--sp-3);
  padding: 0;
  text-align: left;
}

.viewer-map-icon {
  width: 3rem;
  height: 3rem;
  border-radius: var(--viewer-control-radius, var(--radius-sm));
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.34);
  border: 1px solid rgba(255, 255, 255, 0.5);
  color: var(--text-muted);
  flex-shrink: 0;
}

.viewer-map-text {
  margin: 0;
  line-height: 1.55;
  color: var(--text-muted);
}

[data-theme="dark"] .viewer-map-icon {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.08);
}
</style>