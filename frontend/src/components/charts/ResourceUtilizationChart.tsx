import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'

interface ResourceUtilizationProps {
  data: { name: string; cpu: number; memory: number }[]
}

export default function ResourceUtilizationChart({ data }: ResourceUtilizationProps) {
  if (!data.length) {
    return <div className="py-8 text-center text-dark-400">No resource data available</div>
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis dataKey="name" fontSize={12} />
        <YAxis fontSize={12} tickFormatter={(v) => `${v}%`} domain={[0, 100]} />
        <Tooltip formatter={(value: number) => `${value.toFixed(1)}%`} />
        <Legend />
        <Bar dataKey="cpu" fill="#7FB069" name="CPU %" radius={[4, 4, 0, 0]} />
        <Bar dataKey="memory" fill="#3a5c2d" name="Memory %" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
