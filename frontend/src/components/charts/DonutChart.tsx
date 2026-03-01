import { useState, useCallback } from 'react'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'

interface DonutItem {
  name: string
  value: number
}

interface DonutChartProps {
  data: DonutItem[]
  total?: number
  totalLabel?: string
  formatValue?: (v: number) => string
  innerRadius?: number
  outerRadius?: number
  height?: number
}

const COLORS = ['#7FB069', '#5f9548', '#3a5c2d', '#4a7737', '#9ec88d', '#c3deb8', '#e0eeda', '#888']

export default function DonutChart({
  data,
  total,
  totalLabel = 'Total',
  formatValue = (v) => `$${v.toFixed(2)}`,
  innerRadius = 60,
  outerRadius = 90,
  height = 280,
}: DonutChartProps) {
  const [hidden, setHidden] = useState<Record<string, boolean>>({})

  const toggleSlice = useCallback((name: string) => {
    setHidden((prev) => ({ ...prev, [name]: !prev[name] }))
  }, [])

  if (!data.length) {
    return <div className="py-8 text-center text-dark-400">No data available</div>
  }

  const sorted = [...data].sort((a, b) => b.value - a.value)
  let allItems: DonutItem[]
  if (sorted.length > 8) {
    const top = sorted.slice(0, 7)
    const otherValue = sorted.slice(7).reduce((s, d) => s + d.value, 0)
    allItems = [...top, { name: 'Other', value: otherValue }]
  } else {
    allItems = sorted
  }

  const chartData = allItems.filter((d) => !hidden[d.name])
  const computedTotal = total ?? allItems.reduce((s, d) => s + (hidden[d.name] ? 0 : d.value), 0)

  return (
    <div className="flex min-w-0 items-center gap-4">
      <div className="relative flex-shrink-0" style={{ width: outerRadius * 2 + 20, height }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={innerRadius}
              outerRadius={outerRadius}
              paddingAngle={0}
              dataKey="value"
              stroke="none"
            >
              {chartData.map((item) => {
                const origIdx = allItems.findIndex((d) => d.name === item.name)
                return <Cell key={item.name} fill={COLORS[origIdx % COLORS.length]} />
              })}
            </Pie>
            <Tooltip
              formatter={(value: number) => formatValue(value)}
              contentStyle={{ backgroundColor: '#111a2e', border: '1px solid #1e3050', borderRadius: 8, color: '#e5e7eb', fontSize: 12, boxShadow: '0 4px 12px rgba(0,0,0,0.3)' }}
              itemStyle={{ color: '#d1d5db' }}
              labelStyle={{ color: '#9ca3af' }}
              cursor={{ fill: 'transparent' }}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-xl font-bold text-dark-900 dark:text-white">
            {formatValue(computedTotal)}
          </span>
          <span className="text-xs text-dark-400">{totalLabel}</span>
        </div>
      </div>

      <div className="flex min-w-0 flex-1 flex-col gap-1.5 overflow-hidden">
        {allItems.map((item, i) => {
          const isHidden = !!hidden[item.name]
          const pct = computedTotal > 0 && !isHidden ? ((item.value / computedTotal) * 100).toFixed(1) : '0.0'
          return (
            <div
              key={i}
              className="flex cursor-pointer items-center gap-2 text-xs transition-opacity"
              style={{ opacity: isHidden ? 0.4 : 1 }}
              onClick={() => toggleSlice(item.name)}
            >
              <span
                className="h-2.5 w-2.5 flex-shrink-0 rounded-full"
                style={{ backgroundColor: isHidden ? '#6b7280' : COLORS[i % COLORS.length] }}
              />
              <span
                className="min-w-0 truncate text-dark-600 dark:text-dark-300"
                title={item.name}
                style={{ textDecoration: isHidden ? 'line-through' : 'none' }}
              >
                {item.name}
              </span>
              <span className="ml-auto whitespace-nowrap font-medium text-dark-800 dark:text-dark-200">
                {formatValue(item.value)} ({pct}%)
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
