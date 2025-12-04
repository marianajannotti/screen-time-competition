import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import SignIn from './pages/SignIn'
import SignUp from './pages/SignUp'
import Dashboard from './pages/Dashboard'
import Profile from './pages/Profile'
import AddScreenTime from './pages/AddScreenTime'
import Leaderboard from './pages/Leaderboard'
import Friends from './pages/Friends'
import Header from './components/Header'
import PrivateRoute from './components/PrivateRoute'

export default function AppRouter() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <Header />
        <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/signin" element={<SignIn />} />
        <Route path="/signup" element={<SignUp />} />

        <Route path="/dashboard" element={<PrivateRoute element={<Dashboard />} />} />
        <Route path="/profile" element={<PrivateRoute element={<Profile />} />} />
        <Route path="/add" element={<PrivateRoute element={<AddScreenTime />} />} />
        <Route path="/leaderboard" element={<PrivateRoute element={<Leaderboard />} />} />
        <Route path="/friends" element={<PrivateRoute element={<Friends />} />} />

        <Route path="*" element={<div style={{ padding: 20 }}>Not Found</div>} />
        </Routes>
        <footer className="global-footer muted">© 2025 Offy</footer>
      </div>
    </BrowserRouter>
  )
}
