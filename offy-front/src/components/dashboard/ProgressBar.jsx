/**
 * ProgressBar component for displaying goal progress with visual indicators.
 */

/**
 * A horizontal progress bar that shows completion percentage.
 * Displays in red if the goal is exceeded.
 * 
 * @param {Object} props
 * @param {number} props.value - Current value (e.g., minutes used)
 * @param {number} props.max - Maximum/goal value
 * @param {string} props.color - Color for the progress bar (when not exceeded)
 * @param {boolean} props.exceeded - Whether the value has exceeded the goal
 */
export default function ProgressBar({ value, max, color, exceeded }) {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0
  const actualPct = max > 0 ? (value / max) * 100 : 0
  const fillColor = exceeded ? '#ef4444' : color
  const label = exceeded ? `${Math.round(actualPct - 100)}% exceeded` : `${Math.round(pct)}%`
  
  return (
    <div className="progress-bar" aria-label={`Progress ${Math.round(actualPct)}%`}>
      <div className="track" />
      <div className="fill" style={{ width: pct + '%', background: fillColor }} />
      <div className="pct-label">{label}</div>
    </div>
  )
}
