/**
 * Time formatting utilities for screen time display.
 */

/**
 * Convert minutes to a human-readable "Xh Ym" format.
 * @param {number} mins - Total minutes
 * @returns {string} Formatted string like "2h 30m"
 */
export function minutesLabel(mins) {
  const h = Math.floor(mins / 60)
  const m = Math.round(mins % 60)
  return `${h}h ${m}m`
}
