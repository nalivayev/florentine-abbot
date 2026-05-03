/**
 * @typedef {{ lat: number, lon: number }} MapGeoPoint
 * @typedef {{ center: MapGeoPoint, zoom: number, minZoom?: number, maxZoom?: number }} MapViewport
 * @typedef {{ id: string|number, position: MapGeoPoint, label?: string, title?: string }} MapMarker
 * @typedef {{ id?: string|number, points: MapGeoPoint[], label?: string }} MapPolyline
 * @typedef {{ urlTemplate: string, attribution?: string, minZoom?: number, maxZoom?: number }} MapTileSource
 * @typedef {{
 *   viewport: MapViewport,
 *   markers: MapMarker[],
 *   polylines: MapPolyline[],
 *   tileSource?: MapTileSource | null,
 * }} MapModel
 *
 * @typedef {{
 *   mount: (host: HTMLElement) => void,
 *   unmount: () => void,
 *   resize?: () => void,
 *   setView?: (viewport: MapViewport) => void,
 *   setData?: (model: MapModel | null) => void,
 *   fitBounds?: (bounds: { south: number, west: number, north: number, east: number }) => void,
 *   screenToGeo?: (point: { x: number, y: number }) => MapGeoPoint | null,
 *   geoToScreen?: (point: MapGeoPoint) => { x: number, y: number } | null,
 * }} MapEngine
 *
 * @typedef {(handlers?: {
 *   onReady?: (payload?: unknown) => void,
 *   onViewportChange?: (payload: MapViewport) => void,
 *   onMarkerClick?: (markerId: string|number) => void,
 *   onHover?: (payload: unknown) => void,
 * }) => MapEngine} MapEngineFactory
 */

export const DEFAULT_MAP_VIEWPORT = Object.freeze({
  center: Object.freeze({ lat: 0, lon: 0 }),
  zoom: 2,
  minZoom: 1,
  maxZoom: 19,
})

export function createMapModel(overrides = {}) {
  return {
    viewport: {
      ...DEFAULT_MAP_VIEWPORT,
      ...overrides.viewport,
      center: {
        ...DEFAULT_MAP_VIEWPORT.center,
        ...(overrides.viewport?.center ?? {}),
      },
    },
    markers: Array.isArray(overrides.markers) ? overrides.markers : [],
    polylines: Array.isArray(overrides.polylines) ? overrides.polylines : [],
    tileSource: overrides.tileSource ?? null,
  }
}