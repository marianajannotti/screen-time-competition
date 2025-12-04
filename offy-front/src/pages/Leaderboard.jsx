import React, { useEffect, useMemo, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import {
  getLeaderboard,
  minutesLabel,
  computeMonthlyStatsForUser,
  seedMonthlyMockData,
  resetAllMockData,
  getFriendIds,
  addFriendship,
} from '../api/mockApi'

export default function Leaderboard(){
  const { user } = useAuth()
  const [tab, setTab] = useState('friends') // 'friends' | 'global'
  const [globalUsers, setGlobalUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [search, setSearch] = useState('')
  // Auto-seed on first load if needed
  useEffect(()=>{ seedMonthlyMockData() },[])
  const [friends, setFriends] = useState([])

  useEffect(()=>{
    let cancelled = false
    async function loadFriends(){
      if (!user) { setFriends([]); return }
        try{
          const uid = user.user_id || user.id
          const res = await getFriendIds(uid)
        if (!cancelled) setFriends(res.friendIds || [])
      }catch(e){ console.error(e) }
    }
    loadFriends()
    return ()=>{ cancelled = true }
  }, [user])

  // Close modal on Escape key when open
  useEffect(()=>{
    if (!showModal) return
    const onKey = (e) => {
      if (e.key === 'Escape') setShowModal(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [showModal])

  useEffect(()=>{
    let cancelled=false
    async function load(){
      setLoading(true)
      try {
        const { list } = await getLeaderboard()
        if (!cancelled) setGlobalUsers(list)
      } catch(e){ console.error(e) }
      finally{ if(!cancelled) setLoading(false) }
    }
    load()
    return ()=>{ cancelled=true }
  }, [])

  // Build monthly stats and rank by least average (lower is better). Tiebreak: longer streak wins.
  const rankedGlobal = useMemo(()=>{
    const withStats = globalUsers.map(u=>{
      const stats = computeMonthlyStatsForUser(u.user_id)
      return { ...u, _avg: stats.avgPerDay, _streak: stats.streak }
    })
    return withStats.sort((a,b)=>{
      const aHas = a._avg !== undefined
      const bHas = b._avg !== undefined
      if (aHas && bHas){
        if (a._avg === b._avg) return (b._streak||0) - (a._streak||0)
        return a._avg - b._avg
      }
      if (aHas) return -1
      if (bHas) return 1
      // both undefined: tie-break by username
      return (a.username||'').localeCompare(b.username||'')
    })
  },[globalUsers])
  const friendUserSet = useMemo(()=> new Set(friends), [friends])
  const rankedFriends = useMemo(()=> rankedGlobal.filter(u=>friendUserSet.has(u.user_id)), [rankedGlobal, friendUserSet])

  function addFriend(id){
    if(friendUserSet.has(id) || !user) return
    const uid = user.user_id || user.id
    addFriendship(uid, id).then(()=>{
      const next = [...friends, id]
      setFriends(next)
    }).catch((e)=>{
      console.error('Failed to add friend', e)
    })
  }

  const list = tab==='friends' ? rankedFriends : rankedGlobal
  const podium = list.slice(0,3)
  const remainder = list.slice(3)
  const filteredAddable = useMemo(()=>{
    const q = search.trim().toLowerCase()
    return rankedGlobal.filter(u=>u.user_id!==user?.user_id && !friendUserSet.has(u.user_id) && (!q || u.username.toLowerCase().includes(q)))
  }, [search, rankedGlobal, friendUserSet, user])

  return (
    <main className="leaderboard-page">
      <h1 className="lb-title">Monthly Leaderboard</h1>
      <div className="lb-card">
        <div className="lb-tabs">
          <button className={tab==='friends'? 'active': ''} onClick={()=>setTab('friends')}>Friends</button>
          <button className={tab==='global'? 'active': ''} onClick={()=>setTab('global')}>Global</button>
        </div>
        {loading && <div className="lb-loading">Loading...</div>}
        {!loading && tab==='friends' && rankedFriends.length===0 && (
          <div className="lb-empty">Add friends to see them in the leaderboard!</div>
        )}
        <div className="lb-podium refined">
          {['second','first','third'].map((pos) => {
            const rankMap = { first:0, second:1, third:2 }
            const dataIndex = rankMap[pos]
            const p = podium[dataIndex]
            return (
              <div key={pos} className={`podium-col ${pos}`}> 
                <div className={`podium-block ${pos}`}> 
                  <div className="rank-badge">{pos==='first'?1:pos==='second'?2:3}</div>
                  <div className="avatar tiny"><span className="initials">{p?.username?.[0]?.toUpperCase() || (p ? '?' : pos[0].toUpperCase())}</span></div>
                  <div className="name">{p? p.username : pos.charAt(0).toUpperCase()+pos.slice(1)}</div>
                  <div className="metric">{p? (p._avg!==undefined ? minutesLabel(p._avg) : '—') : '—'}</div>
                  {pos==='first' && <div className="crown" aria-hidden="true">👑</div>}
                </div>
              </div>
            )
          })}
        </div>
        {!loading && list.length>0 && (
          <div className="lb-table-wrapper">
            <table className="lb-table">
              <thead>
                <tr>
                  <th scope="col" className="rank">Rank</th>
                  <th scope="col" className="name">Name</th>
                  <th scope="col" className="metric">Avg. Screen Time</th>
                  <th scope="col" className="streak">Streak</th>
                </tr>
              </thead>
              <tbody>
                {remainder.map((u,idx)=>{
                  const rank = idx + 4
                  const isSelf = u.user_id === user?.user_id
                  return (
                    <tr key={u.user_id} className={isSelf? 'self':''}>
                      <td className="rank">{rank}</td>
                      <td className="name">{isSelf? 'You' : u.username}</td>
                      <td className="metric">{u._avg!==undefined ? minutesLabel(u._avg) : '—'}</td>
                      <td className="streak">{(u._streak||0)} day streak</td>
                    </tr>
                  )
                })}
                {remainder.length===0 && podium.length<3 && (
                  <tr><td colSpan={4} className="muted" style={{textAlign:'center'}}>Not enough data yet.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
        <div className="lb-actions">
          <button className="add-btn" onClick={()=>setShowModal(true)}>Add More Friends</button>
        </div>
      </div>
      {showModal && (
        <div className="modal-backdrop" style={{zIndex:70}} onClick={(e)=>{ if (e.target === e.currentTarget) setShowModal(false) }}>
          <div
            className="modal"
            style={{maxWidth:520}}
            role="dialog"
            aria-modal="true"
            aria-labelledby="add-friends-modal-title"
          >
            <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:10}}>
              <h3 id="add-friends-modal-title" style={{margin:0}}>Add Friends</h3>
              <button aria-label="Close modal" onClick={()=>setShowModal(false)} style={{background:'transparent',border:'none',fontSize:18}}>✕</button>
            </div>
            <input type="text" placeholder="Search username" aria-label="Search username" value={search} onChange={e=>setSearch(e.target.value)} />
            <div style={{marginTop:14,maxHeight:300,overflow:'auto',display:'grid',gap:10}}>
              {filteredAddable.map(u=> (
                <div key={u.user_id} style={{display:'flex',alignItems:'center',justifyContent:'space-between',padding:'10px 12px',border:'1px solid #eee',borderRadius:10}}>
                  <div style={{display:'flex',alignItems:'center',gap:10}}>
                    <div className="avatar small"><span className="initials">{u.username?.[0]?.toUpperCase()||'?'}</span></div>
                    <span>{u.username}</span>
                  </div>
                  <button className="btn-primary" onClick={()=>addFriend(u.user_id)}>Add</button>
                </div>
              ))}
              {!filteredAddable.length && <div className="muted" style={{fontSize:14}}>No users match that search.</div>}
            </div>
          </div>
        </div>
      )}
      <div style={{display:'flex',justifyContent:'center',marginTop:14}}>
        <button className="btn-ghost" onClick={()=>{resetAllMockData(); seedMonthlyMockData(); window.location.reload()}}>Reset Mock Data</button>
      </div>
    </main>
  )
}
