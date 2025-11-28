/**
 * Authentication API Client
 * Handles all authentication-related API calls with proper headers
 */

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:5001';

// Default headers for all API requests
const DEFAULT_HEADERS = {
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  'Cache-Control': 'no-cache',
  'Pragma': 'no-cache',
};

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
    headers: DEFAULT_HEADERS,
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
    headers: DEFAULT_HEADERS,
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
    headers: DEFAULT_HEADERS,
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
    headers: DEFAULT_HEADERS,
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
    headers: DEFAULT_HEADERS,
    credentials: 'include',
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error || 'Failed to check auth status');
  }

  return data;
}
