
import React, { useMemo, useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { getScreenTimeEntries } from '../api/screenTimeApi'
import { getChallenges } from '../api/mockApi'
import { minutesLabel } from '../utils/timeFormatters'
import ProgressBar from '../components/dashboard/ProgressBar'
import WeeklyChart from '../components/dashboard/WeeklyChart'
import GoalModal from '../components/dashboard/GoalModal'
import ChallengeRow from '../components/dashboard/ChallengeRow'
import ChallengeModal from '../components/dashboard/ChallengeModal'

// Helper to format a Date as YYYY-MM-DD
function formatDate(date) {
  return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`
}

// Normalize user id from different possible shapes
function getUserId(u) {
  return u?.user_id ?? u?.id ?? u?.userId ?? u?.uid ?? null
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
    const todayStr = formatDate(new Date())
    const groups = {}
    logs.filter(l => l.date === todayStr && l.app !== '__TOTAL__').forEach(l => {
      groups[l.app] = (groups[l.app]||0) + l.minutes
    })
    return Object.entries(groups).sort((a,b)=>b[1]-a[1]).map(([app, minutes])=>({app, minutes}))
  }, [logs])

  const topApps = todayApps

  const todayTotal = useMemo(()=>{
    const todayStr = formatDate(new Date())
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
  
  // Get current week (Sunday to Saturday)
  const today = new Date()
  const todayStr = formatDate(today)
  const currentDayOfWeek = today.getDay() // 0 = Sunday, 6 = Saturday
  
  // Generate all days of current week (Sun-Sat) - use local date to avoid timezone issues
  const currentWeekDays = Array.from({length:7}, (_,i)=>{
    const d = new Date(today.getFullYear(), today.getMonth(), today.getDate() - currentDayOfWeek + i)
    return {
      dateStr: formatDate(d),
      dayLabel: d.toLocaleDateString('en-US',{weekday:'short'})
    }
  })
  
  const chartData = {}
  currentWeekDays.forEach(({dateStr, dayLabel}) => {
    // Only show data for days up to and including today (not future days)
    if (dateStr > todayStr) return
    
    // build day entry
    const dayLogs = logs.filter(l => l.date === dateStr)
    if (!dayLogs.length) return
    const totalEntry = dayLogs.find(l => l.app === '__TOTAL__')
    const apps = {}
    dayLogs.filter(l => l.app !== '__TOTAL__').forEach(l => { apps[l.app] = (apps[l.app]||0) + l.minutes })
    let total = 0
    if (totalEntry) total = totalEntry.minutes
    else total = Object.values(apps).reduce((a,b)=>a+b,0)
    const stackedSum = Object.values(apps).reduce((a,b)=>a+b,0)
    const remainder = Math.max(0, total - stackedSum)
    chartData[dayLabel] = { apps, remainder, total }
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
        <button className="add-btn" aria-label={dailyGoal === undefined ? "Add daily limit" : "Edit daily limit"} title={dailyGoal === undefined ? "Add daily limit" : "Edit daily limit"} onClick={()=>setShowDailyModal(true)}>{dailyGoal === undefined ? '+' : '✏️'}</button>
            </div>
            {dailyGoal === undefined ? (
              <p className="muted small" style={{margin:0}}>Create a new limit by clicking +</p>
            ) : (
              <>
                <ProgressBar value={dailyUsed || 0} max={dailyGoal} color="#d97706" exceeded={dailyUsed > dailyGoal} />
                <div className="sub-row">
                  <span>{dailyUsed ? minutesLabel(dailyUsed) + ' used' : 'Log your hours'}</span>
                  <span>{minutesLabel(dailyGoal)} limit</span>
                </div>
              </>
            )}
          </div>
          <div className="metric-card" style={weeklyGoal !== undefined && weeklyUsed > weeklyGoal ? {backgroundColor: '#fee2e2'} : {}}>
            <div className="card-head">
              <span className="icon target" />
              <span className="title">Weekly Limit</span>
        <button className="add-btn" aria-label={weeklyGoal === undefined ? "Add weekly limit" : "Edit weekly limit"} title={weeklyGoal === undefined ? "Add weekly limit" : "Edit weekly limit"} onClick={()=>setShowWeeklyModal(true)}>{weeklyGoal === undefined ? '+' : '✏️'}</button>
            </div>
            {weeklyGoal === undefined ? (
              <p className="muted small" style={{margin:0}}>Create a new limit by clicking +</p>
            ) : (
              <>
                <ProgressBar value={weeklyUsed || 0} max={weeklyGoal} color="#16a34a" exceeded={weeklyUsed > weeklyGoal} />
                <div className="sub-row">
                  <span>{weeklyUsed ? minutesLabel(weeklyUsed) + ' used' : 'Log your hours'}</span>
                  <span>{minutesLabel(weeklyGoal)} limit</span>
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
                {todayTotal === undefined && (
                  <div className="usage-sub">Click on the +Log Hours button on the bottom right to log your hours</div>
                )}
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

          <div className="chart-card" style={{paddingLeft: '18px'}}>
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
          title={dailyGoal === undefined ? "Create your Daily Limit" : "Edit your Daily Limit"}
          initialMinutes={dailyGoal}
          onClose={()=>setShowDailyModal(false)}
          onSave={(mins)=>{ setDailyGoal(mins); localStorage.setItem(storageKey('daily_goal'), String(mins)); setShowDailyModal(false) }}
        />
      )}
      {showWeeklyModal && (
        <GoalModal
          title={weeklyGoal === undefined ? "Create your Weekly Limit" : "Edit your Weekly Limit"}
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