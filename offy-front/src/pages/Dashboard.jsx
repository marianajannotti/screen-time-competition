import React, { useEffect, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import * as api from '../api/mockApi'

export default function Dashboard() {
  const { user } = useAuth()
  const [logs, setLogs] = useState([])
  const [leaderboard, setLeaderboard] = useState([])

  useEffect(() => {
    if (!user) return
    api.getScreenTimeLogs(user.user_id).then((r) => setLogs(r.logs || []))
    api.getLeaderboard().then((r) => setLeaderboard(r.list || []))
  }, [user])

  return (
    <main style={{ padding: 20 }}>
      <h2>Welcome{user ? `, ${user.username}` : ''}</h2>
      <section style={{ marginBottom: 16 }}>
        <h3>Last Logs</h3>
        {logs.length === 0 && <div>No screen time logged yet.</div>}
        <ul>
          {logs.map((l) => (
            <li key={l.log_id}>{l.date}: {l.screen_time_minutes} minutes</li>
          ))}
        </ul>
      </section>

      <section>
        <h3>Leaderboard (mock)</h3>
        <ol>
          {leaderboard.map((u) => (
            <li key={u.user_id}>{u.username} — {u.total_points || 0} pts</li>
          ))}
        </ol>
      </section>
    </main>
  )
}
