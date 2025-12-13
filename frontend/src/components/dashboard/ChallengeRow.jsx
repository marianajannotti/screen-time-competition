import React, { useState, useEffect } from 'react'
import { getDailyUsage } from '../../api/mockApi'
import { minutesLabel } from '../../utils/timeFormatters'

// Normalize user id from different possible shapes
function getUserId(u) {
  return u?.user_id ?? u?.id ?? u?.userId ?? u?.uid ?? null
}

export default function ChallengeRow({ challenge, currentUser }) {
  const [status, setStatus] = useState('checking') // checking | success | failed | no-data
  
  useEffect(() => {
    let mounted = true
    ;(async () => {
      try {
        const today = new Date().toISOString().slice(0,10)
        const res = await getDailyUsage(getUserId(currentUser), today)
        if (!mounted) return
        const usage = Array.isArray(res.usage) ? res.usage : []
        const app = challenge.criteria?.app || '__TOTAL__'
        const found = usage.find(u => u.app === app)
        const minutes = found ? found.minutes : 0
        const target = Number(challenge.criteria?.targetMinutes || 0)
        if (found) setStatus(minutes <= target ? 'success' : 'failed')
        else setStatus('no-data')
      } catch (err) {
        if (!mounted) return
        setStatus('no-data')
      }
    })()
    return () => { mounted = false }
  }, [challenge, currentUser])

  const statusColor = status === 'success' ? '#16a34a' : status === 'failed' ? '#dc2626' : '#6b7280'
  
  return (
    <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',padding:8,border:'1px solid #f1f5f9',borderRadius:8}}>
      <div>
        <div style={{fontWeight:600}}>{challenge.name}</div>
        <div style={{fontSize:13,color:'#666'}}>
          Target: {challenge.criteria?.app === '__TOTAL__' ? 'Total Screen Time' : challenge.criteria?.app} • {minutesLabel(challenge.criteria?.targetMinutes || 0)}
        </div>
      </div>
      <div style={{display:'flex',alignItems:'center',gap:10}}>
        <div style={{color:statusColor,fontWeight:600}}>
          {status === 'checking' ? 'Checking...' : status === 'no-data' ? 'No entry' : status === 'success' ? 'Success' : 'Failed'}
        </div>
      </div>
    </div>
  )
}
