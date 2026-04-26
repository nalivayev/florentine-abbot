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

function destroyEngine() {
  engine?.unmount?.()
  engine = null
}

function mountEngine() {
  destroyEngine()

  if (!surfaceEl.value) return

  engine = props.engineFactory({
    onReady: (payload) => emit('ready', payload),
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
  width: 100%;
  height: 100%;
  min-width: 0;
  min-height: 0;
}
</style>