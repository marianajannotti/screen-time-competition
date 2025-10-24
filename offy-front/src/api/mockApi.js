// Simple isolated mock API layer. Each function returns a Promise and
// is intentionally easy to replace with real endpoints.
const delay = (ms = 400) => new Promise((res) => setTimeout(res, ms))

// In-memory mock DB (persist in localStorage to survive reloads)
const STORAGE_KEY = 'offy_mock_db_v1'
const initial = {
  users: [
    { user_id: 'u1', username: 'demo', email: 'demo@example.com', profile_picture: '', streak_count: 2, total_points: 120 },
  ],
  screenTimeLogs: [],
  goals: [],
  friendships: [],
}

function load() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return structuredClone(initial)
    return JSON.parse(raw)
  } catch (e) {
    return structuredClone(initial)
  }
}

function save(db) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(db))
}

// Helpers
const genId = (prefix = 'id') => `${prefix}_${Math.random().toString(36).slice(2, 9)}`

export async function signIn({ emailOrUsername, password }) {
  await delay()
  const db = load()
  const user = db.users.find(
    (u) => u.email === emailOrUsername || u.username === emailOrUsername,
  )
  if (!user) return Promise.reject({ message: 'User not found' })
  // NOTE: password checks are mocked out. Real API must validate password hashes.
  return { user }
}

export async function signUp({ username, email, password }) {
  await delay()
  const db = load()
  if (db.users.find((u) => u.email === email)) {
    return Promise.reject({ message: 'Email already in use' })
  }
  if (db.users.find((u) => u.username === username)) {
    return Promise.reject({ message: 'Username already in use' })
  }
  const user = { user_id: genId('user'), username, email, profile_picture: '', streak_count: 0, total_points: 0 }
  db.users.push(user)
  save(db)
  return { user }
}

export async function getProfile(user_id) {
  await delay(200)
  const db = load()
  const user = db.users.find((u) => u.user_id === user_id)
  if (!user) return Promise.reject({ message: 'Not found' })
  return { user }
}

export async function updateProfile(user_id, patch) {
  await delay(200)
  const db = load()
  const idx = db.users.findIndex((u) => u.user_id === user_id)
  if (idx === -1) return Promise.reject({ message: 'Not found' })
  db.users[idx] = { ...db.users[idx], ...patch }
  save(db)
  return { user: db.users[idx] }
}

export async function addScreenTime({ user_id, date, minutes, uploaded_image = null, ocr_extracted = 0 }) {
  await delay()
  const db = load()
  const log = { log_id: genId('log'), user_id, date, screen_time_minutes: minutes, uploaded_image, ocr_extracted, created_at: new Date().toISOString() }
  db.screenTimeLogs.push(log)
  save(db)
  return { log }
}

export async function getScreenTimeLogs(user_id, { from, to } = {}) {
  await delay()
  const db = load()
  return { logs: db.screenTimeLogs.filter((l) => l.user_id === user_id) }
}

export async function getLeaderboard() {
  await delay()
  const db = load()
  // very simple leaderboard by total_points
  const list = db.users.slice().sort((a, b) => (b.total_points || 0) - (a.total_points || 0))
  return { list }
}

export async function getFriends(user_id) {
  await delay()
  const db = load()
  // return all users except the current as mock
  return { friends: db.users.filter((u) => u.user_id !== user_id) }
}

// Expose a helper for tests or bootstrapping
export function _resetMockDb() {
  save(initial)
}

export default {
  signIn,
  signUp,
  getProfile,
  updateProfile,
  addScreenTime,
  getScreenTimeLogs,
  getLeaderboard,
  getFriends,
  _resetMockDb,
}
