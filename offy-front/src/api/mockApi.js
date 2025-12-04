// Simple isolated mock API layer. Each function returns a Promise and
// is intentionally easy to replace with real endpoints.
const delay = (ms = 400) => new Promise((res) => setTimeout(res, ms))

// In-memory mock DB (persist in localStorage to survive reloads)
const STORAGE_KEY = 'offy_mock_db_v1'
const initial = {
  users: [
    { user_id: 'u1', username: 'demo', email: 'demo@example.com', profile_picture: '', streak_count: 2, total_points: 120 },
    { user_id: 'u2', username: 'marcelo', email: 'marcelo@example.com', profile_picture: '', streak_count: 8, total_points: 360 },
    { user_id: 'u3', username: 'luana', email: 'luana@example.com', profile_picture: '', streak_count: 5, total_points: 290 },
    { user_id: 'u4', username: 'sofia', email: 'sofia@example.com', profile_picture: '', streak_count: 1, total_points: 130 },
    { user_id: 'u5', username: 'paul', email: 'paul@example.com', profile_picture: '', streak_count: 10, total_points: 80 },
    { user_id: 'u6', username: 'robert', email: 'robert@example.com', profile_picture: '', streak_count: 7, total_points: 92 },
    { user_id: 'u7', username: 'gwen', email: 'gwen@example.com', profile_picture: '', streak_count: 11, total_points: 75 },
    { user_id: 'u8', username: 'emma', email: 'emma@example.com', profile_picture: '', streak_count: 3, total_points: 140 },
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
  } catch {
    return structuredClone(initial)
  }
}

function save(db) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(db))
}

// Helpers
const genId = (prefix = 'id') => `${prefix}_${Math.random().toString(36).slice(2, 9)}`

// ─── Leaderboard utilities ───────────────────────────────────────────────────

export function minutesLabel(mins) {
  const h = Math.floor((mins || 0) / 60)
  const m = Math.round((mins || 0) % 60)
  return `${h} h ${String(m).padStart(2, '0')} m`
}

export function getMonthRange(date = new Date()) {
  const y = date.getFullYear()
  const mo = date.getMonth()
  const start = new Date(y, mo, 1)
  const end = new Date(y, mo + 1, 0)
  const days = Array.from({ length: end.getDate() }, (_, i) =>
    new Date(y, mo, i + 1).toISOString().slice(0, 10),
  )
  return { start: start.toISOString().slice(0, 10), end: end.toISOString().slice(0, 10), days }
}

export function computeMonthlyStatsForUser(userId) {
  try {
    const raw = localStorage.getItem(`offy_logs_${userId}`)
    const logs = raw ? JSON.parse(raw) : []
    const { days } = getMonthRange()
    const byDay = {}
    logs.forEach((l) => {
      if (days.includes(l.date)) {
        byDay[l.date] = byDay[l.date] || {}
        byDay[l.date][l.app] = l.minutes
      }
    })
    let totalMinutes = 0
    let daysWithLogs = 0
    days.forEach((d) => {
      const dayApps = byDay[d]
      if (!dayApps) return
      const total =
        dayApps['__TOTAL__'] !== undefined
          ? dayApps['__TOTAL__']
          : Object.entries(dayApps)
              .filter(([a]) => a !== '__TOTAL__')
              .reduce((acc, [, min]) => acc + min, 0)
      if (total > 0) {
        totalMinutes += total
        daysWithLogs++
      }
    })
    // streak: longest consecutive days reaching daily goal this month
    const goalRaw = localStorage.getItem(`offy_${userId}_daily_goal`)
    const dailyGoal = goalRaw ? Number(goalRaw) : undefined
    let maxStreak = 0
    let currentStreak = 0
    if (dailyGoal !== undefined) {
      days.forEach((d) => {
        const dayApps = byDay[d]
        if (!dayApps) {
          currentStreak = 0
          return
        }
        const total =
          dayApps['__TOTAL__'] !== undefined
            ? dayApps['__TOTAL__']
            : Object.entries(dayApps)
                .filter(([a]) => a !== '__TOTAL__')
                .reduce((acc, [, min]) => acc + min, 0)
        if (total <= dailyGoal && total > 0) {
          currentStreak++
        } else {
          maxStreak = Math.max(maxStreak, currentStreak)
          currentStreak = 0
        }
      })
      // Update maxStreak for the final consecutive sequence
      maxStreak = Math.max(maxStreak, currentStreak)
    }
    const avgPerDay = daysWithLogs > 0 ? totalMinutes / daysWithLogs : undefined
    return { avgPerDay, streak: maxStreak }
  } catch {
    return { avgPerDay: undefined, streak: 0 }
  }
}

export function seedMonthlyMockData() {
  // Ensure users exist in mock DB
  const existing = localStorage.getItem(STORAGE_KEY)
  let db = existing ? JSON.parse(existing) : null
  if (!db || !Array.isArray(db.users) || db.users.length <= 1) {
    db = db || { users: [], screenTimeLogs: [], goals: [], friendships: [] }
    db.users = initial.users
    localStorage.setItem(STORAGE_KEY, JSON.stringify(db))
  }
  // Seed monthly logs per user if none exist
  const { days } = getMonthRange()
  const usersToSeed = (db && db.users) || []
  usersToSeed.forEach((u) => {
    const key = `offy_logs_${u.user_id}`
    const raw = localStorage.getItem(key)
    if (raw) return
    const logs = []
    const count = Math.floor(Math.random() * 11) + 10 // 10–20 days
    const shuffled = days.slice().sort(() => Math.random() - 0.5).slice(0, count)
    shuffled.forEach((d) => {
      const mins = (Math.floor(Math.random() * 5) + 2) * 60 + Math.floor(Math.random() * 60)
      logs.push({ app: '__TOTAL__', minutes: mins, date: d })
    })
    localStorage.setItem(key, JSON.stringify(logs))
  })
}

export async function signIn({ emailOrUsername }) {
  await delay()
  const db = load()
  const user = db.users.find(
    (u) => u.email === emailOrUsername || u.username === emailOrUsername,
  )
  if (!user) return Promise.reject({ message: 'User not found' })
  // NOTE: password checks are mocked out. Real API must validate password hashes.
  return { user }
}

export async function signUp({ username, email }) {
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

export async function getScreenTimeLogs(user_id) {
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

// Friendships API
export async function getFriendIds(user_id) {
  await delay()
  const db = load()
  db.friendships = db.friendships || []
  const ids = db.friendships.filter((f) => f.user_id === user_id).map((f) => f.friend_id)
  return { friendIds: ids }
}

export async function addFriendship(user_id, friend_id) {
  await delay()
  if (!user_id || !friend_id) return Promise.reject({ message: 'Invalid arguments' })
  if (user_id === friend_id) return Promise.reject({ message: "Can't add yourself" })
  const db = load()
  db.friendships = db.friendships || []
  const exists = db.friendships.some((f) => f.user_id === user_id && f.friend_id === friend_id)
  if (!exists) {
    db.friendships.push({ user_id, friend_id })
    save(db)
  }
  return { success: true }
}

export async function removeFriendship(user_id, friend_id) {
  await delay()
  const db = load()
  db.friendships = (db.friendships || []).filter((f) => !(f.user_id === user_id && f.friend_id === friend_id))
  save(db)
  return { success: true }
}

// Expose a helper for tests or bootstrapping
export function _resetMockDb() {
  save(initial)
}

// Reset all mock data including user logs
export function resetAllMockData() {
  localStorage.removeItem(STORAGE_KEY)
  const db = load()
  // Clear all user-specific logs
  if (db && db.users) {
    db.users.forEach((u) => {
      localStorage.removeItem(`offy_logs_${u.user_id}`)
    })
  }
  // Also clear logs for initial users in case db was corrupted
  initial.users.forEach((u) => {
    localStorage.removeItem(`offy_logs_${u.user_id}`)
  })
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
  getFriendIds,
  addFriendship,
  removeFriendship,
  _resetMockDb,
  resetAllMockData,
  // Leaderboard utilities
  minutesLabel,
  getMonthRange,
  computeMonthlyStatsForUser,
  seedMonthlyMockData,
}
