const MAX_LATITUDE = 85.05112878

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max)
}

export function clampLatitude(lat) {
  return clamp(lat, -MAX_LATITUDE, MAX_LATITUDE)
}

export function wrapLongitude(lon) {
  let wrapped = Number(lon)
  while (wrapped < -180) wrapped += 360
  while (wrapped >= 180) wrapped -= 360
  return wrapped
}

export function wrapNormalizedX(value) {
  const wrapped = value % 1
  return wrapped < 0 ? wrapped + 1 : wrapped
}

export function clampNormalizedY(value) {
  return clamp(value, 0, 1)
}

export function shortestWrappedDeltaX(delta) {
  if (delta > 0.5) return delta - 1
  if (delta < -0.5) return delta + 1
  return delta
}

export function scaleForZoom(zoom) {
  return 256 * (2 ** zoom)
}

export function tileCountForZoom(zoom) {
  return 2 ** zoom
}

export function geoToNormalized(point) {
  const lat = clampLatitude(Number(point?.lat) || 0)
  const lon = wrapLongitude(Number(point?.lon) || 0)
  const sinLat = Math.sin((lat * Math.PI) / 180)

  return {
    x: wrapNormalizedX((lon + 180) / 360),
    y: clampNormalizedY(0.5 - Math.log((1 + sinLat) / (1 - sinLat)) / (4 * Math.PI)),
  }
}

export function normalizedToGeo(point) {
  const x = wrapNormalizedX(Number(point?.x) || 0)
  const y = clampNormalizedY(Number(point?.y) || 0)
  const lon = x * 360 - 180
  const lat = (Math.atan(Math.sinh(Math.PI * (1 - 2 * y))) * 180) / Math.PI

  return {
    lat: clampLatitude(lat),
    lon: wrapLongitude(lon),
  }
}