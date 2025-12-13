import React, { useEffect, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useNavigate } from 'react-router-dom'
import { addScreenTimeEntry } from '../api/screenTimeApi'

// normalize user id shape
function getUserId(u) {
  return u?.user_id ?? u?.id ?? u?.userId ?? u?.uid ?? null
}

export default function AddScreenTime() {
  const { user } = useAuth()
  const [show, setShow] = useState(true)
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10))
  const [hours, setHours] = useState(0)
  const [minutes, setMinutes] = useState(15)
  const [appName, setAppName] = useState('')
  const [message, setMessage] = useState(null)
  const nav = useNavigate()

  useEffect(() => {
    if (!user || !getUserId(user)) nav('/signin')
  }, [user, nav])

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
    
    if (totalMinutes <= 0) {
      setMessage('Screen time must be greater than 0 minutes')
      return
    }
    
    try {
      // Send to backend API - backend expects hours and minutes separately
      const data = {
        date: date,
        hours: Number(hours) || 0,
        minutes: Number(minutes) || 0,
      }
      
      // Only include app_name if it's not the total screen time option
      if (appName) {
        data.app_name = appName
      }
      
      await addScreenTimeEntry(data)
      
      setMessage('Saved successfully!')
      setTimeout(close, 700)
    } catch (error) {
      console.error('Error saving screen time:', error)
      setMessage(error.message || 'Failed to save entry')
    }
  }

  // Note: Backend automatically updates existing entries for the same app/date

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

          {message && (
            <div style={{
              color: message.includes('Failed') || message.includes('cannot') || message.includes('must be greater') ? '#c33' : '#0b6',
              marginTop: 8
            }}>
              {message}
            </div>
          )}
        </form>
      </div>
    </div>
  )
}