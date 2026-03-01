import { useCallback, useEffect, useState } from 'react'
import { getDashboardOverview, getChartData } from '../../api/analysis'
import { useAutoRefresh } from '../../hooks/useAutoRefresh'
import { formatCurrency, formatNumber } from '../../utils/format'
import { DollarSign, TrendingDown, Zap, Server, Gauge } from 'lucide-react'
import Card from '../common/Card'
import { OverviewSkeleton } from '../common/Skeleton'
import OptimizationScoreGauge from '../charts/OptimizationScoreGauge'
import CostBreakdownChart from '../charts/CostBreakdownChart'
import ResourceUtilizationChart from '../charts/ResourceUtilizationChart'
import NodeUtilizationChart from '../charts/NodeUtilizationChart'
import CostTrendChart from '../charts/CostTrendChart'
import SavingsWaterfallChart from '../charts/SavingsWaterfallChart'
import NamespaceCostsChart from '../charts/NamespaceCostsChart'
import WorkloadCostsChart from '../charts/WorkloadCostsChart'
import HpaComparisonChart from '../charts/HpaComparisonChart'
import AnomalyDetectionChart from '../charts/AnomalyDetectionChart'
import NodeRecommendationsTable from '../charts/NodeRecommendationsTable'

interface OverviewTabProps {
  clusterId: string
}

interface Insight {
  category: string
  message: string
}

interface Recommendation {
  title?: string
  description?: string
  savings?: number
  priority?: string
}


export default function OverviewTab({ clusterId }: OverviewTabProps) {
  const [overview, setOverview] = useState<Record<string, unknown> | null>(null)
  const [chartData, setChartData] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchData = useCallback(async () => {
    try {
      const [ov, cd] = await Promise.all([getDashboardOverview(clusterId), getChartData(clusterId)])
      setOverview(ov as Record<string, unknown>)
      setChartData(cd as Record<string, unknown>)
    } catch { /* empty */ } finally { setLoading(false) }
  }, [clusterId])

  useEffect(() => { fetchData() }, [fetchData])
  const { lastRefresh } = useAutoRefresh(fetchData, { intervalMs: 30_000 })

  if (loading) return <OverviewSkeleton />

  const score = (overview?.optimization_score as number) || 0
  const monthlyCost = (overview?.total_monthly_cost as number) || 0
  const savings = (overview?.potential_savings as number) || 0
  const nodeCount = (overview?.node_count as number) || 0
  const hpaEfficiency = (chartData?.hpa_efficiency as number) || 0

  // Formatting helpers
  const ABBREVS: Record<string, string> = { hpa: 'HPA', cpu: 'CPU', gpu: 'GPU', io: 'I/O', aks: 'AKS', eks: 'EKS', gke: 'GKE' }
  const titleCase = (s: string) => s.replace(/_/g, ' ').replace(/\b\w+/g, (w) => ABBREVS[w.toLowerCase()] || (w.charAt(0).toUpperCase() + w.slice(1)))

  // Cost category data (Compute, Storage, Networking, etc.)
  const costCategories = (chartData?.cost_categories as { name: string; value: number }[]) || []
  // Fallback to namespace-based breakdown if no category data
  const costBreakdown = (chartData?.cost_breakdown as { name: string; value: number }[]) || []
  const costDistributionData = (costCategories.length > 0 ? costCategories : costBreakdown)
    .map((d) => ({ ...d, name: titleCase(d.name) }))

  const resourceData = (chartData?.resource_utilization as { name: string; cpu: number; memory: number }[]) || []
  const trendData = (chartData?.trend_data as { date: string; cost: number; projected?: number }[]) || []
  const savingsRaw = chartData?.savings_breakdown as Record<string, unknown> | undefined
  const SAVINGS_EXCLUDE = new Set(['total', 'total_potential_savings', 'current_health_score', 'standards_compliance'])
  const savingsItems = savingsRaw
    ? Object.entries(savingsRaw).filter(([k, v]) => !SAVINGS_EXCLUDE.has(k) && typeof v === 'number')
        .map(([name, value]) => ({ name: titleCase(name.replace(/_savings$/, '')), value: Number((value as number).toFixed(2)) }))
    : []
  const savingsTotal = savingsRaw ? Number(savingsRaw.total_potential_savings ?? 0) : undefined
  const insights = (chartData?.insights as Insight[]) || []
  const namespaceCosts = (chartData?.namespace_costs as { name: string; value: number }[]) || []
  const workloadCosts = (chartData?.workload_costs as { name: string; value: number; type?: string }[]) || []
  const hpaData = (chartData?.hpa_comparison as { time: string; cpu: number; memory: number }[]) || []
  const anomalyData = (chartData?.anomaly_detection as Record<string, unknown>) || {}
  const topRecs = (overview?.top_recommendations as Recommendation[]) || []
  const nodeRecs = (chartData?.node_recommendations as { node_name: string; current_vm: string; recommended_vm: string; monthly_savings: number; avg_cpu_pct: number; avg_memory_pct: number; priority: string; reasoning?: string }[]) || []

  // Compute average CPU/Memory utilization from resourceData for Node Efficiency metric
  const avgCpu = resourceData.length > 0 ? resourceData.reduce((s, d) => s + d.cpu, 0) / resourceData.length : 0
  const avgMem = resourceData.length > 0 ? resourceData.reduce((s, d) => s + d.memory, 0) / resourceData.length : 0
  const nodeEfficiency = (avgCpu + avgMem) / 2

  // Key metrics (Optimization Score excluded — shown as gauge)
  const metrics = [
    { icon: DollarSign, label: 'Monthly Cost', value: formatCurrency(monthlyCost, 2), color: 'var(--text-primary)', iconColor: 'text-blue-500' },
    { icon: TrendingDown, label: 'Savings', value: formatCurrency(savings, 2), color: '#7FB069', iconColor: 'text-green-500' },
    { icon: Zap, label: 'HPA Efficiency', value: `${hpaEfficiency.toFixed(1)}%`, color: hpaEfficiency >= 60 ? '#7FB069' : hpaEfficiency >= 30 ? '#eab308' : '#ef4444', iconColor: 'text-purple-500' },
    { icon: Server, label: 'Nodes', value: formatNumber(nodeCount), color: 'var(--text-primary)', iconColor: 'text-indigo-500' },
    { icon: Gauge, label: 'Efficiency', value: `${nodeEfficiency.toFixed(0)}%`, color: nodeEfficiency >= 60 ? '#7FB069' : nodeEfficiency >= 40 ? '#eab308' : '#ef4444', iconColor: 'text-orange-500' },
  ]

  return (
    <div className="space-y-6">
      {lastRefresh && (
        <p className="text-right text-xs text-dark-400">Last updated: {lastRefresh.toLocaleTimeString()}</p>
      )}

      {/* ─── 1. SCORE + KEY METRICS ─── */}
      <div className="flex flex-col gap-6 md:flex-row md:items-stretch">
        <Card className="flex-shrink-0 md:w-56">
          <h3 className="text-sm font-medium" style={{ color: 'var(--text-muted)' }}>Optimization Score</h3>
          <OptimizationScoreGauge score={score} />
        </Card>
        <div className="flex flex-1 flex-wrap items-center gap-x-6 gap-y-3 rounded-xl px-5 py-4" style={{ backgroundColor: 'var(--bg-surface)', borderWidth: 1, borderStyle: 'solid', borderColor: 'var(--border-subtle)' }}>
          {metrics.map((m, i) => (
            <div key={m.label} className="flex items-center gap-x-6">
              <div className="flex items-center gap-2.5">
                <m.icon className={`h-4 w-4 ${m.iconColor}`} />
                <div>
                  <div className="text-[10px] font-medium uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>{m.label}</div>
                  <div className="text-lg font-bold leading-tight" style={{ color: m.color }}>{m.value}</div>
                </div>
              </div>
              {i < metrics.length - 1 && (
                <div className="hidden h-8 w-px md:block" style={{ backgroundColor: 'var(--border-subtle)' }} />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* ─── 2. COST TREND (full width) ─── */}
      <Card>
        <h3 className="mb-4 text-sm font-medium" style={{ color: 'var(--text-muted)' }}>Cost Trend</h3>
        <CostTrendChart data={trendData} />
      </Card>

      {/* ─── 3. 2x2 GRID: Cost Distribution, Savings, CPU/Mem Gauge, Node Bars ─── */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card className="min-w-0 overflow-hidden">
          <h3 className="mb-4 text-sm font-medium" style={{ color: 'var(--text-muted)' }}>Cost Distribution</h3>
          <CostBreakdownChart data={costDistributionData} />
        </Card>
        <Card className="min-w-0 overflow-hidden">
          <h3 className="mb-4 text-sm font-medium" style={{ color: 'var(--text-muted)' }}>Cost Savings</h3>
          <SavingsWaterfallChart data={savingsItems} total={savingsTotal} />
        </Card>
        <Card className="min-w-0 overflow-hidden">
          <h3 className="mb-4 text-sm font-medium" style={{ color: 'var(--text-muted)' }}>CPU & Memory Utilization</h3>
          <ResourceUtilizationChart data={resourceData} />
        </Card>
        <Card className="min-w-0 overflow-hidden">
          <h3 className="mb-4 text-sm font-medium" style={{ color: 'var(--text-muted)' }}>Node Utilization</h3>
          <NodeUtilizationChart data={resourceData} />
        </Card>
      </div>

      {/* ─── 4. HPA + Anomaly ─── */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card className="min-w-0 overflow-hidden">
          <h3 className="mb-4 text-sm font-medium" style={{ color: 'var(--text-muted)' }}>HPA Impact</h3>
          <HpaComparisonChart data={hpaData} />
        </Card>
        <Card className="min-w-0 overflow-hidden">
          <h3 className="mb-4 text-sm font-medium" style={{ color: 'var(--text-muted)' }}>Anomaly Detection</h3>
          <AnomalyDetectionChart data={anomalyData as unknown as Parameters<typeof AnomalyDetectionChart>[0]['data']} />
        </Card>
      </div>

      {/* ─── 5. Namespace + Workload ─── */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {namespaceCosts.length > 0 && (
          <Card className="min-w-0 overflow-hidden">
            <h3 className="mb-4 text-sm font-medium" style={{ color: 'var(--text-muted)' }}>Namespace Costs</h3>
            <NamespaceCostsChart data={namespaceCosts} />
          </Card>
        )}
        {workloadCosts.length > 0 && (
          <Card className="min-w-0 overflow-hidden">
            <h3 className="mb-4 text-sm font-medium" style={{ color: 'var(--text-muted)' }}>Top Workloads</h3>
            <WorkloadCostsChart data={workloadCosts} />
          </Card>
        )}
      </div>

      {/* ─── 6. NODE OPTIMIZATION RECOMMENDATIONS ─── */}
      {nodeRecs.length > 0 && (
        <Card>
          <h3 className="mb-3 text-sm font-medium" style={{ color: 'var(--text-muted)' }}>
            Node Optimization Recommendations ({nodeRecs.length})
          </h3>
          <NodeRecommendationsTable data={nodeRecs} />
        </Card>
      )}

      {/* ─── 7. TOP RECOMMENDATIONS ─── */}
      {topRecs.length > 0 && (
        <Card>
          <h3 className="mb-3 text-sm font-medium" style={{ color: 'var(--text-muted)' }}>Top Recommendations</h3>
          <div className="space-y-2">
            {topRecs.slice(0, 5).map((rec, i) => (
              <div key={i} className="flex items-center justify-between rounded-lg border px-4 py-2.5" style={{ borderColor: 'var(--border-subtle)' }}>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>{rec.title || rec.description || String(rec)}</p>
                  {rec.title && rec.description && <p className="mt-0.5 truncate text-xs" style={{ color: 'var(--text-muted)' }}>{rec.description}</p>}
                </div>
                {rec.savings != null && rec.savings > 0 && (
                  <span className="ml-3 flex-shrink-0 text-sm font-medium text-green-600">{formatCurrency(rec.savings)}/mo</span>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* ─── 8. INSIGHTS ─── */}
      {insights.length > 0 && (
        <Card>
          <h3 className="mb-3 text-sm font-medium" style={{ color: 'var(--text-muted)' }}>Analysis Insights ({insights.length})</h3>
          <ul className="space-y-1.5 pl-1">
            {insights.slice(0, 15).map((insight, i) => (
              <li key={i} className="flex items-start gap-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
                <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-primary-500" />
                <span className="leading-snug">{insight.message}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  )
}
