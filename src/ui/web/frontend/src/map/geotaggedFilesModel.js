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

function fileName(path) {
  const normalized = String(path || '').replaceAll('\\', '/')
  if (!normalized) return ''
  const parts = normalized.split('/')
  return parts[parts.length - 1] || normalized
}

function normalizeFile(file) {
  if (!file || typeof file !== 'object') return null

  const lat = toFiniteNumber(file?.gps?.lat)
  const lon = toFiniteNumber(file?.gps?.lon)
  const point = normalizeGeoPoint(lat, lon)
  if (!point) return null

  return {
    ...file,
    gps: point,
  }
}

function midpointBounds(bounds) {
  return {
    lat: (bounds.south + bounds.north) / 2,
    lon: (bounds.west + bounds.east) / 2,
  }
}

function markerLabel(file) {
  const title = fileName(file.path)
  if (file.collection_name) return `${title} · ${file.collection_name}`
  return title
}

export function geotaggedFilesBounds(files) {
  const normalizedFiles = files
    .map(normalizeFile)
    .filter(Boolean)

  if (normalizedFiles.length === 0) return null

  return normalizedFiles.reduce((bounds, file) => ({
    south: Math.min(bounds.south, file.gps.lat),
    west: Math.min(bounds.west, file.gps.lon),
    north: Math.max(bounds.north, file.gps.lat),
    east: Math.max(bounds.east, file.gps.lon),
  }), {
    south: normalizedFiles[0].gps.lat,
    west: normalizedFiles[0].gps.lon,
    north: normalizedFiles[0].gps.lat,
    east: normalizedFiles[0].gps.lon,
  })
}

export function geotaggedFilesMapModelFromFiles(files) {
  const normalizedFiles = files
    .map(normalizeFile)
    .filter(Boolean)

  if (normalizedFiles.length === 0) return null

  const bounds = geotaggedFilesBounds(normalizedFiles)
  const singlePoint = normalizedFiles.length === 1 ? normalizedFiles[0].gps : null
  const center = singlePoint ?? midpointBounds(bounds)

  return createMapModel({
    viewport: {
      center,
      zoom: singlePoint ? 14 : 2,
      minZoom: 1,
      maxZoom: 19,
    },
    tileSource: OSM_STANDARD_TILE_SOURCE,
    markers: normalizedFiles.map((file) => ({
      id: file.id,
      position: file.gps,
      title: markerLabel(file),
    })),
  })
}