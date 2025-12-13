// Real API calls for challenges feature
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001';

/**
 * Get all challenges for the current user
 * @returns {Promise<Array>} Array of challenges with user stats
 */
export async function getChallenges() {
  const response = await fetch(`${API_BASE_URL}/api/challenges`, {
    method: 'GET',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to fetch challenges');
  }

  const data = await response.json();
  return data.challenges;
}

/**
 * Get a specific challenge by ID
 * @param {number} challengeId - ID of the challenge
 * @returns {Promise<Object>} Challenge with user stats
 */
export async function getChallenge(challengeId) {
  const response = await fetch(`${API_BASE_URL}/api/challenges/${challengeId}`, {
    method: 'GET',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to fetch challenge');
  }

  const data = await response.json();
  return data.challenge;
}

/**
 * Create a new challenge
 * @param {Object} challengeData - Challenge creation data
 * @param {string} challengeData.name - Challenge name
 * @param {string} challengeData.description - Optional description
 * @param {string} challengeData.target_app - Target app or "__TOTAL__"
 * @param {number} challengeData.target_minutes - Daily target in minutes
 * @param {string} challengeData.start_date - Start date (YYYY-MM-DD)
 * @param {string} challengeData.end_date - End date (YYYY-MM-DD)
 * @param {Array<number>} challengeData.invited_user_ids - Optional array of user IDs to invite
 * @returns {Promise<Object>} Created challenge
 */
export async function createChallenge(challengeData) {
  const response = await fetch(`${API_BASE_URL}/api/challenges`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(challengeData),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to create challenge');
  }

  const data = await response.json();
  return data.challenge;
}

/**
 * Update a challenge's name and/or add new participants
 * @param {number} challengeId - ID of the challenge to update
 * @param {Object} updateData - Update data
 * @param {string} updateData.name - Optional new name
 * @param {Array<number>} updateData.invited_user_ids - Optional array of new user IDs to invite
 * @returns {Promise<Object>} Updated challenge
 */
export async function updateChallenge(challengeId, updateData) {
  const response = await fetch(`${API_BASE_URL}/api/challenges/${challengeId}`, {
    method: 'PATCH',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(updateData),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to update challenge');
  }

  const data = await response.json();
  return data.challenge;
}

/**
 * Get leaderboard for a challenge
 * @param {number} challengeId - ID of the challenge
 * @returns {Promise<Object>} Object with challenge, owner_username, and leaderboard array
 */
export async function getLeaderboard(challengeId) {
  const response = await fetch(`${API_BASE_URL}/api/challenges/${challengeId}/leaderboard`, {
    method: 'GET',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to fetch leaderboard');
  }

  return await response.json();
}

/**
 * Invite users to a challenge (owner only)
 * @param {number} challengeId - ID of the challenge
 * @param {Array<number>} userIds - Array of user IDs to invite
 * @returns {Promise<Object>} Object with message and invited_count
 */
export async function inviteToChallenge(challengeId, userIds) {
  const response = await fetch(`${API_BASE_URL}/api/challenges/${challengeId}/invite`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ user_ids: userIds }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to invite users');
  }

  return await response.json();
}

/**
 * Leave a challenge (non-owner participants only)
 * @param {number} challengeId - ID of the challenge
 * @returns {Promise<Object>} Object with success message
 */
export async function leaveChallenge(challengeId) {
  const response = await fetch(`${API_BASE_URL}/api/challenges/${challengeId}/leave`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to leave challenge');
  }

  return await response.json();
}

/**
 * Delete a challenge (owner only)
 * @param {number} challengeId - ID of the challenge
 * @returns {Promise<Object>} Object with success message
 */
export async function deleteChallenge(challengeId) {
  const response = await fetch(`${API_BASE_URL}/api/challenges/${challengeId}`, {
    method: 'DELETE',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to delete challenge');
  }

  return await response.json();
}

/**
 * Get pending challenge invitations for the current user
 * @returns {Promise<Array>} Array of pending challenge invitations
 */
export async function getPendingInvitations() {
  const response = await fetch(`${API_BASE_URL}/api/challenges/invitations`, {
    method: 'GET',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to fetch invitations');
  }

  const data = await response.json();
  return data.invitations;
}

/**
 * Accept a challenge invitation
 * @param {number} participantId - ID of the participant record (invitation)
 * @returns {Promise<Object>} Object with success message
 */
export async function acceptInvitation(participantId) {
  const response = await fetch(`${API_BASE_URL}/api/challenges/invitations/${participantId}/accept`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to accept invitation');
  }

  return await response.json();
}

/**
 * Decline a challenge invitation
 * @param {number} participantId - ID of the participant record (invitation)
 * @returns {Promise<Object>} Object with success message
 */
export async function declineInvitation(participantId) {
  const response = await fetch(`${API_BASE_URL}/api/challenges/invitations/${participantId}/decline`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to decline invitation');
  }

  return await response.json();
}
