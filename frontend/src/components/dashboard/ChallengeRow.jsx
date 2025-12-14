import React from 'react'
import { minutesLabel } from '../../utils/timeFormatters'

// Normalize user id from different possible shapes
function getUserId(u) {
  return u?.user_id ?? u?.id ?? u?.userId ?? u?.uid ?? null
}

/**
 * Determines the current status of a challenge based on dates
 * @returns {'upcoming' | 'active' | 'completed'}
 */
function getChallengeStatus(challenge) {
  if (!challenge.start_date || !challenge.end_date) return 'active'
  
  const today = new Date().toISOString().slice(0, 10)
  const start = challenge.start_date
  const end = challenge.end_date
  
  if (today < start) return 'upcoming'
  if (today > end) return 'completed'
  return 'active'
}

/**
 * Formats a date string to a readable format
 */
function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr + 'T00:00:00')
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

/**
 * Calculate days remaining in challenge
 */
function getDaysRemaining(endDate) {
  if (!endDate) return null
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const end = new Date(endDate + 'T00:00:00')
  const diffTime = end - today
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  return diffDays
}

export default function ChallengeRow({ challenge, currentUser, onViewDetails }) {
  // Use backend status field
  const challengeStatus = challenge.status || getChallengeStatus(challenge)
  
  // Calculate status based on TODAY's performance from backend
  const userStats = challenge.user_stats || {}
  const todayPassed = userStats.today_passed  // null = no data, true = passed, false = failed
  const isZeroMinuteChallenge = challenge.target_minutes === 0
  
  let status = 'no-data'
  if (todayPassed === true) {
    status = 'success'  // Passed today's goal
  } else if (todayPassed === false) {
    status = 'failed'  // Failed today's goal (over limit)
  } else if (todayPassed === null) {
    // No data for today
    if (isZeroMinuteChallenge) {
      status = 'success'  // For 0-minute challenges, no data = success
    } else {
      status = 'no-data'  // For other challenges, no data = grey
    }
  }
  
  const daysRemaining = getDaysRemaining(challenge.end_date)
  
  // Determine background color based on status (only for active challenges)
  let bgColor = '#fff'
  let borderColor = '#e2e8f0'
  let textColor = '#0f172a'
  let statusLabel = null
  
  if (challengeStatus === 'active') {
    if (status === 'success') {
      bgColor = '#dcfce7' // green
      borderColor = '#86efac'
      statusLabel = { text: 'On track', color: '#166534' }
    } else if (status === 'failed') {
      bgColor = '#fee2e2' // red
      borderColor = '#fca5a5'
      statusLabel = { text: 'Over limit', color: '#991b1b' }
    } else { // no-data
      bgColor = '#f3f4f6' // grey
      borderColor = '#d1d5db'
      statusLabel = { text: 'No data', color: '#6b7280' }
    }
  } else if (challengeStatus === 'completed') {
    bgColor = '#f9fafb'
    borderColor = '#e5e7eb'
    textColor = '#64748b'
  }
  
  const challengeStatusColor = challengeStatus === 'active' ? '#2563eb' : challengeStatus === 'completed' ? '#6b7280' : '#f59e0b'
  const challengeStatusLabel = challengeStatus === 'active' ? 'Active' : challengeStatus === 'completed' ? 'Completed' : 'Upcoming'
  
  return (
    <div 
      onClick={() => onViewDetails && onViewDetails(challenge)}
      style={{
        padding:16,
        border:`2px solid ${borderColor}`,
        borderRadius:12,
        cursor: onViewDetails ? 'pointer' : 'default',
        transition: 'all 0.2s',
        backgroundColor: bgColor,
        position: 'relative'
      }}
      onMouseEnter={(e) => { 
        if (onViewDetails) {
          e.currentTarget.style.transform = 'translateY(-2px)'
          e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)'
        }
      }}
      onMouseLeave={(e) => { 
        e.currentTarget.style.transform = 'translateY(0)'
        e.currentTarget.style.boxShadow = 'none'
      }}
    >
      {/* Status label in top-right corner */}
      {statusLabel && (
        <div style={{
          position: 'absolute',
          top: 12,
          right: 12,
          fontSize: 11,
          fontWeight: 600,
          color: statusLabel.color,
          backgroundColor: 'rgba(255,255,255,0.9)',
          padding: '4px 10px',
          borderRadius: 8,
          border: `1px solid ${statusLabel.color}40`
        }}>
          {statusLabel.text}
        </div>
      )}
      
      {/* Challenge name and status badges */}
      <div style={{display:'flex',alignItems:'center',gap:8,marginBottom:8,flexWrap:'wrap',paddingRight: statusLabel ? 100 : 0}}>
        <div style={{fontWeight:600,fontSize:16,color:textColor}}>{challenge.name}</div>
        {challengeStatus !== 'active' && (
          <span style={{
            fontSize:11,
            padding:'3px 10px',
            borderRadius:12,
            backgroundColor: challengeStatus === 'completed' ? '#e5e7eb' : '#fef3c7',
            color: challengeStatusColor,
            fontWeight:600,
            whiteSpace:'nowrap',
            border: `1px solid ${challengeStatusColor}40`
          }}>
            {challengeStatusLabel}
          </span>
        )}
      </div>
      
      {/* Days remaining badge */}
      {challengeStatus === 'active' && daysRemaining !== null && (
        <div style={{
          fontSize:11,
          padding:'4px 10px',
          borderRadius:8,
          backgroundColor: daysRemaining === 0 && status === 'failed' ? '#dc2626' : daysRemaining <= 2 ? '#fee2e2' : 'rgba(255,255,255,0.7)',
          color: daysRemaining === 0 && status === 'failed' ? '#ffffff' : daysRemaining <= 2 ? '#991b1b' : '#166534',
          fontWeight:600,
          display:'inline-block',
          marginBottom:8,
          border: `1px solid ${daysRemaining === 0 && status === 'failed' ? '#dc2626' : daysRemaining <= 2 ? '#fca5a5' : '#86efac'}`
        }}>
          {daysRemaining === 0 ? 'Last day!' : daysRemaining === 1 ? '1 day left' : `${daysRemaining} days left`}
        </div>
      )}
      
      {/* Target info */}
      <div style={{fontSize:13,color:textColor,marginBottom:6,opacity:0.8}}>
        <strong>Target:</strong> {challenge.target_app === '__TOTAL__' ? 'Total Screen Time' : challenge.target_app} • {minutesLabel(challenge.target_minutes || 0)}/day
      </div>
      
      {/* Date range */}
      {(challenge.start_date || challenge.end_date) && (
        <div style={{fontSize:12,color:textColor,opacity:0.7}}>
          {formatDate(challenge.start_date)} - {formatDate(challenge.end_date)}
        </div>
      )}
      
      {/* Arrow indicator for clickable items */}
      {onViewDetails && (
        <div style={{
          position: 'absolute',
          right: 16,
          bottom: 16,
          color: textColor,
          opacity: 0.4,
          fontSize: 24,
          lineHeight: 1
        }}>
          ›
        </div>
      )}
    </div>
  )
}
