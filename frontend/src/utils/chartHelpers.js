/**
 * Helper functions for chart tooltip interactions.
 */

import { minutesLabel } from './timeFormatters'

/**
 * Show tooltip for chart bar segments with positioning relative to mouse cursor.
 * @param {MouseEvent} e - The mouse event from the bar segment
 * @param {string} day - Day of the week (e.g., "Mon", "Tue")
 * @param {string} label - Label to display (e.g., "Instagram", "Total")
 * @param {number} minutes - Time in minutes to display
 */
export function showChartTooltip(e, day, label, minutes) {
  const tt = document.getElementById('chartTooltip')
  if (!tt) return
  tt.textContent = ''
  const strong = document.createElement('strong')
  strong.textContent = day
  const div = document.createElement('div')
  div.textContent = label + ': ' + minutesLabel(minutes)
  tt.appendChild(strong)
  tt.appendChild(div)
  tt.style.display = 'block'
  const svg = e.target.ownerSVGElement
  const svgRect = svg.getBoundingClientRect()
  tt.style.left = (e.clientX - svgRect.left + 8) + 'px'
  tt.style.top = (e.clientY - svgRect.top - 24) + 'px'
}

/**
 * Hide the chart tooltip.
 */
export function hideChartTooltip() {
  const tt = document.getElementById('chartTooltip')
  if (tt) tt.style.display = 'none'
}
