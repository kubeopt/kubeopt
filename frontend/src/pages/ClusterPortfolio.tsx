import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, RefreshCw, Search, Trash2, ArrowUpDown, DollarSign, TrendingDown, Server, BarChart3, LayoutGrid, List } from 'lucide-react'
import { useClusterStore, type Cluster } from '../store/clusterStore'
import { getClusters, getPortfolioSummary, removeCluster } from '../api/clusters'
import { formatCurrency } from '../utils/format'
import Card from '../components/common/Card'
import Button from '../components/common/Button'
import Badge from '../components/common/Badge'
import Modal from '../components/common/Modal'
import LoadingSpinner from '../components/common/LoadingSpinner'
import AddClusterModal from '../components/clusters/AddClusterModal'

type SortKey = 'name' | 'cost' | 'savings' | 'score'
type ViewMode = 'table' | 'cards'
type ProviderFilter = 'all' | 'azure' | 'aws' | 'gcp'

function timeAgo(dateStr?: string): string {
  if (!dateStr) return 'Never'
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

function ScoreBadge({ score }: { score: number }) {
  const color = score >= 80 ? 'green' : score >= 60 ? 'yellow' : 'red'
  return <Badge variant={color}>{score.toFixed(0)}%</Badge>
}

function CostBar({ cost, maxCost }: { cost: number; maxCost: number }) {
  const pct = maxCost > 0 ? Math.min((cost / maxCost) * 100, 100) : 0
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-20 overflow-hidden rounded-full" style={{ backgroundColor: 'var(--border-subtle)' }}>
        <div className="h-full rounded-full bg-primary-500" style={{ width: `${pct}%` }} />
      </div>
      <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>{formatCurrency(cost)}</span>
    </div>
  )
}

export default function ClusterPortfolio() {
  const { clusters, portfolioSummary, setClusters, setPortfolioSummary, loading, setLoading } = useClusterStore()
  const [error, setError] = useState('')
  const [showAddModal, setShowAddModal] = useState(false)
  const [search, setSearch] = useState('')
  const [sortBy, setSortBy] = useState<SortKey>('cost')
  const [viewMode, setViewMode] = useState<ViewMode>('table')
  const [providerFilter, setProviderFilter] = useState<ProviderFilter>('all')
  const [confirmDelete, setConfirmDelete] = useState<Cluster | null>(null)
  const [deleting, setDeleting] = useState(false)
  const navigate = useNavigate()

  const fetchData = async () => {
    setLoading(true)
    setError('')
    try {
      const [clusterRes, summaryRes] = await Promise.all([getClusters(), getPortfolioSummary()])
      setClusters(clusterRes.clusters)
      setPortfolioSummary(summaryRes)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load clusters')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchData() }, [])

  const filtered = useMemo(() => {
    const q = search.toLowerCase()
    let list = clusters.filter(
      (c) =>
        c.cluster_name.toLowerCase().includes(q) ||
        (c.region || '').toLowerCase().includes(q),
    )
    if (providerFilter !== 'all') list = list.filter((c) => c.cloud_provider === providerFilter)
    list = [...list].sort((a, b) => {
      switch (sortBy) {
        case 'cost': return (b.total_cost ?? 0) - (a.total_cost ?? 0)
        case 'savings': return (b.potential_savings ?? 0) - (a.potential_savings ?? 0)
        case 'score': return (b.optimization_score ?? 0) - (a.optimization_score ?? 0)
        default: return a.cluster_name.localeCompare(b.cluster_name)
      }
    })
    return list
  }, [clusters, search, sortBy, providerFilter])

  const maxCost = useMemo(() => Math.max(...clusters.map((c) => c.total_cost ?? 0), 1), [clusters])

  const handleDelete = async () => {
    if (!confirmDelete) return
    setDeleting(true)
    try {
      await removeCluster(confirmDelete.cluster_id)
      setConfirmDelete(null)
      await fetchData()
    } catch {
      setError('Failed to delete cluster')
    } finally {
      setDeleting(false)
    }
  }

  const providerCounts = useMemo(() => ({
    all: clusters.length,
    azure: clusters.filter((c) => c.cloud_provider === 'azure').length,
    aws: clusters.filter((c) => c.cloud_provider === 'aws').length,
    gcp: clusters.filter((c) => c.cloud_provider === 'gcp').length,
  }), [clusters])

  const savingsPercent = portfolioSummary.total_monthly_cost > 0
    ? ((portfolioSummary.total_potential_savings / portfolioSummary.total_monthly_cost) * 100).toFixed(0)
    : '0'

  return (
    <div>
      {/* ─── Page Header ─── */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>Cluster Portfolio</h1>
          <p className="mt-1 text-sm" style={{ color: 'var(--text-muted)' }}>Monitor and optimize your Kubernetes infrastructure costs</p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" onClick={fetchData}>
            <RefreshCw className="mr-1.5 h-4 w-4" /> Refresh
          </Button>
          <Button size="sm" onClick={() => setShowAddModal(true)}>
            <Plus className="mr-1.5 h-4 w-4" /> Add Cluster
          </Button>
        </div>
      </div>

      {/* ─── Hero Stats ─── */}
      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="relative overflow-hidden">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-primary-100 p-2.5 dark:bg-primary-900/30">
              <Server className="h-5 w-5 text-primary-600 dark:text-primary-400" />
            </div>
            <div>
              <div className="text-xs font-medium uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Clusters</div>
              <div className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>{portfolioSummary.total_clusters}</div>
            </div>
          </div>
          <div className="mt-2 text-xs" style={{ color: 'var(--text-muted)' }}>{portfolioSummary.total_nodes} total nodes</div>
        </Card>

        <Card className="relative overflow-hidden">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-primary-100 p-2.5 dark:bg-primary-900/30">
              <DollarSign className="h-5 w-5 text-primary-600 dark:text-primary-400" />
            </div>
            <div>
              <div className="text-xs font-medium uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Monthly Spend</div>
              <div className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>{formatCurrency(portfolioSummary.total_monthly_cost)}</div>
            </div>
          </div>
          <div className="mt-2 text-xs" style={{ color: 'var(--text-muted)' }}>across all clusters</div>
        </Card>

        <Card className="relative overflow-hidden border-green-200 dark:border-green-900/40" style={{ background: 'var(--accent-glow)' }}>
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-green-100 p-2.5 dark:bg-green-900/30">
              <TrendingDown className="h-5 w-5 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <div className="text-xs font-medium uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Savings Available</div>
              <div className="text-2xl font-bold text-green-600 dark:text-green-400">{formatCurrency(portfolioSummary.total_potential_savings)}</div>
            </div>
          </div>
          <div className="mt-2 text-xs font-medium text-green-600 dark:text-green-400">{savingsPercent}% of total spend</div>
        </Card>

        <Card className="relative overflow-hidden">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-primary-100 p-2.5 dark:bg-primary-900/30">
              <BarChart3 className="h-5 w-5 text-primary-600 dark:text-primary-400" />
            </div>
            <div>
              <div className="text-xs font-medium uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Avg Score</div>
              <div className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>
                {portfolioSummary.average_optimization_score?.toFixed(0) ?? '—'}%
              </div>
            </div>
          </div>
          <div className="mt-2 text-xs" style={{ color: 'var(--text-muted)' }}>{portfolioSummary.clusters_needing_attention || 0} need attention</div>
        </Card>
      </div>

      {/* ─── Provider Filter Tabs + Search + Sort + View Toggle ─── */}
      {clusters.length > 0 && (
        <div className="mb-4 flex flex-wrap items-center gap-3">
          {/* Provider tabs */}
          <div className="flex rounded-lg border" style={{ borderColor: 'var(--border-color)' }}>
            {(['all', 'azure', 'aws', 'gcp'] as ProviderFilter[]).map((p) => (
              <button
                key={p}
                onClick={() => setProviderFilter(p)}
                className={`px-3 py-1.5 text-xs font-medium transition-colors ${
                  p === 'all' ? 'rounded-l-lg' : p === 'gcp' ? 'rounded-r-lg' : ''
                } ${
                  providerFilter === p
                    ? 'bg-primary-500 text-white'
                    : ''
                }`}
                style={providerFilter !== p ? { color: 'var(--text-secondary)' } : undefined}
              >
                {p === 'all' ? 'All' : p.toUpperCase()} {providerCounts[p] > 0 ? `(${providerCounts[p]})` : ''}
              </button>
            ))}
          </div>

          {/* Search */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2" style={{ color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="Search clusters..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full rounded-lg border py-2 pl-9 pr-3 text-sm focus:border-primary-500 focus:outline-none dark:bg-dark-800 dark:text-white"
              style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--bg-surface)' }}
            />
          </div>

          {/* Sort */}
          <div className="flex items-center gap-1.5">
            <ArrowUpDown className="h-4 w-4" style={{ color: 'var(--text-muted)' }} />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortKey)}
              className="rounded-lg border px-2 py-2 text-sm dark:bg-dark-800 dark:text-white"
              style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--bg-surface)' }}
            >
              <option value="cost">Cost</option>
              <option value="savings">Savings</option>
              <option value="score">Score</option>
              <option value="name">Name</option>
            </select>
          </div>

          {/* View toggle */}
          <div className="flex rounded-lg border" style={{ borderColor: 'var(--border-color)' }}>
            <button
              onClick={() => setViewMode('table')}
              className={`rounded-l-lg p-2 ${viewMode === 'table' ? 'bg-primary-500 text-white' : ''}`}
              style={viewMode !== 'table' ? { color: 'var(--text-muted)' } : undefined}
              title="Table view"
            >
              <List className="h-4 w-4" />
            </button>
            <button
              onClick={() => setViewMode('cards')}
              className={`rounded-r-lg p-2 ${viewMode === 'cards' ? 'bg-primary-500 text-white' : ''}`}
              style={viewMode !== 'cards' ? { color: 'var(--text-muted)' } : undefined}
              title="Card view"
            >
              <LayoutGrid className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {error && (
        <div className="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-400">{error}</div>
      )}

      {/* ─── Content ─── */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      ) : clusters.length === 0 ? (
        <Card className="py-16 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary-100 dark:bg-primary-900/30">
            <Server className="h-8 w-8 text-primary-500" />
          </div>
          <h3 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>No clusters yet</h3>
          <p className="mt-2 text-sm" style={{ color: 'var(--text-muted)' }}>
            Connect your first Azure AKS, AWS EKS, or GCP GKE cluster to start optimizing.
          </p>
          <Button className="mt-5" size="sm" onClick={() => setShowAddModal(true)}>
            <Plus className="mr-1.5 h-4 w-4" /> Add Your First Cluster
          </Button>
        </Card>
      ) : filtered.length === 0 ? (
        <Card className="py-8 text-center" style={{ color: 'var(--text-muted)' }}>
          No clusters match your search
        </Card>
      ) : viewMode === 'table' ? (
        /* ─── Table View ─── */
        <Card padding={false}>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b text-xs uppercase" style={{ borderColor: 'var(--border-subtle)', color: 'var(--text-muted)' }}>
                <tr>
                  <th className="px-5 py-3.5">Cluster</th>
                  <th className="px-5 py-3.5">Provider</th>
                  <th className="px-5 py-3.5">Region</th>
                  <th className="px-5 py-3.5">Monthly Cost</th>
                  <th className="px-5 py-3.5">Savings</th>
                  <th className="px-5 py-3.5">Score</th>
                  <th className="px-5 py-3.5">Nodes</th>
                  <th className="px-5 py-3.5">Last Analyzed</th>
                  <th className="px-5 py-3.5"></th>
                </tr>
              </thead>
              <tbody className="divide-y" style={{ borderColor: 'var(--border-subtle)' }}>
                {filtered.map((cluster) => (
                  <tr
                    key={cluster.cluster_id}
                    className="cursor-pointer transition-colors hover:bg-primary-50/50 dark:hover:bg-dark-800/50"
                    onClick={() => navigate(`/cluster/${encodeURIComponent(cluster.cluster_id)}`)}
                  >
                    <td className="px-5 py-3.5">
                      <div className="font-semibold" style={{ color: 'var(--text-primary)' }}>{cluster.cluster_name}</div>
                    </td>
                    <td className="px-5 py-3.5">
                      <Badge variant={
                        cluster.cloud_provider === 'azure' ? 'blue'
                          : cluster.cloud_provider === 'aws' ? 'yellow'
                          : cluster.cloud_provider === 'gcp' ? 'red'
                          : 'gray'
                      }>
                        {cluster.cloud_provider.toUpperCase()}
                      </Badge>
                    </td>
                    <td className="px-5 py-3.5 text-xs" style={{ color: 'var(--text-muted)' }}>{cluster.region || '—'}</td>
                    <td className="px-5 py-3.5">
                      <CostBar cost={cluster.total_cost ?? 0} maxCost={maxCost} />
                    </td>
                    <td className="px-5 py-3.5">
                      <span className="text-sm font-medium text-green-600 dark:text-green-400">
                        {formatCurrency(cluster.potential_savings ?? 0)}
                      </span>
                    </td>
                    <td className="px-5 py-3.5">
                      <ScoreBadge score={cluster.optimization_score ?? 0} />
                    </td>
                    <td className="px-5 py-3.5" style={{ color: 'var(--text-secondary)' }}>{cluster.node_count ?? '—'}</td>
                    <td className="px-5 py-3.5 text-xs" style={{ color: 'var(--text-muted)' }}>
                      {timeAgo((cluster as unknown as Record<string, unknown>).last_analyzed as string | undefined)}
                    </td>
                    <td className="px-5 py-3.5">
                      <button
                        onClick={(e) => { e.stopPropagation(); setConfirmDelete(cluster) }}
                        className="rounded p-1.5 transition-colors hover:bg-red-50 hover:text-red-500 dark:hover:bg-red-900/20"
                        style={{ color: 'var(--text-muted)' }}
                        title="Remove cluster"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      ) : (
        /* ─── Card View ─── */
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {filtered.map((cluster) => (
            <Card
              key={cluster.cluster_id}
              className="cursor-pointer"
              onClick={() => navigate(`/cluster/${encodeURIComponent(cluster.cluster_id)}`)}
            >
              <div className="flex items-start justify-between">
                <div className="min-w-0 flex-1">
                  <h3 className="truncate font-semibold" style={{ color: 'var(--text-primary)' }}>{cluster.cluster_name}</h3>
                  <div className="mt-1 flex items-center gap-2">
                    <Badge variant={
                      cluster.cloud_provider === 'azure' ? 'blue'
                        : cluster.cloud_provider === 'aws' ? 'yellow'
                        : cluster.cloud_provider === 'gcp' ? 'red'
                        : 'gray'
                    }>
                      {cluster.cloud_provider.toUpperCase()}
                    </Badge>
                    <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{cluster.region || 'Unknown'}</span>
                  </div>
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); setConfirmDelete(cluster) }}
                  className="rounded p-1.5 transition-colors hover:bg-red-50 hover:text-red-500 dark:hover:bg-red-900/20"
                  style={{ color: 'var(--text-muted)' }}
                  title="Remove cluster"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>

              {/* Score + Cost inline */}
              <div className="mt-4 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <ScoreBadge score={cluster.optimization_score ?? 0} />
                  <span className="text-xs" style={{ color: 'var(--text-muted)' }}>optimization</span>
                </div>
                <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                  {timeAgo((cluster as unknown as Record<string, unknown>).last_analyzed as string | undefined)}
                </span>
              </div>

              {/* Cost bar */}
              <div className="mt-3">
                <CostBar cost={cluster.total_cost ?? 0} maxCost={maxCost} />
              </div>

              {/* Bottom row */}
              <div className="mt-3 flex items-center justify-between border-t pt-3" style={{ borderColor: 'var(--border-subtle)' }}>
                <div>
                  <div className="text-xs" style={{ color: 'var(--text-muted)' }}>Savings</div>
                  <div className="text-sm font-semibold text-green-600 dark:text-green-400">{formatCurrency(cluster.potential_savings ?? 0)}</div>
                </div>
                <div className="text-right">
                  <div className="text-xs" style={{ color: 'var(--text-muted)' }}>Nodes</div>
                  <div className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{cluster.node_count ?? '—'}</div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      <AddClusterModal open={showAddModal} onClose={() => setShowAddModal(false)} onAdded={fetchData} />

      {/* Delete confirmation */}
      <Modal open={!!confirmDelete} onClose={() => setConfirmDelete(null)} title="Remove Cluster">
        <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
          Are you sure you want to remove <strong>{confirmDelete?.cluster_name}</strong>? This will delete all analysis data for this cluster.
        </p>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="secondary" size="sm" onClick={() => setConfirmDelete(null)}>Cancel</Button>
          <Button variant="danger" size="sm" onClick={handleDelete} disabled={deleting}>
            {deleting ? 'Removing...' : 'Remove'}
          </Button>
        </div>
      </Modal>
    </div>
  )
}
