import DonutChart from './DonutChart'

interface SavingsItem {
  name: string
  value: number
}

export default function SavingsWaterfallChart({ data, total }: { data: SavingsItem[]; total?: number }) {
  if (!data.length) return <p className="py-8 text-center text-sm text-dark-400">No savings data available</p>

  const hasNonZero = data.some((d) => d.value > 0)

  if (!hasNonZero) {
    return (
      <div className="py-4">
        <div className="space-y-2">
          {data.map((item, i) => (
            <div key={i} className="flex items-center justify-between rounded-lg px-3 py-2" style={{ backgroundColor: 'var(--bg-surface)' }}>
              <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>{item.name}</span>
              <span className="text-sm font-medium" style={{ color: 'var(--text-muted)' }}>$0.00</span>
            </div>
          ))}
        </div>
        <p className="mt-3 text-center text-xs" style={{ color: 'var(--text-muted)' }}>
          Run an analysis to identify potential savings
        </p>
      </div>
    )
  }

  return (
    <DonutChart
      data={data.filter((d) => d.value > 0)}
      total={total}
      totalLabel="Potential Savings"
      formatValue={(v) => `$${v.toFixed(0)}`}
    />
  )
}
