import { useState, useCallback } from 'react'
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts'

interface ResourceUtilizationProps {
  data: { name: string; cpu: number; memory: number }[]
}

export default function ResourceUtilizationChart({ data }: ResourceUtilizationProps) {
  const [hidden, setHidden] = useState<Record<string, boolean>>({})

  const toggleSeries = useCallback((key: string) => {
    setHidden((prev) => ({ ...prev, [key]: !prev[key] }))
  }, [])

  if (!data.length) {
    return <div className="py-8 text-center text-dark-400">No resource data available</div>
  }

  const avgCpu = data.reduce((s, d) => s + d.cpu, 0) / data.length
  const avgMemory = data.reduce((s, d) => s + d.memory, 0) / data.length
  const cpuWaste = Math.max(0, 100 - avgCpu)
  const memWaste = Math.max(0, 100 - avgMemory)

  const cpuRing = [
    { name: 'CPU Used', value: avgCpu },
    { name: 'CPU Free', value: Math.max(0, 100 - avgCpu) },
  ]
  const memRing = [
    { name: 'Memory Used', value: avgMemory },
    { name: 'Memory Free', value: Math.max(0, 100 - avgMemory) },
  ]

  // Use theme-aware colors for the "free" ring segments
  const isDark = document.documentElement.classList.contains('dark')
  const freeColor = isDark ? '#1e293b' : '#e2e8f0'

  return (
    <div>
      <div className="relative mx-auto" style={{ width: 200, height: 200 }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            {/* Inner ring — CPU */}
            <Pie data={cpuRing} cx="50%" cy="50%" innerRadius={45} outerRadius={65}
              startAngle={90} endAngle={-270} dataKey="value" stroke="none">
              <Cell fill={hidden.cpu ? freeColor : '#7FB069'} />
              <Cell fill={freeColor} />
            </Pie>
            {/* Outer ring — Memory */}
            <Pie data={memRing} cx="50%" cy="50%" innerRadius={72} outerRadius={92}
              startAngle={90} endAngle={-270} dataKey="value" stroke="none">
              <Cell fill={hidden.memory ? freeColor : '#3a5c2d'} />
              <Cell fill={freeColor} />
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
          {!hidden.cpu && (
            <>
              <span className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>{avgCpu.toFixed(1)}%</span>
              <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>CPU</span>
            </>
          )}
          {!hidden.memory && (
            <>
              <span className={hidden.cpu ? 'text-lg font-bold' : 'mt-0.5 text-sm font-semibold'} style={{ color: hidden.cpu ? 'var(--text-primary)' : 'var(--text-secondary)' }}>{avgMemory.toFixed(1)}%</span>
              <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>Memory</span>
            </>
          )}
        </div>
      </div>

      {/* Clickable Legend */}
      <div className="mt-2 flex items-center justify-center gap-4 text-xs" style={{ color: 'var(--text-muted)' }}>
        <span
          className="flex cursor-pointer items-center gap-1 transition-opacity"
          style={{ opacity: hidden.cpu ? 0.4 : 1 }}
          onClick={() => toggleSeries('cpu')}
        >
          <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: hidden.cpu ? '#6b7280' : '#7FB069' }} />
          <span style={{ textDecoration: hidden.cpu ? 'line-through' : 'none' }}>CPU</span>
        </span>
        <span
          className="flex cursor-pointer items-center gap-1 transition-opacity"
          style={{ opacity: hidden.memory ? 0.4 : 1 }}
          onClick={() => toggleSeries('memory')}
        >
          <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: hidden.memory ? '#6b7280' : '#3a5c2d' }} />
          <span style={{ textDecoration: hidden.memory ? 'line-through' : 'none' }}>Memory</span>
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: freeColor }} />
          Free
        </span>
      </div>

      {/* Waste stats */}
      <div className="mt-3 grid grid-cols-4 gap-2 text-center">
        <div style={{ opacity: hidden.cpu ? 0.3 : 1 }}>
          <div className="text-xs" style={{ color: 'var(--text-muted)' }}>CPU Waste</div>
          <div className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{cpuWaste.toFixed(1)}%</div>
        </div>
        <div style={{ opacity: hidden.cpu ? 0.3 : 1 }}>
          <div className="text-xs" style={{ color: 'var(--text-muted)' }}>Avg CPU</div>
          <div className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{avgCpu.toFixed(1)}%</div>
        </div>
        <div style={{ opacity: hidden.memory ? 0.3 : 1 }}>
          <div className="text-xs" style={{ color: 'var(--text-muted)' }}>Mem Waste</div>
          <div className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{memWaste.toFixed(1)}%</div>
        </div>
        <div style={{ opacity: hidden.memory ? 0.3 : 1 }}>
          <div className="text-xs" style={{ color: 'var(--text-muted)' }}>Avg Mem</div>
          <div className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{avgMemory.toFixed(1)}%</div>
        </div>
      </div>
    </div>
  )
}
