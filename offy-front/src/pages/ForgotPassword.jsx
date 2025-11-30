import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { forgotPassword } from '../api/authApi'

export default function ForgotPassword() {
  const [email, setEmail] = useState('')
  const [status, setStatus] = useState('idle') // idle | loading | success | error
  const [message, setMessage] = useState('')

  async function onSubmit(e) {
    e.preventDefault()
    setStatus('loading')
    setMessage('')

    try {
      const response = await forgotPassword({ email })
      setStatus('success')
      setMessage(response.message || 'If an account with that email exists, a password reset link has been sent.')
    } catch (err) {
      setStatus('error')
      setMessage(err?.message || 'Something went wrong. Please try again.')
    }
  }

  return (
    <main style={{ padding: 32, display: 'flex', justifyContent: 'center' }}>
      <div className="card" style={{ width: 460 }}>
        <h2 style={{ marginTop: 0 }}>Forgot Password</h2>
        <p className="muted">
          Enter your email address and we'll send you a link to reset your password.
        </p>

        {status === 'success' ? (
          <div className="success-box">
            <div className="success-icon">✓</div>
            <p>{message}</p>
            <p className="muted" style={{ marginTop: 12 }}>
              Check your inbox and spam folder. The link expires in 30 minutes.
            </p>
            <Link to="/signin" style={{ marginTop: 16 }}>
              Back to Sign In
            </Link>
          </div>
        ) : (
          <form onSubmit={onSubmit} style={{ display: 'grid', gap: 12, marginTop: 16 }}>
            <label htmlFor="email" className="visually-hidden">Email address</label>
            <input
              id="email"
              type="email"
              placeholder="Email address"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={status === 'loading'}
            />

            <button 
              className="btn-primary" 
              type="submit" 
              disabled={status === 'loading' || !email.trim()}
            >
              {status === 'loading' ? 'Sending...' : 'Send Reset Link'}
            </button>

            {status === 'error' && (
              <div style={{ color: 'red', fontSize: 14 }}>{message}</div>
            )}
          </form>
        )}

        <p style={{ marginTop: 16 }}>
          Remember your password? <Link to="/signin">Sign in</Link>
        </p>
      </div>
    </main>
  )
}
