import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'

interface CostTrendProps {
  data: { date: string; cost: number; projected?: number }[]
}

export default function CostTrendChart({ data }: CostTrendProps) {
  if (!data.length) {
    return <div className="py-8 text-center text-dark-400">No trend data available</div>
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis dataKey="date" fontSize={12} />
        <YAxis fontSize={12} tickFormatter={(v) => `$${v}`} />
        <Tooltip formatter={(value: number) => `$${value.toFixed(2)}`} />
        <Legend />
        <Line type="monotone" dataKey="cost" stroke="#7FB069" strokeWidth={2} dot={false} name="Actual Cost" />
        {data.some((d) => d.projected !== undefined) && (
          <Line type="monotone" dataKey="projected" stroke="#3a5c2d" strokeWidth={2} strokeDasharray="5 5" dot={false} name="Projected" />
        )}
      </LineChart>
    </ResponsiveContainer>
  )
}
