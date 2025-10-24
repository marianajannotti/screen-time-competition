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
    <main style={{ padding: 20 }}>
      <h2>Sign up</h2>
      <form onSubmit={onSubmit} style={{ display: 'grid', gap: 8, maxWidth: 360 }}>
        <input placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
        <input placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
        <input placeholder="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        <button type="submit">Create account</button>
        {error && <div style={{ color: 'red' }}>{error}</div>}
      </form>
      <p>
        Already have an account? <Link to="/signin">Sign in</Link>
      </p>
    </main>
  )
}
