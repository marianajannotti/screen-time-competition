import React, { useMemo, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'

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

  // Temporary mocked stats
  const stats = {
    rank: 3,
    streakDays: 8,
    friends: 10,
  }

  // Badge data derived from documentation/badges.md
  const allBadges = [
    // Streak & Consistency
    { name: 'Fresh Start', desc: 'Complete your first day meeting your screen-time goal.', type: 'streak' },
    { name: 'Weekend Warrior', desc: 'Hit your goal on a Saturday and Sunday.', type: 'streak' },
    { name: '7-Day Focus', desc: '7 days in a row hitting daily goal.', type: 'streak' },
    { name: 'Habit Builder', desc: '14-day streak.', type: 'streak' },
    { name: 'Unstoppable', desc: '30-day streak.', type: 'streak' },
    { name: 'Bounce Back', desc: 'Lose a streak, then start a new one the next day.', type: 'streak' },
    // Screen-Time Reduction
    { name: 'Tiny Wins', desc: 'Reduce total time by 5% from your baseline week.', type: 'reduction' },
    { name: 'The Declutter', desc: 'Reduce total screen time by 10% from baseline.', type: 'reduction' },
    { name: 'Half-Life', desc: 'Reduce screen time by 50% from baseline.', type: 'reduction' },
    { name: 'One Hour Club', desc: 'Stay under 1h of social media in a day.', type: 'reduction' },
    { name: 'Digital Minimalist', desc: 'Average < 2 hours/day over a whole week.', type: 'reduction' },
    // Social & Community
    { name: 'Team Player', desc: 'Add your first friend.', type: 'social' },
    { name: 'The Connector', desc: 'Add 10 friends.', type: 'social' },
    { name: 'Challenge Accepted', desc: 'Join your first challenge.', type: 'social' },
    { name: 'Friendly Rival', desc: 'Participate in 5 challenges.', type: 'social' },
    { name: 'Community Champion', desc: 'Win a weekly challenge among friends.', type: 'social' },
    // Leaderboard
    { name: 'Top 10%', desc: 'Be in top 10% of the leaderboard in a week.', type: 'leaderboard' },
    { name: 'Top 3', desc: 'Finish as #1, #2, or #3 among friends.', type: 'leaderboard' },
    { name: 'The Phantom', desc: 'Win a challenge with the lowest screen time without chatting.', type: 'leaderboard' },
    { name: 'Comeback Kid', desc: 'Go from bottom half to top 3 in the next challenge.', type: 'leaderboard' },
    // Prestige / Long-Term
    { name: 'Offline Legend', desc: 'Average < 2h/day for a full month.', type: 'prestige' },
    { name: 'Master of Attention', desc: 'Maintain a 30-day goal streak and < 2h/day average.', type: 'prestige' },
    { name: 'Life > Screen', desc: 'Complete a full 24h digital detox.', type: 'prestige' },
  ]

  // Simple owned mapping (mock): first few owned for demo
  const ownedSet = new Set(['7-Day Focus', 'Digital Minimalist', 'One Hour Club', 'Top 3'])

  const [modalOpen, setModalOpen] = useState(false)
  const [activeBadge, setActiveBadge] = useState(null)
  const [showAllLocked, setShowAllLocked] = useState(false)

  function openBadge(badge) {
    setActiveBadge(badge)
    setModalOpen(true)
  }
  function closeBadge() {
    setModalOpen(false)
    setActiveBadge(null)
  }

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
            <div className="value">#{stats.rank}</div>
            <div className="label">Leaderboard</div>
          </div>
          <div className="profile-stat">
            <div className="icon">🔥</div>
            <div className="value">{stats.streakDays}</div>
            <div className="label">day streak</div>
          </div>
          <div className="profile-stat">
            <div className="icon">👥</div>
            <div className="value">{stats.friends}</div>
            <div className="label">friends</div>
          </div>
        </div>
      </section>

      {/* Badges per documentation */}
      <section className="card badges-section">
        <h2 className="badges-title">Badges</h2>
        {/* Unlocked */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', margin: '6px 6px 10px' }}>
          <h3 className="badges-subtitle">Unlocked</h3>
        </div>
        <div className="badges-grid">
          {allBadges
            .filter((b) => ownedSet.has(b.name))
            .slice(0, 6)
            .map((b) => (
              <div
                key={b.name}
                className="badge-card owned"
                onClick={() => openBadge(b)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') openBadge(b)
                }}
                aria-label={`View ${b.name} details`}
              >
                <div className="badge-icon">🔥</div>
                <div className="badge-info">
                  <div className="badge-name">{b.name}</div>
                  <div className="badge-date muted">{sampleDateFor(b.name)}</div>
                </div>
              </div>
            ))}
        </div>

        {/* Locked */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', margin: '14px 6px 10px' }}>
          <h3 className="badges-subtitle">Locked</h3>
        </div>
        <div className="badges-grid">
          {allBadges
            .filter((b) => !ownedSet.has(b.name))
            .slice(0, showAllLocked ? allBadges.length : 5)
            .map((b) => (
              <div
                key={b.name}
                className="badge-card locked"
                onClick={() => openBadge(b)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') openBadge(b)
                }}
                aria-label={`View ${b.name} details`}
              >
                <div className="badge-icon">🔒</div>
                <div className="badge-info">
                  <div className="badge-name">{b.name}</div>
                  <div className="badge-date muted"></div>
                </div>
              </div>
            ))}
        </div>
        <div className="see-more-row">
          <button className="btn-link" onClick={() => setShowAllLocked((v) => !v)}>
            {showAllLocked ? 'See less' : 'See more'}
          </button>
        </div>
      </section>

      {/* Badge detail modal */}
      {modalOpen && activeBadge && (
        <div className="modal-backdrop" onClick={closeBadge}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3 style={{ marginTop: 0 }}>{activeBadge.name}</h3>
            <p className="muted" style={{ marginTop: 8 }}>{activeBadge.desc}</p>
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 16 }}>
              <button className="btn-ghost" onClick={closeBadge}>Close</button>
            </div>
          </div>
        </div>
      )}

    </main>
  )
}

function sampleDateFor(name) {
  const map = {
    '7-Day Focus': 'Nov 3, 2025',
    'Digital Minimalist': 'Nov 1, 2025',
    'One Hour Club': 'Nov 8, 2025',
    'Top 3': 'Oct 26, 2025',
  }
  return map[name] || ''
}
