import React, { useState, useEffect } from 'react'
import { minutesLabel } from '../../utils/timeFormatters'
import { getLeaderboard } from '../../api/challengesApi'
import trophyIcon from '../../assets/badges/trophy-icon.png'
import EditChallengeModal from './EditChallengeModal'

// Normalize user id from different possible shapes
function getUserId(u) {
  return u?.user_id ?? u?.id ?? u?.userId ?? u?.uid ?? null
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr + 'T00:00:00')
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function getChallengeStatus(challenge) {
  if (!challenge.start_date || !challenge.end_date) return 'active'
  
  const today = new Date().toISOString().slice(0, 10)
  const start = challenge.start_date
  const end = challenge.end_date
  
  if (today < start) return 'upcoming'
  if (today > end) return 'completed'
  return 'active'
}

export default function ChallengeDetailsModal({ challenge, currentUser, onClose, onDelete, onLeave, onUpdate }) {
  const [leaderboard, setLeaderboard] = useState([])
  const [loadingLeaderboard, setLoadingLeaderboard] = useState(true)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [showLeaveConfirm, setShowLeaveConfirm] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)

  const currentUserId = getUserId(currentUser)
  const isCreator = challenge.owner_id === currentUserId
  const challengeStatus = challenge.status || getChallengeStatus(challenge)

  useEffect(() => {
    let mounted = true
    ;(async () => {
      try {
        setLoadingLeaderboard(true)
        const data = await getLeaderboard(challenge.challenge_id)
        if (!mounted) return
        setLeaderboard(data.leaderboard || [])
      } catch (err) {
        console.error('Error fetching leaderboard:', err)
        if (!mounted) return
        setLeaderboard([])
      } finally {
        if (mounted) setLoadingLeaderboard(false)
      }
    })()
    return () => { mounted = false }
  }, [challenge, currentUserId, currentUser])

  const handleDelete = async () => {
    if (onDelete) {
      await onDelete(challenge)
      onClose()
    }
  }

  const handleLeave = async () => {
    if (onLeave) {
      await onLeave(challenge)
      onClose()
    }
  }

  return (
    <div 
      className="modal-backdrop" 
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
      style={{zIndex: 100}}
    >
      <div 
        className="modal" 
        style={{maxWidth: 600, maxHeight: '90vh', overflow: 'auto'}}
        role="dialog"
        aria-modal="true"
        aria-labelledby="challenge-details-title"
      >
        {/* Header */}
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',marginBottom:20}}>
          <div style={{flex: 1}}>
            <h2 id="challenge-details-title" style={{margin:0,marginBottom:8}}>{challenge.name}</h2>
            <div style={{display:'flex',alignItems:'center',gap:8}}>
              <span style={{
                fontSize:12,
                padding:'4px 12px',
                borderRadius:12,
                backgroundColor: challengeStatus === 'active' ? '#dbeafe' : challengeStatus === 'completed' ? '#f3f4f6' : '#fef3c7',
                color: challengeStatus === 'active' ? '#2563eb' : challengeStatus === 'completed' ? '#6b7280' : '#f59e0b',
                fontWeight:600
              }}>
                {challengeStatus === 'active' ? 'Active' : challengeStatus === 'completed' ? '✓ Completed' : 'Upcoming'}
              </span>
              {isCreator && (
                <span style={{
                  fontSize:12,
                  padding:'4px 12px',
                  borderRadius:12,
                  backgroundColor:'#f0fdf4',
                  color:'#16a34a',
                  fontWeight:600
                }}>
                  Creator
                </span>
              )}
            </div>
          </div>
          <button 
            onClick={onClose}
            style={{background:'transparent',border:'none',fontSize:24,cursor:'pointer',color:'#64748b'}}
            aria-label="Close modal"
          >
            ×
          </button>
        </div>

        {/* Challenge Details */}
        <div style={{marginBottom:24}}>
          <div style={{
            padding:16,
            backgroundColor:'#f8fafc',
            borderRadius:12,
            border:'1px solid #e2e8f0'
          }}>
            <div style={{marginBottom:12}}>
              <div style={{fontSize:13,color:'#64748b',marginBottom:4}}>Target</div>
              <div style={{fontSize:16,fontWeight:600}}>
                {challenge.target_app === '__TOTAL__' ? 'Total Screen Time' : challenge.target_app} • {minutesLabel(challenge.target_minutes || 0)} per day
              </div>
            </div>
            
            {(challenge.start_date || challenge.end_date) && (
              <div style={{marginBottom:12}}>
                <div style={{fontSize:13,color:'#64748b',marginBottom:4}}>Duration</div>
                <div style={{fontSize:15}}>
                  {formatDate(challenge.start_date)} → {formatDate(challenge.end_date)}
                </div>
              </div>
            )}

            {challenge.description && (
              <div>
                <div style={{fontSize:13,color:'#64748b',marginBottom:4}}>Description</div>
                <div style={{fontSize:14,color:'#334155'}}>{challenge.description}</div>
              </div>
            )}
          </div>
        </div>

        {/* Leaderboard */}
        <div style={{marginBottom:24}}>
          <h3 style={{fontSize:16,marginBottom:12,display:'flex',alignItems:'center',gap:8}}>
            <img src={trophyIcon} alt="Trophy" style={{width:20,height:20}} />
            Leaderboard
          </h3>
          {loadingLeaderboard ? (
            <div style={{textAlign:'center',padding:20,color:'#64748b'}}>Loading...</div>
          ) : leaderboard.length === 0 ? (
            <div style={{textAlign:'center',padding:20,color:'#64748b'}}>No participants yet</div>
          ) : (
            <div style={{border:'1px solid #e2e8f0',borderRadius:8,overflow:'hidden'}}>
              {leaderboard.map((participant, index) => {
                const isCurrentUser = participant.user_id === currentUserId
                return (
                  <div 
                    key={participant.user_id}
                    style={{
                      display:'flex',
                      justifyContent:'space-between',
                      alignItems:'center',
                      padding:'12px 16px',
                      backgroundColor: isCurrentUser ? '#f0f9ff' : index % 2 === 0 ? '#fff' : '#f9fafb',
                      borderBottom: index < leaderboard.length - 1 ? '1px solid #e2e8f0' : 'none'
                    }}
                  >
                    <div style={{display:'flex',alignItems:'center',gap:12}}>
                      <div style={{
                        width:28,
                        height:28,
                        borderRadius:'50%',
                        backgroundColor: index === 0 ? '#fbbf24' : index === 1 ? '#9ca3af' : index === 2 ? '#cd7f32' : '#e2e8f0',
                        display:'flex',
                        alignItems:'center',
                        justifyContent:'center',
                        fontWeight:600,
                        fontSize:12,
                        color: index < 3 ? '#fff' : '#64748b'
                      }}>
                        {participant.rank || index + 1}
                      </div>
                      <div>
                        <div style={{fontWeight: isCurrentUser ? 600 : 500}}>
                          {isCurrentUser ? `You (${participant.username})` : participant.username}
                        </div>
                      </div>
                    </div>
                    <div style={{fontSize:14,fontWeight:600,color:'#334155'}}>
                      {participant.invitation_status === 'pending' ? (
                        <span style={{fontSize:13,color:'#6b7280',fontStyle:'italic'}}>Pending invitation</span>
                      ) : (
                        <>{minutesLabel(participant.average_daily_minutes || 0)}/day</>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
          {isCreator && challengeStatus !== 'completed' && (
            <button
              className="btn-secondary"
              onClick={() => setShowEditModal(true)}
              style={{marginTop:12,width:'100%'}}
            >
              + Invite More Friends
            </button>
          )}
        </div>

        {/* Actions */}
        <div style={{display:'flex',gap:12,paddingTop:16,borderTop:'1px solid #e2e8f0'}}>
          {isCreator ? (
            <>
              <button 
                className="btn-secondary"
                onClick={() => setShowEditModal(true)}
                style={{flex:1}}
              >
                Edit
              </button>
              <button 
                className="btn-secondary"
                onClick={() => setShowDeleteConfirm(true)}
                style={{flex:1,backgroundColor:'#fee2e2',color:'#991b1b',border:'1px solid #fecaca'}}
              >
                Delete Challenge
              </button>
            </>
          ) : (
            <button 
              className="btn-secondary"
              onClick={() => setShowLeaveConfirm(true)}
              style={{flex:1,backgroundColor:'#fee2e2',color:'#991b1b',border:'1px solid #fecaca'}}
            >
              Leave Challenge
            </button>
          )}
          <button 
            className="btn-primary"
            onClick={onClose}
            style={{flex:1}}
          >
            Close
          </button>
        </div>

        {/* Delete Confirmation */}
        {showDeleteConfirm && (
          <div style={{
            position:'absolute',
            top:0,
            left:0,
            right:0,
            bottom:0,
            backgroundColor:'rgba(0,0,0,0.5)',
            display:'flex',
            alignItems:'center',
            justifyContent:'center',
            borderRadius:12
          }}>
            <div style={{
              backgroundColor:'#fff',
              padding:24,
              borderRadius:12,
              maxWidth:400,
              margin:20
            }}>
              <h3 style={{marginTop:0}}>Delete Challenge?</h3>
              <p style={{color:'#64748b'}}>
                This will permanently delete the challenge for all participants. This action cannot be undone.
              </p>
              <div style={{display:'flex',gap:12,marginTop:20}}>
                <button 
                  className="btn-secondary"
                  onClick={() => setShowDeleteConfirm(false)}
                  style={{flex:1}}
                >
                  Cancel
                </button>
                <button 
                  className="btn-primary"
                  onClick={handleDelete}
                  style={{flex:1,backgroundColor:'#dc2626'}}
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Leave Confirmation */}
        {showLeaveConfirm && (
          <div style={{
            position:'absolute',
            top:0,
            left:0,
            right:0,
            bottom:0,
            backgroundColor:'rgba(0,0,0,0.5)',
            display:'flex',
            alignItems:'center',
            justifyContent:'center',
            borderRadius:12
          }}>
            <div style={{
              backgroundColor:'#fff',
              padding:24,
              borderRadius:12,
              maxWidth:400,
              margin:20
            }}>
              <h3 style={{marginTop:0}}>Leave Challenge?</h3>
              <p style={{color:'#64748b'}}>
                You will be removed from this challenge and will no longer appear on the leaderboard.
              </p>
              <div style={{display:'flex',gap:12,marginTop:20}}>
                <button 
                  className="btn-secondary"
                  onClick={() => setShowLeaveConfirm(false)}
                  style={{flex:1}}
                >
                  Cancel
                </button>
                <button 
                  className="btn-primary"
                  onClick={handleLeave}
                  style={{flex:1,backgroundColor:'#dc2626'}}
                >
                  Leave
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Edit Modal */}
        {showEditModal && (
          <EditChallengeModal
            challenge={challenge}
            currentUser={currentUser}
            existingParticipants={leaderboard}
            onClose={() => setShowEditModal(false)}
            onUpdate={() => {
              setShowEditModal(false)
              if (onUpdate) onUpdate()
            }}
          />
        )}
      </div>
    </div>
  )
}
