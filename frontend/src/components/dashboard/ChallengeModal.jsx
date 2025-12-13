import React, { useState, useEffect } from 'react'
import { getFriends, getFriendIds, getAllUsers, addFriendship, addChallenge } from '../../api/mockApi'

// Normalize user id from different possible shapes
function getUserId(u) {
  return u?.user_id ?? u?.id ?? u?.userId ?? u?.uid ?? null
}

export default function ChallengeModal({ onClose, onCreate, currentUser }) {
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
      if (!currentUser || !getUserId(currentUser)) { 
        setAllUsers([])
        return 
      }
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
    const payload = { 
      owner: getUserId(currentUser), 
      name, 
      criteria: { app, targetMinutes: total }, 
      members: selected 
    }
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
