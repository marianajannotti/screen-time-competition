/**
 * Shared challenge helper utilities
 */

/**
 * Determines the current status of a challenge based on dates
 * @param {Object} challenge - Challenge object with start_date and end_date
 * @returns {'upcoming' | 'active' | 'completed'}
 */
export function getChallengeStatus(challenge) {
  if (!challenge.start_date || !challenge.end_date) return 'active'
  
  const today = new Date().toISOString().slice(0, 10)
  const start = challenge.start_date
  const end = challenge.end_date
  
  if (today < start) return 'upcoming'
  if (today > end) return 'completed'
  return 'active'
}

/**
 * Formats a date string to a readable format
 * Uses local timezone by appending T00:00:00 to ensure consistent parsing
 * @param {string} dateStr - Date string in YYYY-MM-DD format
 * @returns {string} Formatted date like "Dec 13, 2025"
 */
export function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr + 'T00:00:00')
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

/**
 * Formats a date range for display
 * @param {string} start - Start date in YYYY-MM-DD format
 * @param {string} end - End date in YYYY-MM-DD format
 * @returns {string} Formatted range like "Dec 1 - Dec 7, 2025"
 */
export function formatDateRange(start, end) {
  if (!start || !end) return ''
  const startDate = new Date(start + 'T00:00:00')
  const endDate = new Date(end + 'T00:00:00')
  const startStr = startDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  const endStr = endDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  return `${startStr} - ${endStr}`
}

/**
 * Normalize user id from different possible shapes
 * @param {Object} u - User object
 * @returns {number|null} User ID
 */
export function getUserId(u) {
  return u?.user_id ?? u?.id ?? u?.userId ?? u?.uid ?? null
}
