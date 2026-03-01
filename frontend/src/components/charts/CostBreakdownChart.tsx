import DonutChart from './DonutChart'

interface CostBreakdownProps {
  data: { name: string; value: number }[]
}

export default function CostBreakdownChart({ data }: CostBreakdownProps) {
  return (
    <DonutChart
      data={data}
      totalLabel="Total Cost"
      formatValue={(v) => `$${v.toFixed(2)}`}
    />
  )
}
