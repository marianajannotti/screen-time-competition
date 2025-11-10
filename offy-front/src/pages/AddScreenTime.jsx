import React, { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import * as api from '../api/mockApi'
import { useNavigate } from 'react-router-dom'

export default function AddScreenTime() {
  const { user } = useAuth()
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10))
  const [minutes, setMinutes] = useState(30)
  const [message, setMessage] = useState(null)
  const nav = useNavigate()

  async function onSubmit(e) {
    e.preventDefault()
    if (!user) return
    try {
      await api.addScreenTime({ user_id: user.user_id, date, minutes })
      setMessage('Saved')
      setTimeout(() => nav('/dashboard'), 800)
    } catch (err) {
      setMessage(err?.message || 'Failed')
    }
  }

  return (
    <main style={{ padding: 20 }}>
      <h2>Add screen time</h2>
      <form onSubmit={onSubmit} style={{ display: 'grid', gap: 8, maxWidth: 420 }}>
        <label>
          Date
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
        </label>
        <label>
          Minutes
          <input type="number" min={0} value={minutes} onChange={(e) => setMinutes(Number(e.target.value))} />
        </label>
        <button type="submit">Add</button>
        {message && <div>{message}</div>}
      </form>
    </main>
  )
}
