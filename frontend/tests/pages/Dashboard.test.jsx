import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import Dashboard from '../../src/pages/Dashboard'

const mockUser = { username: 'testuser', user_id: 'u1' }

vi.mock('../../../offy-front/src/contexts/AuthContext', () => ({
  useAuth: () => ({
    user: mockUser
  })
}))

describe('Dashboard Page', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('renders dashboard header and navigation', () => {
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    )

    expect(screen.getByText('Overview')).toBeInTheDocument()
    expect(screen.getByText('This Week')).toBeInTheDocument()
    expect(screen.getByText('By App')).toBeInTheDocument()
  })

  it('shows no data message when no screen time is logged', () => {
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    )

    expect(screen.getByText(/No screen time data for this week/)).toBeInTheDocument()
  })

  it('displays daily goal section', () => {
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    )

    expect(screen.getByText(/Daily Goal/)).toBeInTheDocument()
  })
})
