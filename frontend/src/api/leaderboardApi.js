const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:5001'
const JSON_HEADERS = { 'Accept': 'application/json', 'Content-Type': 'application/json' }
const GET_HEADERS = { 'Accept': 'application/json' }

async function fetchJson(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: 'include',
    ...options,
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const msg = data?.error || data?.message || 'Request failed'
    throw new Error(msg)
  }
  return data
}

export async function getGlobalLeaderboard() {
  const data = await fetchJson('/api/leaderboard/global', { headers: GET_HEADERS })
  return (data && data.leaderboard) || []
}

export async function getFriendships() {
  return fetchJson('/api/friendships', { headers: GET_HEADERS })
}

export const leaderboardApi = {
  getGlobalLeaderboard,
  getFriendships,
}
