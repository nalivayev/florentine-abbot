/**
 * Wrapper around fetch that adds the Authorization header automatically.
 */
const API_VERSION = 'v1'
const API_BASE = `/api/${API_VERSION}`

export async function fetchWithTimeout(url, options = {}) {
  const { timeoutMs, signal, ...fetchOptions } = options
  if (!timeoutMs) return fetch(url, { ...fetchOptions, signal })

  const controller = new AbortController()
  let timedOut = false
  let abortListener = null

  if (signal) {
    if (signal.aborted) {
      controller.abort(signal.reason)
    } else {
      abortListener = () => controller.abort(signal.reason)
      signal.addEventListener('abort', abortListener, { once: true })
    }
  }

  const timeoutId = window.setTimeout(() => {
    timedOut = true
    controller.abort()
  }, timeoutMs)

  try {
    return await fetch(url, { ...fetchOptions, signal: controller.signal })
  } catch (error) {
    if (timedOut && (error?.name === 'AbortError' || error?.name === 'TimeoutError')) {
      const timeoutError = new Error(`Request timed out after ${timeoutMs}ms`)
      timeoutError.name = 'TimeoutError'
      throw timeoutError
    }
    throw error
  } finally {
    window.clearTimeout(timeoutId)
    if (signal && abortListener) signal.removeEventListener('abort', abortListener)
  }
}

export function apiUrl(path) {
  return `${API_BASE}${path}`
}

export async function apiFetch(url, options = {}) {
  url = apiUrl(url)
  const { timeoutMs, ...fetchOptions } = options
  const token = localStorage.getItem('token')
  const headers = { ...fetchOptions.headers }
  if (token) headers['Authorization'] = `Bearer ${token}`
  if (fetchOptions.body && typeof fetchOptions.body === 'object') {
    headers['Content-Type'] = 'application/json'
    fetchOptions.body = JSON.stringify(fetchOptions.body)
  }
  return fetchWithTimeout(url, { ...fetchOptions, headers, cache: fetchOptions.cache ?? 'no-store', timeoutMs })
}
