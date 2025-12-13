/**
 * Screen Time API - handles all screen time related API calls
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001';

/**
 * Add a screen time entry
 * @param {Object} data - Screen time entry data
 * @param {string} data.date - Date in YYYY-MM-DD format
 * @param {number} data.hours - Hours component of screen time
 * @param {number} data.minutes - Minutes component (0-59) of screen time
 * @param {string} [data.app_name] - Optional app name (or empty for total screen time)
 * @returns {Promise} Response with the created entry
 */
export async function addScreenTimeEntry(data) {
  const response = await fetch(`${API_BASE}/api/screen-time/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include', // Important for session cookies
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to add screen time entry');
  }

  return response.json();
}

/**
 * Get screen time entries for the current user
 * @param {Object} filters - Optional filters
 * @param {string} [filters.date] - Specific date
 * @param {string} [filters.start_date] - Start date for range
 * @param {string} [filters.end_date] - End date for range
 * @param {string} [filters.app_name] - Filter by app name
 * @param {number} [filters.limit] - Max number of entries (default 20)
 * @returns {Promise} Response with logs array
 */
export async function getScreenTimeEntries(filters = {}) {
  const params = new URLSearchParams();
  
  if (filters.date) params.append('date', filters.date);
  if (filters.start_date) params.append('start_date', filters.start_date);
  if (filters.end_date) params.append('end_date', filters.end_date);
  if (filters.app_name) params.append('app_name', filters.app_name);
  if (filters.limit) params.append('limit', filters.limit);

  const queryString = params.toString();
  const url = `${API_BASE}/api/screen-time/${queryString ? '?' + queryString : ''}`;

  const response = await fetch(url, {
    method: 'GET',
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to fetch screen time entries');
  }

  return response.json();
}

/**
 * Get list of allowed apps
 * @returns {Promise} Response with apps array
 */
export async function getAllowedApps() {
  const response = await fetch(`${API_BASE}/api/screen-time/apps`, {
    method: 'GET',
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to fetch allowed apps');
  }

  return response.json();
}

export default {
  addScreenTimeEntry,
  getScreenTimeEntries,
  getAllowedApps,
};
