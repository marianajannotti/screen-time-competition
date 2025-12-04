import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function SignIn() {
  const { signIn } = useAuth()
  const [identifier, setIdentifier] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const nav = useNavigate()

  async function onSubmit(e) {
    e.preventDefault()
    setError(null)
    try {
      await signIn({ emailOrUsername: identifier, password })
      nav('/dashboard')
    } catch (err) {
      setError(err?.message || 'Sign in failed')
    }
  }

  return (
    <main style={{ padding: 32, display: 'flex', justifyContent: 'center' }}>
      <div className="card" style={{ width: 460 }}>
        <h2 style={{ marginTop: 0 }}>Welcome back</h2>
        <p className="muted">Sign in to continue</p>
        <form onSubmit={onSubmit} style={{ display: 'grid', gap: 12, marginTop: 16 }}>
          <input
            placeholder="Email or username"
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
          />

          <input
            placeholder="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />

          <div style={{ textAlign: 'right' }}>
            <Link to="/forgot-password" className="forgot-password-link">
              Forgot password?
            </Link>
          </div>

          <button className="btn-primary" type="submit">
            Sign in
          </button>

          {error && <div style={{ color: 'red' }}>{error}</div>}
        </form>

        <p style={{ marginTop: 12 }}>
          Need an account? <Link to="/signup">Sign up</Link>
        </p>
      </div>
    </main>
  )
}
