import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import SignIn from './pages/SignIn'
import SignUp from './pages/SignUp'
import ForgotPassword from './pages/ForgotPassword'
import ResetPassword from './pages/ResetPassword'
import Dashboard from './pages/Dashboard'
import Profile from './pages/Profile'
import AddScreenTime from './pages/AddScreenTime'
import Leaderboard from './pages/Leaderboard'
import Header from './components/Header'
import PrivateRoute from './components/PrivateRoute'

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Header />
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/signin" element={<SignIn />} />
        <Route path="/signup" element={<SignUp />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />

        <Route path="/dashboard" element={<PrivateRoute element={<Dashboard />} />} />
        <Route path="/profile" element={<PrivateRoute element={<Profile />} />} />
        <Route path="/add" element={<PrivateRoute element={<AddScreenTime />} />} />
        <Route path="/leaderboard" element={<PrivateRoute element={<Leaderboard />} />} />

        <Route path="*" element={<div style={{ padding: 20 }}>Not Found</div>} />
      </Routes>
    </BrowserRouter>
  )
}
