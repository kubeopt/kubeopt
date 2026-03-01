import { useState, useCallback } from 'react'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts'

interface CostTrendProps {
  data: { date: string; cost: number; projected?: number }[]
}

export default function CostTrendChart({ data }: CostTrendProps) {
  const [hidden, setHidden] = useState<Record<string, boolean>>({})

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleLegendClick = useCallback((e: any) => {
    const key = String(e?.dataKey ?? '')
    if (key) setHidden((prev) => ({ ...prev, [key]: !prev[key] }))
  }, [])

  if (!data.length) {
    return <div className="py-8 text-center text-dark-400">No trend data available</div>
  }

  const hasProjected = data.some((d) => d.projected !== undefined && d.projected !== null)

  return (
    <ResponsiveContainer width="100%" height={280}>
      <AreaChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id="costAreaGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#7FB069" stopOpacity={0.5} />
            <stop offset="100%" stopColor="#7FB069" stopOpacity={0.05} />
          </linearGradient>
          <linearGradient id="projAreaGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#3a5c2d" stopOpacity={0.3} />
            <stop offset="100%" stopColor="#3a5c2d" stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <XAxis dataKey="date" fontSize={11} tick={{ fill: '#6b7280' }} axisLine={false} tickLine={false} />
        <YAxis fontSize={11} tickFormatter={(v) => `$${v}`} tick={{ fill: '#6b7280' }} axisLine={false} tickLine={false} width={50} />
        <Tooltip
          formatter={(value: number, name: string) => [`$${value.toFixed(2)}`, name === 'cost' ? 'Actual' : 'Projected']}
          contentStyle={{ backgroundColor: '#111a2e', border: '1px solid #1e3050', borderRadius: 8, color: '#e5e7eb', fontSize: 12, boxShadow: '0 4px 12px rgba(0,0,0,0.3)' }}
          itemStyle={{ color: '#d1d5db' }}
          labelStyle={{ color: '#9ca3af' }}
          cursor={{ stroke: 'var(--border-color)', strokeWidth: 1 }}
        />
        <Legend
          wrapperStyle={{ fontSize: 11, cursor: 'pointer' }}
          onClick={handleLegendClick}
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          formatter={(_value: string, entry: any) => {
            const key = String(entry?.dataKey ?? '')
            const label = key === 'cost' ? 'Actual' : 'Projected'
            return (
              <span style={{ color: hidden[key] ? '#6b7280' : '#d1d5db', textDecoration: hidden[key] ? 'line-through' : 'none' }}>
                {label}
              </span>
            )
          }}
        />
        <Area
          type="monotone" dataKey="cost" name="cost"
          stroke={hidden.cost ? 'transparent' : '#7FB069'}
          strokeWidth={2}
          fill={hidden.cost ? 'transparent' : 'url(#costAreaGrad)'}
          dot={false}
          activeDot={hidden.cost ? false : { r: 4, fill: '#7FB069', stroke: '#fff', strokeWidth: 2 }}
        />
        {hasProjected && (
          <Area
            type="monotone" dataKey="projected" name="projected"
            stroke={hidden.projected ? 'transparent' : '#3a5c2d'}
            strokeWidth={2}
            strokeDasharray="6 4"
            fill={hidden.projected ? 'transparent' : 'url(#projAreaGrad)'}
            dot={false}
          />
        )}
      </AreaChart>
    </ResponsiveContainer>
  )
}
