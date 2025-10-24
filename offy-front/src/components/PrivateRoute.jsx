import React from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function PrivateRoute({ component: Component }) {
  const { user, loading } = useAuth()
  if (loading) return <div style={{ padding: 20 }}>Loading...</div>
  if (!user) return <Navigate to="/signin" replace />
  return <Component />
}
