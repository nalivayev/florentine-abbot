/**
 * Wrapper around fetch that adds the Authorization header automatically.
 */
const API_VERSION = 'v1'
const API_BASE = `/api/${API_VERSION}`

export function apiUrl(path) {
  return `${API_BASE}${path}`
}

export async function apiFetch(url, options = {}) {
  url = apiUrl(url)
  const token = localStorage.getItem('token')
  const headers = { ...options.headers }
  if (token) headers['Authorization'] = `Bearer ${token}`
  if (options.body && typeof options.body === 'object') {
    headers['Content-Type'] = 'application/json'
    options = { ...options, body: JSON.stringify(options.body) }
  }
  return fetch(url, { ...options, headers })
}
