const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:5001'
const BASE_URL = `${API_BASE}/api/friendships`

const JSON_HEADERS = {
  'Content-Type': 'application/json',
  Accept: 'application/json',
}

function parseJsonSafe(res) {
  const ct = res.headers.get('content-type') || ''
  if (!ct.includes('application/json')) {
    return null
  }
  return res.json()
}

function buildError(res, fallback) {
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
    if (!res.ok) {
      const data = await parseJsonSafe(res)
      const msg =
        (data && data.error) ||
        (await buildError(res, 'Failed to cancel request')())
      throw new Error(msg)
    }
    return { ok: true }
  },
}
