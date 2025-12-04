import React, { useEffect, useMemo, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import {
  getLeaderboard,
  getFriendIds,
  addFriendship,
  removeFriendship,
  minutesLabel,
  computeMonthlyStatsForUser,
} from '../api/mockApi'

export default function Friends(){
  const { user } = useAuth()
  const [allUsers, setAllUsers] = useState([])
  const [friendIds, setFriendIds] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  useEffect(()=>{
    let cancelled = false
    async function load(){
      setLoading(true)
      try{
        const { list } = await getLeaderboard()
        if (!cancelled) setAllUsers(list)
        const uid = user?.user_id || user?.id
        if (uid) {
          const res = await getFriendIds(uid)
          if (!cancelled) setFriendIds(res.friendIds || [])
        } else {
          if (!cancelled) setFriendIds([])
        }
      }catch(e){ console.error(e) }
      finally{ if(!cancelled) setLoading(false) }
    }
    load()
    return ()=>{ cancelled = true }
  }, [user])

  const friendSet = useMemo(()=> new Set(friendIds), [friendIds])

  const friends = useMemo(()=>{
    return allUsers.filter(u=> friendSet.has(u.user_id)).map(u=>{
      const stats = computeMonthlyStatsForUser(u.user_id)
      return { ...u, _avg: stats.avgPerDay, _streak: stats.streak }
    })
  }, [allUsers, friendSet])

  const available = useMemo(()=>{
    const q = search.trim().toLowerCase()
    return allUsers.filter(u=> u.user_id !== (user?.user_id || user?.id) && !friendSet.has(u.user_id) && (!q || u.username.toLowerCase().includes(q)))
  }, [allUsers, friendSet, search, user])

  async function handleAdd(id){
    const uid = user?.user_id || user?.id
    if (!uid) return
    try{
      await addFriendship(uid, id)
      setFriendIds(prev => Array.from(new Set([...prev, id])))
    }catch(e){ console.error('Add friend failed', e) }
  }

  async function handleRemove(id){
    const uid = user?.user_id || user?.id
    if (!uid) return
    try{
      await removeFriendship(uid, id)
      setFriendIds(prev => prev.filter(x=> x!==id))
    }catch(e){ console.error('Remove friend failed', e) }
  }

  return (
    <main className="friends-page">
      <h1 className="lb-title">Friends</h1>
      <div className="lb-card">
        <div style={{display:'flex',gap:12,alignItems:'center',justifyContent:'space-between',marginBottom:12}}>
          <div style={{fontSize:16,fontWeight:600}}>Your friends</div>
          <div style={{display:'flex',gap:8,alignItems:'center'}}>
            <input placeholder="Search to add" value={search} onChange={e=>setSearch(e.target.value)} style={{padding:8,borderRadius:8,border:'1px solid #ddd'}} />
          </div>
        </div>

        {loading && <div className="lb-loading">Loading...</div>}

        {!loading && friends.length===0 && (
          <div className="lb-empty">You have no friends yet. Add some below!</div>
        )}

        {!loading && friends.length>0 && (
          <div className="lb-table-wrapper">
            <table className="lb-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Avg. Screen Time</th>
                  <th>Streak</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {friends.map(u=> (
                  <tr key={u.user_id}>
                    <td>{u.username}</td>
                    <td>{u._avg!==undefined ? minutesLabel(u._avg) : '—'}</td>
                    <td>{(u._streak||0)} day streak</td>
                    <td><button className="btn-ghost" onClick={()=>handleRemove(u.user_id)}>Remove</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <hr style={{margin:'18px 0'}} />

        <div style={{fontSize:16,fontWeight:600,marginBottom:8}}>Add new friends</div>
        <div style={{display:'grid',gap:10,maxHeight:320,overflow:'auto'}}>
          {available.map(u=> (
            <div key={u.user_id} style={{display:'flex',alignItems:'center',justifyContent:'space-between',padding:'10px 12px',border:'1px solid #eee',borderRadius:10}}>
              <div style={{display:'flex',alignItems:'center',gap:10}}>
                <div className="avatar small"><span className="initials">{u.username?.[0]?.toUpperCase()||'?'}</span></div>
                <div>
                  <div style={{fontWeight:600}}>{u.username}</div>
                  <div className="muted" style={{fontSize:12}}>{u.email || ''}</div>
                </div>
              </div>
              <button className="btn-primary" onClick={()=>handleAdd(u.user_id)}>Add</button>
            </div>
          ))}
          {!available.length && <div className="muted" style={{fontSize:14}}>No users match that search.</div>}
        </div>
      </div>
    </main>
  )
}
