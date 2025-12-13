import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import Friends from '../../src/pages/Friends'

const mockUser = { username: 'testuser', user_id: 'u1' }

vi.mock('../../../offy-front/src/contexts/AuthContext', () => ({
  useAuth: () => ({
    user: mockUser
  })
}))

describe('Friends Page', () => {
  beforeEach(() => {
    localStorage.clear()
    // Seed some mock data
    const mockDB = {
      users: [
        { user_id: 'u1', username: 'testuser', email: 'test@example.com', streak_count: 5, total_points: 200 },
        { user_id: 'u2', username: 'friend1', email: 'friend1@example.com', streak_count: 3, total_points: 150 },
        { user_id: 'u3', username: 'friend2', email: 'friend2@example.com', streak_count: 7, total_points: 250 }
      ],
      screenTimeLogs: [],
      goals: [],
      friendships: [
        { user_id: 'u1', friend_id: 'u2' }
      ]
    }
    localStorage.setItem('offy_mock_db_v1', JSON.stringify(mockDB))
  })

  it('renders friends page with title', async () => {
    render(
      <BrowserRouter>
        <Friends />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Friends')).toBeInTheDocument()
    })
  })

  it('displays current friends list', async () => {
    render(
      <BrowserRouter>
        <Friends />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('friend1')).toBeInTheDocument()
    })
  })

  it('shows search input to add new friends', async () => {
    render(
      <BrowserRouter>
        <Friends />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Search to add')).toBeInTheDocument()
    })
  })

  it('filters available friends by search query', async () => {
    const user = userEvent.setup()
    
    render(
      <BrowserRouter>
        <Friends />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Search to add')).toBeInTheDocument()
    })

    const searchInput = screen.getByPlaceholderText('Search to add')
    await user.type(searchInput, 'friend2')

    await waitFor(() => {
      expect(screen.getByText('friend2')).toBeInTheDocument()
    })
  })

  it('shows empty state when no friends exist', async () => {
    // Clear friendships
    const mockDB = {
      users: [
        { user_id: 'u1', username: 'testuser', email: 'test@example.com', streak_count: 5, total_points: 200 },
        { user_id: 'u2', username: 'friend1', email: 'friend1@example.com', streak_count: 3, total_points: 150 }
      ],
      screenTimeLogs: [],
      goals: [],
      friendships: []
    }
    localStorage.setItem('offy_mock_db_v1', JSON.stringify(mockDB))

    render(
      <BrowserRouter>
        <Friends />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/You have no friends yet/i)).toBeInTheDocument()
    })
  })
})
