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
      <div className="dashboard-grid">
        <aside className="left-rail">
          <div className="small-card">
            <h4>Daily Limit</h4>
            <div className="muted">3h 15m used of 4h 30m goal</div>
          </div>
          <div className="small-card">
            <h4>Weekly Goal</h4>
            <div className="muted">14h 28m used of 31h 30m goal</div>
          </div>
          <div className="small-card">
            <h4>Challenges</h4>
            <div className="muted">Complete challenges to earn rewards</div>
          </div>
        </aside>

        <section>
          <div style={{display:'flex',gap:12,marginBottom:16}}>
            <div className="card" style={{flex:1}}> 
              <h3>Top Used Apps Today</h3>
              <div style={{display:'flex',gap:12,marginTop:12}}>
                <div className="small-card" style={{flex:1}}>YouTube<br/><strong>18h 32m</strong></div>
                <div className="small-card" style={{flex:1}}>Instagram<br/><strong>15h 24m</strong></div>
                <div className="small-card" style={{flex:1}}>TikTok<br/><strong>12h 51m</strong></div>
              </div>
            </div>
          </div>

          <div className="card" style={{height:360}}>
            <h3>Last Week's Screen Time</h3>
            <div style={{height:300,display:'flex',alignItems:'center',justifyContent:'center',color:'#999'}}>Chart placeholder</div>
          </div>

        </section>
      </div>
      <div className="corner-action">
        <button className="btn-primary" onClick={() => (window.location.href = '/add')}>+ Log Hours</button>
      </div>
    </main>
  )
}
