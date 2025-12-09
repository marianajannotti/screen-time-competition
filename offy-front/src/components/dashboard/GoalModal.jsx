/**
 * GoalModal component for creating/editing daily or weekly screen time goals.
 */

import { useState } from 'react'

/**
 * A modal dialog for setting screen time goals in hours and minutes.
 * 
 * @param {Object} props
 * @param {string} props.title - Modal title (e.g., "Create Daily Limit")
 * @param {number} props.initialMinutes - Initial value in total minutes
 * @param {Function} props.onClose - Callback when modal is closed
 * @param {Function} props.onSave - Callback with total minutes when saved
 */
export default function GoalModal({ title, initialMinutes, onClose, onSave }) {
  const initH = initialMinutes ? Math.floor(initialMinutes / 60) : 0
  const initM = initialMinutes ? initialMinutes % 60 : 0
  const [hours, setHours] = useState(initH)
  const [minutes, setMinutes] = useState(initM)
  const [error, setError] = useState(null)

  function submit(e) {
    e.preventDefault()
    const h = Number(hours) || 0
    const m = Number(minutes) || 0
    if (m >= 60) { 
      setError('Minutes must be < 60')
      return 
    }
    const total = h * 60 + m
    if (total <= 0) { 
      setError('Goal must be greater than 0')
      return 
    }
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
