import React, { useEffect, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import * as api from '../api/mockApi'

export default function Profile() {
  const { user } = useAuth()
  const [profile, setProfile] = useState(null)
  const [editing, setEditing] = useState(false)
  const [username, setUsername] = useState('')

  useEffect(() => {
    if (!user) return
    api.getProfile(user.user_id).then((r) => {
      setProfile(r.user)
      setUsername(r.user.username)
    })
  }, [user])

  async function save() {
    if (!user) return
    const { user: updated } = await api.updateProfile(user.user_id, { username })
    setProfile(updated)
    setEditing(false)
  }

  if (!profile) return <div style={{ padding: 20 }}>Loading profile...</div>

  return (
    <main style={{ padding: 20 }}>
      <h2>Profile</h2>
      <div>
        <strong>Username:</strong>{' '}
        {editing ? (
          <>
            <input value={username} onChange={(e) => setUsername(e.target.value)} />
            <button onClick={save}>Save</button>
            <button onClick={() => setEditing(false)}>Cancel</button>
          </>
        ) : (
          <>
            {profile.username} <button onClick={() => setEditing(true)}>Edit</button>
          </>
        )}
      </div>
      <div style={{ marginTop: 12 }}>
        <strong>Points:</strong> {profile.total_points || 0}
      </div>
    </main>
  )
}
