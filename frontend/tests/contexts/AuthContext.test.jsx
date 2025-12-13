import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { AuthProvider, useAuth } from '../../src/contexts/AuthContext'
import * as authApi from '../../src/api/authApi'

// Mock the authApi module
vi.mock('../../../offy-front/src/api/authApi', () => ({
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
  getAuthStatus: vi.fn()
}))

// Test component that uses AuthContext
function TestComponent() {
  const { user, isAuthenticated, loading, signIn, signUp, signOut } = useAuth()
  
  return (
    <div>
      <div data-testid="loading">{loading ? 'loading' : 'not-loading'}</div>
      <div data-testid="authenticated">{isAuthenticated ? 'authenticated' : 'not-authenticated'}</div>
      <div data-testid="username">{user?.username || 'no-user'}</div>
      <button onClick={() => signIn({ username: 'testuser', password: 'pass123' })}>Sign In</button>
      <button onClick={() => signUp({ username: 'newuser', email: 'new@example.com', password: 'pass123' })}>Sign Up</button>
      <button onClick={signOut}>Sign Out</button>
    </div>
  )
}

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('starts with loading state and checks authentication status', async () => {
    authApi.getAuthStatus.mockResolvedValueOnce({ authenticated: false })

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    // Initially loading
    expect(screen.getByTestId('loading')).toHaveTextContent('loading')

    // After auth check completes
    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('not-loading')
    })

    expect(authApi.getAuthStatus).toHaveBeenCalledTimes(1)
  })

  it('sets user when already authenticated', async () => {
    const mockUser = { username: 'existinguser', user_id: 'u1' }
    authApi.getAuthStatus.mockResolvedValueOnce({ authenticated: true, user: mockUser })

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('authenticated')
      expect(screen.getByTestId('username')).toHaveTextContent('existinguser')
    })
  })

  it('handles sign in successfully', async () => {
    const mockUser = { username: 'testuser', user_id: 'u1' }
    authApi.getAuthStatus.mockResolvedValueOnce({ authenticated: false })
    authApi.login.mockResolvedValueOnce({ user: mockUser })

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('not-loading')
    })

    const signInButton = screen.getByText('Sign In')
    signInButton.click()

    await waitFor(() => {
      expect(authApi.login).toHaveBeenCalledWith({
        username: 'testuser',
        password: 'pass123'
      })
      expect(screen.getByTestId('authenticated')).toHaveTextContent('authenticated')
      expect(screen.getByTestId('username')).toHaveTextContent('testuser')
    })
  })

  it('handles sign up successfully', async () => {
    const mockUser = { username: 'newuser', user_id: 'u2', email: 'new@example.com' }
    authApi.getAuthStatus.mockResolvedValueOnce({ authenticated: false })
    authApi.register.mockResolvedValueOnce({ user: mockUser })

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('not-loading')
    })

    const signUpButton = screen.getByText('Sign Up')
    signUpButton.click()

    await waitFor(() => {
      expect(authApi.register).toHaveBeenCalledWith({
        username: 'newuser',
        email: 'new@example.com',
        password: 'pass123'
      })
      expect(screen.getByTestId('authenticated')).toHaveTextContent('authenticated')
      expect(screen.getByTestId('username')).toHaveTextContent('newuser')
    })
  })

  it('handles sign out', async () => {
    const mockUser = { username: 'testuser', user_id: 'u1' }
    authApi.getAuthStatus.mockResolvedValueOnce({ authenticated: true, user: mockUser })
    authApi.logout.mockResolvedValueOnce({})

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('authenticated')
    })

    const signOutButton = screen.getByText('Sign Out')
    signOutButton.click()

    await waitFor(() => {
      expect(authApi.logout).toHaveBeenCalledTimes(1)
      expect(screen.getByTestId('authenticated')).toHaveTextContent('not-authenticated')
      expect(screen.getByTestId('username')).toHaveTextContent('no-user')
    })
  })

  it('handles sign in failure', async () => {
    authApi.getAuthStatus.mockResolvedValueOnce({ authenticated: false })
    authApi.login.mockRejectedValueOnce(new Error('Invalid credentials'))

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('not-loading')
    })

    const signInButton = screen.getByText('Sign In')
    
    await expect(async () => {
      signInButton.click()
      await waitFor(() => {
        expect(authApi.login).toHaveBeenCalled()
      })
    }).rejects.toThrow()

    expect(screen.getByTestId('authenticated')).toHaveTextContent('not-authenticated')
  })
})
