import React, { useEffect, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import * as api from '../api/mockApi'
import { useNavigate } from 'react-router-dom'

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
    if (!user) nav('/signin')
  }, [user])

  function close() {
    setShow(false)
    setTimeout(() => nav('/dashboard'), 150)
  }

  async function onSubmit(e) {
    e.preventDefault()
    if (!user) return
    const totalMinutes = (Number(hours) || 0) * 60 + (Number(minutes) || 0)
    try {
      await api.addScreenTime({ user_id: user.user_id, date, minutes: totalMinutes, uploaded_image: appName || null })
      setMessage('Saved')
      setTimeout(close, 700)
    } catch (err) {
      setMessage(err?.message || 'Failed')
    }
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
          <label>
            App Name
            <input placeholder="e.g., YouTube, Instagram" value={appName} onChange={(e)=>setAppName(e.target.value)} />
          </label>

          <div style={{display:'flex',gap:12}}>
            <label style={{flex:1}}>
              Hours
              <input type="number" min={0} value={hours} onChange={(e)=>setHours(e.target.value)} />
            </label>
            <label style={{flex:1}}>
              Minutes
              <input type="number" min={0} max={59} value={minutes} onChange={(e)=>setMinutes(e.target.value)} />
            </label>
          </div>

          <div style={{display:'flex',gap:8,alignItems:'center'}}>
            <button className="btn-primary" type="submit" style={{flex:1}}>Save Entry</button>
            <button type="button" className="btn-ghost" onClick={close}>Cancel</button>
          </div>

          {message && <div style={{color:'#0b6'}}> {message} </div>}
        </form>
      </div>
    </div>
  )
}
