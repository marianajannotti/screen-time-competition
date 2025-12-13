/**
 * WeeklyChart component for visualizing screen time data across a week.
 */

import { showChartTooltip, hideChartTooltip } from '../../utils/chartHelpers'

/**
 * A stacked bar chart showing screen time for each day of the week.
 * Each bar shows individual app usage (colored segments) and unassigned time (gray).
 * 
 * @param {Object} props
 * @param {string[]} props.days - Array of day names (e.g., ['Sun', 'Mon', ...])
 * @param {Object} props.chartData - Data for each day: { [day]: { apps, remainder, total } }
 * @param {Object} props.appColorMap - Color mapping for each app: { [appName]: color }
 */
export default function WeeklyChart({ days, chartData, appColorMap }) {
  if (!days.length) {
    return (
      <div style={{height:300,display:'flex',alignItems:'center',justifyContent:'center',color:'#999'}}>
        No screen time data for this week
      </div>
    )
  }

  const height = 180
  const barW = 54
  const gap = 64
  const BAR_X_OFFSET = 14
  const totals = days.map(d => chartData[d]?.total || 0)
  const max = Math.max(...totals, 1)
  const maxHours = Math.ceil(max / 60)
  const ticks = Array.from({length: maxHours + 1}, (_,i)=>i)

  return (
    <div className="chart-wrapper">
      <svg viewBox={`0 0 ${gap * days.length + 40} ${height + 50}`} className="weekly-chart" preserveAspectRatio="xMidYMid meet">
        {/* Y Axis */}
        <line x1={34} y1={height - 10} x2={34} y2={20} stroke="#ccc" strokeWidth="1" />
        {ticks.map(h => {
          const y = (height - 10) - (h * 60 / max) * (height - 30)
          return (
            <g key={h}>
              <line x1={34} x2={gap * days.length + 40} y1={y} y2={y} stroke="#f1f5f9" strokeWidth="1" />
              <text x={28} y={y + 4} fontSize="10" textAnchor="end" fill="#555">{h}h</text>
            </g>
          )
        })}
        {days.map((day, i) => {
          const x = 20 + i * gap
          const yBase = height - 10
          const dayData = chartData[day]
          if (!dayData) {
            // No logs: just show day label without a bar.
            return (
              <g key={day}>
                <text x={x + barW/2 + BAR_X_OFFSET} y={height + 14} textAnchor="middle" fontSize="12" fill="#999">{day}</text>
              </g>
            )
          }
          const { apps, remainder } = dayData
          let yOffset = 0
          // stack apps first
          const segments = Object.entries(apps)
          const total = dayData.total
          return (
            <g key={day} className="bar-group" data-day={day}>
              {segments.map(([app, minutes]) => {
                const h = (minutes / max) * (height - 30)
                const y = yBase - yOffset - h
                yOffset += h
                return (
                  <rect
                    key={app}
                    x={x + BAR_X_OFFSET}
                    y={y}
                    width={barW}
                    height={h}
                    fill={appColorMap[app] || '#999'}
                    data-app={app}
                    data-minutes={minutes}
                    className="bar-segment"
                    onMouseEnter={(e) => {
                      const appName = e.target.getAttribute('data-app')
                      const mins = Number(e.target.getAttribute('data-minutes'))
                      showChartTooltip(e, day, appName, mins)
                    }}
                    onMouseLeave={hideChartTooltip}
                  />
                )
              })}
              {/* 
                Gray remainder segment: Represents unassigned screen time.
                This is the difference between total screen time and the sum of individual app times.
                For example: 3h total with 1h Instagram logged = 2h gray remainder (unassigned).
                Hovering shows the total screen time for the day.
              */}
              {remainder > 0 && (()=>{
                const remH = (remainder / max) * (height - 30)
                const remY = yBase - yOffset - remH
                return (
                  <rect 
                    x={x + BAR_X_OFFSET} 
                    y={remY} 
                    width={barW} 
                    height={remH} 
                    fill="#e2e8f0"
                    data-total={total}
                    onMouseEnter={(e) => showChartTooltip(e, day, 'Total', total)}
                    onMouseLeave={hideChartTooltip}
                  />
                )
              })()}
              {/* Small transparent strip at top for total hover without blocking app segments */}
              {total > 0 && (()=>{
                const totalH = (total / max) * (height - 30)
                const stripH = Math.min(18, totalH) // only top strip
                const stripY = yBase - totalH
                return (
                  <rect
                    x={x + BAR_X_OFFSET}
                    y={stripY}
                    width={barW}
                    height={stripH}
                    fill="transparent"
                    data-total={total}
                    onMouseEnter={(e) => showChartTooltip(e, day, 'Total', total)}
                    onMouseLeave={hideChartTooltip}
                  />
                )
              })()}
      <text x={x + barW/2 + BAR_X_OFFSET} y={height + 14} textAnchor="middle" fontSize="12" fill="#444">{day}</text>
            </g>
          )
        })}
      </svg>
      <div className="chart-tooltip" id="chartTooltip" style={{display:'none'}} />
    </div>
  )
}
