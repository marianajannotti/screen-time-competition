import React, { useState } from 'react'
import { Link, useSearchParams, useNavigate } from 'react-router-dom'
import { resetPassword } from '../api/authApi'

export default function ResetPassword() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const token = searchParams.get('token') || ''

  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [status, setStatus] = useState('idle') // idle | loading | success | error
  const [message, setMessage] = useState('')

  // Validate token exists
  const hasToken = token.trim().length > 0

  async function onSubmit(e) {
    e.preventDefault()
    setMessage('')

    // Validate passwords match
    if (newPassword !== confirmPassword) {
      setStatus('error')
      setMessage('Passwords do not match')
      return
    }

    // Validate password length
    if (newPassword.length < 6) {
      setStatus('error')
      setMessage('Password must be at least 6 characters')
      return
    }

    setStatus('loading')

    try {
      const response = await resetPassword({ token, new_password: newPassword })
      setStatus('success')
      setMessage(response.message || 'Password has been reset successfully!')
    } catch (err) {
      setStatus('error')
      setMessage(err?.message || 'Failed to reset password. The link may have expired.')
    }
  }

  // No token provided
  if (!hasToken) {
    return (
      <main style={{ padding: 32, display: 'flex', justifyContent: 'center' }}>
        <div className="card" style={{ width: 460 }}>
          <h2 style={{ marginTop: 0 }}>Invalid Reset Link</h2>
          <div className="error-box">
            <p>This password reset link is invalid or missing.</p>
            <p className="muted" style={{ marginTop: 8 }}>
              Please request a new password reset link.
            </p>
          </div>
          <Link 
            to="/forgot-password" 
            className="btn-primary" 
            style={{ display: 'inline-block', marginTop: 16, textDecoration: 'none' }}
          >
            Request New Link
          </Link>
        </div>
      </main>
    )
  }

  return (
    <main style={{ padding: 32, display: 'flex', justifyContent: 'center' }}>
      <div className="card" style={{ width: 460 }}>
        <h2 style={{ marginTop: 0 }}>Reset Password</h2>
        
        {status === 'success' ? (
          <div className="success-box">
            <div className="success-icon">✓</div>
            <p>{message}</p>
            <p className="muted" style={{ marginTop: 12 }}>
              You can now sign in with your new password.
            </p>
            <button 
              className="btn-primary" 
              onClick={() => navigate('/signin')}
              style={{ marginTop: 16 }}
            >
              Go to Sign In
            </button>
          </div>
        ) : (
          <>
            <p className="muted">Enter your new password below.</p>

            <form onSubmit={onSubmit} style={{ display: 'grid', gap: 12, marginTop: 16 }}>
              <input
                type="password"
                placeholder="New password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                disabled={status === 'loading'}
                minLength={6}
              />

              <input
                type="password"
                placeholder="Confirm new password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                disabled={status === 'loading'}
                minLength={6}
              />

              <button 
                className="btn-primary" 
                type="submit" 
                disabled={status === 'loading' || !newPassword || !confirmPassword}
              >
                {status === 'loading' ? 'Resetting...' : 'Reset Password'}
              </button>

              {status === 'error' && (
                <div style={{ color: 'red', fontSize: 14 }}>{message}</div>
              )}
            </form>

            <p style={{ marginTop: 16 }}>
              <Link to="/forgot-password">Request a new reset link</Link>
            </p>
          </>
        )}
      </div>
    </main>
  )
}
