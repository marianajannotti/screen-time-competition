import React, { useEffect, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
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
  const nav = useNavigate()

  useEffect(() => {
    if (!user) nav('/signin')
  }, [user, nav])

  function close() {
    setShow(false)
    setTimeout(() => nav('/dashboard'), 150)
  }

  async function onSubmit(e) {
    e.preventDefault()
    if (!user) return
    // Guard against future dates (should be impossible with max constraint but double-check)
    const todayStr = new Date().toISOString().slice(0,10)
    if (date > todayStr) {
      setMessage('Date cannot be in the future')
      return
    }
    const totalMinutes = (Number(hours) || 0) * 60 + (Number(minutes) || 0)
    // Duplicate detection (localStorage based for FE testing)
    const storageKey = `offy_logs_${user.user_id}`
    const existingRaw = localStorage.getItem(storageKey)
    const existing = existingRaw ? JSON.parse(existingRaw) : []
    const targetApp = appName || '__TOTAL__'
    const dupIndex = existing.findIndex(l => l.date === date && l.app === targetApp)
    if (dupIndex !== -1) {
      setDupTarget({ app: targetApp, date })
      setPendingMinutes(totalMinutes)
      return
    }
    // Save new entry
    existing.push({ app: targetApp, date, minutes: totalMinutes })
    localStorage.setItem(storageKey, JSON.stringify(existing))
    setMessage('Saved')
    setTimeout(close, 700)
  }

  function resolveDuplicate(replace) {
    if (!dupTarget) return
    if (replace) {
      const storageKey = `offy_logs_${user.user_id}`
      const existingRaw = localStorage.getItem(storageKey)
      const arr = existingRaw ? JSON.parse(existingRaw) : []
      const idx = arr.findIndex(l => l.date === dupTarget.date && l.app === dupTarget.app)
      if (idx !== -1) {
        arr[idx].minutes = pendingMinutes
        localStorage.setItem(storageKey, JSON.stringify(arr))
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
