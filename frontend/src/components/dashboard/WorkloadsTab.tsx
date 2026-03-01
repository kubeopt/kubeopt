import { useCallback, useEffect, useMemo, useState } from 'react'
import { ChevronDown, ChevronUp, RefreshCw } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { api } from '../../api/client'
import Card from '../common/Card'
import Badge from '../common/Badge'
import { TableSkeleton } from '../common/Skeleton'

interface WorkloadsTabProps {
  clusterId: string
  subscriptionId: string
}

interface Workload {
  name: string
  namespace: string
  type: string
  replicas?: number | { current?: number; desired?: number }
  ready?: number
  image?: string
  status?: string
  health_score?: number
  hpa_enabled?: boolean
}

interface WorkloadSummary {
  healthy_count?: number
  warning_count?: number
  critical_count?: number
  total_replicas?: number
  avg_health_score?: number
}

type SortKey = 'name' | 'namespace' | 'type' | 'replicas' | 'health_score' | 'status'

function SortHeader({
  label,
  sortKey,
  active,
  direction,
  onSort,
}: {
  label: string
  sortKey: SortKey
  active: boolean
  direction: 'asc' | 'desc'
  onSort: (key: SortKey) => void
}) {
  return (
    <th
      className="cursor-pointer select-none px-4 py-3 hover:text-dark-700 dark:hover:text-dark-200"
      onClick={() => onSort(sortKey)}
    >
      <span className="inline-flex items-center gap-1">
        {label}
        {active && (direction === 'asc' ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />)}
      </span>
    </th>
  )
}

function getReplicaCounts(w: Workload): { current: number; desired: number } {
  if (typeof w.replicas === 'object' && w.replicas !== null) {
    return { current: w.replicas.current ?? 0, desired: w.replicas.desired ?? 0 }
  }
  return { current: w.ready ?? (w.replicas as number ?? 0), desired: (w.replicas as number) ?? 0 }
}

function getWorkloadStatus(w: Workload): string {
  if (w.status) return w.status
  const { current, desired } = getReplicaCounts(w)
  if (desired === 0) return 'unknown'
  if (current === desired) return 'healthy'
  if (current === 0) return 'critical'
  return 'warning'
}

function getHealthScore(w: Workload): number {
  if (w.health_score !== undefined) return w.health_score
  const { current, desired } = getReplicaCounts(w)
  return desired > 0 ? Math.round((current / desired) * 100) : 50
}

const DARK_TOOLTIP = {
  contentStyle: { backgroundColor: '#1f2937', border: 'none', borderRadius: 8, color: '#e5e7eb', fontSize: 12 },
  itemStyle: { color: '#d1d5db' },
  labelStyle: { color: '#9ca3af' },
}

export default function WorkloadsTab({ clusterId, subscriptionId }: WorkloadsTabProps) {
  const [workloads, setWorkloads] = useState<Workload[]>([])
  const [summary, setSummary] = useState<WorkloadSummary>({})
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [search, setSearch] = useState('')
  const [nsFilter, setNsFilter] = useState('All')
  const [statusFilter, setStatusFilter] = useState('All')
  const [sortKey, setSortKey] = useState<SortKey>('name')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')

  const fetchData = useCallback(async (showRefresh = false) => {
    if (showRefresh) setRefreshing(true)
    else setLoading(true)
    try {
      const url = subscriptionId
        ? `/api/kubernetes/workloads/${encodeURIComponent(clusterId)}/${encodeURIComponent(subscriptionId)}`
        : `/api/kubernetes/workloads-by-cluster?cluster_id=${encodeURIComponent(clusterId)}`
      const data = await api.get<{
        workloads?: Workload[]
        deployments?: Workload[]
        statefulsets?: Workload[]
        daemonsets?: Workload[]
        summary?: WorkloadSummary
        total_count?: number
      }>(url)

      // Handle both flat workloads[] and split deployments/statefulsets/daemonsets responses
      let all: Workload[]
      if (data.workloads) {
        all = data.workloads
      } else {
        all = [
          ...(data.deployments || []).map((w) => ({ ...w, type: w.type || 'Deployment' })),
          ...(data.statefulsets || []).map((w) => ({ ...w, type: w.type || 'StatefulSet' })),
          ...(data.daemonsets || []).map((w) => ({ ...w, type: w.type || 'DaemonSet' })),
        ]
      }
      setWorkloads(all)
      setSummary(data.summary || {})
    } catch {
      setWorkloads([])
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [clusterId, subscriptionId])

  useEffect(() => { fetchData() }, [fetchData])

  const handleSort = (key: SortKey) => {
    if (key === sortKey) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    else { setSortKey(key); setSortDir('asc') }
  }

  const namespaces = useMemo(() => [...new Set(workloads.map((w) => w.namespace))].sort(), [workloads])

  const filtered = useMemo(() => {
    const q = search.toLowerCase()
    let list = workloads.filter(
      (w) => w.name.toLowerCase().includes(q) || w.namespace.toLowerCase().includes(q),
    )
    if (nsFilter !== 'All') list = list.filter((w) => w.namespace === nsFilter)
    if (statusFilter !== 'All') list = list.filter((w) => getWorkloadStatus(w) === statusFilter)
    return [...list].sort((a, b) => {
      let cmp = 0
      switch (sortKey) {
        case 'replicas': cmp = getReplicaCounts(a).desired - getReplicaCounts(b).desired; break
        case 'health_score': cmp = getHealthScore(a) - getHealthScore(b); break
        default: cmp = String(a[sortKey] ?? '').localeCompare(String(b[sortKey] ?? ''))
      }
      return sortDir === 'desc' ? -cmp : cmp
    })
  }, [workloads, search, nsFilter, statusFilter, sortKey, sortDir])

  // Chart data
  const healthChartData = useMemo(() => {
    const healthy = workloads.filter((w) => getWorkloadStatus(w) === 'healthy').length
    const warning = workloads.filter((w) => getWorkloadStatus(w) === 'warning').length
    const critical = workloads.filter((w) => getWorkloadStatus(w) === 'critical').length
    return [
      { name: 'Healthy', value: healthy, color: '#7FB069' },
      { name: 'Warning', value: warning, color: '#eab308' },
      { name: 'Critical', value: critical, color: '#ef4444' },
    ].filter((d) => d.value > 0)
  }, [workloads])

  const nsDistData = useMemo(() => {
    const nsMap: Record<string, number> = {}
    workloads.forEach((w) => { nsMap[w.namespace] = (nsMap[w.namespace] || 0) + 1 })
    return Object.entries(nsMap)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 8)
      .map(([ns, count]) => ({ namespace: ns, count }))
  }, [workloads])

  const topReplicaData = useMemo(() => {
    return [...workloads]
      .sort((a, b) => getReplicaCounts(b).desired - getReplicaCounts(a).desired)
      .slice(0, 8)
      .map((w) => ({ name: w.name.length > 25 ? w.name.slice(0, 24) + '\u2026' : w.name, replicas: getReplicaCounts(w).desired }))
  }, [workloads])

  // Summary values
  const totalDeployments = workloads.filter((w) => w.type === 'Deployment').length
  const totalReplicas = summary.total_replicas ?? workloads.reduce((s, w) => s + getReplicaCounts(w).desired, 0)
  const avgHealth = summary.avg_health_score ?? (workloads.length > 0 ? workloads.reduce((s, w) => s + getHealthScore(w), 0) / workloads.length : 0)

  const resetFilters = () => { setSearch(''); setNsFilter('All'); setStatusFilter('All') }

  if (loading) return <Card padding={false}><TableSkeleton rows={8} /></Card>

  return (
    <div className="space-y-6">
      {/* ─── Header: Workloads Overview ─── */}
      <div>
        <h2 className="text-lg font-semibold text-dark-900 dark:text-white">Workloads Overview</h2>
        <div className="mt-2 flex flex-wrap items-center gap-3">
          <span className="rounded-full bg-gray-100 px-3 py-1 text-sm font-medium text-dark-700 dark:bg-dark-700 dark:text-dark-200">
            {totalDeployments} Deployments
          </span>
          <span className="rounded-full bg-gray-100 px-3 py-1 text-sm font-medium text-dark-700 dark:bg-dark-700 dark:text-dark-200">
            {totalReplicas} Total Replicas
          </span>
          <span className="rounded-full bg-green-100 px-3 py-1 text-sm font-medium text-green-800 dark:bg-green-900/30 dark:text-green-400">
            Health Score: {avgHealth.toFixed(0)}%
          </span>
        </div>
      </div>

      {/* ─── 3 Charts Row ─── */}
      {workloads.length > 0 && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Health Status Overview */}
          <Card>
            <h3 className="mb-3 text-sm font-medium text-dark-500 dark:text-dark-400">Health Status Overview</h3>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={healthChartData} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
                <XAxis dataKey="name" fontSize={11} tick={{ fill: '#6b7280' }} axisLine={false} tickLine={false} />
                <YAxis fontSize={11} tick={{ fill: '#6b7280' }} axisLine={false} tickLine={false} allowDecimals={false} />
                <Tooltip {...DARK_TOOLTIP} />
                <Bar dataKey="value" radius={[4, 4, 0, 0]} barSize={32}>
                  {healthChartData.map((d, i) => (
                    <Cell key={i} fill={d.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Card>

          {/* Namespace Distribution */}
          <Card>
            <h3 className="mb-3 text-sm font-medium text-dark-500 dark:text-dark-400">Namespace Distribution</h3>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={nsDistData} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
                <XAxis dataKey="namespace" fontSize={9} tick={{ fill: '#6b7280' }} axisLine={false} tickLine={false} angle={-30} textAnchor="end" height={40} />
                <YAxis fontSize={11} tick={{ fill: '#6b7280' }} axisLine={false} tickLine={false} allowDecimals={false} />
                <Tooltip {...DARK_TOOLTIP} />
                <Bar dataKey="count" name="Workloads" fill="#5f9548" radius={[4, 4, 0, 0]} barSize={24} />
              </BarChart>
            </ResponsiveContainer>
          </Card>

          {/* Top Replica Count */}
          <Card>
            <h3 className="mb-3 text-sm font-medium text-dark-500 dark:text-dark-400">Top Replica Count</h3>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={topReplicaData} layout="vertical" margin={{ top: 4, right: 12, bottom: 4, left: 4 }}>
                <XAxis type="number" fontSize={11} tick={{ fill: '#6b7280' }} axisLine={false} tickLine={false} allowDecimals={false} />
                <YAxis type="category" dataKey="name" width={100} fontSize={10} tick={{ fill: '#6b7280' }} axisLine={false} tickLine={false} />
                <Tooltip {...DARK_TOOLTIP} />
                <Bar dataKey="replicas" name="Replicas" fill="#7FB069" radius={[0, 4, 4, 0]} barSize={16} />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </div>
      )}

      {/* ─── Filters ─── */}
      <Card padding={false}>
        <div className="flex flex-wrap items-center gap-3 border-b border-gray-200 p-4 dark:border-dark-700">
          <input
            type="text"
            placeholder="Search workloads..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full max-w-xs rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none dark:border-dark-600 dark:bg-dark-800 dark:text-white"
          />
          <select
            value={nsFilter}
            onChange={(e) => setNsFilter(e.target.value)}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-dark-600 dark:bg-dark-800 dark:text-white"
          >
            <option value="All">All Namespaces</option>
            {namespaces.map((ns) => (
              <option key={ns} value={ns}>{ns}</option>
            ))}
          </select>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-dark-600 dark:bg-dark-800 dark:text-white"
          >
            <option value="All">All Statuses</option>
            <option value="healthy">Healthy</option>
            <option value="warning">Warning</option>
            <option value="critical">Critical</option>
          </select>
          <button
            onClick={resetFilters}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm text-dark-600 hover:bg-gray-50 dark:border-dark-600 dark:text-dark-300 dark:hover:bg-dark-800"
          >
            Reset
          </button>
          <button
            onClick={() => fetchData(true)}
            disabled={refreshing}
            className="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 px-3 py-2 text-sm text-dark-600 hover:bg-gray-50 dark:border-dark-600 dark:text-dark-300 dark:hover:bg-dark-800"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <span className="ml-auto text-sm text-dark-400">{filtered.length} workloads</span>
        </div>

        {/* ─── Deployment Details Table ─── */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-gray-200 text-xs uppercase text-dark-500 dark:border-dark-700 dark:text-dark-400">
              <tr>
                <SortHeader label="Name" sortKey="name" active={sortKey === 'name'} direction={sortDir} onSort={handleSort} />
                <SortHeader label="Namespace" sortKey="namespace" active={sortKey === 'namespace'} direction={sortDir} onSort={handleSort} />
                <SortHeader label="Status" sortKey="status" active={sortKey === 'status'} direction={sortDir} onSort={handleSort} />
                <SortHeader label="Replicas" sortKey="replicas" active={sortKey === 'replicas'} direction={sortDir} onSort={handleSort} />
                <SortHeader label="Health" sortKey="health_score" active={sortKey === 'health_score'} direction={sortDir} onSort={handleSort} />
                <th className="px-4 py-3">Image</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-dark-800">
              {filtered.map((w, i) => {
                const status = getWorkloadStatus(w)
                const { current, desired } = getReplicaCounts(w)
                const health = getHealthScore(w)
                return (
                  <tr key={i} className="hover:bg-gray-50 dark:hover:bg-dark-800/50">
                    <td className="max-w-[200px] truncate px-4 py-2.5 font-medium text-dark-900 dark:text-white" title={w.name}>{w.name}</td>
                    <td className="px-4 py-2.5 text-dark-600 dark:text-dark-300">{w.namespace}</td>
                    <td className="px-4 py-2.5">
                      <Badge variant={status === 'healthy' ? 'green' : status === 'warning' ? 'yellow' : status === 'critical' ? 'red' : 'gray'}>
                        {status.toUpperCase()}
                      </Badge>
                    </td>
                    <td className="px-4 py-2.5 font-mono text-xs text-dark-600 dark:text-dark-300">{current}/{desired}</td>
                    <td className="px-4 py-2.5">
                      <span className={health >= 80 ? 'font-medium text-green-600 dark:text-green-400' : health >= 50 ? 'font-medium text-yellow-600 dark:text-yellow-400' : 'font-medium text-red-600 dark:text-red-400'}>
                        {health}%
                      </span>
                    </td>
                    <td className="max-w-[200px] truncate px-4 py-2.5 font-mono text-xs text-dark-400" title={w.image}>{w.image || '—'}</td>
                  </tr>
                )
              })}
              {filtered.length === 0 && (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-dark-400">No workloads found</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}
