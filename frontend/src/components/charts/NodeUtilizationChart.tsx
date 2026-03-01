import { useState, useCallback } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'

interface NodeUtilizationProps {
  data: { name: string; cpu: number; memory: number }[]
}

function truncate(s: string, max = 14) {
  return s.length > max ? s.slice(0, max - 1) + '\u2026' : s
}

export default function NodeUtilizationChart({ data }: NodeUtilizationProps) {
  const [hidden, setHidden] = useState<Record<string, boolean>>({})

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleLegendClick = useCallback((e: any) => {
    const key = String(e?.dataKey ?? '')
    if (key) setHidden((prev) => ({ ...prev, [key]: !prev[key] }))
  }, [])

  if (!data.length) {
    return <div className="py-8 text-center text-dark-400">No node data available</div>
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} margin={{ bottom: 20, right: 8 }}>
        <CartesianGrid stroke="var(--border-subtle)" strokeOpacity={0.5} vertical={false} />
        <XAxis
          dataKey="name"
          fontSize={10}
          tickFormatter={(v: string) => truncate(v)}
          angle={-30}
          textAnchor="end"
          height={50}
          tick={{ fill: '#6b7280' }}
          axisLine={false}
        />
        <YAxis
          fontSize={11}
          tickFormatter={(v) => `${v}%`}
          domain={[0, 100]}
          tick={{ fill: '#6b7280' }}
          axisLine={false}
          tickLine={false}
          width={40}
        />
        <Tooltip
          formatter={(value: number, name: string) => [`${value.toFixed(1)}%`, name]}
          contentStyle={{ backgroundColor: '#111a2e', border: '1px solid #1e3050', borderRadius: 8, color: '#e5e7eb', fontSize: 12, boxShadow: '0 4px 12px rgba(0,0,0,0.3)' }}
          itemStyle={{ color: '#d1d5db' }} labelStyle={{ color: '#9ca3af' }}
          cursor={{ fill: 'rgba(127,176,105,0.08)' }}
        />
        <Legend
          wrapperStyle={{ fontSize: 11, cursor: 'pointer' }}
          onClick={handleLegendClick}
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          formatter={(value: string, entry: any) => {
            const key = String(entry?.dataKey ?? '')
            return (
              <span style={{ color: hidden[key] ? '#6b7280' : '#d1d5db', textDecoration: hidden[key] ? 'line-through' : 'none' }}>
                {value}
              </span>
            )
          }}
        />
        <Bar dataKey="cpu" fill={hidden.cpu ? 'transparent' : '#7FB069'} name="CPU %" radius={[4, 4, 0, 0]} barSize={16} />
        <Bar dataKey="memory" fill={hidden.memory ? 'transparent' : '#3a5c2d'} name="Memory %" radius={[4, 4, 0, 0]} barSize={16} />
      </BarChart>
    </ResponsiveContainer>
  )
}
