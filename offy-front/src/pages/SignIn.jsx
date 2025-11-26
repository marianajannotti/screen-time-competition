import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import './SignIn.css'

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
    <div className="signin-page-container">
      {/* Left Side - Login Form */}
      <div className="signin-right-panel">
        <div className="signin-form-container">
          <div className="signin-form-header">
            <h1 className="signin-title">Log In</h1>
            <p className="signin-subtitle">Sign in with your personal info to keep your streak!</p>
          </div>

          <form onSubmit={onSubmit} className="signin-login-form">
            <div className="signin-form-group">
              <label htmlFor="email" className="signin-form-label">Email or Username</label>
              <input 
                type="text"
                id="email" 
                name="email" 
                className="signin-form-input" 
                placeholder="Enter your email or username"
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                required
              />
            </div>

            <div className="signin-form-group">
              <div className="signin-password-label-row">
                <label htmlFor="password" className="signin-form-label">Password</label>
                <a href="#" className="signin-forgot-password">Forgot password?</a>
              </div>
              <input 
                type="password" 
                id="password" 
                name="password" 
                className="signin-form-input"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            {error && <div className="signin-error">{error}</div>}

            <button type="submit" className="signin-login-button">Log in</button>

            <p className="signin-signup-link">
              Don't have an account? <Link to="/signup" className="signin-link-purple">Sign Up</Link>
            </p>
          </form>

          <footer className="signin-footer">
            <p>&copy; 2025 Offy. All rights reserved.</p>
          </footer>
        </div>
      </div>

      {/* Right Side - Branding */}
      <div className="signin-left-panel">
        <div className="signin-branding">
          <div className="signin-logo-container">
            <div className="signin-avatar-circle">O</div>
            <span className="signin-brand-name">Offy</span>
          </div>
          <h2 className="signin-welcome-text">Welcome Back!</h2>
          <p className="signin-tagline">Track your screen time, compete with friends, and build healthier digital habits.</p>
          <div className="signin-features">
            <div className="signin-feature-item">
              <span className="signin-feature-icon">📊</span>
              <span>Track daily screen time</span>
            </div>
            <div className="signin-feature-item">
              <span className="signin-feature-icon">🎯</span>
              <span>Set personal goals</span>
            </div>
            <div className="signin-feature-item">
              <span className="signin-feature-icon">👥</span>
              <span>Compete with friends</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
