import React, { useState, useEffect } from 'react'
import { friendshipApi } from '../../api/friendshipApi'
import { createChallenge } from '../../api/challengesApi'
import { getUserId } from '../../utils/challengeHelpers'

export default function ChallengeModal({ onClose, onCreate, currentUser }) {
  const [friends, setFriends] = useState([])
  const [name, setName] = useState('')
  const [app, setApp] = useState('__TOTAL__')
  const [hours, setHours] = useState(0)
  const [minutes, setMinutes] = useState(30)
  const [startDate, setStartDate] = useState(() => new Date().toISOString().slice(0, 10))
  const [endDate, setEndDate] = useState(() => {
    const future = new Date()
    future.setDate(future.getDate() + 7)
    return future.toISOString().slice(0, 10)
  })
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
        const data = await friendshipApi.list()
        if (!mounted) return
        // Extract accepted friends from the response
        const acceptedFriends = (data.friends || [])
          .map(f => f.counterpart)
          .filter(Boolean)
        setFriends(acceptedFriends)
      } catch (err) {
        console.error('Error fetching friends:', err)
        if (!mounted) return
        setFriends([])
      }
    })()
    return () => { mounted = false }
  }, [currentUser])

  function toggle(id) {
    setSelected(s => s.includes(id) ? s.filter(x=>x!==id) : [...s, id])
  }

  async function submit(e) {
    e.preventDefault()
    const total = (Number(hours)||0) * 60 + (Number(minutes)||0)
    if (!name.trim()) {
      alert('Challenge name is required')
      return
    }
    if (total < 0) {
      alert('Target time cannot be negative')
      return
    }
    if (!currentUser || !getUserId(currentUser)) return
    
    const payload = { 
      name: name.trim(), 
      target_app: app,
      target_minutes: total,
      start_date: startDate,
      end_date: endDate,
      invited_user_ids: selected.map(id => Number(id))
    }
    
    try {
      await createChallenge(payload)
      onCreate && onCreate()
      onClose()
    } catch (err) {
      console.error('Failed to create challenge:', err)
      alert(err.message || 'Failed to create challenge')
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
          <div style={{display:'flex',gap:12}}>
            <label style={{flex:1,display:'flex',flexDirection:'column',gap:4}}>
              <span>Start Date</span>
              <input type="date" value={startDate} onChange={e=>setStartDate(e.target.value)} />
            </label>
            <label style={{flex:1,display:'flex',flexDirection:'column',gap:4}}>
              <span>End Date</span>
              <input type="date" value={endDate} onChange={e=>setEndDate(e.target.value)} min={startDate} />
            </label>
          </div>
          <div>
            <div style={{fontSize:13,fontWeight:600,marginBottom:6}}>Invite Friends (Optional)</div>
            {friends.length === 0 ? (
              <div className="muted" style={{padding:8}}>
                No friends yet. Add friends from the Friends page to invite them to challenges.
              </div>
            ) : (
              <div style={{display:'flex',flexWrap:'wrap',gap:8}}>
                {friends.map(f => (
                  <button 
                    key={f.id} 
                    type="button" 
                    className={selected.includes(f.id) ? 'btn-primary' : 'btn-ghost'} 
                    onClick={() => toggle(f.id)}
                  >
                    {f.username}
                  </button>
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
