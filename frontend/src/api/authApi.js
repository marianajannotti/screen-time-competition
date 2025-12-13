/**
 * Authentication API Client
 * Handles all authentication-related API calls with proper headers
 */

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:5001';

// Minimal headers to avoid unnecessary CORS complications
const JSON_HEADERS = {
  'Content-Type': 'application/json',
  'Accept': 'application/json',
}
const GET_HEADERS = {
  'Accept': 'application/json',
}

/**
 * Register a new user
 * @param {Object} userData - User registration data
 * @param {string} userData.username - Username
 * @param {string} userData.email - Email address
 * @param {string} userData.password - Password
 * @returns {Promise<Object>} Registration response with user data
 */
export async function register({ username, email, password }) {
  const response = await fetch(`${API_BASE}/api/auth/register`, {
    method: 'POST',
    headers: JSON_HEADERS,
    credentials: 'include', // Important for session cookies
    body: JSON.stringify({ username, email, password }),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error || 'Registration failed');
  }

  return data;
}

/**
 * Login user
 * @param {Object} credentials - Login credentials
 * @param {string} credentials.username - Username
 * @param {string} credentials.password - Password
 * @returns {Promise<Object>} Login response with user data
 */
export async function login({ username, password }) {
  const response = await fetch(`${API_BASE}/api/auth/login`, {
    method: 'POST',
    headers: JSON_HEADERS,
    credentials: 'include',
    body: JSON.stringify({ username, password }),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error || 'Login failed');
  }

  return data;
}

/**
 * Logout current user
 * @returns {Promise<Object>} Logout response
 */
export async function logout() {
  const response = await fetch(`${API_BASE}/api/auth/logout`, {
    method: 'POST',
    headers: JSON_HEADERS,
    credentials: 'include',
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error || 'Logout failed');
  }

  return data;
}

/**
 * Get current logged-in user
 * @returns {Promise<Object>} Current user data
 */
export async function getCurrentUser() {
  const response = await fetch(`${API_BASE}/api/auth/me`, {
    method: 'GET',
    headers: GET_HEADERS,
    credentials: 'include',
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error || 'Failed to get user');
  }

  return data;
}

/**
 * Check authentication status
 * @returns {Promise<Object>} Authentication status
 */
export async function getAuthStatus() {
  const response = await fetch(`${API_BASE}/api/auth/status`, {
    method: 'GET',
    headers: GET_HEADERS,
    credentials: 'include',
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error || 'Failed to check auth status');
  }

  return data;
}

/**
 * Request password reset email
 * @param {Object} data - Request data
 * @param {string} data.email - User's email address
 * @returns {Promise<Object>} Response message
 */
export async function forgotPassword({ email }) {
  const response = await fetch(`${API_BASE}/api/auth/forgot-password`, {
    method: 'POST',
    headers: JSON_HEADERS,
    credentials: 'include',
    body: JSON.stringify({ email }),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error || 'Failed to send reset email');
  }

  return data;
}

/**
 * Reset password with token
 * @param {Object} data - Reset data
 * @param {string} data.token - Reset token from email
 * @param {string} data.new_password - New password
 * @returns {Promise<Object>} Response message
 */
export async function resetPassword({ token, new_password }) {
  const response = await fetch(`${API_BASE}/api/auth/reset-password`, {
    method: 'POST',
    headers: JSON_HEADERS,
    credentials: 'include',
    body: JSON.stringify({ token, new_password }),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error || 'Failed to reset password');
  }

  return data;
}
