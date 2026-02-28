import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

interface SavingsItem {
  name: string
  value: number
}

export default function SavingsWaterfallChart({ data }: { data: SavingsItem[] }) {
  if (!data.length) return <p className="py-8 text-center text-sm text-dark-400">No savings data available</p>

  // Build waterfall: each bar starts where the previous ended
  let cumulative = 0
  const waterfallData = data.map((item) => {
    const start = cumulative
    cumulative += item.value
    return { name: item.name, start, value: item.value, end: cumulative }
  })
  // Add total bar
  waterfallData.push({ name: 'Total', start: 0, value: cumulative, end: cumulative })

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={waterfallData} margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis dataKey="name" tick={{ fontSize: 12 }} />
        <YAxis tick={{ fontSize: 12 }} tickFormatter={(v: number) => `$${v}`} />
        <Tooltip formatter={(value: number) => [`$${value.toFixed(0)}`, 'Savings']} />
        {/* Invisible base bar */}
        <Bar dataKey="start" stackId="waterfall" fill="transparent" />
        <Bar dataKey="value" stackId="waterfall">
          {waterfallData.map((_, i) => (
            <Cell key={i} fill={i === waterfallData.length - 1 ? '#7FB069' : '#60a5fa'} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
