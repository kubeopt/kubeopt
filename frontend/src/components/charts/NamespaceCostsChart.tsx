import { Treemap, ResponsiveContainer, Tooltip } from 'recharts'

interface NamespaceCostsProps {
  data: { name: string; value: number }[]
}

const COLORS = ['#5f9548', '#7FB069', '#4a7737', '#9ec88d', '#3a5c2d', '#c3deb8', '#314a28', '#86efac']

// Custom content renderer for treemap cells
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function CustomContent(props: any) {
  const { x, y, width, height, index, name, value } = props
  if (!width || !height || width < 4 || height < 4) return null

  const fill = COLORS[(index ?? 0) % COLORS.length]
  const label = name ?? ''
  const cost = typeof value === 'number' ? value : 0
  const showText = width > 50 && height > 30 && label

  return (
    <g>
      <rect x={x} y={y} width={width} height={height} rx={4} fill={fill} stroke="#fff" strokeWidth={2} />
      {showText && (
        <>
          <text x={x + width / 2} y={y + height / 2 - 6} textAnchor="middle" fill="#fff" fontSize={11} fontWeight={600}>
            {label.length > width / 7 ? label.slice(0, Math.floor(width / 7)) + '\u2026' : label}
          </text>
          <text x={x + width / 2} y={y + height / 2 + 10} textAnchor="middle" fill="rgba(255,255,255,0.8)" fontSize={10}>
            ${cost.toFixed(0)}
          </text>
        </>
      )}
    </g>
  )
}

export default function NamespaceCostsChart({ data }: NamespaceCostsProps) {
  if (!data.length) {
    return <div className="py-8 text-center text-sm text-dark-400">No namespace cost data</div>
  }

  const sorted = [...data].sort((a, b) => b.value - a.value).slice(0, 12)
  const total = sorted.reduce((s, d) => s + d.value, 0)

  return (
    <div>
      <div className="mb-2 flex items-baseline justify-between">
        <span className="text-xs text-dark-400">{sorted.length} namespaces</span>
        <span className="text-sm font-semibold text-dark-800 dark:text-dark-200">
          ${total.toFixed(0)} total
        </span>
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <Treemap
          data={sorted}
          dataKey="value"
          aspectRatio={4 / 3}
          content={<CustomContent />}
        >
          <Tooltip
            formatter={(v: number) => [`$${v.toFixed(2)}`, 'Cost']}
            contentStyle={{ backgroundColor: '#111a2e', border: '1px solid #1e3050', borderRadius: 8, color: '#e5e7eb', fontSize: 12, boxShadow: '0 4px 12px rgba(0,0,0,0.3)' }}
            itemStyle={{ color: '#d1d5db' }}
            labelStyle={{ color: '#9ca3af' }}
          />
        </Treemap>
      </ResponsiveContainer>
    </div>
  )
}
