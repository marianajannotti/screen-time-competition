import React, { createContext, useContext, useEffect, useState } from 'react'
import * as api from '../api/mockApi'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('offy_user')) || null
    } catch (e) {
      return null
    }
  })
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (user) localStorage.setItem('offy_user', JSON.stringify(user))
    else localStorage.removeItem('offy_user')
  }, [user])

  async function signIn({ emailOrUsername, password }) {
    setLoading(true)
    try {
      const { user } = await api.signIn({ emailOrUsername, password })
      setUser(user)
      return { user }
    } catch (err) {
      return Promise.reject(err)
    } finally {
      setLoading(false)
    }
  }

  async function signUp({ username, email, password }) {
    setLoading(true)
    try {
      const { user } = await api.signUp({ username, email, password })
      setUser(user)
      return { user }
    } catch (err) {
      return Promise.reject(err)
    } finally {
      setLoading(false)
    }
  }

  function signOut() {
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, signIn, signUp, signOut }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
