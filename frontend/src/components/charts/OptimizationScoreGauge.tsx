interface OptimizationScoreGaugeProps {
  score: number
}

export default function OptimizationScoreGauge({ score }: OptimizationScoreGaugeProps) {
  const clampedScore = Math.max(0, Math.min(100, score))
  const color = clampedScore >= 70 ? '#7FB069' : clampedScore >= 40 ? '#eab308' : '#ef4444'

  const cx = 100
  const cy = 90
  const r = 60
  const strokeW = 10
  const scoreAngle = (clampedScore / 100) * 180
  const toRad = (deg: number) => (deg * Math.PI) / 180

  const arcPath = (startDeg: number, endDeg: number) => {
    const x1 = cx + r * Math.cos(toRad(startDeg))
    const y1 = cy - r * Math.sin(toRad(startDeg))
    const x2 = cx + r * Math.cos(toRad(endDeg))
    const y2 = cy - r * Math.sin(toRad(endDeg))
    const largeArc = Math.abs(startDeg - endDeg) > 180 ? 1 : 0
    return `M ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2}`
  }

  const bgPath = arcPath(180, 0)
  const fillPath = scoreAngle > 0 ? arcPath(180, 180 - scoreAngle) : ''

  return (
    <div className="relative flex items-center justify-center" style={{ height: 140 }}>
      <svg width="100%" viewBox="0 10 200 100" style={{ maxWidth: 200 }}>
        <path d={bgPath} fill="none" stroke="var(--border-subtle, #e2eede)" strokeWidth={strokeW} strokeLinecap="round" />
        {fillPath && (
          <path d={fillPath} fill="none" stroke={color} strokeWidth={strokeW} strokeLinecap="round" />
        )}
      </svg>
      {/* Text overlay — avoids SVG fill/CSS-var issues */}
      <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center" style={{ paddingTop: 8 }}>
        <span className="text-3xl font-bold" style={{ color: 'var(--text-primary)' }}>
          {clampedScore.toFixed(0)}
        </span>
        <span className="text-xs" style={{ color: 'var(--text-muted)' }}>/ 100</span>
      </div>
    </div>
  )
}
