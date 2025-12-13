// Keep badges API in the same directory as other API clients for consistency
const API_BASE_URL = import.meta.env.VITE_API_BASE || 'http://localhost:5001/api'

export const badgesApi = {
  // Get all available badges
  getAllBadges: async () => {
    const res = await fetch(`${API_BASE_URL}/badges`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
      credentials: 'include',
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || 'Failed to fetch badges')
    return data
  },

  // Get user's earned badges
  getUserBadges: async (userId) => {
    const res = await fetch(`${API_BASE_URL}/users/${userId}/badges`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
      credentials: 'include',
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || 'Failed to fetch user badges')
    return data
  },

  // Award a badge to a user (for testing/admin purposes)
  awardBadge: async (userId, badgeName) => {
    const res = await fetch(`${API_BASE_URL}/users/${userId}/badges`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ badge_name: badgeName }),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || 'Failed to award badge')
    return data
  },

  // Check and award badges for a user (manual trigger)
  checkBadges: async (userId) => {
    const res = await fetch(`${API_BASE_URL}/users/${userId}/badges/check`, {
      method: 'POST',
      headers: { 'Accept': 'application/json' },
      credentials: 'include',
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || 'Failed to check badges')
    return data
  }
}

// Fallback badge data for development/offline use
export function getFallbackBadges() {
  return [
    { name: 'Fresh Start', description: 'Complete your first day meeting your screen-time goal.', badge_type: 'streak', icon: '🔥' },
    { name: 'Weekend Warrior', description: 'Hit your goal on a Saturday and Sunday.', badge_type: 'streak', icon: '🔥' },
    { name: '7-Day Focus', description: '7 days in a row hitting daily goal.', badge_type: 'streak', icon: '🔥' },
    { name: 'Habit Builder', description: '14-day streak.', badge_type: 'streak', icon: '🔥' },
    { name: 'Unstoppable', description: '30-day streak.', badge_type: 'streak', icon: '🔥' },
    { name: 'Tiny Wins', description: 'Reduce total time by 5% from your baseline week.', badge_type: 'reduction', icon: '📉' },
    { name: 'Digital Minimalist', description: 'Average < 2 hours/day over a whole week.', badge_type: 'reduction', icon: '📉' },
  ]
}

export function getFallbackUserBadges() {
  return [
    { name: 'Fresh Start', earned_at: new Date().toISOString() },
    { name: '7-Day Focus', earned_at: new Date().toISOString() },
  ]
}
