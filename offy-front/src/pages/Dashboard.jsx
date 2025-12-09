import React, { useMemo, useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { getScreenTimeEntries } from '../api/screenTimeApi'

// Helpers
function minutesLabel(mins) {
  const h = Math.floor(mins / 60)
  const m = Math.round(mins % 60)
  return `${h}h ${m}m`
}

/**
 * Show tooltip for chart bar segments with positioning relative to mouse cursor.
 * @param {MouseEvent} e - The mouse event from the bar segment
 * @param {string} day - Day of the week (e.g., "Mon", "Tue")
 * @param {string} label - Label to display (e.g., "Instagram", "Total")
 * @param {number} minutes - Time in minutes to display
 */
function showChartTooltip(e, day, label, minutes) {
  const tt = document.getElementById('chartTooltip')
  if (!tt) return
  tt.textContent = ''
  const strong = document.createElement('strong')
  strong.textContent = day
  const div = document.createElement('div')
  div.textContent = label + ': ' + minutesLabel(minutes)
  tt.appendChild(strong)
  tt.appendChild(div)
  tt.style.display = 'block'
  const svg = e.target.ownerSVGElement
  const svgRect = svg.getBoundingClientRect()
  tt.style.left = (e.clientX - svgRect.left + 8) + 'px'
  tt.style.top = (e.clientY - svgRect.top - 24) + 'px'
}

/**
 * Hide the chart tooltip.
 */
function hideChartTooltip() {
  const tt = document.getElementById('chartTooltip')
  if (tt) tt.style.display = 'none'
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
                      const appName = e.target.getAttribute('data-app')
                      const mins = Number(e.target.getAttribute('data-minutes'))
                      showChartTooltip(e, day, appName, mins)
                    }}
                    onMouseLeave={hideChartTooltip}
                  />
                )
              })}
              {/* 
                Gray remainder segment: Represents unassigned screen time.
                This is the difference between total screen time and the sum of individual app times.
                For example: 3h total with 1h Instagram logged = 2h gray remainder (unassigned).
                Hovering shows the total screen time for the day.
              */}
              {remainder > 0 && (()=>{
                const remH = (remainder / max) * (height - 30)
                const remY = yBase - yOffset - remH
                return (
                  <rect 
                    x={x + 14} 
                    y={remY} 
                    width={barW} 
                    height={remH} 
                    fill="#e2e8f0"
                    data-total={total}
                    onMouseEnter={(e) => showChartTooltip(e, day, 'Total', total)}
                    onMouseLeave={hideChartTooltip}
                  />
                )
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
                    onMouseEnter={(e) => showChartTooltip(e, day, 'Total', total)}
                    onMouseLeave={hideChartTooltip}
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
  const storageKey = (k) => `offy_${user?.user_id || 'anon'}_${k}`
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
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  /**
   * Fetch screen time logs from backend API on component mount or when user changes.
   * Retrieves the last 30 days of data to populate the dashboard and weekly chart.
   */
  useEffect(() => {
    if (!user) {
      setLogs([])
      setLoading(false)
      return
    }

    const fetchLogs = async () => {
      try {
        setLoading(true)
        setError(null)
        
        // Get logs for the last 30 days to have enough data for charts and metrics
        const endDate = new Date().toISOString().slice(0, 10)
        const startDate = new Date()
        startDate.setDate(startDate.getDate() - 30)
        const startDateStr = startDate.toISOString().slice(0, 10)
        
        // Fetch from backend API with date range filter
        const response = await getScreenTimeEntries({
          start_date: startDateStr,
          end_date: endDate,
          limit: 100
        })
        
        /**
         * Transform backend response format to match dashboard's expected format.
         * Backend returns: { app_name, date, screen_time_minutes }
         * Dashboard expects: { app, date, minutes }
         */
        const transformedLogs = response.logs.map(log => ({
          app: (log.app_name === 'Total' || !log.app_name) ? '__TOTAL__' : log.app_name,
          date: log.date,
          minutes: log.screen_time_minutes
        }))
        
        setLogs(transformedLogs)
      } catch (err) {
        console.error('Error fetching screen time logs:', err)
        setError(err.message || 'Failed to load screen time data')
        setLogs([])
      } finally {
        setLoading(false)
      }
    }

    fetchLogs()
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

  // Loading state: Show spinner while fetching data from backend API
  if (loading) {
    return (
      <main className="dashboard-main">
        <div style={{display:'flex',alignItems:'center',justifyContent:'center',minHeight:'60vh'}}>
          <div style={{textAlign:'center',color:'#666'}}>
            <div style={{fontSize:'24px',marginBottom:'8px'}}>⏳</div>
            <div>Loading your screen time data...</div>
          </div>
        </div>
      </main>
    )
  }

  // Error state: Show error message with retry button if API call fails
  if (error) {
    return (
      <main className="dashboard-main">
        <div style={{display:'flex',alignItems:'center',justifyContent:'center',minHeight:'60vh'}}>
          <div style={{textAlign:'center',padding:'24px',background:'#fee2e2',borderRadius:'12px',maxWidth:'500px'}}>
            <div style={{fontSize:'24px',marginBottom:'8px'}}>⚠️</div>
            <div style={{color:'#991b1b',fontWeight:'600',marginBottom:'8px'}}>Error loading data</div>
            <div style={{color:'#7f1d1d',fontSize:'14px'}}>{error}</div>
            <button 
              className="btn-primary" 
              onClick={() => window.location.reload()}
              style={{marginTop:'16px'}}
            >
              Retry
            </button>
          </div>
        </div>
      </main>
    )
  }

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
            <p className="muted" style={{margin:0}}>This feature is coming soon.</p>
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
