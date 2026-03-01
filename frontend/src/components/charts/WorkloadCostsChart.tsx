import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

interface WorkloadCost {
  name: string
  value: number
  type?: string
}

interface WorkloadCostsProps {
  data: WorkloadCost[]
}

const TYPE_COLORS: Record<string, string> = {
  Deployment: '#5f9548',
  StatefulSet: '#4a7737',
  DaemonSet: '#7fb069',
  Job: '#9ec88d',
  CronJob: '#c3deb8',
}

function truncate(s: string, max = 20) {
  return s.length > max ? s.slice(0, max - 1) + '\u2026' : s
}

export default function WorkloadCostsChart({ data }: WorkloadCostsProps) {
  if (!data.length) {
    return <div className="py-8 text-center text-sm text-dark-400">No workload cost data</div>
  }

  const sorted = [...data].sort((a, b) => b.value - a.value).slice(0, 8)

  return (
    <ResponsiveContainer width="100%" height={Math.min(sorted.length * 34 + 24, 300)}>
      <BarChart data={sorted} layout="vertical" margin={{ left: 4, right: 20, top: 4, bottom: 4 }}>
        <XAxis type="number" tickFormatter={(v: number) => `$${v.toFixed(0)}`} tick={{ fontSize: 11 }} />
        <YAxis
          type="category"
          dataKey="name"
          width={130}
          tick={{ fontSize: 11 }}
          tickFormatter={(v: string) => truncate(v)}
        />
        <Tooltip
          formatter={(v: number) => `$${v.toFixed(2)}`}
          labelFormatter={(label: string) => {
            const item = sorted.find((d) => d.name === label)
            return item?.type ? `${label} (${item.type})` : label
          }}
          contentStyle={{ backgroundColor: '#111a2e', border: '1px solid #1e3050', borderRadius: 8, color: '#e5e7eb', fontSize: 12, boxShadow: '0 4px 12px rgba(0,0,0,0.3)' }}
          itemStyle={{ color: '#d1d5db' }}
          labelStyle={{ color: '#9ca3af' }}
          cursor={{ fill: 'rgba(127,176,105,0.08)' }}
        />
        <Bar
          dataKey="value"
          radius={[0, 4, 4, 0]}
          fill="#5f9548"
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          shape={(props: any) => {
            const fill = TYPE_COLORS[sorted[props.index]?.type || ''] || '#5f9548'
            return <rect {...props} fill={fill} />
          }}
        />
      </BarChart>
    </ResponsiveContainer>
  )
}
