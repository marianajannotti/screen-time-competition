import { createContext, useContext, useState, useEffect } from 'react'
import { login, register, logout, getAuthStatus } from '../api/authApi'

// Create the authentication context.
// We pass `null` as the default because the provider will always override it.
const AuthContext = createContext(null)

// Custom hook so components can call `useAuth()` instead of `useContext(AuthContext)`
export function useAuth() {
  return useContext(AuthContext)
}

export function AuthProvider({ children }) {
  // `user` stores the currently authenticated user (or null if logged out)
  const [user, setUser] = useState(null)
  // Track last auth-related error to surface in UI if desired
  const [authError, setAuthError] = useState(null)

  // `loading` tracks whether we are in the middle of:
// 1. Checking if a session cookie exists (app startup)
// 2. Logging in / logging out / registering
  const [loading, setLoading] = useState(true)

  // When the provider mounts (on page load), we immediately check
  // if the user already has a valid session on the backend.
  // This prevents UI flicker and ensures persistence across page refreshes.
  useEffect(() => {
    checkUser()
  }, [])

  // Checks whether the user is authenticated by asking the backend.
  // This depends on cookies, so the backend must send session cookies.
  async function checkUser() {
    try {
      // Expected response from Flask:
      // { authenticated: true, user: { ...userData } }
      const data = await getAuthStatus()

      if (data.authenticated) {
        // If the backend says the user is logged in, store the user data.
        setUser(data.user)
      } else {
        // Otherwise, ensure we reset the user state.
        setUser(null)
      }
    } catch (error) {
      // If the API fails (network error, server down, invalid cookie),
      // we assume the user is not logged in.
      console.error("Auth check failed:", error)
      setUser(null)
    } finally {
      // We always stop loading — the check is complete.
      setLoading(false)
    }
  }

  // Login with username & password.
  // This sends credentials to the backend, which should set a session cookie.
  // Unified signIn expecting an object for future extensibility (email/username OTP etc.)
  async function signIn({ username, password, emailOrUsername }) {
    setAuthError(null)
    try {
      // Allow either explicit username or a combined identifier field
      const identifier = username || emailOrUsername
      const data = await login({ username: identifier, password })
      setUser(data.user)
      return data.user
    } catch (err) {
      console.error('Login failed', err)
      setAuthError(err.message || 'Login failed')
      throw err
    }
  }

  // Register a new user (username, email, password)
  async function signUp({ username, email, password }) {
    setAuthError(null)
    try {
      const data = await register({ username, email, password })
      setUser(data.user)
      return data.user
    } catch (err) {
      console.error('Registration failed', err)
      setAuthError(err.message || 'Registration failed')
      throw err
    }
  }

  // Log out the current user.
  // The backend should clear the session cookie.
  async function signOut() {
    setAuthError(null)
    try {
      await logout()
    } catch (error) {
      console.error('Logout failed', error)
      // Non-blocking: still clear user locally
    } finally {
      setUser(null)
    }
  }

  // Everything that will be available to the rest of the app
  const value = {
    user,
    isAuthenticated: !!user,
    signIn,
    signUp,
    signOut,
    loading,
    authError,
    refreshAuth: checkUser,
  }

  return (
    <AuthContext.Provider value={value}>
      {/* 
        Only render children after the initial session check is finished.
        This prevents unwanted redirects or UI flicker.
      */}
      {!loading && children}
    </AuthContext.Provider>
  )
}
