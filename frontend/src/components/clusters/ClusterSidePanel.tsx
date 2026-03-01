import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { X, Play, ExternalLink, Server, DollarSign, TrendingDown, Activity, ChevronRight, ChevronLeft } from 'lucide-react'
import { analyzeCluster } from '../../api/clusters'
import { getDashboardOverview } from '../../api/analysis'
import { formatCurrency } from '../../utils/format'
import Badge from '../common/Badge'
import Button from '../common/Button'
import type { Cluster } from '../../store/clusterStore'

interface ClusterSidePanelProps {
  cluster: Cluster | null
  onClose: () => void
}

function ScoreRing({ score, size = 56 }: { score: number; size?: number }) {
  const radius = (size - 8) / 2
  const circumference = 2 * Math.PI * radius
  const progress = (score / 100) * circumference
  const color = score >= 80 ? '#7FB069' : score >= 60 ? '#eab308' : '#ef4444'

  return (
    <svg width={size} height={size} className="-rotate-90">
      <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="var(--border-subtle)" strokeWidth={3} />
      <circle
        cx={size / 2} cy={size / 2} r={radius} fill="none"
        stroke={color} strokeWidth={3}
        strokeDasharray={circumference}
        strokeDashoffset={circumference - progress}
        strokeLinecap="round"
        className="transition-all duration-700"
      />
      <text
        x={size / 2} y={size / 2}
        textAnchor="middle" dominantBaseline="central"
        className="fill-current"
        style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)' }}
        transform={`rotate(90, ${size / 2}, ${size / 2})`}
      >
        {score.toFixed(0)}%
      </text>
    </svg>
  )
}

function timeAgo(dateStr?: string): string {
  if (!dateStr) return 'Never analyzed'
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

export default function ClusterSidePanel({ cluster, onClose }: ClusterSidePanelProps) {
  const navigate = useNavigate()
  const [overview, setOverview] = useState<Record<string, unknown> | null>(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [expanded, setExpanded] = useState(true)

  useEffect(() => {
    if (!cluster) return
    setOverview(null)
    setExpanded(true)
    getDashboardOverview(cluster.cluster_id)
      .then((data) => setOverview(data as Record<string, unknown>))
      .catch(() => {})
  }, [cluster])

  if (!cluster) return null

  const score = cluster.optimization_score ?? (overview?.optimization_score as number) ?? 0
  const monthlyCost = cluster.total_cost ?? (overview?.total_monthly_cost as number) ?? 0
  const savings = cluster.potential_savings ?? (overview?.potential_savings as number) ?? 0
  const nodeCount = cluster.node_count ?? (overview?.node_count as number) ?? 0
  const healthScore = (overview?.health_score as number) ?? 0
  const providerColors: Record<string, 'blue' | 'yellow' | 'red'> = { azure: 'blue', aws: 'yellow', gcp: 'red' }

  const handleAnalyze = async () => {
    setAnalyzing(true)
    try {
      await analyzeCluster(cluster.cluster_id)
    } catch { /* empty */ }
    finally { setAnalyzing(false) }
  }

  // Collapsed state — just a thin strip
  if (!expanded) {
    return (
      <div
        className="flex w-10 flex-shrink-0 cursor-pointer flex-col items-center border-l pt-4 transition-all"
        style={{ backgroundColor: 'var(--bg-surface)', borderColor: 'var(--border-color)' }}
        onClick={() => setExpanded(true)}
      >
        <ChevronLeft className="h-4 w-4" style={{ color: 'var(--text-muted)' }} />
        <div className="mt-4 [writing-mode:vertical-lr] text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>
          {cluster.cluster_name}
        </div>
        <div className="mt-2">
          <ScoreRing score={score} size={32} />
        </div>
      </div>
    )
  }

  return (
    <div
      className="flex w-80 flex-shrink-0 flex-col border-l transition-all xl:w-96"
      style={{ backgroundColor: 'var(--bg-surface)', borderColor: 'var(--border-color)' }}
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b p-4" style={{ borderColor: 'var(--border-color)' }}>
        <div className="min-w-0 flex-1">
          <h2 className="truncate text-sm font-bold" style={{ color: 'var(--text-primary)' }}>{cluster.cluster_name}</h2>
          <div className="mt-1 flex items-center gap-2">
            <Badge variant={providerColors[cluster.cloud_provider] || 'gray'}>
              {cluster.cloud_provider.toUpperCase()}
            </Badge>
            <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{cluster.region || 'Unknown'}</span>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setExpanded(false)}
            className="rounded-lg p-1.5 transition-colors hover:bg-primary-50 dark:hover:bg-dark-800"
            style={{ color: 'var(--text-muted)' }}
            title="Collapse"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 transition-colors hover:bg-primary-50 dark:hover:bg-dark-800"
            style={{ color: 'var(--text-muted)' }}
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Score */}
      <div className="flex items-center gap-4 border-b p-4" style={{ borderColor: 'var(--border-color)' }}>
        <ScoreRing score={score} />
        <div>
          <div className="text-xs font-medium uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Score</div>
          <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
            {timeAgo((cluster as unknown as Record<string, unknown>).last_analyzed as string | undefined)}
          </div>
        </div>
      </div>

      {/* Metrics grid */}
      <div className="grid grid-cols-2 gap-px border-b" style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--border-subtle)' }}>
        {[
          { icon: DollarSign, label: 'Monthly Cost', value: formatCurrency(monthlyCost), color: 'var(--text-primary)' },
          { icon: TrendingDown, label: 'Savings', value: formatCurrency(savings), color: '#7FB069' },
          { icon: Server, label: 'Nodes', value: String(nodeCount), color: 'var(--text-primary)' },
          { icon: Activity, label: 'Health', value: `${healthScore.toFixed(0)}%`, color: healthScore >= 80 ? '#7FB069' : healthScore >= 60 ? '#eab308' : '#ef4444' },
        ].map((m) => (
          <div key={m.label} className="p-3" style={{ backgroundColor: 'var(--bg-surface)' }}>
            <div className="flex items-center gap-1.5">
              <m.icon className="h-3 w-3" style={{ color: 'var(--text-muted)' }} />
              <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{m.label}</span>
            </div>
            <div className="mt-0.5 text-lg font-bold" style={{ color: m.color }}>{m.value}</div>
          </div>
        ))}
      </div>

      {/* Savings bar */}
      {monthlyCost > 0 && savings > 0 && (
        <div className="border-b p-4" style={{ borderColor: 'var(--border-color)' }}>
          <div className="mb-1.5 flex items-center justify-between">
            <span className="text-[10px] font-medium uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Savings Opportunity</span>
            <span className="text-xs font-medium text-primary-600">{((savings / monthlyCost) * 100).toFixed(0)}%</span>
          </div>
          <div className="h-1.5 overflow-hidden rounded-full" style={{ backgroundColor: 'var(--border-subtle)' }}>
            <div
              className="h-full rounded-full bg-primary-500 transition-all duration-700"
              style={{ width: `${Math.min((savings / monthlyCost) * 100, 100)}%` }}
            />
          </div>
          <div className="mt-1 flex justify-between text-[10px]" style={{ color: 'var(--text-muted)' }}>
            <span>Current: {formatCurrency(monthlyCost)}/mo</span>
            <span>Save: {formatCurrency(savings)}/mo</span>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="mt-auto border-t p-4" style={{ borderColor: 'var(--border-color)' }}>
        <div className="flex gap-2">
          <Button
            className="flex-1"
            size="sm"
            onClick={() => navigate(`/cluster/${encodeURIComponent(cluster.cluster_id)}`)}
          >
            <ExternalLink className="mr-1.5 h-3.5 w-3.5" />
            Dashboard
          </Button>
          <Button variant="secondary" size="sm" onClick={handleAnalyze} disabled={analyzing}>
            <Play className="mr-1.5 h-3.5 w-3.5" />
            {analyzing ? 'Running...' : 'Analyze'}
          </Button>
        </div>
      </div>
    </div>
  )
}
