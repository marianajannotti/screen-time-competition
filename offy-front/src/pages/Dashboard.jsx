import React, { useMemo, useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { getMonthlyLogs, getFriends, getFriendIds, getChallenges, addChallenge, getDailyUsage, getAllUsers, addFriendship } from '../api/mockApi'

// Normalize user id from different possible shapes
function getUserId(u) {
  return u?.user_id ?? u?.id ?? u?.userId ?? u?.uid ?? null
}

// Helpers
function minutesLabel(mins) {
  const h = Math.floor(mins / 60)
  const m = Math.round(mins % 60)
  return `${h}h ${m}m`
}

function ProgressBar({ value, max, color, exceeded }) {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0
  const actualPct = max > 0 ? (value / max) * 100 : 0
  const fillColor = exceeded ? '#ef4444' : color
  const label = exceeded ? `${Math.round(actualPct - 100)}% exceeded` : `${Math.round(pct)}%`
  return (
    <div className="progress-bar" aria-label={`Progress ${Math.round(actualPct)}%`}>
      <div className="track" />
      <div className="fill" style={{ width: pct + '%', background: fillColor }} />
      <div className="pct-label">{label}</div>
    </div>
  )
}

function WeeklyChart({ days, chartData, appColorMap }) {
  if (!days.length) return <div style={{height:300,display:'flex',alignItems:'center',justifyContent:'center',color:'#999'}}>No screen time data for this week</div>
  const height = 180
  const barW = 54
  const gap = 64
  const totals = days.map(d => chartData[d]?.total || 0)
  const max = Math.max(...totals, 1)
  const maxHours = Math.ceil(max / 60)
  const ticks = Array.from({length: maxHours + 1}, (_,i)=>i)
  return (
    <div className="chart-wrapper">
      <svg viewBox={`0 0 ${gap * days.length + 40} ${height + 50}`} className="weekly-chart" preserveAspectRatio="xMidYMid meet">
        {/* Y Axis */}
        <line x1={34} y1={height - 10} x2={34} y2={20} stroke="#ccc" strokeWidth="1" />
        {ticks.map(h => {
          const y = (height - 10) - (h * 60 / max) * (height - 30)
          return (
            <g key={h}>
              <line x1={34} x2={gap * days.length + 40} y1={y} y2={y} stroke="#f1f5f9" strokeWidth="1" />
              <text x={28} y={y + 4} fontSize="10" textAnchor="end" fill="#555">{h}h</text>
            </g>
          )
        })}
        {days.map((day, i) => {
          const x = 20 + i * gap
          const yBase = height - 10
          const dayData = chartData[day]
          if (!dayData) {
            // No logs: just show day label without a bar.
            return (
              <g key={day}>
                <text x={x + barW/2} y={height + 14} textAnchor="middle" fontSize="12" fill="#999">{day}</text>
              </g>
            )
          }
          const { apps, remainder } = dayData
          let yOffset = 0
          // stack apps first
          const segments = Object.entries(apps)
          const total = dayData.total
          return (
            <g key={day} className="bar-group" data-day={day}>
              {segments.map(([app, minutes]) => {
                const h = (minutes / max) * (height - 30)
                const y = yBase - yOffset - h
                yOffset += h
                return (
                  <rect
                    key={app}
                    x={x + 14}
                    y={y}
                    width={barW}
                    height={h}
                    fill={appColorMap[app] || '#999'}
                    data-app={app}
                    data-minutes={minutes}
                    className="bar-segment"
                    onMouseEnter={(e) => {
                      const tt = document.getElementById('chartTooltip')
                      if (!tt) return
                      const appName = e.target.getAttribute('data-app')
                      const mins = Number(e.target.getAttribute('data-minutes'))
                      tt.textContent = ''
                      const strong = document.createElement('strong')
                      strong.textContent = day
                      const div = document.createElement('div')
                      div.textContent = appName + ': ' + minutesLabel(mins)
                      tt.appendChild(strong)
                      tt.appendChild(div)
                      tt.style.display = 'block'
                      const svg = e.target.ownerSVGElement
                      const svgRect = svg.getBoundingClientRect()
                      tt.style.left = (e.clientX - svgRect.left + 8) + 'px'
                      tt.style.top = (e.clientY - svgRect.top - 24) + 'px'
                    }}
                    onMouseLeave={() => {
                      const tt = document.getElementById('chartTooltip')
                      if (tt) tt.style.display = 'none'
                    }}
                  />
                )
              })}
              {remainder > 0 && (()=>{
                const remH = (remainder / max) * (height - 30)
                const remY = yBase - yOffset - remH
                return <rect x={x + 14} y={remY} width={barW} height={remH} fill="#e2e8f0" />
              })()}
              {/* Small transparent strip at top for total hover without blocking app segments */}
              {total > 0 && (()=>{
                const totalH = (total / max) * (height - 30)
                const stripH = Math.min(18, totalH) // only top strip
                const stripY = yBase - totalH
                return (
                  <rect
                    x={x + 14}
                    y={stripY}
                    width={barW}
                    height={stripH}
                    fill="transparent"
                    data-total={total}
                    onMouseEnter={(e)=>{
                      const tt = document.getElementById('chartTooltip')
                      if (!tt) return
                      tt.textContent=''
                      const strong = document.createElement('strong')
                      strong.textContent = day
                      const div = document.createElement('div')
                      div.textContent = 'Total: ' + minutesLabel(total)
                      tt.appendChild(strong)
                      tt.appendChild(div)
                      tt.style.display='block'
                      const svg = e.target.ownerSVGElement
                      const svgRect = svg.getBoundingClientRect()
                      tt.style.left = (e.clientX - svgRect.left + 8) + 'px'
                      tt.style.top = (e.clientY - svgRect.top - 24) + 'px'
                    }}
                    onMouseLeave={()=>{ const tt = document.getElementById('chartTooltip'); if (tt) tt.style.display='none' }}
                  />
                )
              })()}
      <text x={x + barW/2 + 14} y={height + 14} textAnchor="middle" fontSize="12" fill="#444">{day}</text>
            </g>
          )
        })}
      </svg>
      <div className="chart-tooltip" id="chartTooltip" style={{display:'none'}} />
    </div>
  )
}

export default function Dashboard() {
  const { user } = useAuth()
  // Persist goals in localStorage keyed per user
  const storageKey = (k) => `offy_${getUserId(user) || 'anon'}_${k}`
  const [dailyGoal, setDailyGoal] = useState(() => {
    const v = localStorage.getItem(storageKey('daily_goal'))
    return v ? Number(v) : undefined
  })
  const [weeklyGoal, setWeeklyGoal] = useState(() => {
    const v = localStorage.getItem(storageKey('weekly_goal'))
    return v ? Number(v) : undefined
  })
  const [showDailyModal, setShowDailyModal] = useState(false)
  const [showWeeklyModal, setShowWeeklyModal] = useState(false)
  const [showChallengeModal, setShowChallengeModal] = useState(false)
  const [challenges, setChallenges] = useState([])
  // Fetch logs (mock) via mockApi helpers and compute aggregates
  const [logs, setLogs] = useState([])
  useEffect(() => {
    let mounted = true
    if (!user) { setLogs([]); return }
    ;(async () => {
      try {
        const res = await getMonthlyLogs(getUserId(user))
        if (!mounted) return
        const arr = Array.isArray(res.logs) ? res.logs : []
        // last 7 days filter
        const today = new Date()
        const cutoff = new Date(today.getFullYear(), today.getMonth(), today.getDate() - 6)
        const recent = arr.filter((l) => {
          const d = new Date(l.date)
          return d >= cutoff && d <= today
        })
        setLogs(recent)
      } catch (err) {
        if (!mounted) return
        setLogs([])
      }
    })()
    return () => { mounted = false }
  }, [user])

  // Fetch user's challenges
  useEffect(() => {
    let mounted = true
    if (!user) { setChallenges([]); return }
    ;(async () => {
      try {
        const res = await getChallenges(getUserId(user))
        if (!mounted) return
        setChallenges(Array.isArray(res.challenges) ? res.challenges : [])
      } catch (err) {
        if (!mounted) return
        setChallenges([])
      }
    })()
    return () => { mounted = false }
  }, [user])

  const todayApps = useMemo(() => {
    const todayStr = new Date().toISOString().slice(0,10)
    const groups = {}
    logs.filter(l => l.date === todayStr && l.app !== '__TOTAL__').forEach(l => {
      groups[l.app] = (groups[l.app]||0) + l.minutes
    })
    return Object.entries(groups).sort((a,b)=>b[1]-a[1]).map(([app, minutes])=>({app, minutes}))
  }, [logs])

  const topApps = todayApps

  const todayTotal = useMemo(()=>{
    const todayStr = new Date().toISOString().slice(0,10)
    const t = logs.find(l => l.date === todayStr && l.app === '__TOTAL__')
    return t ? t.minutes : undefined
  }, [logs])
  const dailyUsed = todayTotal !== undefined ? todayTotal : todayApps.reduce((a,b)=>a+b.minutes,0)
  // dailyGoal state above
  const weeklyUsed = useMemo(()=>{
    // sum totals if present, else sum app entries (excluding __TOTAL__ to avoid duplicate count)
    const dayMap = {}
    logs.forEach(l => { dayMap[l.date] = dayMap[l.date] || {}; dayMap[l.date][l.app] = l.minutes })
    let sum = 0
    Object.values(dayMap).forEach(dayApps => {
      if (dayApps['__TOTAL__'] !== undefined) sum += dayApps['__TOTAL__']
      else {
        Object.entries(dayApps).forEach(([app,min])=>{ if (app !== '__TOTAL__') sum += min })
      }
    })
    return sum
  }, [logs])
  // weeklyGoal state above

  // Prepare weekly chart breakdown
  const chartColors = ['#6b21a8','#805ad5','#8bafff','#93c5fd','#6366f1']
  // Deterministic color mapping based on sorted unique app names for stability
  const uniqueApps = Array.from(new Set(logs.filter(l=>l.app !== '__TOTAL__').map(l=>l.app))).sort()
  const appColorMap = uniqueApps.reduce((acc, app, idx) => { acc[app] = chartColors[idx % chartColors.length]; return acc }, {})
  const last7Days = Array.from({length:7}, (_,i)=>{
    const d = new Date()
    d.setDate(d.getDate() - (6 - i))
    return d.toISOString().slice(0,10)
  })
  const chartData = {}
  last7Days.forEach(ds => {
    // build day entry
    const dayLogs = logs.filter(l => l.date === ds)
    if (!dayLogs.length) return
    const totalEntry = dayLogs.find(l => l.app === '__TOTAL__')
    const apps = {}
    dayLogs.filter(l => l.app !== '__TOTAL__').forEach(l => { apps[l.app] = (apps[l.app]||0) + l.minutes })
    let total = 0
    if (totalEntry) total = totalEntry.minutes
    else total = Object.values(apps).reduce((a,b)=>a+b,0)
    const stackedSum = Object.values(apps).reduce((a,b)=>a+b,0)
    const remainder = Math.max(0, total - stackedSum)
    chartData[new Date(ds).toLocaleDateString('en-US',{weekday:'short'})] = { apps, remainder, total }
  })
  const days = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat']

  return (
    <main className="dashboard-main">
      <div className="dashboard-grid">
        <aside className="left-rail">
      <div className="metric-card" style={dailyGoal !== undefined && dailyUsed > dailyGoal ? {backgroundColor: '#fee2e2'} : {}}>
            <div className="card-head">
              <span className="icon clock" />
              <span className="title">Daily Limit</span>
        <button className="add-btn" aria-label="Add daily goal" title="Add daily goal" onClick={()=>setShowDailyModal(true)}>+</button>
            </div>
            {dailyGoal === undefined ? (
              <p className="muted small" style={{margin:0}}>Create a new limit by clicking +</p>
            ) : (
              <>
                <ProgressBar value={dailyUsed || 0} max={dailyGoal} color="#d97706" exceeded={dailyUsed > dailyGoal} />
                <div className="sub-row">
                  <span>{dailyUsed ? minutesLabel(dailyUsed) + ' used' : 'Log your hours'}</span>
                  <span>{minutesLabel(dailyGoal)} goal</span>
                </div>
              </>
            )}
          </div>
          <div className="metric-card" style={weeklyGoal !== undefined && weeklyUsed > weeklyGoal ? {backgroundColor: '#fee2e2'} : {}}>
            <div className="card-head">
              <span className="icon target" />
              <span className="title">Weekly Goal</span>
        <button className="add-btn" aria-label="Add weekly goal" title="Add weekly goal" onClick={()=>setShowWeeklyModal(true)}>+</button>
            </div>
            {weeklyGoal === undefined ? (
              <p className="muted small" style={{margin:0}}>Create a new goal by clicking +</p>
            ) : (
              <>
                <ProgressBar value={weeklyUsed || 0} max={weeklyGoal} color="#16a34a" exceeded={weeklyUsed > weeklyGoal} />
                <div className="sub-row">
                  <span>{weeklyUsed ? minutesLabel(weeklyUsed) + ' used' : 'Log your hours'}</span>
                  <span>{minutesLabel(weeklyGoal)} goal</span>
                </div>
              </>
            )}
          </div>
          <div className="metric-card">
            <div className="card-head">
              <span className="icon trophy" />
              <span className="title">Challenges</span>
            </div>
            <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',gap:8}}>
              <div style={{fontSize:14,color:'#333'}}>Your active challenges</div>
              <button className="add-btn" aria-label="Create challenge" title="Create challenge" onClick={()=>setShowChallengeModal(true)}>+</button>
            </div>
            {challenges.length === 0 ? (
              <p className="muted" style={{margin:0,marginTop:8}}>Create a challenge to get started</p>
            ) : (
              <div style={{display:'grid',gap:8,marginTop:8}}>
                {challenges.map(c => (
                  <ChallengeRow key={c.challenge_id} challenge={c} currentUser={user} />
                ))}
              </div>
            )}
          </div>
        </aside>

        <section>
          <div className="top-apps-row">
            <div className="top-app-card" style={{ background: 'linear-gradient(180deg,#fff,#fafcff)' }}>
              <div className="app-inner">
                <div className="usage-main">{todayTotal !== undefined ? minutesLabel(todayTotal) : <span style={{fontSize:'12px'}}>Log your Total Screen Time</span>}</div>
                <div className="usage-sub">Total Screen Time</div>
              </div>
            </div>
            {topApps.map(app => (
              <div key={app.app} className="top-app-card" style={{ background: 'linear-gradient(180deg,#fff,#fafcff)' }}>
                <div className="app-inner">
                  <div className="usage-main">{minutesLabel(app.minutes)}</div>
                  <div className="usage-sub">{app.app}</div>
                </div>
              </div>
            ))}
          </div>

          <div className="chart-card">
            <h3>Last Week's Screen Time</h3>
            <WeeklyChart days={days} chartData={chartData} appColorMap={appColorMap} />
            <div className="chart-legend" style={{display:'flex',flexWrap:'wrap',gap:12,marginTop:10}}>
              {Object.entries(appColorMap).map(([app,color]) => (
                <div key={app} style={{display:'flex',alignItems:'center',gap:6,fontSize:12}}>
                  <span style={{display:'inline-block',width:14,height:14,background:color,borderRadius:3}} />
                  <span>{app}</span>
                </div>
              ))}
              <div style={{display:'flex',alignItems:'center',gap:6,fontSize:12}}>
                <span style={{display:'inline-block',width:14,height:14,background:'#e2e8f0',borderRadius:3}} />
                <span>Remainder (unassigned)</span>
              </div>
            </div>
          </div>

        </section>
      </div>
      {showDailyModal && (
        <GoalModal
          title="Create or Edit your Daily Limit"
          initialMinutes={dailyGoal}
          onClose={()=>setShowDailyModal(false)}
          onSave={(mins)=>{ setDailyGoal(mins); localStorage.setItem(storageKey('daily_goal'), String(mins)); setShowDailyModal(false) }}
        />
      )}
      {showWeeklyModal && (
        <GoalModal
          title="Create or Edit your Weekly Goal"
          initialMinutes={weeklyGoal}
          onClose={()=>setShowWeeklyModal(false)}
          onSave={(mins)=>{ setWeeklyGoal(mins); localStorage.setItem(storageKey('weekly_goal'), String(mins)); setShowWeeklyModal(false) }}
        />
      )}
      {showChallengeModal && (
        <ChallengeModal
          currentUser={user}
          onClose={()=>setShowChallengeModal(false)}
            onCreate={async ()=>{
            try {
              const res = await getChallenges(getUserId(user))
              setChallenges(Array.isArray(res.challenges) ? res.challenges : [])
            } catch {
              setChallenges([])
            }
          }}
        />
      )}
      <div className="corner-action">
        <button className="btn-primary" onClick={() => (window.location.href = '/add')}>+ Log Hours</button>
      </div>
    </main>
  )
}

function GoalModal({ title, initialMinutes, onClose, onSave }) {
  const initH = initialMinutes ? Math.floor(initialMinutes / 60) : 0
  const initM = initialMinutes ? initialMinutes % 60 : 0
  const [hours, setHours] = useState(initH)
  const [minutes, setMinutes] = useState(initM)
  const [error, setError] = useState(null)

  function submit(e) {
    e.preventDefault()
    const h = Number(hours) || 0
    const m = Number(minutes) || 0
    if (m >= 60) { setError('Minutes must be < 60'); return }
    const total = h * 60 + m
    if (total <= 0) { setError('Goal must be greater than 0'); return }
    onSave(total)
  }

  return (
    <div className="modal-backdrop" style={{zIndex:60}}>
      <div className="modal" style={{maxWidth:520}}>
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:6}}>
          <h3 style={{margin:0}}>{title}</h3>
          <button onClick={onClose} style={{background:'transparent',border:'none',fontSize:18}}>✕</button>
        </div>
        <form onSubmit={submit} style={{display:'grid',gap:14}}>
          <div style={{display:'flex',gap:14}}>
            <label style={{flex:1,display:'flex',flexDirection:'column',gap:4}}>
              <span>Hours</span>
              <input type="number" min={0} value={hours} onChange={e=>setHours(e.target.value)} />
            </label>
            <label style={{flex:1,display:'flex',flexDirection:'column',gap:4}}>
              <span>Minutes</span>
              <input type="number" min={0} max={59} value={minutes} onChange={e=>setMinutes(e.target.value)} />
            </label>
          </div>
          {error && <div style={{color:'#b91c1c',fontSize:14}}>{error}</div>}
          <div style={{display:'flex',gap:10}}>
            <button type="submit" className="btn-primary" style={{flex:1}}>Save Goal</button>
            <button type="button" className="btn-ghost" onClick={onClose}>Cancel</button>
          </div>
        </form>
      </div>
    </div>
  )
}

function ChallengeRow({ challenge, currentUser }) {
  const [status, setStatus] = useState('checking') // checking | success | failed | no-data
  useEffect(() => {
    let mounted = true
    ;(async () => {
      try {
        const today = new Date().toISOString().slice(0,10)
        const res = await getDailyUsage(getUserId(currentUser), today)
        if (!mounted) return
        const usage = Array.isArray(res.usage) ? res.usage : []
        const app = challenge.criteria?.app || '__TOTAL__'
        const found = usage.find(u => u.app === app)
        const minutes = found ? found.minutes : 0
        const target = Number(challenge.criteria?.targetMinutes || 0)
        if (found) setStatus(minutes <= target ? 'success' : 'failed')
        else setStatus('no-data')
      } catch (err) {
        if (!mounted) return
        setStatus('no-data')
      }
    })()
    return () => { mounted = false }
  }, [challenge, currentUser])

  const statusColor = status === 'success' ? '#16a34a' : status === 'failed' ? '#dc2626' : '#6b7280'
  return (
    <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',padding:8,border:'1px solid #f1f5f9',borderRadius:8}}>
      <div>
        <div style={{fontWeight:600}}>{challenge.name}</div>
        <div style={{fontSize:13,color:'#666'}}>
          Target: {challenge.criteria?.app === '__TOTAL__' ? 'Total Screen Time' : challenge.criteria?.app} • {minutesLabel(challenge.criteria?.targetMinutes || 0)}
        </div>
      </div>
      <div style={{display:'flex',alignItems:'center',gap:10}}>
        <div style={{color:statusColor,fontWeight:600}}>{status === 'checking' ? 'Checking...' : status === 'no-data' ? 'No entry' : status === 'success' ? 'Success' : 'Failed'}</div>
      </div>
    </div>
  )
}

function ChallengeModal({ onClose, onCreate, currentUser }) {
  const [friends, setFriends] = useState([])
  const [showFindUsers, setShowFindUsers] = useState(false)
  const [allUsers, setAllUsers] = useState([])
  const [name, setName] = useState('')
  const [app, setApp] = useState('__TOTAL__')
  const [hours, setHours] = useState(0)
  const [minutes, setMinutes] = useState(30)
  const [selected, setSelected] = useState([])
  useEffect(() => {
    let mounted = true
    ;(async () => {
      try {
        if (!currentUser || !getUserId(currentUser)) {
          if (!mounted) return
          setFriends([])
          return
        }
        const res = await getFriends(getUserId(currentUser))
        if (!mounted) return
        let fetched = Array.isArray(res.friends) ? res.friends : []
        // Fallback: if empty, try getFriendIds and map to user objects via getAllUsers
        if (fetched.length === 0) {
          try {
            const idsRes = await getFriendIds(getUserId(currentUser))
            const ids = Array.isArray(idsRes.friendIds) ? idsRes.friendIds : []
            if (ids.length > 0) {
              const all = await getAllUsers(getUserId(currentUser))
              const users = Array.isArray(all.users) ? all.users : []
              fetched = users.filter(u => ids.includes(u.user_id))
            }
          } catch {
            // ignore
          }
        }
        // If still empty, seed two demo friendships for convenience (only for demo user)
        if (fetched.length === 0 && getUserId(currentUser)) {
          try {
            // avoid adding self or duplicates
            const seedTargets = ['u2','u3'].filter(id => id !== getUserId(currentUser))
            for (const t of seedTargets) {
              await addFriendship(getUserId(currentUser), t)
            }
            // refresh
            const refreshed = await getFriends(getUserId(currentUser))
            fetched = Array.isArray(refreshed.friends) ? refreshed.friends : []
          } catch {
            // ignore seeding errors
          }
        }
        setFriends(fetched)
      } catch {
        if (!mounted) return
        setFriends([])
      }
    })()
    return () => { mounted = false }
  }, [currentUser])

  async function fetchAllUsers() {
    try {
        if (!currentUser || !getUserId(currentUser)) { setAllUsers([]); return }
      const res = await getAllUsers(getUserId(currentUser))
      setAllUsers(Array.isArray(res.users) ? res.users : [])
    } catch {
      setAllUsers([])
    }
  }

  function toggle(id) {
    setSelected(s => s.includes(id) ? s.filter(x=>x!==id) : [...s, id])
  }

  async function addAsFriend(userToAdd) {
    try {
      if (!currentUser || !getUserId(currentUser)) return
      await addFriendship(getUserId(currentUser), userToAdd.user_id)
      // refresh friends list
      const res = await getFriends(getUserId(currentUser))
      setFriends(Array.isArray(res.friends) ? res.friends : [])
      // select the user for the challenge
      setSelected(s => s.includes(userToAdd.user_id) ? s : [...s, userToAdd.user_id])
    } catch {
      // ignore
    }
  }

  async function submit(e) {
    e.preventDefault()
    const total = (Number(hours)||0) * 60 + (Number(minutes)||0)
    if (!name) return
    if (!currentUser || !getUserId(currentUser)) return
    const payload = { owner: getUserId(currentUser), name, criteria: { app, targetMinutes: total }, members: selected }
    try {
      await addChallenge(payload)
      onCreate && onCreate()
      onClose()
    } catch (err) {
      onClose()
    }
  }

  return (
    <div className="modal-backdrop">
      <div className="modal" style={{maxWidth:520}}>
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
          <h3 style={{margin:0}}>Create Challenge</h3>
          <button onClick={onClose} style={{background:'transparent',border:'none',fontSize:18}}>✕</button>
        </div>
        <form onSubmit={submit} style={{display:'grid',gap:12,marginTop:8}}>
          <label style={{display:'flex',flexDirection:'column',gap:4}}>
            <span>Name</span>
            <input value={name} onChange={(e)=>setName(e.target.value)} />
          </label>
          <label style={{display:'flex',flexDirection:'column',gap:4}}>
            <span>Target App</span>
            <select value={app} onChange={e=>setApp(e.target.value)}>
              <option value="__TOTAL__">Total Screen Time</option>
              <option value="YouTube">YouTube</option>
              <option value="Instagram">Instagram</option>
              <option value="TikTok">TikTok</option>
              <option value="Safari">Safari</option>
              <option value="Messages">Messages</option>
            </select>
          </label>
          <div style={{display:'flex',gap:12}}>
            <label style={{flex:1,display:'flex',flexDirection:'column',gap:4}}>
              <span>Hours</span>
              <input type="number" min={0} value={hours} onChange={e=>setHours(e.target.value)} />
            </label>
            <label style={{flex:1,display:'flex',flexDirection:'column',gap:4}}>
              <span>Minutes</span>
              <input type="number" min={0} max={59} value={minutes} onChange={e=>setMinutes(e.target.value)} />
            </label>
          </div>
          <div>
            <div style={{fontSize:13,fontWeight:600,marginBottom:6}}>Invite Friends</div>
            {friends.length === 0 ? (
              <div style={{display:'flex',flexDirection:'column',gap:8}}>
                <div className="muted">You have no friends yet. Find users to add and invite them.</div>
                <div style={{display:'flex',gap:8}}>
                  <button type="button" className="btn-primary" onClick={async ()=>{ setShowFindUsers(true); await fetchAllUsers() }}>Find users</button>
                  <button type="button" className="btn-ghost" onClick={()=>setShowFindUsers(false)}>Cancel</button>
                </div>
                {showFindUsers && (
                  <div style={{display:'flex',flexWrap:'wrap',gap:8,marginTop:8}}>
                    {allUsers.map(u => (
                      <div key={u.user_id} style={{display:'flex',flexDirection:'column',gap:6}}>
                        <button type="button" className={'btn-ghost'} onClick={()=>addAsFriend(u)}>{u.username}</button>
                        <small style={{color:'#666'}}>Add friend & invite</small>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div style={{display:'flex',flexWrap:'wrap',gap:8}}>
                {friends.map(f => (
                  <button key={f.user_id} type="button" className={selected.includes(f.user_id)?'btn-primary':'btn-ghost'} onClick={()=>toggle(f.user_id)}>{f.username}</button>
                ))}
              </div>
            )}
          </div>
          <div style={{display:'flex',gap:8}}>
            <button className="btn-primary" type="submit" style={{flex:1}}>Create</button>
            <button type="button" className="btn-ghost" onClick={onClose}>Cancel</button>
          </div>
        </form>
      </div>
    </div>
  )
}
