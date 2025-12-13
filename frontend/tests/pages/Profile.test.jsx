import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Profile from '../../src/pages/Profile'

const mockUser = { username: 'testuser', user_id: 'u1' }

vi.mock('../../../offy-front/src/contexts/AuthContext', () => ({
  useAuth: () => ({
    user: mockUser
  })
}))

describe('Profile Page', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('renders profile with user information', () => {
    render(
      <BrowserRouter>
        <Profile />
      </BrowserRouter>
    )

    expect(screen.getByText('Testuser')).toBeInTheDocument()
    expect(screen.getByText('T')).toBeInTheDocument() // Avatar initial
  })

  it('displays badges section', () => {
    render(
      <BrowserRouter>
        <Profile />
      </BrowserRouter>
    )

    expect(screen.getByText(/Badges/i)).toBeInTheDocument()
  })

  it('displays stats section', () => {
    render(
      <BrowserRouter>
        <Profile />
      </BrowserRouter>
    )

    expect(screen.getByText(/Rank/i)).toBeInTheDocument()
    expect(screen.getByText(/Streak/i)).toBeInTheDocument()
  })
})
