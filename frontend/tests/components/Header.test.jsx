import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Header from '../../src/components/Header'
import { AuthProvider } from '../../src/contexts/AuthContext'

// Mock the useNavigate and useLocation hooks
const mockNavigate = vi.fn()
const mockLocation = { pathname: '/dashboard' }

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => mockLocation
  }
})

// Mock AuthContext
const mockSignOut = vi.fn()
const mockAuthContext = {
  user: { username: 'testuser', user_id: 'u1' },
  signOut: mockSignOut,
  isAuthenticated: true,
  loading: false
}

vi.mock('../../../offy-front/src/contexts/AuthContext', async () => {
  const actual = await vi.importActual('../../../offy-front/src/contexts/AuthContext')
  return {
    ...actual,
    useAuth: () => mockAuthContext
  }
})

describe('Header Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockLocation.pathname = '/dashboard'
  })

  it('renders brand and navigation when authenticated', () => {
    render(
      <BrowserRouter>
        <Header />
      </BrowserRouter>
    )

    expect(screen.getByText('Offy')).toBeInTheDocument()
    expect(screen.getByText('🏠 Home')).toBeInTheDocument()
    expect(screen.getByText('🏆 Leaderboard')).toBeInTheDocument()
    expect(screen.getByText('👥 Friends')).toBeInTheDocument()
  })

  it('displays user initials in avatar', () => {
    render(
      <BrowserRouter>
        <Header />
      </BrowserRouter>
    )

    expect(screen.getByText('T')).toBeInTheDocument() // First letter of 'testuser'
  })

  it('displays welcome message on dashboard page', () => {
    render(
      <BrowserRouter>
        <Header />
      </BrowserRouter>
    )

    expect(screen.getByText(/Welcome, testuser/)).toBeInTheDocument()
  })

  it('does not display welcome message on non-dashboard pages', () => {
    mockLocation.pathname = '/leaderboard'
    
    render(
      <BrowserRouter>
        <Header />
      </BrowserRouter>
    )

    expect(screen.queryByText(/Welcome, testuser/)).not.toBeInTheDocument()
  })

  it('calls signOut and navigates to signin when sign out button clicked', () => {
    render(
      <BrowserRouter>
        <Header />
      </BrowserRouter>
    )

    const signOutButton = screen.getByText('Sign out')
    fireEvent.click(signOutButton)

    expect(mockSignOut).toHaveBeenCalledTimes(1)
    expect(mockNavigate).toHaveBeenCalledWith('/signin')
  })

  it('navigates to profile when avatar is clicked', () => {
    render(
      <BrowserRouter>
        <Header />
      </BrowserRouter>
    )

    const avatar = screen.getByLabelText('Open profile')
    fireEvent.click(avatar)

    expect(mockNavigate).toHaveBeenCalledWith('/profile')
  })

  it('shows minimal header on signin page', () => {
    mockLocation.pathname = '/signin'
    
    render(
      <BrowserRouter>
        <Header />
      </BrowserRouter>
    )

    expect(screen.queryByText('Offy')).not.toBeInTheDocument()
    expect(screen.getByText('O')).toBeInTheDocument() // Just the dot
  })

  it('shows minimal header on signup page', () => {
    mockLocation.pathname = '/signup'
    
    render(
      <BrowserRouter>
        <Header />
      </BrowserRouter>
    )

    expect(screen.queryByText('Offy')).not.toBeInTheDocument()
    expect(screen.getByText('O')).toBeInTheDocument()
  })
})
