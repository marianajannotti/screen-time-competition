import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import './SignUp.css'

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
    <div className="signup-page-container">
      {/* Left Side - Sign Up Form */}
      <div className="signup-right-panel">
        <div className="signup-form-container">
          <div className="signup-form-header">
            <h1 className="signup-title">Create Account</h1>
            <p className="signup-subtitle">Join us and start tracking your screen time today!</p>
          </div>

          <form onSubmit={onSubmit} className="signup-signup-form">
            <div className="signup-form-group">
              <label htmlFor="username" className="signup-form-label">Username</label>
              <input 
                type="text"
                id="username" 
                name="username" 
                className="signup-form-input" 
                placeholder="Choose a username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </div>

            <div className="signup-form-group">
              <label htmlFor="email" className="signup-form-label">Email</label>
              <input 
                type="email"
                id="email" 
                name="email" 
                className="signup-form-input" 
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div className="signup-form-group">
              <label htmlFor="password" className="signup-form-label">Password</label>
              <input 
                type="password" 
                id="password" 
                name="password" 
                className="signup-form-input"
                placeholder="Create a password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            {error && <div className="signup-error">{error}</div>}

            <button type="submit" className="signup-signup-button">Create Account</button>

            <p className="signup-signin-link">
              Already have an account? <Link to="/signin" className="signup-link-purple">Sign In</Link>
            </p>
          </form>

          <footer className="signup-footer">
            <p>&copy; 2025 Offy. All rights reserved.</p>
          </footer>
        </div>
      </div>

      {/* Right Side - Branding */}
      <div className="signup-left-panel">
        <div className="signup-branding">
          <div className="signup-logo-container">
            <div className="signup-avatar-circle">O</div>
            <span className="signup-brand-name">Offy</span>
          </div>
          <h2 className="signup-welcome-text">Start Your Journey!</h2>
          <p className="signup-tagline">Join thousands of users taking control of their screen time and building better digital habits.</p>
          <div className="signup-features">
            <div className="signup-feature-item">
              <span className="signup-feature-icon">⚡</span>
              <span>Quick and easy setup</span>
            </div>
            <div className="signup-feature-item">
              <span className="signup-feature-icon">🏆</span>
              <span>Compete and stay motivated</span>
            </div>
            <div className="signup-feature-item">
              <span className="signup-feature-icon">📈</span>
              <span>Track your progress</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
