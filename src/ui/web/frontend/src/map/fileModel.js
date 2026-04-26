import { createMapModel } from './contracts.js'
import { OSM_STANDARD_TILE_SOURCE } from './tileSources.js'

function toFiniteNumber(value) {
  const number = Number(value)
  return Number.isFinite(number) ? number : null
}

function normalizeGeoPoint(lat, lon) {
  if (lat == null || lon == null) return null
  if (lat < -90 || lat > 90 || lon < -180 || lon > 180) return null

  return { lat, lon }
}

function extractGps(fileInfo, metadata = null) {
  const candidates = [
    metadata?.gps,
    metadata,
    fileInfo?.gps,
    fileInfo?.metadata?.gps,
    fileInfo?.metadata,
  ]

  for (const candidate of candidates) {
    if (!candidate || typeof candidate !== 'object') continue

    const lat = toFiniteNumber(candidate.lat ?? candidate.latitude)
    const lon = toFiniteNumber(candidate.lon ?? candidate.longitude)
    const point = normalizeGeoPoint(lat, lon)
    if (point) return point
  }

  return null
}

function fileLabel(fileInfo) {
  const path = String(fileInfo?.path || '').replaceAll('\\', '/')
  if (!path) return ''

  const parts = path.split('/')
  return parts[parts.length - 1] || path
}

export function fileMapModelFromFile(fileInfo, metadata = null) {
  const point = extractGps(fileInfo, metadata)
  if (!point) return null

  return createMapModel({
    viewport: {
      center: point,
      zoom: 14,
      minZoom: 1,
      maxZoom: 19,
    },
    tileSource: OSM_STANDARD_TILE_SOURCE,
    markers: [
      {
        id: 'file-location',
        position: point,
        label: fileLabel(fileInfo),
      },
    ],
  })
}