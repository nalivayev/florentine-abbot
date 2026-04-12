<template>
  <div class="file-viewer" ref="containerEl">
    <canvas ref="canvasEl" class="viewer-canvas"
      @wheel.prevent="onWheel"
      @mousedown="onMouseDown"
      @mousemove="onMouseMove"
      @mouseup="onMouseUp"
      @mouseleave="onMouseUp"
    />
    <div class="viewer-back">
      <router-link :to="`/albums/${collectionId}`" class="ctrl-btn">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <rect x="2" y="2" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.5"/>
          <rect x="9" y="2" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.5"/>
          <rect x="2" y="9" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.5"/>
          <rect x="9" y="9" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.5"/>
        </svg>
      </router-link>
    </div>
    <div class="viewer-controls">
      <router-link to="" class="ctrl-btn" @click.prevent="zoomStep(1.5)">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M8 3v10M3 8h10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
      </router-link>
      <router-link to="" class="ctrl-btn" @click.prevent="zoomStep(1 / 1.5)">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M3 8h10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
      </router-link>
    </div>
    <div class="viewer-nav">
      <router-link v-if="prevId" :to="`/albums/${collectionId}/${prevId}`" class="ctrl-btn nav-btn">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M10 3L5 8l5 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </router-link>
      <router-link v-else to="" class="ctrl-btn nav-btn disabled">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M10 3L5 8l5 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </router-link>
      <router-link v-if="nextId" :to="`/albums/${collectionId}/${nextId}`" class="ctrl-btn nav-btn">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M6 3l5 5-5 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </router-link>
      <router-link v-else to="" class="ctrl-btn nav-btn disabled">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M6 3l5 5-5 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiFetch } from '../api.js'

const route = useRoute()
const router = useRouter()
const canvasEl = ref(null)
const containerEl = ref(null)
const collectionId = route.params.id
const prevId = ref(null)
const nextId = ref(null)

let meta = null
let scale = 1
let offsetX = 0
let offsetY = 0
let dragging = false
let lastX = 0
let lastY = 0
const tileCache = new Map()
let rafId = null

async function loadFile() {
  const fileId = Number(route.params.fileId)
  const res = await apiFetch(`/collections/${collectionId}/files/${fileId}`)
  if (!res.ok) return
  const file = await res.json()
  if (!file.tile_base_url) return

  prevId.value = file.prev_id
  nextId.value = file.next_id

  const metaRes = await fetch(`${file.tile_base_url}/meta.json`)
  if (!metaRes.ok) return
  tileCache.clear()
  meta = { ...(await metaRes.json()), tileBaseUrl: file.tile_base_url }

  resizeCanvas()
  fitImage()
}

onMounted(async () => {
  await loadFile()
  startRender()
  window.addEventListener('resize', onResize)
  window.addEventListener('keydown', onKeyDown)
})

watch(() => route.params.fileId, async () => {
  await loadFile()
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  window.removeEventListener('keydown', onKeyDown)
  if (rafId) cancelAnimationFrame(rafId)
})

function resizeCanvas() {
  const c = canvasEl.value
  c.width = containerEl.value.clientWidth
  c.height = containerEl.value.clientHeight
}

function fitImage() {
  const c = canvasEl.value
  const sx = c.width / meta.width
  const sy = c.height / meta.height
  scale = Math.min(sx, sy) * 0.95
  offsetX = (c.width - meta.width * scale) / 2
  offsetY = (c.height - meta.height * scale) / 2
}

function onResize() {
  const c = canvasEl.value
  const cx = (c.width / 2 - offsetX) / scale
  const cy = (c.height / 2 - offsetY) / scale
  resizeCanvas()
  offsetX = c.width / 2 - cx * scale
  offsetY = c.height / 2 - cy * scale
}

function bestZoom() {
  const z = Math.round(meta.max_zoom + Math.log2(scale))
  return Math.max(0, Math.min(meta.max_zoom, z))
}

function getTile(z, x, y) {
  const key = `${z}/${x}/${y}`
  if (tileCache.has(key)) return tileCache.get(key)
  const img = new Image()
  img.src = `${meta.tileBaseUrl}/${z}/${x}/${y}.png`
  tileCache.set(key, img)
  return img
}

function startRender() {
  const frame = () => { render(); rafId = requestAnimationFrame(frame) }
  rafId = requestAnimationFrame(frame)
}

function render() {
  if (!meta) return
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
}

function applyZoom(factor, pivotX, pivotY) {
  if (!meta) return
  const maxScale = Math.pow(2, meta.max_zoom) * 2
  const newScale = Math.max(0.02, Math.min(scale * factor, maxScale))
  offsetX = pivotX - (pivotX - offsetX) * (newScale / scale)
  offsetY = pivotY - (pivotY - offsetY) * (newScale / scale)
  scale = newScale
}

function zoomStep(factor) {
  const c = canvasEl.value
  applyZoom(factor, c.width / 2, c.height / 2)
}

function onWheel(e) {
  const rect = canvasEl.value.getBoundingClientRect()
  applyZoom(e.deltaY < 0 ? 1.12 : 1 / 1.12, e.clientX - rect.left, e.clientY - rect.top)
}

function onMouseDown(e) {
  dragging = true
  lastX = e.clientX
  lastY = e.clientY
  canvasEl.value.style.cursor = 'grabbing'
}

function onMouseMove(e) {
  if (!dragging) return
  offsetX += e.clientX - lastX
  offsetY += e.clientY - lastY
  lastX = e.clientX
  lastY = e.clientY
}

function onKeyDown(e) {
  if (e.key === 'ArrowLeft' && prevId.value) router.push(`/albums/${collectionId}/${prevId.value}`)
  if (e.key === 'ArrowRight' && nextId.value) router.push(`/albums/${collectionId}/${nextId.value}`)
}

function onMouseUp() {
  dragging = false
  canvasEl.value.style.cursor = 'grab'
}
</script>

<style scoped>
.file-viewer {
  position: absolute;
  inset: 0;
}
.viewer-canvas {
  width: 100%;
  height: 100%;
  cursor: grab;
  display: block;
}
.viewer-back {
  position: absolute;
  top: var(--sp-4);
  left: var(--sp-4);
}
.viewer-controls {
  position: absolute;
  bottom: var(--sp-4);
  right: var(--sp-4);
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
}
.ctrl-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  background: rgba(0, 0, 0, 0.45);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  font-size: var(--fs-base);
  text-decoration: none;
  cursor: pointer;
  transition: background 0.15s;
  backdrop-filter: blur(4px);
}
.ctrl-btn:hover {
  background: rgba(0, 0, 0, 0.7);
}
.viewer-nav {
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  transform: translateY(-50%);
  display: flex;
  justify-content: space-between;
  padding: 0 var(--sp-4);
  pointer-events: none;
}
.nav-btn {
  pointer-events: all;
}
.nav-btn.disabled {
  opacity: 0.2;
  cursor: default;
  pointer-events: none;
}
</style>
