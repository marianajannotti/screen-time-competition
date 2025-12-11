import React from 'react'
import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import homeIcon from '../assets/badges/home-icon.png?url'
import trophyIcon from '../assets/badges/trophy-icon.png?url'

export default function Header() {
  const { user, signOut } = useAuth()
  const nav = useNavigate()
  const location = useLocation()

  const initials = (user?.username || user?.name || 'U').trim().charAt(0).toUpperCase()
  const isDashboard = location.pathname.startsWith('/dashboard')

  function onSignOut() {
    signOut()
    nav('/signin')
  }

  // Hide full header on auth pages, show centered brand dot above the auth card
  if (location.pathname === '/signin' || location.pathname === '/signup') {
    return (
      <div className="auth-top-brand center" onClick={() => nav('/')}> 
        <span className="dot">O</span>
      </div>
    )
  }

  const Brand = (
    <div className="brand" onClick={() => nav('/dashboard')} style={{ cursor: 'pointer' }}>
      <div className="dot">O</div>
      <div>Offy</div>
    </div>
  )

  // Nav links vary by page
  const NavLinks = (
    <nav className="nav-links">
      <NavLink to="/dashboard" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
        <img src={homeIcon} alt="Home" />
        Home
      </NavLink>
      <NavLink to="/leaderboard" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
        <img src={trophyIcon} alt="Leaderboard" />
        Leaderboard
      </NavLink>
      <button aria-label="Open profile" onClick={() => nav('/profile')} className={`header-avatar ${location.pathname.startsWith('/profile') ? 'active' : ''}`}>
        {initials}
      </button>
    </nav>
  )

  const Actions = (
    <div className="header-actions">
      {NavLinks}
      {user && (
        <>
          <button onClick={onSignOut} className="btn-ghost">Sign out</button>
        </>
      )}
      {!user && (
        <>
          <NavLink to="/signin" className="btn-ghost">Sign in</NavLink>
          <NavLink to="/signup" className="btn-primary">Create Account</NavLink>
        </>
      )}
    </div>
  )

  // Welcome only on Home, slightly more to the left: we’ll keep it centered but allow brand to be wider and reduce spacing
  const homeInlineWelcome = isDashboard ? (
    <span className="home-inline-welcome">{`Welcome, ${user ? user.username : 'Guest'}`}</span>
  ) : null

  return (
    <header>
      <div className="inner">
        <div className="left-brand-welcome">
          {Brand}
          {homeInlineWelcome}
        </div>
        {Actions}
      </div>
    </header>
  )
}
