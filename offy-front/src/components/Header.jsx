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
    <header style={{ padding: 12, borderBottom: '1px solid #eee', display: 'flex', justifyContent: 'space-between' }}>
      <div>
        <Link to="/dashboard" style={{ marginRight: 12 }}>
          Offy
        </Link>
        {user && <Link to="/add">Add</Link>}
      </div>
      <div>
        {user ? (
          <>
            <span style={{ marginRight: 12 }}>Hi, {user.username}</span>
            <button onClick={onSignOut}>Sign out</button>
          </>
        ) : (
          <>
            <Link to="/signin" style={{ marginRight: 8 }}>
              Sign in
            </Link>
            <Link to="/signup">Sign up</Link>
          </>
        )}
      </div>
    </header>
  )
}
