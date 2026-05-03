<template>
  <div class="file-viewer">
    <section class="viewer-stage" ref="containerEl" :class="stageClasses" :style="stageStyle">
      <canvas ref="canvasEl" class="viewer-canvas"
        @wheel.prevent="onWheel"
        @mousedown="onMouseDown"
        @mousemove="onMouseMove"
        @mouseup="onMouseUp"
        @mouseleave="onMouseLeave"
      />

      <div
        v-if="faceHoverTooltipText"
        class="viewer-face-hover-tooltip"
        :style="{ left: `${hoverTooltipX}px`, top: `${hoverTooltipY}px` }"
      >
        {{ faceHoverTooltipText }}
      </div>

      <div v-if="showViewerEmpty" class="viewer-empty">
        <div class="viewer-empty-card">
          <div class="viewer-empty-kicker">{{ t('collections.details') }}</div>
          <h2 class="viewer-empty-title">{{ fileTitle }}</h2>
          <p class="viewer-empty-text">{{ t('collections.no_preview') }}</p>
        </div>
      </div>

      <div class="viewer-controls">
        <button
          type="button"
          class="ctrl-btn"
          :class="{ active: infoPanelOpen }"
          :title="infoPanelOpen ? t('collections.close_panel') : t('collections.open_details')"
          :aria-pressed="infoPanelOpen"
          @click="togglePanel('info')"
        >
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <rect x="2.25" y="3" width="13.5" height="12" rx="2" stroke="currentColor" stroke-width="1.5"/>
            <path d="M5.25 6.75H12.75" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <path d="M5.25 9H12.75" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <path d="M5.25 11.25H9.75" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
        </button>

        <button
          type="button"
          class="ctrl-btn"
          :class="{ active: mapPanelOpen }"
          :title="mapPanelOpen ? t('collections.close_panel') : t('collections.open_map')"
          :aria-pressed="mapPanelOpen"
          @click="togglePanel('map')"
        >
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <path d="M9 15.25C11.95 11.88 13.5 9.52 13.5 7.5C13.5 5.01 11.49 3 9 3C6.51 3 4.5 5.01 4.5 7.5C4.5 9.52 6.05 11.88 9 15.25Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
            <circle cx="9" cy="7.5" r="1.5" stroke="currentColor" stroke-width="1.5"/>
          </svg>
        </button>

        <button
          type="button"
          class="ctrl-btn"
          :class="{ active: peoplePanelOpen }"
          :title="peoplePanelOpen ? t('collections.close_panel') : t('collections.open_people')"
          :aria-pressed="peoplePanelOpen"
          @click="togglePanel('people')"
        >
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <circle cx="6.25" cy="6" r="2.25" stroke="currentColor" stroke-width="1.5"/>
            <circle cx="12.25" cy="7.25" r="1.75" stroke="currentColor" stroke-width="1.5"/>
            <path d="M2.75 14C2.75 11.93 4.43 10.25 6.5 10.25H7.25C9.32 10.25 11 11.93 11 14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <path d="M10.5 13.25C10.77 11.86 11.99 10.85 13.5 10.85C14.93 10.85 16.11 11.75 16.5 13.03" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
        </button>

        <button type="button" class="ctrl-btn" :title="t('collections.zoom_in')" @click="zoomStep(1.5)">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M8 3v10M3 8h10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
        </button>

        <button type="button" class="ctrl-btn" :title="t('collections.zoom_out')" @click="zoomStep(1 / 1.5)">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M3 8h10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
        </button>

        <div class="viewer-nav-row">
          <router-link v-if="prevId" :to="`/collections/${collectionId}/${prevId}`" class="ctrl-btn nav-btn" :title="t('collections.previous')">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M10 3L5 8l5 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </router-link>
          <button v-else type="button" class="ctrl-btn nav-btn disabled" :title="t('collections.previous')">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M10 3L5 8l5 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>

          <router-link v-if="nextId" :to="`/collections/${collectionId}/${nextId}`" class="ctrl-btn nav-btn" :title="t('collections.next')">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M6 3l5 5-5 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </router-link>
          <button v-else type="button" class="ctrl-btn nav-btn disabled" :title="t('collections.next')">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M6 3l5 5-5 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
        </div>
      </div>

      <div ref="mobileDockEl" class="viewer-mobile-dock">
        <InfoPanel
          v-if="fileInfo"
          ref="infoPanelEl"
          :open="infoPanelOpen"
          :file-name="fileName"
          :formatted-photo-date="formattedPhotoDate"
          :file-source="fileMetadata?.source || ''"
          :file-credit="fileMetadata?.credit || ''"
          :description="fileDescription"
          :creators="fileCreators"
          :has-semantic-metadata="hasSemanticMetadata"
        />

        <aside
          class="viewer-panel viewer-panel-map"
          ref="mapPanelEl"
          :class="{ open: mapPanelOpen }"
        >
          <MapPanel
            :model="mapModel"
            :engine-factory="createRasterTileMapEngine"
            :empty-text="t('collections.map_placeholder')"
          />
        </aside>
      </div>

      <PeoplePanel
        ref="peoplePanelEl"
        :open="peoplePanelOpen"
        :face-cards="peopleFaceCards"
        :preview-url="fileInfo?.preview_url || ''"
        :has-left-fade="!peopleListAtStart"
        :has-right-fade="!peopleListAtEnd"
        :empty-text="peoplePanelEmptyText"
        @scroll="updatePeopleListFade"
        @face-click="focusFace"
        @face-enter="setHoveredCardFace"
        @face-leave="setHoveredCardFace(null)"
      />
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, ref, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import InfoPanel from '../components/InfoPanel.vue'
import MapPanel from '../components/MapPanel.vue'
import PeoplePanel from '../components/PeoplePanel.vue'
import { apiFetch, fetchWithTimeout } from '../api.js'
import { createRasterTileMapEngine } from '../map/engines/rasterTileEngine.js'
import { fileMapModelFromFile } from '../map/fileModel.js'
import { replaceForRouteFailure, ROUTE_LOAD_TIMEOUT_MS } from '../routeErrors.js'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const canvasEl = ref(null)
const containerEl = ref(null)
const mobileDockEl = ref(null)
const infoPanelEl = ref(null)
const mapPanelEl = ref(null)
const peoplePanelEl = ref(null)
const collectionId = computed(() => String(route.params.id))
const prevId = ref(null)
const nextId = ref(null)
const fileInfo = ref(null)
const fileMetadata = ref(null)
const faces = ref([])
const facesLoading = ref(false)
const facesLoadFailed = ref(false)
const viewerReady = ref(false)
const viewerLoading = ref(false)
const infoPanelOpen = ref(false)
const mapPanelOpen = ref(false)
const peoplePanelOpen = ref(false)
const compactLayout = ref(false)
const viewerWidth = ref(typeof window === 'undefined' ? 1024 : window.innerWidth)
const compactBottomInset = ref(0)
const peopleListAtStart = ref(true)
const peopleListAtEnd = ref(true)
const hoveredFaceId = ref(null)
const hoveredCardFaceId = ref(null)
const hoverTooltipX = ref(0)
const hoverTooltipY = ref(0)

const INFO_PANEL_KEY = 'viewer-panel-info-open'
const MAP_PANEL_KEY = 'viewer-panel-map-open'
const PEOPLE_PANEL_KEY = 'viewer-panel-people-open'
const FACE_CARD_RATIO = 4 / 5
const FACE_STROKE_WIDTH = 1.5
const FACE_HOVER_STROKE_WIDTH = 2.5
const FACE_CLICK_TOLERANCE_PX = 4
const FACE_FOCUS_MIN_FACTOR = 1.06
const FACE_FOCUS_TARGET_WIDTH_RATIO = 0.22
const FACE_FOCUS_TARGET_HEIGHT_RATIO = 0.3
const FACE_FOCUS_TARGET_Y_RATIO = 0.43
const FACE_TAG_HEIGHT = 20
const FACE_TAG_PADDING_X = 6
const FACE_TAG_FONT = '600 12px "Segoe UI", sans-serif'
const COMPACT_LAYOUT_MAX_WIDTH = 900
const COMPACT_DOCK_STACK_MAX_WIDTH = 640
const PEOPLE_LIST_FADE_TOLERANCE_PX = 24

let meta = null
let scale = 1
let fitScaleValue = 1
let offsetX = 0
let offsetY = 0
let dragging = false
let draggedDuringPointer = false
let dragStartX = 0
let dragStartY = 0
let lastX = 0
let lastY = 0
const tileCache = new Map()
let rafId = null
let fileLoadToken = 0
let resizeObserver = null

const fileName = computed(() => {
  const path = String(fileInfo.value?.path || '').replaceAll('\\', '/')
  if (!path) return ''
  const parts = String(path).split('/')
  return parts[parts.length - 1] || String(path)
})

const fileTitle = computed(() => fileName.value || '…')

const fileDescription = computed(() => fileMetadata.value?.description || '')

const fileCreators = computed(() => (
  Array.isArray(fileInfo.value?.creators) ? fileInfo.value.creators : []
))

const formattedPhotoDate = computed(() => formatPhotoDate(fileMetadata.value))

const hasSemanticMetadata = computed(() => Boolean(
  formattedPhotoDate.value
  || fileDescription.value
  || fileCreators.value.length > 0
  || fileMetadata.value?.source
  || fileMetadata.value?.credit
))

const mapModel = computed(() => fileMapModelFromFile(fileInfo.value, fileMetadata.value))

const peopleFaceCards = computed(() => faces.value.map((face, index) => ({
  id: face.id,
  face,
  label: String(index + 1),
  name: faceDisplayName(face, index),
  cardStyle: faceCardStyle(face),
  imageStyle: faceCardImageStyle(face),
})))

const peoplePanelEmptyText = computed(() => {
  if (facesLoading.value) return t('collections.loading')
  if (facesLoadFailed.value) return t('collections.faces_load_error')
  return t('collections.no_faces')
})

const faceHoverTooltipText = computed(() => {
  if (peoplePanelOpen.value) return ''

  const hoveredIndex = faces.value.findIndex((face) => face.id === hoveredFaceId.value)
  if (hoveredIndex === -1) return ''

  return faceDisplayName(faces.value[hoveredIndex], hoveredIndex)
})

const showViewerEmpty = computed(() => (
  fileInfo.value !== null && !viewerLoading.value && !viewerReady.value
))

const compactDockOpen = computed(() => infoPanelOpen.value || mapPanelOpen.value)
const compactDockSingle = computed(() => compactLayout.value && (infoPanelOpen.value !== mapPanelOpen.value))
const compactDockStacked = computed(() => (
  compactLayout.value
  && infoPanelOpen.value
  && mapPanelOpen.value
  && viewerWidth.value <= COMPACT_DOCK_STACK_MAX_WIDTH
))

const stageClasses = computed(() => ({
  'compact-layout': compactLayout.value,
  'compact-panel-open': compactLayout.value && (compactDockOpen.value || peoplePanelOpen.value),
  'compact-dock-single': compactDockSingle.value,
  'compact-dock-stacked': compactDockStacked.value,
  'compact-people-open': compactLayout.value && peoplePanelOpen.value,
}))

const stageStyle = computed(() => {
  if (compactLayout.value) {
    return {
      '--controls-right': 'var(--viewer-edge)',
      '--controls-bottom': compactBottomInset.value > 0
        ? `calc(var(--viewer-edge) + ${compactBottomInset.value}px + var(--viewer-gap))`
        : 'var(--viewer-edge)',
      '--people-right': 'var(--viewer-edge)',
      '--info-bottom': 'var(--viewer-edge)',
    }
  }

  return {
    '--controls-right': infoPanelOpen.value
      ? 'calc(var(--viewer-edge) + var(--viewer-side-width) + var(--viewer-gap))'
      : 'var(--viewer-edge)',
    '--controls-bottom': peoplePanelOpen.value || (mapPanelOpen.value && !infoPanelOpen.value)
      ? 'calc(var(--viewer-edge) + var(--viewer-people-height) + var(--viewer-gap))'
      : 'var(--viewer-edge)',
    '--people-right': infoPanelOpen.value || mapPanelOpen.value
      ? 'calc(var(--viewer-edge) + var(--viewer-side-width) + var(--viewer-gap))'
      : 'var(--viewer-edge)',
    '--info-bottom': mapPanelOpen.value
      ? 'calc(var(--viewer-edge) + var(--viewer-people-height) + var(--viewer-gap))'
      : 'var(--viewer-edge)',
  }
})

async function loadFile() {
  const loadToken = ++fileLoadToken
  viewerLoading.value = true
  prevId.value = null
  nextId.value = null
  fileInfo.value = null
  fileMetadata.value = null
  faces.value = []
  facesLoading.value = true
  facesLoadFailed.value = false
  hoveredFaceId.value = null
  hoveredCardFaceId.value = null
  hoverTooltipX.value = 0
  hoverTooltipY.value = 0
  viewerReady.value = false
  tileCache.clear()
  meta = null
  clearCanvas()

  try {
    const fileId = Number(route.params.fileId)
    const collectionRouteId = Number(collectionId.value)
    const [fileRes, metadataRes, navigationRes] = await Promise.all([
      apiFetch(`/files/${fileId}`, { timeoutMs: ROUTE_LOAD_TIMEOUT_MS }),
      apiFetch(`/files/${fileId}/metadata`, { timeoutMs: ROUTE_LOAD_TIMEOUT_MS }),
      apiFetch(`/files/${fileId}/navigation?collection_id=${collectionRouteId}`, { timeoutMs: ROUTE_LOAD_TIMEOUT_MS }),
    ])

    if (loadToken !== fileLoadToken) return

    if (!fileRes.ok) {
      await replaceForRouteFailure(router, route, fileRes)
      return
    }

    if (!metadataRes.ok) {
      await replaceForRouteFailure(router, route, metadataRes)
      return
    }

    const [fileData, metadataData] = await Promise.all([
      fileRes.json(),
      metadataRes.json(),
    ])

    if (loadToken !== fileLoadToken) return

    fileInfo.value = fileData
    fileMetadata.value = metadataData

    if (navigationRes.ok) {
      const navigationData = await navigationRes.json()
      prevId.value = navigationData.prev_id
      nextId.value = navigationData.next_id
    }

    try {
      const facesRes = await apiFetch(`/files/${fileId}/faces`, {
        timeoutMs: ROUTE_LOAD_TIMEOUT_MS,
      })

      if (loadToken !== fileLoadToken) return

      if (facesRes.ok) {
        faces.value = await facesRes.json()
        facesLoadFailed.value = false
      } else {
        faces.value = []
        facesLoadFailed.value = true
      }
    } catch {
      if (loadToken !== fileLoadToken) return
      faces.value = []
      facesLoadFailed.value = true
    } finally {
      if (loadToken === fileLoadToken) facesLoading.value = false
    }

    if (!fileData.tile_base_url) return

    const metaRes = await fetchWithTimeout(`${fileData.tile_base_url}/meta.json`, {
      timeoutMs: ROUTE_LOAD_TIMEOUT_MS,
    })

    if (loadToken !== fileLoadToken) return

    if (!metaRes.ok) {
      await replaceForRouteFailure(router, route, metaRes)
      return
    }

    meta = {
      ...(await metaRes.json()),
      tileBaseUrl: fileData.tile_base_url,
    }

    if (loadToken !== fileLoadToken) return

    resizeCanvas()
    fitImage()
    viewerReady.value = true
    scheduleRender()
  } catch (error) {
    if (loadToken !== fileLoadToken) return
    await replaceForRouteFailure(router, route, error)
  } finally {
    if (loadToken === fileLoadToken) {
      viewerLoading.value = false
      facesLoading.value = false
    }
  }
}

onMounted(() => {
  infoPanelOpen.value = localStorage.getItem(INFO_PANEL_KEY) === 'true'
  mapPanelOpen.value = localStorage.getItem(MAP_PANEL_KEY) === 'true'
  peoplePanelOpen.value = localStorage.getItem(PEOPLE_PANEL_KEY) === 'true'
  normalizePanelStateForLayout()
  window.addEventListener('keydown', onKeyDown)
  resizeObserver = new ResizeObserver(onResize)
  if (containerEl.value instanceof Element) {
    resizeObserver.observe(containerEl.value)
  }
  void nextTick(updateOverlayMetrics)
  void nextTick(updatePeopleListFade)
  void loadFile()
})

watch(() => route.params.fileId, loadFile)

persistPanelState(infoPanelOpen, INFO_PANEL_KEY)
persistPanelState(mapPanelOpen, MAP_PANEL_KEY)
persistPanelState(peoplePanelOpen, PEOPLE_PANEL_KEY)

watch(peoplePanelOpen, (value) => {
  const hadHoveredFace = hoveredFaceId.value !== null || hoveredCardFaceId.value !== null
  if (!value) hoveredCardFaceId.value = null
  if (hadHoveredFace) scheduleRender()
  void nextTick(updatePeopleListFade)
})

watch(faces, async () => {
  await nextTick()
  updatePeopleListFade()
})

watch([infoPanelOpen, mapPanelOpen, peoplePanelOpen, compactDockSingle, compactDockStacked], async () => {
  await nextTick()
  updateOverlayMetrics()
  updatePeopleListFade()
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeyDown)
  if (resizeObserver) resizeObserver.disconnect()
  if (rafId) cancelAnimationFrame(rafId)
})

function updateCompactLayout() {
  viewerWidth.value = containerEl.value?.clientWidth ?? window.innerWidth
  compactLayout.value = viewerWidth.value <= COMPACT_LAYOUT_MAX_WIDTH
}

function normalizePanelStateForLayout() {
  updateCompactLayout()
}

function persistPanelState(panelState, storageKey) {
  watch(panelState, (value) => {
    localStorage.setItem(storageKey, value ? 'true' : 'false')
  })
}

function togglePanel(panel) {
  updateCompactLayout()

  if (panel === 'info') infoPanelOpen.value = !infoPanelOpen.value
  if (panel === 'map') mapPanelOpen.value = !mapPanelOpen.value
  if (panel === 'people') peoplePanelOpen.value = !peoplePanelOpen.value
}

function updateOverlayMetrics() {
  if (!compactLayout.value) {
    compactBottomInset.value = 0
    return
  }

  const containerRect = containerEl.value?.getBoundingClientRect()
  if (!containerRect) {
    compactBottomInset.value = 0
    return
  }

  let top = containerRect.bottom
  const dockRect = compactDockOpen.value ? mobileDockEl.value?.getBoundingClientRect() : null
  const peopleRect = peoplePanelOpen.value ? peoplePanelEl.value?.rootEl?.getBoundingClientRect() : null

  if (dockRect && dockRect.height > 0) top = Math.min(top, dockRect.top)
  if (peopleRect && peopleRect.height > 0) top = Math.min(top, peopleRect.top)

  compactBottomInset.value = Math.max(0, Math.round(containerRect.bottom - top))
}

function updatePeopleListFade() {
  const list = peoplePanelEl.value?.listEl
  if (!list) {
    peopleListAtStart.value = true
    peopleListAtEnd.value = true
    return
  }

  const maxScrollLeft = Math.max(0, list.scrollWidth - list.clientWidth)
  if (maxScrollLeft <= 1) {
    peopleListAtStart.value = true
    peopleListAtEnd.value = true
    return
  }

  const scrollLeft = Math.max(0, list.scrollLeft)
  peopleListAtStart.value = scrollLeft <= 1
  peopleListAtEnd.value = scrollLeft >= (maxScrollLeft - PEOPLE_LIST_FADE_TOLERANCE_PX)
}

function resizeCanvas() {
  const c = canvasEl.value
  if (!c || !containerEl.value) return
  c.width = containerEl.value.clientWidth
  c.height = containerEl.value.clientHeight
}

function clearCanvas() {
  const c = canvasEl.value
  if (!c) return
  const ctx = c.getContext('2d')
  ctx.clearRect(0, 0, c.width, c.height)
}

function fitImage() {
  if (!meta) return
  const c = canvasEl.value
  const sx = c.width / meta.width
  const sy = c.height / meta.height
  fitScaleValue = Math.min(sx, sy) * 0.95
  scale = fitScaleValue
  offsetX = (c.width - meta.width * scale) / 2
  offsetY = (c.height - meta.height * scale) / 2
}

function onResize() {
  updateCompactLayout()
  normalizePanelStateForLayout()
  updateOverlayMetrics()
  updatePeopleListFade()
  if (!meta) return
  const c = canvasEl.value
  const cx = (c.width / 2 - offsetX) / scale
  const cy = (c.height / 2 - offsetY) / scale
  resizeCanvas()
  fitScaleValue = Math.min(c.width / meta.width, c.height / meta.height) * 0.95
  offsetX = c.width / 2 - cx * scale
  offsetY = c.height / 2 - cy * scale
  scheduleRender()
}

function bestZoom() {
  if (!meta) return 0
  const z = Math.round(meta.max_zoom + Math.log2(scale))
  return Math.max(0, Math.min(meta.max_zoom, z))
}

function getTile(z, x, y) {
  const key = `${z}/${x}/${y}`
  if (tileCache.has(key)) return tileCache.get(key)
  const img = new Image()
  img.addEventListener('load', scheduleRender, { once: true })
  img.src = `${meta.tileBaseUrl}/${z}/${x}/${y}.png`
  tileCache.set(key, img)
  return img
}

function scheduleRender() {
  if (rafId !== null) return

  rafId = requestAnimationFrame(() => {
    rafId = null
    render()
  })
}

function render() {
  if (!meta) {
    clearCanvas()
    return
  }
  const canvas = canvasEl.value
  const ctx = canvas.getContext('2d')
  ctx.clearRect(0, 0, canvas.width, canvas.height)

  const { width, height, tile_size, max_zoom } = meta
  const max_dim = Math.max(width, height)
  const z = bestZoom()
  const scale_z = Math.min(1.0, (tile_size * Math.pow(2, z)) / max_dim)
  const zw = Math.max(1, Math.round(width * scale_z))
  const zh = Math.max(1, Math.round(height * scale_z))

  const tileScreenW = tile_size * (width * scale) / zw
  const tileScreenH = tile_size * (height * scale) / zh
  const nx = Math.ceil(zw / tile_size)
  const ny = Math.ceil(zh / tile_size)

  ctx.imageSmoothingEnabled = scale < 1
  ctx.imageSmoothingQuality = 'high'

  for (let tx = 0; tx < nx; tx++) {
    for (let ty = 0; ty < ny; ty++) {
      const sx = offsetX + tx * tileScreenW
      const sy = offsetY + ty * tileScreenH
      if (sx + tileScreenW < 0 || sy + tileScreenH < 0 ||
          sx > canvas.width || sy > canvas.height) continue
      const img = getTile(z, tx, ty)
      if (img.complete && img.naturalWidth > 0) {
        ctx.drawImage(img, sx, sy, tileScreenW, tileScreenH)
      }
    }
  }

  drawFaceOverlays(ctx)
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max)
}

function faceCardCrop(face) {
  if (!face?.region) return null

  let cropHeight = Math.max(
    face.region.height * 2.4,
    (face.region.width * 2.1) / FACE_CARD_RATIO,
    0.42,
  )
  cropHeight = Math.min(1, cropHeight)

  let cropWidth = cropHeight * FACE_CARD_RATIO
  if (cropWidth > 1) {
    cropWidth = 1
    cropHeight = cropWidth / FACE_CARD_RATIO
  }

  const left = clamp(face.region.center_x - cropWidth / 2, 0, 1 - cropWidth)
  const top = clamp(face.region.center_y - cropHeight / 2, 0, 1 - cropHeight)

  return {
    left,
    top,
    width: cropWidth,
    height: cropHeight,
  }
}

function faceCardImageStyle(face) {
  const crop = faceCardCrop(face)
  if (!crop) return {}

  return {
    width: `${100 / crop.width}%`,
    height: `${100 / crop.height}%`,
    left: `${-(crop.left / crop.width) * 100}%`,
    top: `${-(crop.top / crop.height) * 100}%`,
  }
}

function isFaceHovered(faceId) {
  return peoplePanelOpen.value && (faceId === hoveredFaceId.value || faceId === hoveredCardFaceId.value)
}

function faceCardStyle(face) {
  const hovered = isFaceHovered(face?.id)
  return {
    '--face-card-accent': faceAccent(face),
    '--face-card-fill': faceFill(face),
    '--face-card-stroke-width': `${hovered ? FACE_HOVER_STROKE_WIDTH : FACE_STROKE_WIDTH}px`,
    '--face-card-tag-height': `${FACE_TAG_HEIGHT}px`,
    '--face-card-tag-padding-x': `${FACE_TAG_PADDING_X}px`,
  }
}

function faceDisplayName(face, index) {
  return face?.person?.name || t('collections.unknown_person_numbered', { index: index + 1 })
}

function revealPeopleCard(faceId) {
  if (!peoplePanelOpen.value || faceId == null) return

  const card = peoplePanelEl.value?.listEl?.querySelector(`.viewer-people-card[data-face-id="${String(faceId)}"]`)
  if (!card) return

  card.scrollIntoView({ block: 'nearest', inline: 'nearest', behavior: 'auto' })
}

function viewerTargetPoint() {
  const container = containerEl.value
  if (!container) return null

  let sideInset = 0
  let bottomInset = 0

  if (compactLayout.value) {
    bottomInset = compactBottomInset.value
  } else {
    if (infoPanelOpen.value) sideInset = Math.max(sideInset, infoPanelEl.value?.rootEl?.offsetWidth ?? 0)
    if (mapPanelOpen.value) sideInset = Math.max(sideInset, mapPanelEl.value?.offsetWidth ?? 0)
    if (peoplePanelOpen.value) bottomInset = Math.max(bottomInset, peoplePanelEl.value?.rootEl?.offsetHeight ?? 0)
  }

  const width = Math.max(1, container.clientWidth - sideInset)
  const height = Math.max(1, container.clientHeight - bottomInset)

  return {
    width,
    height,
    x: width / 2,
    y: height * FACE_FOCUS_TARGET_Y_RATIO,
  }
}

function focusFace(face) {
  if (!meta || !face?.region) return

  const target = viewerTargetPoint()
  if (!target) return

  const faceWidth = face.region.width * meta.width
  const faceHeight = face.region.height * meta.height
  if (faceWidth <= 0 || faceHeight <= 0) return

  const maxScale = Math.pow(2, meta.max_zoom) * 2
  const focusScaleByWidth = (target.width * FACE_FOCUS_TARGET_WIDTH_RATIO) / faceWidth
  const focusScaleByHeight = (target.height * FACE_FOCUS_TARGET_HEIGHT_RATIO) / faceHeight
  const focusScale = Math.min(maxScale, Math.max(
    fitScaleValue * FACE_FOCUS_MIN_FACTOR,
    Math.min(focusScaleByWidth, focusScaleByHeight),
  ))

  scale = focusScale

  offsetX = target.x - face.region.center_x * meta.width * scale
  offsetY = target.y - face.region.center_y * meta.height * scale
  scheduleRender()
}

function setHoveredCardFace(faceId) {
  if (hoveredCardFaceId.value === faceId) return
  hoveredCardFaceId.value = faceId
  scheduleRender()
}

function faceScreenRect(face) {
  if (!meta || !face?.region) return null

  const left = (face.region.center_x - face.region.width / 2) * meta.width
  const top = (face.region.center_y - face.region.height / 2) * meta.height
  const width = face.region.width * meta.width
  const height = face.region.height * meta.height
  if (width <= 0 || height <= 0) return null

  return {
    left: offsetX + left * scale,
    top: offsetY + top * scale,
    width: width * scale,
    height: height * scale,
  }
}

function faceAtCanvasPoint(canvasX, canvasY) {
  for (const face of faces.value) {
    const rect = faceScreenRect(face)
    if (!rect) continue
    if (
      canvasX >= rect.left && canvasX <= rect.left + rect.width &&
      canvasY >= rect.top && canvasY <= rect.top + rect.height
    ) {
      return face
    }
  }

  return null
}

function faceAtClientPoint(clientX, clientY) {
  const canvas = canvasEl.value
  if (!canvas) return null

  const rect = canvas.getBoundingClientRect()
  return faceAtCanvasPoint(clientX - rect.left, clientY - rect.top)
}

function updateHoveredFace(clientX, clientY) {
  const canvas = canvasEl.value
  if (!canvas || !meta || faces.value.length === 0) {
    hoveredFaceId.value = null
    if (canvas) canvas.style.cursor = 'grab'
    return
  }

  const face = faceAtClientPoint(clientX, clientY)
  const nextHoveredFaceId = face?.id ?? null

  canvas.style.cursor = nextHoveredFaceId == null ? 'grab' : 'pointer'
  if (!peoplePanelOpen.value && nextHoveredFaceId !== null) {
    const container = containerEl.value
    if (container) {
      const rect = container.getBoundingClientRect()
      const maxX = Math.max(12, container.clientWidth - 220)
      const maxY = Math.max(12, container.clientHeight - 48)
      hoverTooltipX.value = clamp(clientX - rect.left + 16, 12, maxX)
      hoverTooltipY.value = clamp(clientY - rect.top + 16, 12, maxY)
    }
  }

  if (hoveredFaceId.value === nextHoveredFaceId) {
    return
  }

  hoveredFaceId.value = nextHoveredFaceId
  if (peoplePanelOpen.value) scheduleRender()
}

function faceAccent(face) {
  if (face.person?.name) return '#2f8f7d'
  return '#d19b2f'
}

function faceFill(face) {
  if (face.person?.name) return 'rgba(47, 143, 125, 0.14)'
  return 'rgba(209, 155, 47, 0.14)'
}

function drawFaceTag(ctx, rect, label, color, strokeWidth) {
  const inset = strokeWidth / 2
  const tagX = rect.left + inset
  const tagY = rect.top + inset
  const textWidth = ctx.measureText(label).width
  const tagWidth = Math.ceil(textWidth + FACE_TAG_PADDING_X * 2)

  ctx.fillStyle = color
  ctx.fillRect(tagX, tagY, tagWidth, FACE_TAG_HEIGHT)
  ctx.fillStyle = '#ffffff'
  ctx.fillText(label, tagX + FACE_TAG_PADDING_X, tagY + FACE_TAG_HEIGHT / 2)
}

function drawFaceOverlays(ctx) {
  if (!meta || faces.value.length === 0) return

  ctx.save()
  ctx.font = FACE_TAG_FONT
  ctx.textBaseline = 'middle'

  faces.value.forEach((face, index) => {
    const rect = faceScreenRect(face)
    if (!rect) return
    if (
      rect.left + rect.width < 0 || rect.top + rect.height < 0 ||
      rect.left > canvasEl.value.width || rect.top > canvasEl.value.height
    ) {
      return
    }

    if (!isFaceHovered(face.id)) return

    const accent = faceAccent(face)
    const strokeWidth = FACE_HOVER_STROKE_WIDTH

    ctx.strokeStyle = accent
    ctx.lineWidth = strokeWidth
    ctx.strokeRect(rect.left, rect.top, rect.width, rect.height)
    drawFaceTag(ctx, rect, String(index + 1), accent, strokeWidth)
  })

  ctx.restore()
}

function applyZoom(factor, pivotX, pivotY) {
  if (!meta) return
  const maxScale = Math.pow(2, meta.max_zoom) * 2
  const newScale = Math.max(0.02, Math.min(scale * factor, maxScale))
  offsetX = pivotX - (pivotX - offsetX) * (newScale / scale)
  offsetY = pivotY - (pivotY - offsetY) * (newScale / scale)
  scale = newScale
  scheduleRender()
}

function zoomStep(factor) {
  const c = canvasEl.value
  applyZoom(factor, c.width / 2, c.height / 2)
}

function onWheel(e) {
  const rect = canvasEl.value.getBoundingClientRect()
  applyZoom(e.deltaY < 0 ? 1.12 : 1 / 1.12, e.clientX - rect.left, e.clientY - rect.top)
  updateHoveredFace(e.clientX, e.clientY)
}

function onMouseDown(e) {
  if (hoveredFaceId.value !== null) {
    hoveredFaceId.value = null
    if (peoplePanelOpen.value) scheduleRender()
  }
  dragging = true
  draggedDuringPointer = false
  dragStartX = e.clientX
  dragStartY = e.clientY
  lastX = e.clientX
  lastY = e.clientY
  canvasEl.value.style.cursor = 'grabbing'
}

function onMouseMove(e) {
  if (!dragging) {
    updateHoveredFace(e.clientX, e.clientY)
    return
  }

  if (!draggedDuringPointer) {
    draggedDuringPointer = Math.abs(e.clientX - dragStartX) > FACE_CLICK_TOLERANCE_PX
      || Math.abs(e.clientY - dragStartY) > FACE_CLICK_TOLERANCE_PX
  }

  offsetX += e.clientX - lastX
  offsetY += e.clientY - lastY
  lastX = e.clientX
  lastY = e.clientY
  scheduleRender()
}

function onKeyDown(e) {
  if (e.key === 'ArrowLeft' && prevId.value) router.push(`/collections/${collectionId.value}/${prevId.value}`)
  if (e.key === 'ArrowRight' && nextId.value) router.push(`/collections/${collectionId.value}/${nextId.value}`)
}

function onMouseUp(e) {
  const shouldRevealCard = Boolean(
    e
    && peoplePanelOpen.value
    && !draggedDuringPointer,
  )
  dragging = false
  canvasEl.value.style.cursor = 'grab'

  if (!shouldRevealCard) return

  const face = faceAtClientPoint(e.clientX, e.clientY)
  if (!face) return

  revealPeopleCard(face.id)
}

function onMouseLeave() {
  const hadHoveredFace = peoplePanelOpen.value && hoveredFaceId.value !== null
  dragging = false
  hoveredFaceId.value = null
  canvasEl.value.style.cursor = 'grab'
  if (hadHoveredFace) scheduleRender()
}

function formatPhotoDate(metadata) {
  if (!metadata || !metadata.photo_year) return ''

  const parts = [String(metadata.photo_year).padStart(4, '0')]
  if (metadata.photo_month) parts.push(String(metadata.photo_month).padStart(2, '0'))
  if (metadata.photo_day) parts.push(String(metadata.photo_day).padStart(2, '0'))

  let result = parts.join('-')
  if (metadata.photo_time) result += ` ${metadata.photo_time}`

  if (metadata.date_accuracy && metadata.date_accuracy !== 'exact') {
    result += ` (${t(`collections.date_accuracy.${metadata.date_accuracy}`)})`
  }

  return result
}
</script>

<style scoped>
.file-viewer {
  position: absolute;
  inset: 0;
  background: var(--bg);
}

.viewer-stage {
  position: relative;
  width: 100%;
  height: 100%;
  min-width: 0;
  min-height: 0;
  --viewer-panel-radius: var(--radius-lg);
  --viewer-control-radius: var(--radius-sm);
  --viewer-card-radius: var(--radius-md);
  --viewer-badge-radius: var(--radius-xs);
  --viewer-edge: var(--sp-4);
  --viewer-gap: var(--sp-3);
  --viewer-media-panel-padding: var(--sp-2-5);
  --viewer-side-width: clamp(17rem, 23vw, 20rem);
  --viewer-people-height: 10rem;
  --viewer-mobile-sheet-height: clamp(11.25rem, 34vh, 15.5rem);
  --viewer-mobile-people-height: var(--viewer-people-height);
  --controls-right: var(--viewer-edge);
  --controls-bottom: var(--viewer-edge);
  --people-right: var(--viewer-edge);
  --info-bottom: var(--viewer-edge);
  background:
    radial-gradient(circle at 50% 8%, rgba(255, 255, 255, 0.2), transparent 34%),
    linear-gradient(180deg, rgba(0, 0, 0, 0.03), rgba(0, 0, 0, 0.08)),
    var(--surface-muted);
}

.viewer-canvas {
  width: 100%;
  height: 100%;
  cursor: grab;
  display: block;
}

.viewer-face-hover-tooltip {
  position: absolute;
  z-index: 5;
  max-width: min(13.75rem, calc(100% - var(--viewer-edge) * 2));
  padding: var(--inset-tooltip-y) var(--inset-tooltip-x);
  border: 1px solid rgba(14, 18, 24, 0.14);
  background: rgba(17, 21, 27, 0.92);
  color: #fff;
  font-size: 12px;
  line-height: 1.15;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  pointer-events: none;
  box-shadow: var(--shadow-floating-strong);
}

.viewer-empty {
  position: absolute;
  inset: 0;
  padding: var(--sp-8);
  pointer-events: none;
}

.viewer-empty-card {
  max-width: 24rem;
  padding: var(--sp-6);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.84);
  box-shadow: var(--shadow-elevated);
  text-align: center;
}

.viewer-empty-kicker {
  margin-bottom: var(--sp-2);
  font-size: var(--fs-2xs);
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.viewer-empty-title {
  margin: 0 0 var(--sp-2);
  font-size: var(--fs-lg);
  line-height: 1.3;
  color: var(--text-heading);
  overflow-wrap: anywhere;
}

.viewer-empty-text {
  margin: 0;
  color: var(--text-muted);
}

.viewer-face-hover-tooltip {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.viewer-empty {
  display: flex;
  align-items: center;
  justify-content: center;
}

.viewer-controls {
  position: absolute;
  right: var(--controls-right);
  bottom: var(--controls-bottom);
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: var(--sp-2-5);
  z-index: 4;
  transition: right var(--motion-panel) var(--ease-standard), bottom var(--motion-panel) var(--ease-standard);
}

.viewer-mobile-dock {
  display: contents;
}

.viewer-nav-row {
  display: flex;
  gap: var(--sp-2);
}

.ctrl-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.75rem;
  height: 2.75rem;
  padding: 0;
  background: rgba(20, 24, 29, 0.74);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: var(--viewer-control-radius);
  font-size: var(--fs-base);
  text-decoration: none;
  cursor: pointer;
  transition: background var(--motion-base);
  backdrop-filter: blur(4px);
  box-shadow: var(--shadow-floating);
}

.ctrl-btn:hover {
  background: rgba(15, 18, 22, 0.88);
}

.ctrl-btn.active {
  background: rgba(22, 88, 118, 0.92);
}

.nav-btn.disabled {
  opacity: 0.24;
  cursor: default;
  pointer-events: none;
}


.viewer-panel {
  position: relative;
  display: flex;
  flex-direction: column;
  padding: var(--sp-4);
  border: 1px solid rgba(255, 255, 255, 0.58);
  border-radius: var(--viewer-panel-radius);
  background: linear-gradient(180deg, rgba(247, 248, 250, 0.84), rgba(236, 239, 242, 0.72));
  backdrop-filter: blur(20px) saturate(1.08);
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-gutter: stable;
  opacity: 0;
  pointer-events: none;
  box-shadow: var(--shadow-panel);
  transform: translateY(0.5rem) scale(0.988);
  transition: transform var(--motion-panel) var(--ease-standard), opacity var(--motion-panel) var(--ease-standard);
  scrollbar-width: thin;
  scrollbar-color: rgba(82, 92, 105, 0.46) transparent;
  z-index: 3;
}

.viewer-panel::-webkit-scrollbar {
  width: 0.4rem;
  height: 0.4rem;
}

.viewer-panel::-webkit-scrollbar-thumb {
  background: rgba(82, 92, 105, 0.46);
}

.viewer-panel::-webkit-scrollbar-track {
  background: transparent;
}

.viewer-panel.open {
  opacity: 1;
  pointer-events: auto;
  transform: translateY(0) scale(1);
}

.viewer-panel-info {
  position: absolute;
  top: var(--viewer-edge);
  right: var(--viewer-edge);
  bottom: var(--info-bottom);
  width: var(--viewer-side-width);
}

.viewer-panel-map {
  position: absolute;
  right: var(--viewer-edge);
  bottom: var(--viewer-edge);
  width: var(--viewer-side-width);
  height: var(--viewer-people-height);
  padding: var(--viewer-media-panel-padding);
  overflow-y: hidden;
  scrollbar-gutter: auto;
}

.viewer-panel-map :deep(.map-raster-engine__attribution) {
  display: none;
}

.viewer-panel-people {
  position: absolute;
  left: var(--viewer-edge);
  right: var(--people-right);
  bottom: var(--viewer-edge);
  height: var(--viewer-people-height);
  padding: var(--viewer-media-panel-padding) var(--viewer-media-panel-padding) 0;
  z-index: 3;
}

[data-theme="dark"] .viewer-stage {
  background:
    radial-gradient(circle at 50% 8%, rgba(255, 255, 255, 0.05), transparent 34%),
    linear-gradient(180deg, rgba(0, 0, 0, 0.14), rgba(0, 0, 0, 0.22)),
    #14181d;
}

[data-theme="dark"] .viewer-panel {
  border-color: rgba(255, 255, 255, 0.08);
  background: linear-gradient(180deg, rgba(24, 28, 34, 0.9), rgba(16, 19, 24, 0.82));
  box-shadow: var(--shadow-panel-dark);
}

[data-theme="dark"] .viewer-panel::-webkit-scrollbar-thumb {
  background: rgba(206, 214, 224, 0.18);
}

.viewer-stage.compact-layout {
  --viewer-edge: var(--sp-3);
}

.viewer-stage.compact-layout .viewer-mobile-dock {
  position: absolute;
  left: var(--viewer-edge);
  right: var(--viewer-edge);
  bottom: var(--viewer-edge);
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  align-items: stretch;
  gap: var(--viewer-gap);
  z-index: 3;
}

.viewer-stage.compact-people-open .viewer-mobile-dock {
  bottom: calc(var(--viewer-edge) + var(--viewer-mobile-people-height) + var(--viewer-gap));
}

.viewer-stage.compact-dock-single .viewer-mobile-dock,
.viewer-stage.compact-dock-stacked .viewer-mobile-dock {
  grid-template-columns: 1fr;
}

.viewer-stage.compact-layout .viewer-mobile-dock > .viewer-panel {
  position: relative;
  top: auto;
  left: auto;
  right: auto;
  bottom: auto;
  width: auto;
  height: var(--viewer-mobile-sheet-height);
}

.viewer-stage.compact-layout .viewer-mobile-dock > .viewer-panel:not(.open) {
  display: none;
}

.viewer-stage.compact-layout .viewer-panel-people {
  left: var(--viewer-edge);
  right: var(--viewer-edge);
  bottom: var(--viewer-edge);
  height: var(--viewer-mobile-people-height);
}

</style>
