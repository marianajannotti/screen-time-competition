const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:5001'
const BASE_URL = `${API_BASE}/api/friendships`

const JSON_HEADERS = {
  'Content-Type': 'application/json',
  Accept: 'application/json',
}

export const friendshipApi = {
  list: async () => {
    const res = await fetch(BASE_URL, {
      method: 'GET',
      headers: { Accept: 'application/json' },
      credentials: 'include',
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || 'Failed to load friendships')
    return data
  },

  sendRequest: async (username) => {
    const res = await fetch(`${BASE_URL}/request`, {
      method: 'POST',
      headers: JSON_HEADERS,
      credentials: 'include',
      body: JSON.stringify({ username }),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || 'Failed to send request')
    return data
  },

  accept: async (friendshipId) => {
    const res = await fetch(`${BASE_URL}/${friendshipId}/accept`, {
      method: 'POST',
      headers: { Accept: 'application/json' },
      credentials: 'include',
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || 'Failed to accept request')
    return data
  },

  reject: async (friendshipId) => {
    const res = await fetch(`${BASE_URL}/${friendshipId}/reject`, {
      method: 'POST',
      headers: { Accept: 'application/json' },
      credentials: 'include',
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || 'Failed to reject request')
    return data
  },

  cancel: async (friendshipId) => {
    const res = await fetch(`${BASE_URL}/${friendshipId}/cancel`, {
      method: 'POST',
      headers: { Accept: 'application/json' },
      credentials: 'include',
    })
    if (!res.ok) {
      let data
      try {
        data = await res.json()
      } catch {
        data = {}
      }
      throw new Error(data.error || 'Failed to cancel request')
    }
    return { ok: true }
  },
}
