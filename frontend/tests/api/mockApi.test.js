import { describe, it, expect, beforeEach } from 'vitest'
import {
  signIn,
  signUp,
  getProfile,
  updateProfile,
  addScreenTime,
  getScreenTimeLogs,
  getLeaderboard,
  getFriendIds,
  addFriendship,
  removeFriendship,
  minutesLabel,
  getMonthRange,
  computeMonthlyStatsForUser,
  _resetMockDb,
  resetAllMockData
} from '../../src/api/mockApi'

describe('mockApi', () => {
  beforeEach(() => {
    localStorage.clear()
    _resetMockDb()
  })

  describe('Authentication', () => {
    it('signIn returns user when credentials match', async () => {
      const result = await signIn({ emailOrUsername: 'demo' })
      expect(result.user).toBeDefined()
      expect(result.user.username).toBe('demo')
    })

    it('signIn accepts email as identifier', async () => {
      const result = await signIn({ emailOrUsername: 'demo@example.com' })
      expect(result.user).toBeDefined()
      expect(result.user.email).toBe('demo@example.com')
    })

    it('signIn rejects when user not found', async () => {
      await expect(signIn({ emailOrUsername: 'nonexistent' }))
        .rejects.toMatchObject({ message: 'User not found' })
    })

    it('signUp creates new user', async () => {
      const result = await signUp({ 
        username: 'newuser', 
        email: 'new@example.com',
        password: 'pass123' 
      })
      
      expect(result.user).toBeDefined()
      expect(result.user.username).toBe('newuser')
      expect(result.user.email).toBe('new@example.com')
    })

    it('signUp rejects duplicate email', async () => {
      await expect(signUp({ 
        username: 'newuser',
        email: 'demo@example.com',
        password: 'pass123' 
      })).rejects.toMatchObject({ message: 'Email already in use' })
    })

    it('signUp rejects duplicate username', async () => {
      await expect(signUp({ 
        username: 'demo',
        email: 'newemail@example.com',
        password: 'pass123' 
      })).rejects.toMatchObject({ message: 'Username already in use' })
    })
  })

  describe('Profile Management', () => {
    it('getProfile returns user data', async () => {
      const result = await getProfile('u1')
      expect(result.user).toBeDefined()
      expect(result.user.user_id).toBe('u1')
    })

    it('getProfile rejects for non-existent user', async () => {
      await expect(getProfile('nonexistent'))
        .rejects.toMatchObject({ message: 'Not found' })
    })

    it('updateProfile modifies user data', async () => {
      const result = await updateProfile('u1', { profile_picture: 'newpic.jpg' })
      expect(result.user.profile_picture).toBe('newpic.jpg')
      
      const updated = await getProfile('u1')
      expect(updated.user.profile_picture).toBe('newpic.jpg')
    })
  })

  describe('Screen Time Logs', () => {
    it('addScreenTime creates new log', async () => {
      const result = await addScreenTime({
        user_id: 'u1',
        date: '2025-12-10',
        minutes: 120
      })
      
      expect(result.log).toBeDefined()
      expect(result.log.screen_time_minutes).toBe(120)
      expect(result.log.date).toBe('2025-12-10')
    })

    it('getScreenTimeLogs returns user logs', async () => {
      await addScreenTime({ user_id: 'u1', date: '2025-12-10', minutes: 120 })
      await addScreenTime({ user_id: 'u1', date: '2025-12-11', minutes: 90 })
      
      const result = await getScreenTimeLogs('u1')
      expect(result.logs).toHaveLength(2)
      expect(result.logs[0].user_id).toBe('u1')
    })

    it('getScreenTimeLogs filters by user', async () => {
      await addScreenTime({ user_id: 'u1', date: '2025-12-10', minutes: 120 })
      await addScreenTime({ user_id: 'u2', date: '2025-12-10', minutes: 90 })
      
      const result = await getScreenTimeLogs('u1')
      expect(result.logs).toHaveLength(1)
      expect(result.logs.every(log => log.user_id === 'u1')).toBe(true)
    })
  })

  describe('Leaderboard', () => {
    it('getLeaderboard returns sorted user list', async () => {
      const result = await getLeaderboard()
      expect(result.list).toBeDefined()
      expect(result.list.length).toBeGreaterThan(0)
      
      // Check sorting by total_points
      for (let i = 1; i < result.list.length; i++) {
        expect(result.list[i-1].total_points).toBeGreaterThanOrEqual(result.list[i].total_points)
      }
    })
  })

  describe('Friendships', () => {
    it('getFriendIds returns empty array initially', async () => {
      const result = await getFriendIds('u1')
      expect(result.friendIds).toEqual([])
    })

    it('addFriendship creates friendship', async () => {
      await addFriendship('u1', 'u2')
      const result = await getFriendIds('u1')
      expect(result.friendIds).toContain('u2')
    })

    it('addFriendship prevents duplicate friendships', async () => {
      await addFriendship('u1', 'u2')
      await addFriendship('u1', 'u2')
      const result = await getFriendIds('u1')
      expect(result.friendIds.filter(id => id === 'u2')).toHaveLength(1)
    })

    it('addFriendship rejects self-friending', async () => {
      await expect(addFriendship('u1', 'u1'))
        .rejects.toMatchObject({ message: "Can't add yourself" })
    })

    it('removeFriendship removes friendship', async () => {
      await addFriendship('u1', 'u2')
      await removeFriendship('u1', 'u2')
      const result = await getFriendIds('u1')
      expect(result.friendIds).not.toContain('u2')
    })
  })

  describe('Utility Functions', () => {
    it('minutesLabel formats minutes correctly', () => {
      expect(minutesLabel(0)).toBe('0 h 00 m')
      expect(minutesLabel(45)).toBe('0 h 45 m')
      expect(minutesLabel(60)).toBe('1 h 00 m')
      expect(minutesLabel(90)).toBe('1 h 30 m')
      expect(minutesLabel(125)).toBe('2 h 05 m')
    })

    it('getMonthRange returns correct date range', () => {
      const testDate = new Date('2025-12-15')
      const result = getMonthRange(testDate)
      
      expect(result.start).toBe('2025-12-01')
      expect(result.end).toBe('2025-12-31')
      expect(result.days).toHaveLength(31)
      expect(result.days[0]).toBe('2025-12-01')
      expect(result.days[30]).toBe('2025-12-31')
    })

    it('computeMonthlyStatsForUser returns stats', () => {
      const result = computeMonthlyStatsForUser('u1')
      expect(result).toHaveProperty('avgPerDay')
      expect(result).toHaveProperty('streak')
    })

    it('resetAllMockData clears all data', () => {
      localStorage.setItem('test_key', 'test_value')
      resetAllMockData()
      
      const stored = localStorage.getItem('offy_mock_db_v1')
      expect(stored).toBeNull()
    })
  })

  describe('Data Persistence', () => {
    it('data persists across function calls', async () => {
      await signUp({ username: 'persistent', email: 'persist@example.com', password: 'pass' })
      
      const result = await signIn({ emailOrUsername: 'persistent' })
      expect(result.user.username).toBe('persistent')
    })

    it('screen time logs persist in localStorage', async () => {
      await addScreenTime({ user_id: 'u1', date: '2025-12-10', minutes: 120 })
      
      // Simulate page reload by calling getScreenTimeLogs
      const result = await getScreenTimeLogs('u1')
      expect(result.logs).toHaveLength(1)
    })
  })
})
