import './rasterTileEngine.css'

import {
  clampNormalizedY,
  geoToNormalized,
  normalizedToGeo,
  scaleForZoom,
  shortestWrappedDeltaX,
  tileCountForZoom,
  wrapNormalizedX,
} from '../webMercator.js'

const SVG_NS = 'http://www.w3.org/2000/svg'
const TILE_SIZE = 256
const DEFAULT_MIN_ZOOM = 0
const DEFAULT_MAX_ZOOM = 19
const DEFAULT_VIEWPORT = Object.freeze({
  center: Object.freeze({ lat: 0, lon: 0 }),
  zoom: 2,
  minZoom: DEFAULT_MIN_ZOOM,
  maxZoom: DEFAULT_MAX_ZOOM,
})

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max)
}

function wrapTileIndex(index, count) {
  return ((index % count) + count) % count
}

function tileUrl(template, x, y, z) {
  return template
    .replace('{x}', String(x))
    .replace('{y}', String(y))
    .replace('{z}', String(z))
}

function clampZoom(zoom, model) {
  const minZoom = Math.max(DEFAULT_MIN_ZOOM, Number(model?.tileSource?.minZoom ?? model?.viewport?.minZoom ?? DEFAULT_MIN_ZOOM))
  const maxZoom = Math.min(DEFAULT_MAX_ZOOM, Number(model?.tileSource?.maxZoom ?? model?.viewport?.maxZoom ?? DEFAULT_MAX_ZOOM))
  return clamp(Math.round(Number(zoom) || DEFAULT_VIEWPORT.zoom), minZoom, maxZoom)
}

function normalizeViewport(source, model) {
  const zoom = clampZoom(source?.zoom ?? model?.viewport?.zoom ?? DEFAULT_VIEWPORT.zoom, model)
  return {
    center: {
      lat: Number(source?.center?.lat ?? model?.viewport?.center?.lat ?? DEFAULT_VIEWPORT.center.lat),
      lon: Number(source?.center?.lon ?? model?.viewport?.center?.lon ?? DEFAULT_VIEWPORT.center.lon),
    },
    zoom,
    minZoom: Math.max(DEFAULT_MIN_ZOOM, Number(source?.minZoom ?? model?.viewport?.minZoom ?? DEFAULT_MIN_ZOOM)),
    maxZoom: Math.min(DEFAULT_MAX_ZOOM, Number(source?.maxZoom ?? model?.viewport?.maxZoom ?? DEFAULT_MAX_ZOOM)),
  }
}

function removeChildren(node) {
  while (node.firstChild) node.removeChild(node.firstChild)
}

export function createRasterTileMapEngine(handlers = {}) {
  let host = null
  let rootEl = null
  let viewportEl = null
  let tileLayerEl = null
  let vectorEl = null
  let markerLayerEl = null
  let attributionEl = null
  let resizeObserver = null
  let size = { width: 0, height: 0 }
  let model = null
  let viewport = { ...DEFAULT_VIEWPORT }
  let dragState = null

  function emitViewportChange() {
    handlers.onViewportChange?.({
      center: { ...viewport.center },
      zoom: viewport.zoom,
      minZoom: viewport.minZoom,
      maxZoom: viewport.maxZoom,
    })
  }

  function measure() {
    if (!host) {
      size = { width: 0, height: 0 }
      return
    }

    size = {
      width: Math.max(0, host.clientWidth),
      height: Math.max(0, host.clientHeight),
    }
  }

  function currentCenterNormalized() {
    return geoToNormalized(viewport.center)
  }

  function setViewport(nextViewport, { emit = true } = {}) {
    viewport = normalizeViewport(nextViewport, model)
    render()
    if (emit) emitViewportChange()
  }

  function worldToScreen(pointNormalized) {
    if (!size.width || !size.height) return null

    const center = currentCenterNormalized()
    const scale = scaleForZoom(viewport.zoom)
    return {
      x: size.width / 2 + shortestWrappedDeltaX(pointNormalized.x - center.x) * scale,
      y: size.height / 2 + (pointNormalized.y - center.y) * scale,
    }
  }

  function screenToNormalized(point) {
    if (!size.width || !size.height) return null

    const center = currentCenterNormalized()
    const scale = scaleForZoom(viewport.zoom)
    return {
      x: wrapNormalizedX(center.x + (point.x - size.width / 2) / scale),
      y: clampNormalizedY(center.y + (point.y - size.height / 2) / scale),
    }
  }

  function zoomAtPoint(nextZoom, point) {
    if (!size.width || !size.height) return

    const clampedZoom = clampZoom(nextZoom, model)
    if (clampedZoom === viewport.zoom) return

    const pivotNormalized = screenToNormalized(point)
    if (!pivotNormalized) return

    const nextScale = scaleForZoom(clampedZoom)
    const nextCenterNormalized = {
      x: wrapNormalizedX(pivotNormalized.x - (point.x - size.width / 2) / nextScale),
      y: clampNormalizedY(pivotNormalized.y - (point.y - size.height / 2) / nextScale),
    }

    setViewport({
      ...viewport,
      zoom: clampedZoom,
      center: normalizedToGeo(nextCenterNormalized),
    })
  }

  function renderPolylines() {
    removeChildren(vectorEl)
    if (!Array.isArray(model?.polylines) || model.polylines.length === 0) return

    model.polylines.forEach((polyline) => {
      if (!Array.isArray(polyline.points) || polyline.points.length < 2) return

      const points = polyline.points
        .map((point) => worldToScreen(geoToNormalized(point)))
        .filter(Boolean)
        .map((point) => `${point.x},${point.y}`)

      if (points.length < 2) return

      const line = document.createElementNS(SVG_NS, 'polyline')
      line.setAttribute('points', points.join(' '))
      line.setAttribute('fill', 'none')
      line.setAttribute('stroke', 'rgba(29, 101, 134, 0.95)')
      line.setAttribute('stroke-width', '3')
      line.setAttribute('stroke-linecap', 'round')
      line.setAttribute('stroke-linejoin', 'round')
      vectorEl.appendChild(line)
    })
  }

  function renderMarkers() {
    removeChildren(markerLayerEl)
    if (!Array.isArray(model?.markers) || model.markers.length === 0) return

    model.markers.forEach((marker) => {
      const screenPoint = worldToScreen(geoToNormalized(marker.position))
      if (!screenPoint) return
      const markerTitle = marker.title ?? marker.label

      const markerEl = document.createElement('button')
      markerEl.type = 'button'
      markerEl.className = 'map-raster-engine__marker'
      markerEl.style.left = `${screenPoint.x}px`
      markerEl.style.top = `${screenPoint.y}px`
      if (markerTitle) markerEl.title = markerTitle
      markerEl.addEventListener('click', () => handlers.onMarkerClick?.(marker.id))

      const dotEl = document.createElement('span')
      dotEl.className = 'map-raster-engine__marker-dot'
      markerEl.appendChild(dotEl)

      if (marker.label) {
        const labelEl = document.createElement('span')
        labelEl.className = 'map-raster-engine__marker-label'
        labelEl.textContent = marker.label
        markerEl.appendChild(labelEl)
      }

      markerLayerEl.appendChild(markerEl)
    })
  }

  function renderTiles() {
    removeChildren(tileLayerEl)

    if (!model?.tileSource || !size.width || !size.height) return

    const zoom = viewport.zoom
    const scale = scaleForZoom(zoom)
    const tileCount = tileCountForZoom(zoom)
    const center = currentCenterNormalized()
    const centerWorld = {
      x: center.x * scale,
      y: center.y * scale,
    }
    const leftWorld = centerWorld.x - size.width / 2
    const topWorld = centerWorld.y - size.height / 2
    const minTileX = Math.floor(leftWorld / TILE_SIZE)
    const maxTileX = Math.floor((leftWorld + size.width) / TILE_SIZE)
    const minTileY = Math.floor(topWorld / TILE_SIZE)
    const maxTileY = Math.floor((topWorld + size.height) / TILE_SIZE)

    for (let tileX = minTileX; tileX <= maxTileX; tileX += 1) {
      for (let tileY = minTileY; tileY <= maxTileY; tileY += 1) {
        if (tileY < 0 || tileY >= tileCount) continue

        const tileEl = document.createElement('img')
        tileEl.className = 'map-raster-engine__tile'
        tileEl.alt = ''
        tileEl.draggable = false
        tileEl.decoding = 'async'
        tileEl.loading = 'eager'
        tileEl.style.left = `${tileX * TILE_SIZE - leftWorld}px`
        tileEl.style.top = `${tileY * TILE_SIZE - topWorld}px`
        tileEl.src = tileUrl(
          model.tileSource.urlTemplate,
          wrapTileIndex(tileX, tileCount),
          tileY,
          zoom,
        )
        tileLayerEl.appendChild(tileEl)
      }
    }
  }

  function render() {
    if (!rootEl) return

    rootEl.dataset.hasTiles = model?.tileSource ? 'true' : 'false'
    attributionEl.textContent = model?.tileSource?.attribution || ''

    renderTiles()
    renderPolylines()
    renderMarkers()
  }

  function onWheel(event) {
    if (!model?.tileSource || !viewportEl) return
    event.preventDefault()

    const rect = viewportEl.getBoundingClientRect()
    zoomAtPoint(
      viewport.zoom + (event.deltaY < 0 ? 1 : -1),
      { x: event.clientX - rect.left, y: event.clientY - rect.top },
    )
  }

  function onPointerDown(event) {
    if (!viewportEl || event.button !== 0) return

    dragState = {
      pointerId: event.pointerId,
      startX: event.clientX,
      startY: event.clientY,
      startCenter: currentCenterNormalized(),
    }
    viewportEl.classList.add('is-dragging')
    viewportEl.setPointerCapture?.(event.pointerId)
  }

  function onPointerMove(event) {
    if (!dragState || event.pointerId !== dragState.pointerId) return

    const scale = scaleForZoom(viewport.zoom)
    const nextCenterNormalized = {
      x: wrapNormalizedX(dragState.startCenter.x - (event.clientX - dragState.startX) / scale),
      y: clampNormalizedY(dragState.startCenter.y - (event.clientY - dragState.startY) / scale),
    }

    setViewport({
      ...viewport,
      center: normalizedToGeo(nextCenterNormalized),
    })
  }

  function clearDragState(pointerId = null) {
    if (!viewportEl || !dragState) return
    if (pointerId !== null && pointerId !== dragState.pointerId) return
    viewportEl.classList.remove('is-dragging')
    dragState = null
  }

  function mount(hostElement) {
    if (!(hostElement instanceof HTMLElement)) return

    host = hostElement

    rootEl = document.createElement('div')
    rootEl.className = 'map-raster-engine'

    viewportEl = document.createElement('div')
    viewportEl.className = 'map-raster-engine__viewport'
    viewportEl.addEventListener('wheel', onWheel, { passive: false })
    viewportEl.addEventListener('pointerdown', onPointerDown)
    viewportEl.addEventListener('pointermove', onPointerMove)
    viewportEl.addEventListener('pointerup', (event) => clearDragState(event.pointerId))
    viewportEl.addEventListener('pointercancel', (event) => clearDragState(event.pointerId))
    viewportEl.addEventListener('pointerleave', (event) => clearDragState(event.pointerId))

    tileLayerEl = document.createElement('div')
    tileLayerEl.className = 'map-raster-engine__tiles'

    vectorEl = document.createElementNS(SVG_NS, 'svg')
    vectorEl.classList.add('map-raster-engine__vector')
    vectorEl.setAttribute('viewBox', '0 0 100 100')
    vectorEl.setAttribute('preserveAspectRatio', 'none')

    markerLayerEl = document.createElement('div')
    markerLayerEl.className = 'map-raster-engine__markers'

    attributionEl = document.createElement('div')
    attributionEl.className = 'map-raster-engine__attribution'

    viewportEl.appendChild(tileLayerEl)
    viewportEl.appendChild(vectorEl)
    viewportEl.appendChild(markerLayerEl)
    rootEl.appendChild(viewportEl)
    rootEl.appendChild(attributionEl)
    host.appendChild(rootEl)

    resizeObserver = new ResizeObserver(() => {
      measure()
      render()
    })
    resizeObserver.observe(host)

    measure()
    render()
    handlers.onReady?.({})
  }

  function unmount() {
    resizeObserver?.disconnect()
    resizeObserver = null
    dragState = null
    if (rootEl && host?.contains(rootEl)) host.removeChild(rootEl)
    host = null
    rootEl = null
    viewportEl = null
    tileLayerEl = null
    vectorEl = null
    markerLayerEl = null
    attributionEl = null
    size = { width: 0, height: 0 }
  }

  function resize() {
    measure()
    render()
  }

  function setView(nextViewport) {
    setViewport(nextViewport)
  }

  function setData(nextModel) {
    model = nextModel
    viewport = normalizeViewport(nextModel?.viewport, nextModel)
    render()
  }

  function fitBounds(bounds) {
    if (!bounds || !size.width || !size.height) return

    const southWest = geoToNormalized({ lat: bounds.south, lon: bounds.west })
    const northEast = geoToNormalized({ lat: bounds.north, lon: bounds.east })
    const xDelta = Math.max(0.000001, Math.abs(shortestWrappedDeltaX(northEast.x - southWest.x)))
    const yDelta = Math.max(0.000001, Math.abs(northEast.y - southWest.y))

    const zoomX = Math.log2(size.width / (TILE_SIZE * xDelta))
    const zoomY = Math.log2(size.height / (TILE_SIZE * yDelta))
    const nextZoom = clampZoom(Math.floor(Math.min(zoomX, zoomY)), model)
    const centerNormalized = {
      x: wrapNormalizedX(southWest.x + shortestWrappedDeltaX(northEast.x - southWest.x) / 2),
      y: clampNormalizedY((southWest.y + northEast.y) / 2),
    }

    setViewport({
      ...viewport,
      zoom: nextZoom,
      center: normalizedToGeo(centerNormalized),
    })
  }

  function screenToGeo(point) {
    const normalized = screenToNormalized(point)
    return normalized ? normalizedToGeo(normalized) : null
  }

  function geoToScreen(point) {
    return worldToScreen(geoToNormalized(point))
  }

  return {
    mount,
    unmount,
    resize,
    setView,
    setData,
    fitBounds,
    screenToGeo,
    geoToScreen,
  }
}