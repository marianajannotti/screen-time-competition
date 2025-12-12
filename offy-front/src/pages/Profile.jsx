import React, { useEffect, useMemo, useRef, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { badgesApi } from '../api/badgesApi'
import { getGlobalLeaderboard, getFriendships } from '../api/leaderboardApi'

// Badge icons by type for visual differentiation
const BADGE_ICONS = {
  streak: '🔥',
  reduction: '📉',
  social: '👥',
  leaderboard: '🏆',
  prestige: '⭐',
}

export default function Profile() {
  const { user } = useAuth()

  // Get user id from AuthContext user object
  const getUserId = (u) => u?.id ?? null

  // Live stats
  const [rank, setRank] = useState('—')
  const [streakDays, setStreakDays] = useState('—')
  const [friendCount, setFriendCount] = useState('—')
  const [statsError, setStatsError] = useState(null)

  // Fallbacks while backend profile endpoints are not ready
  const displayName = useMemo(() => {
    if (!user) return 'User'
    const name = user.username || user.name || 'User'
    // Title case for nicer display
    return name
      .split(' ')
      .map((s) => (s ? s[0].toUpperCase() + s.slice(1) : ''))
      .join(' ')
  }, [user])

  const initial = useMemo(() => {
    const source = user?.username || user?.name || 'U'
    return source.trim().charAt(0).toUpperCase()
  }, [user])

  // Badge state
  const [allBadges, setAllBadges] = useState([])
  const [userBadges, setUserBadges] = useState([])
  const [badgesLoading, setBadgesLoading] = useState(true)
  const [badgesError, setBadgesError] = useState(null)
  
  const [modalOpen, setModalOpen] = useState(false)
  const [activeBadge, setActiveBadge] = useState(null)
  const [showAllLocked, setShowAllLocked] = useState(false)
  const [showAllUnlocked, setShowAllUnlocked] = useState(false)
  const triggerRef = useRef(null)

  function openBadge(badge, event) {
    triggerRef.current = event?.currentTarget
    setActiveBadge(badge)
    setModalOpen(true)
  }
  function closeBadge() {
    setModalOpen(false)
    setActiveBadge(null)
    // Restore focus to the triggering element
    if (triggerRef.current) {
      triggerRef.current.focus()
      triggerRef.current = null
    }
  }

  // Fetch badge data on mount
  useEffect(() => {
    const fetchBadgesData = async () => {
      setBadgesLoading(true)
      setBadgesError(null)
      
      try {
        const [badges, userBadgeData] = await Promise.all([
          badgesApi.getAllBadges(),
          user?.id ? badgesApi.getUserBadges(user.id) : Promise.resolve([])
        ])
        
        setAllBadges(badges)
        setUserBadges(userBadgeData)
      } catch (error) {
        console.error('Failed to fetch badge data:', error)
        setBadgesError('Failed to load badges. Please try again later.')
      } finally {
        setBadgesLoading(false)
      }
    }

    fetchBadgesData()
  }, [user?.id])

  // Fetch leaderboard rank, streak, and friends count for the current user
  useEffect(() => {
    const uid = getUserId(user)
    if (!uid) {
      setRank('—')
      setStreakDays('—')
      setFriendCount('—')
      return
    }

    let cancelled = false
    async function loadStats() {
      setStatsError(null)
      try {
        const [leaderboard, friendships] = await Promise.all([
          getGlobalLeaderboard(),
          getFriendships(),
        ])

        if (cancelled) return

        const entry = leaderboard.find((u) => getUserId(u) === uid)
        setRank(entry ? entry.rank ?? '—' : '—')
        setStreakDays(entry ? (entry.streak ?? entry._streak ?? 0) : '—')
        setFriendCount((friendships?.friends?.length ?? 0))
      } catch (err) {
        console.error('Failed to load profile stats', err)
        if (!cancelled) setStatsError('Unable to load latest stats')
      }
    }

    loadStats()
    return () => { cancelled = true }
  }, [user?.id, user?.streak_count])

  // Handle Escape key to close modal
  useEffect(() => {
    if (!modalOpen) return
    const handleEscape = (e) => {
      if (e.key === 'Escape') closeBadge()
    }
    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [modalOpen])

  // Create lookup for earned badges
  const earnedBadgeMap = useMemo(() => {
    const map = new Map()
    userBadges.forEach(badge => {
      map.set(badge.name, badge.earnedAt)
    })
    return map
  }, [userBadges])

  // Memoize filtered badge lists
  const unlockedBadges = useMemo(
    () => allBadges.filter((b) => earnedBadgeMap.has(b.name)),
    [allBadges, earnedBadgeMap]
  )
  const lockedBadges = useMemo(
    () => allBadges.filter((b) => !earnedBadgeMap.has(b.name)),
    [allBadges, earnedBadgeMap]
  )

  return (
    <main>
      {/* Hero section */}
      <section className="profile-hero card">
        <div className="profile-left">
          <div className="profile-avatar-ring">
            <div className="profile-avatar">{initial}</div>
          </div>
          <div className="profile-name">
            <div className="profile-first">{displayName}</div>
          </div>
        </div>
        <div className="profile-right">
          <div className="profile-stat">
            <div className="icon">🏆</div>
            <div className="value">#{rank}</div>
            <div className="label">Global Leaderboard</div>
          </div>
          <div className="profile-stat">
            <div className="icon">🔥</div>
            <div className="value">{streakDays}</div>
            <div className="label">day streak</div>
          </div>
          <div className="profile-stat">
            <div className="icon">👥</div>
            <div className="value">{friendCount}</div>
            <div className="label">friends</div>
          </div>
        </div>
      </section>

      {/* Badges per documentation */}
      <section className="card badges-section">
        <h2 className="badges-title">Badges</h2>
        {badgesError && (
          <div className="error-message" style={{ color: '#e74c3c', marginBottom: '1rem' }}>
            {badgesError}
          </div>
        )}
        {badgesLoading && (
          <div className="loading-message" style={{ color: '#666', marginBottom: '1rem' }}>
            Loading badges...
          </div>
        )}
        {/* Unlocked */}
        <div className="badges-header">
          <h3 className="badges-subtitle">Unlocked</h3>
        </div>
        <div className="badges-grid">
          {unlockedBadges
            .slice(0, showAllUnlocked ? unlockedBadges.length : 6)
            .map((b) => (
              <div
                key={b.name}
                className="badge-card owned"
                onClick={(e) => openBadge(b, e)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault()
                    openBadge(b, e)
                  }
                }}
                aria-label={`View ${b.name} details`}
              >
                <div className="badge-icon">{BADGE_ICONS[b.type] || '🔥'}</div>
                <div className="badge-info">
                  <div className="badge-name">{b.name}</div>
                  <div className="badge-date muted">{formatEarnedDate(earnedBadgeMap.get(b.name))}</div>
                </div>
              </div>
            ))}
        </div>
        {unlockedBadges.length > 6 && (
          <div className="see-more-row">
            <button type="button" className="btn-link" onClick={() => setShowAllUnlocked((v) => !v)}>
              {showAllUnlocked ? 'See less' : 'See more'}
            </button>
          </div>
        )}

        {/* Locked */}
        <div className="badges-header badges-header-locked">
          <h3 className="badges-subtitle">Locked</h3>
        </div>
        <div className="badges-grid">
          {lockedBadges
            .slice(0, showAllLocked ? lockedBadges.length : 4)
            .map((b) => (
              <div
                key={b.name}
                className="badge-card locked"
                onClick={(e) => openBadge(b, e)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault()
                    openBadge(b, e)
                  }
                }}
                aria-label={`View ${b.name} details`}
              >
                <div className="badge-icon locked-icon">🔒</div>
                <div className="badge-info">
                  <div className="badge-name">{b.name}</div>
                  <div className="badge-date muted"></div>
                </div>
              </div>
            ))}
        </div>
        <div className="see-more-row">
          <button type="button" className="btn-link" onClick={() => setShowAllLocked((v) => !v)}>
            {showAllLocked ? 'See less' : 'See more'}
          </button>
        </div>
      </section>

      {/* Badge detail modal */}
      {modalOpen && activeBadge && (
        <div className="modal-backdrop" onClick={closeBadge} aria-label="Close badge details">
          <div 
            className="modal" 
            onClick={(e) => e.stopPropagation()} 
            role="dialog" 
            aria-modal="true" 
            aria-labelledby="badge-modal-title"
          >
            <h3 id="badge-modal-title" className="modal-title">{activeBadge.name}</h3>
            <p className="muted modal-desc">{activeBadge.desc}</p>
            <div className="modal-actions">
              <button type="button" className="btn-ghost" onClick={closeBadge}>Close</button>
            </div>
          </div>
        </div>
      )}

    </main>
  )
}

function formatEarnedDate(dateString) {
  if (!dateString) return ''
  
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  } catch (error) {
    console.error('Error formatting date:', error)
    return ''
  }
}
