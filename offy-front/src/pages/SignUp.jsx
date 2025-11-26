import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function SignUp() {
  const { signUp } = useAuth()
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const nav = useNavigate()

  async function onSubmit(e) {
    e.preventDefault()
    setError(null)
    try {
      await signUp({ username, email, password })
      nav('/dashboard')
    } catch (err) {
      setError(err?.message || 'Sign up failed')
    }
  }

  return (
    <main style={{ padding: 32, display: 'flex', justifyContent: 'center' }}>
      <div className="card" style={{ width: 520 }}>
        <h2 style={{ marginTop: 0 }}>Create Account</h2>
        <p className="muted">Join us and start tracking your screen time today!</p>

        <form onSubmit={onSubmit} style={{ display: 'grid', gap: 12, marginTop: 16 }}>
          <input placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} required />
          <input placeholder="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          <input placeholder="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />

          {error && <div style={{ color: 'red' }}>{error}</div>}

          <button className="btn-primary" type="submit">Create account</button>
        </form>

        <p style={{ marginTop: 12 }}>
          Already have an account? <Link to="/signin">Sign In</Link>
        </p>
      </div>
    </main>
  )
}
