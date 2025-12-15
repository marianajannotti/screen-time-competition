import React, { useState, useEffect, useMemo } from 'react'
import { friendshipApi } from '../../api/friendshipApi'
import { updateChallenge } from '../../api/challengesApi'
import { getUserId } from '../../utils/challengeHelpers'

export default function EditChallengeModal({ challenge, currentUser, onClose, onUpdate, existingParticipants = [] }) {
  const [friends, setFriends] = useState([])
  const [name, setName] = useState(challenge.name || '')
  const [selected, setSelected] = useState([])
  
  // Memoize existing participant IDs to prevent unnecessary re-renders
  const existingParticipantIds = useMemo(() => 
    new Set(existingParticipants.map(p => p.user_id || getUserId(p)).filter(Boolean)),
    [existingParticipants]
  )
  
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
        // Extract accepted friends who are not already participants
        const acceptedFriends = (data.friends || [])
          .map(f => f.counterpart)
          .filter(Boolean)
          .filter(friend => !existingParticipantIds.has(getUserId(friend)))
        
        setFriends(acceptedFriends)
      } catch (err) {
        console.error('Error fetching friends:', err)
        if (!mounted) return
        setFriends([])
      }
    })()
    return () => { mounted = false }
  }, [currentUser, existingParticipantIds])

  function toggle(id) {
    setSelected(s => s.includes(id) ? s.filter(x=>x!==id) : [...s, id])
  }

  async function submit(e) {
    e.preventDefault()
    
    const trimmedName = name.trim()
    if (!trimmedName) {
      alert('Challenge name is required')
      return
    }
    
    if (!currentUser || !getUserId(currentUser)) return
    
    const payload = {}
    
    // Only include name if it changed
    if (trimmedName !== challenge.name) {
      payload.name = trimmedName
    }
    
    // Only include invited users if any selected
    if (selected.length > 0) {
      payload.invited_user_ids = selected.map(id => Number(id))
    }
    
    // Don't send empty payload
    if (Object.keys(payload).length === 0) {
      alert('No changes to save')
      return
    }
    
    try {
      await updateChallenge(challenge.challenge_id, payload)
      onUpdate && onUpdate()
      onClose()
    } catch (err) {
      console.error('Failed to update challenge:', err)
      alert(err.message || 'Failed to update challenge')
    }
  }

  return (
    <div className="modal-backdrop">
      <div className="modal" style={{maxWidth:520}}>
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
          <h3 style={{margin:0}}>Edit Challenge</h3>
          <button onClick={onClose} style={{background:'transparent',border:'none',fontSize:18}}>✕</button>
        </div>
        <form onSubmit={submit} style={{display:'grid',gap:12,marginTop:8}}>
          <label style={{display:'flex',flexDirection:'column',gap:4}}>
            <span>Name</span>
            <input value={name} onChange={(e)=>setName(e.target.value)} />
          </label>
          
          <div>
            <label style={{display:'block',marginBottom:8}}>Invite More Friends</label>
            {friends.length === 0 ? (
              <p className="muted" style={{fontSize:13,margin:'8px 0'}}>All your friends are already in this challenge or you have no friends to invite.</p>
            ) : (
              <div style={{display:'flex',flexWrap:'wrap',gap:8}}>
                {friends.map(f => (
                  <button 
                    key={getUserId(f)} 
                    type="button" 
                    className={selected.includes(getUserId(f)) ? 'btn-primary' : 'btn-ghost'} 
                    onClick={() => toggle(getUserId(f))}
                  >
                    {f.username}
                  </button>
                ))}
              </div>
            )}
          </div>
          
          <div style={{display:'flex',gap:8}}>
            <button className="btn-primary" type="submit" style={{flex:1}}>Save Changes</button>
            <button type="button" className="btn-ghost" onClick={onClose}>Cancel</button>
          </div>
        </form>
      </div>
    </div>
  )
}
