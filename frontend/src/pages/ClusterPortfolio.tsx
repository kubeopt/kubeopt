import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, RefreshCw, Cloud, Search, Trash2, ArrowUpDown } from 'lucide-react'
import { useClusterStore, type Cluster } from '../store/clusterStore'
import { getClusters, getPortfolioSummary, removeCluster } from '../api/clusters'
import Card from '../components/common/Card'
import Button from '../components/common/Button'
import Badge from '../components/common/Badge'
import Modal from '../components/common/Modal'
import LoadingSpinner from '../components/common/LoadingSpinner'
import AddClusterModal from '../components/clusters/AddClusterModal'

type SortKey = 'name' | 'cost' | 'savings' | 'score'

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <Card>
      <div className="text-sm text-dark-500 dark:text-dark-400">{label}</div>
      <div className="mt-1 text-2xl font-bold text-dark-900 dark:text-white">{value}</div>
      {sub && <div className="mt-0.5 text-xs text-dark-400">{sub}</div>}
    </Card>
  )
}

function timeAgo(dateStr?: string): string {
  if (!dateStr) return 'Never'
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

function ClusterCard({
  cluster,
  onClick,
  onDelete,
}: {
  cluster: Cluster
  onClick: () => void
  onDelete: (e: React.MouseEvent) => void
}) {
  const providerColors: Record<string, string> = { azure: 'blue', aws: 'yellow', gcp: 'red' }
  return (
    <Card className="cursor-pointer transition-shadow hover:shadow-md" onClick={onClick}>
      <div className="flex items-start justify-between">
        <div className="min-w-0 flex-1">
          <h3 className="truncate font-semibold text-dark-900 dark:text-white">{cluster.cluster_name}</h3>
          <p className="mt-0.5 text-sm text-dark-500 dark:text-dark-400">{cluster.region || 'Unknown region'}</p>
        </div>
        <div className="ml-2 flex items-center gap-2">
          <Badge variant={providerColors[cluster.cloud_provider] as 'blue' | 'yellow' | 'red' || 'gray'}>
            {cluster.cloud_provider.toUpperCase()}
          </Badge>
          <button
            onClick={onDelete}
            className="rounded p-1 text-dark-300 hover:bg-red-50 hover:text-red-500 dark:hover:bg-red-900/20"
            title="Remove cluster"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>
      <div className="mt-3 text-xs text-dark-400">
        Analyzed: {timeAgo((cluster as unknown as Record<string, unknown>).last_analyzed as string | undefined)}
      </div>
      <div className="mt-2 grid grid-cols-3 gap-4 text-sm">
        <div>
          <div className="text-dark-400">Cost/mo</div>
          <div className="font-medium text-dark-800 dark:text-dark-200">${cluster.total_cost?.toFixed(0) ?? '—'}</div>
        </div>
        <div>
          <div className="text-dark-400">Savings</div>
          <div className="font-medium text-green-600">${cluster.potential_savings?.toFixed(0) ?? '—'}</div>
        </div>
        <div>
          <div className="text-dark-400">Score</div>
          <div className="font-medium text-dark-800 dark:text-dark-200">{cluster.optimization_score?.toFixed(0) ?? '—'}%</div>
        </div>
      </div>
    </Card>
  )
}

export default function ClusterPortfolio() {
  const { clusters, portfolioSummary, setClusters, setPortfolioSummary, loading, setLoading } = useClusterStore()
  const [error, setError] = useState('')
  const [showAddModal, setShowAddModal] = useState(false)
  const [search, setSearch] = useState('')
  const [sortBy, setSortBy] = useState<SortKey>('name')
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
    list = [...list].sort((a, b) => {
      switch (sortBy) {
        case 'cost': return (b.total_cost ?? 0) - (a.total_cost ?? 0)
        case 'savings': return (b.potential_savings ?? 0) - (a.potential_savings ?? 0)
        case 'score': return (b.optimization_score ?? 0) - (a.optimization_score ?? 0)
        default: return a.cluster_name.localeCompare(b.cluster_name)
      }
    })
    return list
  }, [clusters, search, sortBy])

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

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-dark-900 dark:text-white">Cluster Portfolio</h1>
          <p className="mt-1 text-sm text-dark-500 dark:text-dark-400">Manage and monitor your Kubernetes clusters</p>
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

      {/* Summary stats */}
      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Total Clusters" value={portfolioSummary.total_clusters} />
        <StatCard label="Monthly Cost" value={`$${portfolioSummary.total_monthly_cost.toFixed(0)}`} />
        <StatCard label="Potential Savings" value={`$${portfolioSummary.total_potential_savings.toFixed(0)}`} sub="per month" />
        <StatCard label="Total Nodes" value={portfolioSummary.total_nodes} />
      </div>

      {/* Search + sort bar */}
      {clusters.length > 0 && (
        <div className="mb-4 flex flex-wrap items-center gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-dark-400" />
            <input
              type="text"
              placeholder="Search clusters by name or region..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full rounded-lg border border-gray-300 py-2 pl-9 pr-3 text-sm focus:border-primary-500 focus:outline-none dark:border-dark-600 dark:bg-dark-800 dark:text-white"
            />
          </div>
          <div className="flex items-center gap-1.5">
            <ArrowUpDown className="h-4 w-4 text-dark-400" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortKey)}
              className="rounded-lg border border-gray-300 px-2 py-2 text-sm dark:border-dark-600 dark:bg-dark-800 dark:text-white"
            >
              <option value="name">Name</option>
              <option value="cost">Cost</option>
              <option value="savings">Savings</option>
              <option value="score">Score</option>
            </select>
          </div>
        </div>
      )}

      {error && (
        <div className="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-400">{error}</div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      ) : clusters.length === 0 ? (
        <Card className="py-12 text-center">
          <Cloud className="mx-auto h-12 w-12 text-dark-300 dark:text-dark-600" />
          <h3 className="mt-3 text-lg font-medium text-dark-700 dark:text-dark-300">No clusters yet</h3>
          <p className="mt-1 text-sm text-dark-500">Add your first Azure, AWS, or GCP cluster to get started.</p>
          <Button className="mt-4" size="sm" onClick={() => setShowAddModal(true)}>
            <Plus className="mr-1.5 h-4 w-4" /> Add Cluster
          </Button>
        </Card>
      ) : filtered.length === 0 ? (
        <Card className="py-8 text-center text-dark-400">
          No clusters match &ldquo;{search}&rdquo;
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {filtered.map((cluster) => (
            <ClusterCard
              key={cluster.cluster_id}
              cluster={cluster}
              onClick={() => navigate(`/cluster/${encodeURIComponent(cluster.cluster_id)}`)}
              onDelete={(e) => { e.stopPropagation(); setConfirmDelete(cluster) }}
            />
          ))}
        </div>
      )}

      <AddClusterModal open={showAddModal} onClose={() => setShowAddModal(false)} onAdded={fetchData} />

      {/* Delete confirmation */}
      <Modal open={!!confirmDelete} onClose={() => setConfirmDelete(null)} title="Remove Cluster">
        <p className="text-sm text-dark-600 dark:text-dark-300">
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
