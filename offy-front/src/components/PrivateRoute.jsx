import React from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

// Accept an "element" prop (React element) to align with common usage: <PrivateRoute element={<Dashboard/>} />
export default function PrivateRoute({ element }) {
  const { isAuthenticated, loading } = useAuth()
  const location = useLocation()

  if (loading) return <div style={{ padding: 20 }}>Loading...</div>
  if (!isAuthenticated) {
    return <Navigate to="/signin" replace state={{ from: location }} />
  }
  return element
}
