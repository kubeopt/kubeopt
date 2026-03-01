import { useState, useCallback } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts'

interface HpaDataPoint {
  time: string
  cpu: number
  memory: number
}

interface HpaComparisonProps {
  data: HpaDataPoint[]
}

export default function HpaComparisonChart({ data }: HpaComparisonProps) {
  const [hidden, setHidden] = useState<Record<string, boolean>>({})

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleLegendClick = useCallback((e: any) => {
    const key = String(e?.dataKey ?? '')
    if (key) setHidden((prev) => ({ ...prev, [key]: !prev[key] }))
  }, [])

  if (!data.length) {
    return <div className="py-8 text-center text-sm text-dark-400">No HPA data available</div>
  }

  return (
    <div>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data} margin={{ left: 0, right: 10, top: 4, bottom: 4 }}>
          <XAxis dataKey="time" tick={{ fontSize: 10 }} />
          <YAxis tick={{ fontSize: 11 }} label={{ value: 'Replicas', angle: -90, position: 'insideLeft', style: { fontSize: 11 } }} />
          <Tooltip
            contentStyle={{ backgroundColor: '#111a2e', border: '1px solid #1e3050', borderRadius: 8, color: '#e5e7eb', fontSize: 12, boxShadow: '0 4px 12px rgba(0,0,0,0.3)' }}
            itemStyle={{ color: '#d1d5db' }}
            labelStyle={{ color: '#9ca3af' }}
            cursor={{ fill: 'rgba(127,176,105,0.08)' }}
          />
          <Legend
            wrapperStyle={{ cursor: 'pointer' }}
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
          <Bar dataKey="cpu" name="CPU Replicas" fill={hidden.cpu ? 'transparent' : '#5f9548'} radius={[4, 4, 0, 0]} />
          <Bar dataKey="memory" name="Memory Replicas" fill={hidden.memory ? 'transparent' : '#9ec88d'} radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
      <p className="mt-2 text-center text-xs text-dark-400">Active HPAs: {data.length}</p>
    </div>
  )
}
