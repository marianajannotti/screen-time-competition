// Base URL for friendship endpoints
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:5001'
const BASE_URL = `${API_BASE}/api/friendships`

// Shared JSON headers for POST calls
const JSON_HEADERS = {
  'Content-Type': 'application/json',
  Accept: 'application/json',
}

function parseJsonSafe(res) {
  // Avoid throwing when the server returns HTML (e.g., redirect)
  const ct = res.headers.get('content-type') || ''
  if (!ct.includes('application/json')) {
    return null
  }
  return res.json()
}

function buildError(res, fallback) {
  // Prefer API error messages; fall back to sensible defaults
  return async () => {
    const data = await parseJsonSafe(res)
    if (data && data.error) return data.error
    const text = !data ? await res.text().catch(() => '') : ''
    if (text.toLowerCase().startsWith('<!doctype')) {
      return 'Not authenticated. Please sign in again.'
    }
    return fallback
  }
}

export const friendshipApi = {
  list: async () => {
    const res = await fetch(BASE_URL, {
      method: 'GET',
      headers: { Accept: 'application/json' },
      credentials: 'include',
    })
    const data = await parseJsonSafe(res)
    if (!res.ok) throw new Error((data && data.error) || (await buildError(res, 'Failed to load friendships')()))
    return data
  },

  sendRequest: async (username) => {
    const res = await fetch(`${BASE_URL}/request`, {
      method: 'POST',
      headers: JSON_HEADERS,
      credentials: 'include',
      body: JSON.stringify({ username }),
    })
    const data = await parseJsonSafe(res)
    if (!res.ok) throw new Error((data && data.error) || (await buildError(res, 'Failed to send request')()))
    return data
  },

  accept: async (friendshipId) => {
    const res = await fetch(`${BASE_URL}/${friendshipId}/accept`, {
      method: 'POST',
      headers: { Accept: 'application/json' },
      credentials: 'include',
    })
    const data = await parseJsonSafe(res)
    if (!res.ok) throw new Error((data && data.error) || (await buildError(res, 'Failed to accept request')()))
    return data
  },

  reject: async (friendshipId) => {
    const res = await fetch(`${BASE_URL}/${friendshipId}/reject`, {
      method: 'POST',
      headers: { Accept: 'application/json' },
      credentials: 'include',
    })
    const data = await parseJsonSafe(res)
    if (!res.ok) throw new Error((data && data.error) || (await buildError(res, 'Failed to reject request')()))
    return data
  },

  cancel: async (friendshipId) => {
    const res = await fetch(`${BASE_URL}/${friendshipId}/cancel`, {
      method: 'POST',
      headers: { Accept: 'application/json' },
      credentials: 'include',
    })
    const data = await parseJsonSafe(res)
    if (!res.ok) throw new Error((data && data.error) || (await buildError(res, 'Failed to cancel request')()))
    return data
  },
}
