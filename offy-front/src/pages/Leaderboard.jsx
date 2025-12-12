import React, { useEffect, useMemo, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { minutesLabel } from '../utils/timeFormatters'
import { getGlobalLeaderboard, getFriendships } from '../api/leaderboardApi'

export default function Leaderboard(){
  const { user } = useAuth()
  // Normalize user id from different possible shapes
  function getUserId(u) {
    return u?.user_id ?? u?.id ?? u?.userId ?? u?.uid ?? null
  }
  
  // Get current user's ID for comparisons
  const currentUserId = getUserId(user)
  
  // Core UI state: tab selection, data, loading/error, modal controls, and search text.
  const [tab, setTab] = useState('friends') // 'friends' | 'global'
  const [globalUsers, setGlobalUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [search, setSearch] = useState('')
  const [friendships, setFriendships] = useState({ friends: [], incoming: [], outgoing: [] })
  const [error, setError] = useState(null)

  // Fetch friendships (accepted/pending) from backend
  useEffect(()=>{
    let cancelled = false
    async function loadFriendships(){
      if (!user) { setFriendships({ friends: [], incoming: [], outgoing: [] }); return }
      setError(null)
      try {
        const res = await getFriendships()
        if (!cancelled) setFriendships(res)
      } catch (e) {
        console.error(e)
        if (!cancelled) setError(e.message)
      }
    }
    loadFriendships()
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

  // Fetch global leaderboard from backend
  useEffect(()=>{
    let cancelled=false
    async function load(){
      setLoading(true)
      setError(null)
      try {
        const data = await getGlobalLeaderboard()
        if (!cancelled) setGlobalUsers(data)
      } catch(e){
        console.error(e)
        if (!cancelled) setError(e.message)
      }
      finally{ if(!cancelled) setLoading(false) }
    }
    load()
    return ()=>{ cancelled=true }
  }, [])

  const rankedGlobal = useMemo(()=>{
    // Backend already returns sorted list; keep order but normalize metrics for display
    return (globalUsers || []).map((u, idx)=> ({
      ...u,
      _rank: u.rank || idx + 1,
      _avg: u.avg_per_day,
      _streak: u.streak,
    }))
  },[globalUsers])

  // Pull accepted friends (counterparts) and track which friend IDs are surfaced in the tab.
  const acceptedFriends = useMemo(()=> (friendships?.friends || []).map(f=> f.counterpart).filter(Boolean), [friendships])
  const [visibleFriendIds, setVisibleFriendIds] = useState(new Set())

  // Friends tab shows only IDs explicitly added (plus current user auto-included below).
  const rankedFriends = useMemo(()=> rankedGlobal.filter(u=>visibleFriendIds.has(u.user_id)), [rankedGlobal, visibleFriendIds])

  // Ensure the current user always appears in the Friends tab
  useEffect(()=>{
    if (!currentUserId) return
    setVisibleFriendIds(prev => {
      const next = new Set(prev)
      next.add(currentUserId)
      return next
    })
  }, [currentUserId])

  // Add a friend ID to the Friends tab display list (from modal selection).
  function addVisibleFriend(id){
    setVisibleFriendIds(prev => {
      const next = new Set(prev)
      next.add(id)
      return next
    })
  }

  const list = tab==='friends' ? rankedFriends : rankedGlobal
  const podium = list.slice(0,3)
  const remainder = list.slice(3)
  // Modal list: accepted friends not yet shown; supports simple case-insensitive search.
  const filteredAddable = useMemo(()=>{
    const q = search.trim().toLowerCase()
    return acceptedFriends.filter(u => !visibleFriendIds.has(u.id || u.user_id)).filter(u => !q || (u.username||'').toLowerCase().includes(q))
  }, [search, acceptedFriends, visibleFriendIds])

  return (
    <main className="leaderboard-page">
      <h1 className="lb-title">Monthly Leaderboard</h1>
      <div className="lb-card">
        <div className="lb-tabs">
          <button className={tab==='friends'? 'active': ''} onClick={()=>setTab('friends')}>Friends</button>
          <button className={tab==='global'? 'active': ''} onClick={()=>setTab('global')}>Global</button>
        </div>
        {error && <div className="error-banner" style={{marginBottom:8}}>{error}</div>}
        {loading && <div className="lb-loading">Loading...</div>}
        {!loading && tab==='friends' && rankedFriends.length===0 && (
          <div className="lb-empty">Use “Add More Friends” to place friends into the leaderboard.</div>
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
                  <div className="name">{p ? (p.user_id === currentUserId ? `You (${p.username})` : p.username) : pos.charAt(0).toUpperCase()+pos.slice(1)}</div>
                  <div className="metric">{p? minutesLabel(p._avg) : '—'}</div>
                  <div className="streak" style={{fontSize:12, color:'#fff', opacity:0.8}}>{p ? `${p._streak || 0} day streak` : '—'}</div>
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
                  const rank = tab === 'friends' ? (idx + 4) : (u._rank || (idx + 4))
                  const isSelf = u.user_id === currentUserId
                  const displayName = isSelf ? `You (${u.username})` : u.username
                  return (
                    <tr key={u.user_id} className={isSelf? 'self':''}>
                      <td className="rank">{rank}</td>
                      <td className="name">{displayName}</td>
                      <td className="metric">{minutesLabel(u._avg)}</td>
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
        {tab === 'friends' && (
          <div className="lb-actions">
            <button className="add-btn" onClick={()=>setShowModal(true)}>Add More Friends</button>
          </div>
        )}
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
              <h3 id="add-friends-modal-title" style={{margin:0}}>Add Friends to Leaderboard</h3>
              <button aria-label="Close modal" onClick={()=>setShowModal(false)} style={{background:'transparent',border:'none',fontSize:18}}>✕</button>
            </div>
            <input type="text" placeholder="Search friends" aria-label="Search friends" value={search} onChange={e=>setSearch(e.target.value)} />
            <div style={{marginTop:14,maxHeight:300,overflow:'auto',display:'grid',gap:10}}>
              {filteredAddable.map(u=> {
                const uid = u.id || u.user_id
                const already = visibleFriendIds.has(uid)
                return (
                  <div key={uid} style={{display:'flex',alignItems:'center',justifyContent:'space-between',padding:'10px 12px',border:'1px solid #eee',borderRadius:10}}>
                    <div style={{display:'flex',alignItems:'center',gap:10}}>
                      <div className="avatar small"><span className="initials">{u.username?.[0]?.toUpperCase()||'?'}</span></div>
                      <span>{u.username}</span>
                    </div>
                    <button className="btn-primary" onClick={()=>addVisibleFriend(uid)} disabled={already}>{already ? 'Added' : 'Add'}</button>
                  </div>
                )
              })}
              {!filteredAddable.length && <div className="muted" style={{fontSize:14}}>No friends to add.</div>}
            </div>
          </div>
        </div>
      )}
    </main>
  )
}
