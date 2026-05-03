<template>
  <div class="viewer-map-panel">
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
      <p class="viewer-map-text">{{ emptyText }}</p>
    </div>
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
.viewer-map-panel,
.viewer-map-surface {
  display: flex;
  width: 100%;
  flex: 1 1 auto;
  min-height: 0;
}

.viewer-map-panel {
  min-width: 0;
  overflow: hidden;
}

.viewer-map-placeholder {
  flex: 1 1 auto;
  width: 100%;
  min-height: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  text-align: center;
}

.viewer-map-text {
  margin: 0;
  max-width: 18rem;
  line-height: 1.55;
  color: var(--text-muted);
}

.viewer-map-panel :deep(.map-raster-engine) {
  border-radius: var(--viewer-card-radius);
  background: transparent;
}
</style>