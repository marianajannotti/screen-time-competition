const API_BASE_URL = import.meta.env.VITE_API_BASE || 'http://localhost:5001/api'

export const badgesApi = {
  // Get all available badges
  getAllBadges: async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/badges`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Include cookies for authentication
      })
      
      if (!response.ok) {
        throw new Error(`Failed to fetch badges: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('Error fetching badges:', error)
      // Return fallback data if API is unavailable
      return getFallbackBadges()
    }
  },

  // Get user's earned badges
  getUserBadges: async (userId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/users/${userId}/badges`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Include cookies for authentication
      })
      
      if (!response.ok) {
        if (response.status === 403) {
          console.warn('Access denied - user not authenticated')
          return []
        }
        throw new Error(`Failed to fetch user badges: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('Error fetching user badges:', error)
      // Return fallback data for development
      return getFallbackUserBadges()
    }
  },

  // Award a badge to a user (for testing/admin purposes)
  awardBadge: async (userId, badgeName) => {
    try {
      const response = await fetch(`${API_BASE_URL}/users/${userId}/badges`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ badge_name: badgeName }),
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || `Failed to award badge: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('Error awarding badge:', error)
      throw error
    }
  },

  // Check and award badges for a user (manual trigger)
  checkBadges: async (userId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/users/${userId}/badges/check`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || `Failed to check badges: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('Error checking badges:', error)
      throw error
    }
  }
}

// Fallback badge data for development/offline use
function getFallbackBadges() {
  return [
    // Streak & Consistency
    { name: 'Fresh Start', desc: 'Complete your first day meeting your screen-time goal.', type: 'streak' },
    { name: 'Weekend Warrior', desc: 'Hit your goal on a Saturday and Sunday.', type: 'streak' },
    { name: '7-Day Focus', desc: '7 days in a row hitting daily goal.', type: 'streak' },
    { name: 'Habit Builder', desc: '14-day streak.', type: 'streak' },
    { name: 'Unstoppable', desc: '30-day streak.', type: 'streak' },
    { name: 'Bounce Back', desc: 'Lose a streak, then start a new one the next day.', type: 'streak' },
    // Screen-Time Reduction
    { name: 'Tiny Wins', desc: 'Reduce total time by 5% from your baseline week.', type: 'reduction' },
    { name: 'The Declutter', desc: 'Reduce total screen time by 10% from baseline.', type: 'reduction' },
    { name: 'Half-Life', desc: 'Reduce screen time by 50% from baseline.', type: 'reduction' },
    { name: 'One Hour Club', desc: 'Stay under 1h of social media in a day.', type: 'reduction' },
    { name: 'Digital Minimalist', desc: 'Average < 2 hours/day over a whole week.', type: 'reduction' },
    // Social & Community
    { name: 'Team Player', desc: 'Add your first friend.', type: 'social' },
    { name: 'The Connector', desc: 'Add 10 friends.', type: 'social' },
    { name: 'Challenge Accepted', desc: 'Join your first challenge.', type: 'social' },
    { name: 'Friendly Rival', desc: 'Participate in 5 challenges.', type: 'social' },
    { name: 'Community Champion', desc: 'Win a weekly challenge among friends.', type: 'social' },
    // Leaderboard
    { name: 'Top 10%', desc: 'Be in top 10% of the leaderboard in a week.', type: 'leaderboard' },
    { name: 'Top 3', desc: 'Finish as #1, #2, or #3 among friends.', type: 'leaderboard' },
    { name: 'The Phantom', desc: 'Win a challenge with the lowest screen time without chatting.', type: 'leaderboard' },
    { name: 'Comeback Kid', desc: 'Go from bottom half to top 3 in the next challenge.', type: 'leaderboard' },
    // Prestige / Long-Term
    { name: 'Offline Legend', desc: 'Average < 2h/day for a full month.', type: 'prestige' },
    { name: 'Master of Attention', desc: 'Maintain a 30-day goal streak and < 2h/day average.', type: 'prestige' },
    { name: 'Life > Screen', desc: 'Complete a full 24h digital detox.', type: 'prestige' },
  ]
}

function getFallbackUserBadges() {
  return [
    { name: '7-Day Focus', earnedAt: '2025-11-03T00:00:00Z' },
    { name: 'Digital Minimalist', earnedAt: '2025-11-01T00:00:00Z' },
    { name: 'One Hour Club', earnedAt: '2025-11-08T00:00:00Z' },
    { name: 'Top 3', earnedAt: '2025-10-26T00:00:00Z' },
  ]
}