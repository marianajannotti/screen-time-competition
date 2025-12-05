import React, { useEffect, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { addScreenTime as apiAddScreenTime, getMonthlyLogs, saveMonthlyLogs, getChallenges } from '../api/mockApi'

// normalize user id shape
function getUserId(u) {
  return u?.user_id ?? u?.id ?? u?.userId ?? u?.uid ?? null
}
import { useNavigate } from 'react-router-dom'

export default function AddScreenTime() {
  const { user } = useAuth()
  const [show, setShow] = useState(true)
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10))
  const [hours, setHours] = useState(0)
  const [minutes, setMinutes] = useState(15)
  const [appName, setAppName] = useState('')
  const [message, setMessage] = useState(null)
  const [pendingMinutes, setPendingMinutes] = useState(null)
  const [dupTarget, setDupTarget] = useState(null) // { app, date }
  const [challenges, setChallenges] = useState([])
  const [challengeId, setChallengeId] = useState('')
  const nav = useNavigate()

  useEffect(() => {
    if (!user || !getUserId(user)) nav('/signin')
  }, [user, nav])

  // fetch user's challenges so they can optionally tag an entry
  useEffect(() => {
    let mounted = true
    if (!user || !getUserId(user)) { setChallenges([]); return }
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

  function close() {
    setShow(false)
    setTimeout(() => nav('/dashboard'), 150)
  }

  async function onSubmit(e) {
    e.preventDefault()
    const uid = getUserId(user)
    if (!uid) return
    // Guard against future dates (should be impossible with max constraint but double-check)
    const todayStr = new Date().toISOString().slice(0,10)
    if (date > todayStr) {
      setMessage('Date cannot be in the future')
      return
    }
    const totalMinutes = (Number(hours) || 0) * 60 + (Number(minutes) || 0)
    // Use mock API helpers for monthly logs (keeps leaderboard utilities consistent)
    const { logs: existing } = await getMonthlyLogs(uid)
    const targetApp = appName || '__TOTAL__'
    const dupIndex = existing.findIndex((l) => l.date === date && l.app === targetApp)
    if (dupIndex !== -1) {
      setDupTarget({ app: targetApp, date })
      setPendingMinutes(totalMinutes)
      return
    }
    // Save new entry to monthly logs and also add a screenTime log entry
    existing.push({ app: targetApp, date, minutes: totalMinutes })
    await saveMonthlyLogs(uid, existing)
    try {
      // include challenge_id if selected so entries can be traced to challenges
      const payload = { user_id: uid, date, minutes: totalMinutes }
      if (challengeId) payload.challenge_id = challengeId
      await apiAddScreenTime(payload)
    } catch (err) {
      // non-fatal for monthly logging; ignore
    }
    setMessage('Saved')
    setTimeout(close, 700)
  }

  async function resolveDuplicate(replace) {
    const uid = getUserId(user)
    if (!dupTarget || !uid) return
    if (replace) {
      const { logs: arr } = await getMonthlyLogs(uid)
      const idx = arr.findIndex((l) => l.date === dupTarget.date && l.app === dupTarget.app)
      if (idx !== -1) {
        arr[idx].minutes = pendingMinutes
        await saveMonthlyLogs(uid, arr)
        try {
          const payload = { user_id: uid, date: dupTarget.date, minutes: pendingMinutes }
          if (challengeId) payload.challenge_id = challengeId
          await apiAddScreenTime(payload)
        } catch (err) {
          // ignore
        }
      }
    }
    setDupTarget(null)
    setPendingMinutes(null)
    setMessage(replace ? 'Updated' : 'Kept previous')
    setTimeout(close, 700)
  }

  if (!show) return null

  return (
    <div className="modal-backdrop">
      <div className="modal">
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
          <h3 style={{margin:0}}>Log Your Screen Time</h3>
          <button onClick={close} style={{background:'transparent',border:'none',fontSize:18}}>✕</button>
        </div>

        <p className="muted">Record your daily screen time by category</p>

        <form onSubmit={onSubmit} style={{display:'grid',gap:12,marginTop:8}}>
          <label style={{display:'flex',flexDirection:'column',gap:4}}>
            <span>Date</span>
            <input
              type="date"
              value={date}
              max={new Date().toISOString().slice(0,10)}
              onChange={(e)=>setDate(e.target.value)}
              style={{paddingLeft:18}}
            />
          </label>
          <label style={{display:'flex',flexDirection:'column',gap:4}}>
            <span>App Name</span>
            <select value={appName} onChange={(e)=>setAppName(e.target.value)} style={{paddingLeft:18}}>
              <option value="">Total Screen Time</option>
              <option value="YouTube">YouTube</option>
              <option value="Instagram">Instagram</option>
              <option value="TikTok">TikTok</option>
              <option value="Safari">Safari</option>
              <option value="Messages">Messages</option>
            </select>
            <small className="muted" style={{marginTop:2}}>If you want to log your total screen time, choose that option</small>
          </label>

          {challenges.length > 0 && (
            <label style={{display:'flex',flexDirection:'column',gap:4}}>
              <span>Apply to Challenge (optional)</span>
              <select value={challengeId} onChange={e=>setChallengeId(e.target.value)} style={{paddingLeft:18}}>
                <option value="">(None)</option>
                {challenges.map(c=> (
                  <option key={c.challenge_id} value={c.challenge_id}>{c.name}</option>
                ))}
              </select>
              <small className="muted" style={{marginTop:2}}>Optionally tag this entry as part of one of your challenges</small>
            </label>
          )}

          <div style={{display:'flex',gap:12}}>
            <label style={{flex:1,display:'flex',flexDirection:'column',gap:4}}>
              <span>Hours</span>
              <input type="number" min={0} value={hours} onChange={(e)=>setHours(e.target.value)} style={{paddingLeft:18}} />
            </label>
            <label style={{flex:1,display:'flex',flexDirection:'column',gap:4}}>
              <span>Minutes</span>
              <input type="number" min={0} max={59} value={minutes} onChange={(e)=>setMinutes(e.target.value)} style={{paddingLeft:18}} />
            </label>
          </div>

          <div style={{display:'flex',gap:8,alignItems:'center'}}>
            <button className="btn-primary" type="submit" style={{flex:1}}>Save Entry</button>
            <button type="button" className="btn-ghost" onClick={close}>Cancel</button>
          </div>

          {message && <div style={{color:'#0b6'}}> {message} </div>}
        </form>
        {dupTarget && (
          <div className="modal" style={{marginTop:20,background:'#fffbe6'}}>
            <h4 style={{margin:'0 0 8px'}}>Entry already exists</h4>
            <p style={{margin:'0 0 12px',fontSize:14}}>You already logged {dupTarget.app === '__TOTAL__' ? 'Total Screen Time' : dupTarget.app} for {dupTarget.date}. Replace previous value or keep existing?</p>
            <div style={{display:'flex',gap:10}}>
              <button type="button" className="btn-primary" onClick={()=>resolveDuplicate(true)}>Replace</button>
              <button type="button" className="btn-ghost" onClick={()=>resolveDuplicate(false)}>Keep Previous</button>
              <button type="button" className="btn-ghost" onClick={()=>{ setDupTarget(null); setPendingMinutes(null); }}>Cancel</button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
