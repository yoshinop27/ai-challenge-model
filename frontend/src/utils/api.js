const DEFAULT_TIMEOUT_MS = 120000
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').trim().replace(/\/+$/, '')

export function buildApiUrl(path) {
  if (/^https?:\/\//.test(path)) return path
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return API_BASE_URL ? `${API_BASE_URL}${normalizedPath}` : normalizedPath
}

export async function fetchWithTimeout(url, options = {}, timeoutMs = DEFAULT_TIMEOUT_MS) {
  const controller = new AbortController()
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs)

  try {
    return await fetch(buildApiUrl(url), {
      ...options,
      signal: options.signal ?? controller.signal,
    })
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new Error('Request timed out. Check that the backend is running and try again.')
    }
    throw error
  } finally {
    window.clearTimeout(timeoutId)
  }
}
