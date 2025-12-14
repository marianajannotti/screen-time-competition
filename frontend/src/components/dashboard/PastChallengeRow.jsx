import React from 'react'
import { formatDateRange } from '../../utils/challengeHelpers'

export default function PastChallengeRow({ challenge, onViewDetails }) {

  return (
    <div
      onClick={() => onViewDetails(challenge)}
      style={{
        padding: '12px 16px',
        borderRadius: 8,
        backgroundColor: '#f3f4f6',
        cursor: 'pointer',
        transition: 'all 0.2s ease',
        border: '1px solid #e5e7eb',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.backgroundColor = '#e5e7eb'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = '#f3f4f6'
      }}
    >
      <div style={{ fontWeight: 500, fontSize: 14, color: '#111', marginBottom: 4 }}>
        {challenge.name}
      </div>
      <div style={{ fontSize: 12, color: '#6b7280' }}>
        {formatDateRange(challenge.start_date, challenge.end_date)}
      </div>
    </div>
  )
}
