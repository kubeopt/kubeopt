import { useCallback, useEffect, useState } from 'react'
import { getDashboardOverview, getChartData } from '../../api/analysis'
import { useAutoRefresh } from '../../hooks/useAutoRefresh'
import { formatCurrency, formatNumber } from '../../utils/format'
import Card from '../common/Card'
import LoadingSpinner from '../common/LoadingSpinner'
import OptimizationScoreGauge from '../charts/OptimizationScoreGauge'
import CostBreakdownChart from '../charts/CostBreakdownChart'
import ResourceUtilizationChart from '../charts/ResourceUtilizationChart'
import CostTrendChart from '../charts/CostTrendChart'
import SavingsWaterfallChart from '../charts/SavingsWaterfallChart'

interface OverviewTabProps {
  clusterId: string
}

export default function OverviewTab({ clusterId }: OverviewTabProps) {
  const [overview, setOverview] = useState<Record<string, unknown> | null>(null)
  const [chartData, setChartData] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchData = useCallback(async () => {
    try {
      const [ov, cd] = await Promise.all([
        getDashboardOverview(clusterId),
        getChartData(clusterId),
      ])
      setOverview(ov as Record<string, unknown>)
      setChartData(cd as Record<string, unknown>)
    } catch {
      // Errors handled gracefully with empty state
    } finally {
      setLoading(false)
    }
  }, [clusterId])

  useEffect(() => { fetchData() }, [fetchData])

  const { lastRefresh } = useAutoRefresh(fetchData, { intervalMs: 30_000 })

  if (loading) return <div className="flex justify-center py-12"><LoadingSpinner size="lg" /></div>

  const score = (overview?.optimization_score as number) || 0
  const costBreakdown = (chartData?.cost_breakdown as { name: string; value: number }[]) || []
  const resourceData = (chartData?.resource_utilization as { name: string; cpu: number; memory: number }[]) || []
  const trendData = (chartData?.trend_data as { date: string; cost: number; projected?: number }[]) || []
  const savingsRaw = chartData?.savings_breakdown as Record<string, unknown> | undefined
  const savingsItems = savingsRaw
    ? Object.entries(savingsRaw)
        .filter(([k, v]) => k !== 'total' && typeof v === 'number' && (v as number) > 0)
        .map(([name, value]) => ({ name: name.replace(/_/g, ' '), value: value as number }))
    : []
  const insights = (chartData?.insights as unknown[]) || []
  const hpaCount = ((chartData?.hpa_comparison as unknown[]) || []).length
  const namespaceCount = ((chartData?.namespace_costs as unknown[]) || []).length

  return (
    <div className="space-y-6">
      {lastRefresh && (
        <p className="text-right text-xs text-dark-400">
          Last updated: {lastRefresh.toLocaleTimeString()}
        </p>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Score */}
        <Card>
          <h3 className="text-sm font-medium text-dark-500 dark:text-dark-400">Optimization Score</h3>
          <OptimizationScoreGauge score={score} />
        </Card>

        {/* Key metrics — 8 cards */}
        <Card className="lg:col-span-2">
          <h3 className="mb-4 text-sm font-medium text-dark-500 dark:text-dark-400">Key Metrics</h3>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            {[
              { label: 'Monthly Cost', value: formatCurrency((overview?.total_monthly_cost as number) || 0) },
              { label: 'Savings', value: formatCurrency((overview?.potential_savings as number) || 0) },
              { label: 'Nodes', value: formatNumber((overview?.node_count as number) || 0) },
              { label: 'Pods', value: formatNumber((overview?.pod_count as number) || 0) },
              { label: 'Health Score', value: `${((overview?.health_score as number) || 0).toFixed(0)}%` },
              { label: 'Insights', value: formatNumber(insights.length) },
              { label: 'HPAs', value: formatNumber(hpaCount) },
              { label: 'Namespaces', value: formatNumber(namespaceCount) },
            ].map((m) => (
              <div key={m.label}>
                <div className="text-xs text-dark-400">{m.label}</div>
                <div className="text-lg font-semibold text-dark-900 dark:text-white">{m.value}</div>
              </div>
            ))}
          </div>
        </Card>

        {/* Cost breakdown */}
        <Card className="lg:col-span-2">
          <h3 className="mb-4 text-sm font-medium text-dark-500 dark:text-dark-400">Cost Breakdown</h3>
          <CostBreakdownChart data={costBreakdown} />
        </Card>

        {/* Resource utilization */}
        <Card>
          <h3 className="mb-4 text-sm font-medium text-dark-500 dark:text-dark-400">Resource Utilization</h3>
          <ResourceUtilizationChart data={resourceData} />
        </Card>

        {/* Cost trend */}
        <Card className="lg:col-span-2">
          <h3 className="mb-4 text-sm font-medium text-dark-500 dark:text-dark-400">Cost Trend</h3>
          <CostTrendChart data={trendData} />
        </Card>

        {/* Savings waterfall */}
        <Card>
          <h3 className="mb-4 text-sm font-medium text-dark-500 dark:text-dark-400">Savings Breakdown</h3>
          <SavingsWaterfallChart data={savingsItems} />
        </Card>
      </div>
    </div>
  )
}
