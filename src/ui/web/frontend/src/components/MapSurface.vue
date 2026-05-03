<template>
  <div ref="surfaceEl" class="map-surface"></div>
</template>

<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'

const props = defineProps({
  engineFactory: { type: Function, required: true },
  model: { type: Object, default: null },
})

const emit = defineEmits(['ready', 'viewport-change', 'marker-click', 'hover'])

const surfaceEl = ref(null)

let engine = null

function normalizeReadyPayload(payload) {
  if (payload && typeof payload === 'object' && !Array.isArray(payload)) {
    return { ...payload, engine }
  }
  return { engine, payload }
}

function destroyEngine() {
  engine?.unmount?.()
  engine = null
}

function mountEngine() {
  destroyEngine()

  if (!surfaceEl.value) return

  engine = props.engineFactory({
    onReady: (payload) => emit('ready', normalizeReadyPayload(payload)),
    onViewportChange: (payload) => emit('viewport-change', payload),
    onMarkerClick: (payload) => emit('marker-click', payload),
    onHover: (payload) => emit('hover', payload),
  })

  engine.mount?.(surfaceEl.value)
  engine.setData?.(props.model)
}

watch(() => props.engineFactory, mountEngine)

watch(
  () => props.model,
  (value) => {
    engine?.setData?.(value)
  },
  { deep: true },
)

onMounted(mountEngine)
onUnmounted(destroyEngine)
</script>

<style scoped>
.map-surface {
  position: relative;
  width: 100%;
  flex: 1 1 auto;
  min-width: 0;
  min-height: 0;
}
</style>