import React, { useEffect, useMemo, useRef, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { badgesApi } from '../api/badgesApi'

// Temporary mocked stats - moved outside component
const MOCK_STATS = {
  rank: 3,
  streakDays: 8,
  friends: 10,
}

// Badge icons by type for visual differentiation (fallback)
const BADGE_ICONS = {
  streak: '🔥',
  reduction: '📉',
  social: '👥',
  leaderboard: '🏆',
  prestige: '⭐',
}

// Import lock icon and stat icons
import lockIcon from '../assets/badges/lock-icon.png'
import trophyIcon from '../assets/badges/trophy-icon.png'
import streakIcon from '../assets/badges/streak-icon.png'
import friendsIcon from '../assets/badges/friends-icon.png'

// Helper function to get badge icon path
function getBadgeIconPath(badgeName) {
  // Convert badge name to kebab-case filename
  const fileName = badgeName
    .toLowerCase()
    .replace(/\s+/g, '-')
    .replace(/[^a-z0-9-]/g, '')
  
  try {
    // Dynamically import the badge icon
    return new URL(`../assets/badges/${fileName}-icon.png`, import.meta.url).href
  } catch {
    // Return null if image doesn't exist
    return null
  }
}

export default function Profile() {
  const { user } = useAuth()

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
    // Merge badge data with earned date if available
    const earnedDate = earnedBadgeMap.get(badge.name)
    const badgeWithDate = {
      ...badge,
      earned_at: earnedDate || null
    }
    console.log('Opening badge:', badgeWithDate)
    setActiveBadge(badgeWithDate)
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
        
        console.log('User badges data:', userBadgeData)
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
      map.set(badge.name, badge.earned_at || badge.earnedAt)
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
            <div className="icon">
              <img src={trophyIcon} alt="Trophy" style={{ width: '25%', height: '25%', objectFit: 'contain' }} />
            </div>
            <div className="value">#{MOCK_STATS.rank}</div>
            <div className="label">Leaderboard</div>
          </div>
          <div className="profile-stat">
            <div className="icon">
              <img src={streakIcon} alt="Streak" style={{ width: '25%', height: '25%', objectFit: 'contain' }} />
            </div>
            <div className="value">{MOCK_STATS.streakDays}</div>
            <div className="label">Day Streak</div>
          </div>
          <div className="profile-stat">
            <div className="icon">
              <img src={friendsIcon} alt="Friends" style={{ width: '25%', height: '25%', objectFit: 'contain' }} />
            </div>
            <div className="value">{MOCK_STATS.friends}</div>
            <div className="label">Friends</div>
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
                <div className="badge-icon">
                  {getBadgeIconPath(b.name) ? (
                    <img 
                      src={getBadgeIconPath(b.name)} 
                      alt={b.name}
                      style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                    />
                  ) : (
                    BADGE_ICONS[b.type] || '🔥'
                  )}
                </div>
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
        <div className="badges-header badges-header-locked" style={{ marginTop: '32px' }}>
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
                <div className="badge-icon locked-icon">
                  <img 
                    src={lockIcon} 
                    alt="Locked"
                    style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                  />
                </div>
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
            className="modal badge-modal" 
            onClick={(e) => e.stopPropagation()} 
            role="dialog" 
            aria-modal="true" 
            aria-labelledby="badge-modal-title"
          >
            <div className="badge-modal-icon">
              <img 
                src={activeBadge.earned_at ? getBadgeIconPath(activeBadge.name) : lockIcon}
                alt={activeBadge.name}
                onError={(e) => {
                  // Fallback to emoji if icon fails to load
                  e.target.style.display = 'none'
                  e.target.parentElement.innerHTML = `<span style="font-size: 80px;">${BADGE_ICONS[activeBadge.badge_type] || '🏅'}</span>`
                }}
                style={{ width: '80px', height: '80px', objectFit: 'contain' }}
              />
            </div>
            <h3 id="badge-modal-title" className="modal-title">{activeBadge.name}</h3>
            <p className="muted modal-desc">{activeBadge.description}</p>
            {console.log('activeBadge.earned_at:', activeBadge.earned_at)}
            {console.log('formatEarnedDate result:', activeBadge.earned_at ? formatEarnedDate(activeBadge.earned_at) : 'no earned_at')}
            {activeBadge.earned_at && (
              <div className="badge-earned-date">
                <span className="earned-label">Earned</span>
                <span className="earned-value">{formatEarnedDate(activeBadge.earned_at)}</span>
              </div>
            )}
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
