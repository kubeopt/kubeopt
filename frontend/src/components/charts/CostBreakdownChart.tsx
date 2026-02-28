import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts'

interface CostBreakdownProps {
  data: { name: string; value: number; color?: string }[]
}

const COLORS = ['#7FB069', '#5f9548', '#3a5c2d', '#4a7737', '#9ec88d', '#c3deb8', '#e0eeda']

export default function CostBreakdownChart({ data }: CostBreakdownProps) {
  if (!data.length) {
    return <div className="py-8 text-center text-dark-400">No cost data available</div>
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={100}
          paddingAngle={2}
          dataKey="value"
          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
        >
          {data.map((_, index) => (
            <Cell key={index} fill={data[index].color || COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip formatter={(value: number) => `$${value.toFixed(2)}`} />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  )
}
