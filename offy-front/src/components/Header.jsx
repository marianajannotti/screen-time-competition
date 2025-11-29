import React from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function Header() {
  const { user, signOut } = useAuth()
  const nav = useNavigate()

  function onSignOut() {
    signOut()
    nav('/signin')
  }

  return (
    <header>
      <div className="inner">
        <div style={{display:'flex',alignItems:'center',gap:12}}>
          <div className="brand">
            <div className="dot">O</div>
            <div>Offy</div>
          </div>
          <div className="top-title">Welcome, {user ? user.username : 'Guest'}</div>
        </div>

        <div className="header-actions">
          <Link to="/leaderboard">Leaderboard</Link>
          <Link to="/dashboard" className="btn-ghost">Dashboard</Link>
          {user && <button className="btn-primary" onClick={() => nav('/add')}>+ Log Hours</button>}
          {user ? (
            <>
              <div style={{display:'flex',alignItems:'center',gap:8}}>
                {/* Make avatar clickable to go to profile */}
                <button
                  type="button"
                  aria-label="Open profile"
                  onClick={() => nav('/profile')}
                  className="header-avatar"
                >
                  {user.username?.[0]?.toUpperCase()}
                </button>
                <button onClick={onSignOut} className="btn-ghost">Sign out</button>
              </div>
            </>
          ) : (
            <>
              <Link to="/signin" className="btn-ghost">Sign in</Link>
              <Link to="/signup" className="btn-ghost">Sign up</Link>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
