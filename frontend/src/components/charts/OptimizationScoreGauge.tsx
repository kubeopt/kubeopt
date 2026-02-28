import { RadialBarChart, RadialBar, ResponsiveContainer } from 'recharts'

interface OptimizationScoreGaugeProps {
  score: number
}

export default function OptimizationScoreGauge({ score }: OptimizationScoreGaugeProps) {
  const data = [{ name: 'score', value: score, fill: score >= 70 ? '#7FB069' : score >= 40 ? '#eab308' : '#ef4444' }]

  return (
    <div className="relative">
      <ResponsiveContainer width="100%" height={200}>
        <RadialBarChart
          cx="50%"
          cy="50%"
          innerRadius="60%"
          outerRadius="90%"
          startAngle={180}
          endAngle={0}
          data={data}
        >
          <RadialBar background dataKey="value" cornerRadius={10} />
        </RadialBarChart>
      </ResponsiveContainer>
      <div className="absolute inset-0 flex items-center justify-center pt-6">
        <div className="text-center">
          <div className="text-3xl font-bold text-dark-900 dark:text-white">{score}</div>
          <div className="text-xs text-dark-400">/ 100</div>
        </div>
      </div>
    </div>
  )
}
