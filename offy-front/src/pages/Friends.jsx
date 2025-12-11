import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { friendshipApi } from '../api/friendshipApi'
import { useAuth } from '../contexts/AuthContext'

export default function Friends() {
  useAuth()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [username, setUsername] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [data, setData] = useState({ friends: [], incoming: [], outgoing: [] })

  // Quick indicator to adjust empty-state copy
  const hasAny = useMemo(
    () =>
      (data.friends?.length || 0) + (data.incoming?.length || 0) + (data.outgoing?.length || 0) > 0,
    [data],
  )

  // Fetch friendship lists from the backend
  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await friendshipApi.list()
      setData(res)
    } catch (err) {
      setError(err.message || 'Failed to load friends')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  // Send a new request and refresh lists
  async function handleSend(e) {
    e.preventDefault()
    if (!username.trim()) return
    setSubmitting(true)
    setError(null)
    try {
      await friendshipApi.sendRequest(username.trim())
      setUsername('')
      await load()
    } catch (err) {
      setError(err.message || 'Failed to send request')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleAction(actionFn) {
    setError(null)
    try {
      await actionFn()
      await load()
    } catch (err) {
      setError(err.message || 'Action failed')
    }
  }

  return (
    <main className="friends-page">
      <div className="page-header">
        <div>
          <h1 className="lb-title">Friends</h1>
        </div>
      </div>

      <section className="card friends-send-card">
        <div>
          <h3>Send a friend request</h3>
          <p className="muted">Share usernames to connect with friends.</p>
        </div>
        <form className="friends-send-form" onSubmit={handleSend}>
          <input
            type="text"
            placeholder="Enter username"
            aria-label="Friend username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            disabled={submitting}
          />
          <button type="submit" className="btn-primary" disabled={submitting || !username.trim()}>
            {submitting ? 'Sending...' : 'Send request'}
          </button>
        </form>
      </section>

      {error && <div className="error-banner">{error}</div>}

      {loading ? (
        <div className="muted">Loading friends…</div>
      ) : (
        <div className="friends-grid">
          <FriendsColumn
            title="Incoming requests"
            emptyText="No incoming requests."
            items={data.incoming}
            renderActions={(item) => (
              <div className="friends-actions">
                <button
                  className="btn-primary"
                  onClick={() => handleAction(() => friendshipApi.accept(item.id))}
                  aria-label={`Accept friend request from ${item.counterpart?.username || 'Unknown user'}`}
                >
                  Accept
                </button>
                <button
                  className="btn-ghost"
                  onClick={() => handleAction(() => friendshipApi.reject(item.id))}
                  aria-label={`Reject friend request from ${item.counterpart?.username || 'Unknown user'}`}
                >
                  Reject
                </button>
              </div>
            )}
          />

          <FriendsColumn
            title="Outgoing requests"
            emptyText="No pending outgoing requests."
            items={data.outgoing}
            renderActions={(item) => (
              <div className="friends-actions">
                <button
                  className="btn-ghost"
                  onClick={() => handleAction(() => friendshipApi.cancel(item.id))}
                  aria-label={`Cancel friend request to ${item.counterpart?.username}`}
                >
                  Cancel
                </button>
              </div>
            )}
          />

          <FriendsColumn
            title="Friends"
            emptyText={hasAny ? 'No accepted friends yet.' : 'No friends yet — send your first request!'}
            items={data.friends}
            renderActions={null}
          />
        </div>
      )}
    </main>
  )
}

function FriendsColumn({ title, emptyText, items, renderActions }) {
  return (
    <section className="card friends-column">
      <div className="friends-column-header">
        <h3>{title}</h3>
        <span className="pill">{items?.length || 0}</span>
      </div>
      {(!items || items.length === 0) && <p className="muted">{emptyText}</p>}
      <div className="friends-list">
        {items?.map((item) => (
          <FriendRow key={item.id} item={item} renderActions={renderActions} />
        ))}
      </div>
    </section>
  )
}

function FriendRow({ item, renderActions }) {
  const counterpart = item.counterpart || {}
  const initials = (counterpart.username || '?').slice(0, 2).toUpperCase()

  return (
    <div className="friend-row">
      <div className="friend-row-left">
        <div className="avatar-circle">{initials}</div>
        <div>
          <div className="friend-name">{counterpart.username || 'Unknown user'}</div>
          <div className="muted small">{counterpart.email || 'No email'}</div>
        </div>
      </div>
      {renderActions ? renderActions(item) : null}
    </div>
  )
}
