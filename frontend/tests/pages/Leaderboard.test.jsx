import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import Leaderboard from '../../src/pages/Leaderboard'

const mockUser = { username: 'testuser', user_id: 'u1' }

vi.mock('../../../offy-front/src/contexts/AuthContext', () => ({
  useAuth: () => ({
    user: mockUser
  })
}))

describe('Leaderboard Page', () => {
  beforeEach(() => {
    localStorage.clear()
    // Seed some mock data
    const mockDB = {
      users: [
        { user_id: 'u1', username: 'testuser', email: 'test@example.com', streak_count: 5, total_points: 200 },
        { user_id: 'u2', username: 'otheruser', email: 'other@example.com', streak_count: 3, total_points: 150 }
      ],
      screenTimeLogs: [],
      goals: [],
      friendships: []
    }
    localStorage.setItem('offy_mock_db_v1', JSON.stringify(mockDB))
  })

  it('renders leaderboard with tabs', async () => {
    render(
      <BrowserRouter>
        <Leaderboard />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Friends')).toBeInTheDocument()
      expect(screen.getByText('Global')).toBeInTheDocument()
    })
  })

  it('switches between friends and global tabs', async () => {
    const user = userEvent.setup()
    
    render(
      <BrowserRouter>
        <Leaderboard />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Friends')).toBeInTheDocument()
    })

    const globalTab = screen.getByText('Global')
    await user.click(globalTab)

    expect(globalTab.parentElement).toHaveClass('active')
  })

  it('displays leaderboard users', async () => {
    render(
      <BrowserRouter>
        <Leaderboard />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('testuser')).toBeInTheDocument()
      expect(screen.getByText('otheruser')).toBeInTheDocument()
    })
  })
})
