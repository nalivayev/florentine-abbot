<template>
  <section class="map-view">
    <MapSurface
      v-if="mapModel"
      class="map-view__surface"
      :engine-factory="createRasterTileMapEngine"
      :model="mapModel"
      @ready="onMapReady"
      @marker-click="onMarkerClick"
    />

    <div v-else-if="!loading" class="map-view__empty">
      <p class="map-view__empty-text">{{ t('map_view.empty') }}</p>
    </div>

    <div v-if="loading" class="map-view__loading">{{ t('collections.loading') }}</div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { apiFetch } from '../api.js'
import MapSurface from '../components/MapSurface.vue'
import { createRasterTileMapEngine } from '../map/engines/rasterTileEngine.js'
import {
  geotaggedFilesBounds,
  geotaggedFilesMapModelFromFiles,
} from '../map/geotaggedFilesModel.js'
import { replaceForRouteFailure, ROUTE_LOAD_TIMEOUT_MS } from '../routeErrors.js'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const loading = ref(true)
const files = ref([])
const mapEngine = ref(null)

const mapModel = computed(() => geotaggedFilesMapModelFromFiles(files.value))
const mapBounds = computed(() => geotaggedFilesBounds(files.value))
const filesById = computed(() => new Map(files.value.map((file) => [String(file.id), file])))

onMounted(async () => {
  try {
    const response = await apiFetch('/map/files', { timeoutMs: ROUTE_LOAD_TIMEOUT_MS })
    if (!response.ok) {
      await replaceForRouteFailure(router, route, response)
      return
    }

    files.value = await response.json()
  } catch (error) {
    await replaceForRouteFailure(router, route, error)
  } finally {
    loading.value = false
  }
})

watch([mapBounds, mapModel, mapEngine], ([bounds, model, engine]) => {
  if (!engine || !model) return

  if (files.value.length > 1 && bounds) {
    engine.fitBounds?.(bounds)
    return
  }

  engine.setView?.(model.viewport)
}, { immediate: true })

function onMapReady(payload) {
  mapEngine.value = payload?.engine ?? null
}

function openFile(file) {
  if (file?.collection_id == null || file?.id == null) return
  router.push(`/collections/${file.collection_id}/${file.id}`)
}

function onMarkerClick(markerId) {
  const file = filesById.value.get(String(markerId))
  if (!file) return
  openFile(file)
}
</script>

<style scoped>
.map-view {
  position: absolute;
  inset: 0;
  background: var(--bg);
}

.map-view__surface,
.map-view__empty,
.map-view__loading {
  position: absolute;
  inset: 0;
}

.map-view__surface {
  min-height: 100%;
  background: var(--surface-muted);
}

.map-view__empty {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--sp-5);
  text-align: center;
  background:
    radial-gradient(circle at 50% 8%, rgba(255, 255, 255, 0.2), transparent 34%),
    linear-gradient(180deg, rgba(0, 0, 0, 0.03), rgba(0, 0, 0, 0.08)),
    var(--surface-muted);
}

.map-view__empty-text {
  margin: 0;
  max-width: 18rem;
  color: var(--text-muted);
  line-height: 1.55;
}

.map-view__loading {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  background:
    radial-gradient(circle at 50% 8%, rgba(255, 255, 255, 0.2), transparent 34%),
    linear-gradient(180deg, rgba(0, 0, 0, 0.03), rgba(0, 0, 0, 0.08)),
    var(--surface-muted);
}
</style>