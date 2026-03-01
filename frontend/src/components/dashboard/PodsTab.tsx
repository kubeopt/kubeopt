import { useCallback, useEffect, useMemo, useState } from 'react'
import { ChevronDown, ChevronUp, RefreshCw } from 'lucide-react'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { api } from '../../api/client'
import Card from '../common/Card'
import Badge from '../common/Badge'
import { TableSkeleton } from '../common/Skeleton'

interface PodsTabProps {
  clusterId: string
  subscriptionId: string
}

interface Pod {
  name: string
  namespace: string
  status: string
  cpu_request?: number | string
  memory_request?: number | string
  cpu_limit?: number | string
  memory_limit?: number | string
  node?: string
  restarts?: number
  health_score?: number
  severity?: string
}

interface PodSummary {
  healthy_count?: number
  warning_count?: number
  critical_count?: number
  total_cpu_request?: number
  total_memory_request?: number
  avg_health_score?: number
}

type SortKey = 'name' | 'namespace' | 'status' | 'node' | 'cpu_request' | 'memory_request' | 'restarts'

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

function parseCpuValue(v: number | string | undefined): number {
  if (v === undefined || v === null) return 0
  if (typeof v === 'number') return v
  const s = String(v)
  if (s.endsWith('m')) return parseFloat(s) / 1000
  return parseFloat(s) || 0
}

function parseMemoryValue(v: number | string | undefined): number {
  if (v === undefined || v === null) return 0
  if (typeof v === 'number') return v
  const s = String(v)
  if (s.endsWith('Gi')) return parseFloat(s)
  if (s.endsWith('Mi')) return parseFloat(s) / 1024
  if (s.endsWith('Ki')) return parseFloat(s) / (1024 * 1024)
  return parseFloat(s) || 0
}

function MiniBar({ value, max, color }: { value: number; max: number; color: string }) {
  const pct = max > 0 ? Math.min((value / max) * 100, 100) : 0
  return (
    <div className="flex items-center gap-2">
      <div className="h-2 w-20 overflow-hidden rounded-full bg-gray-200 dark:bg-dark-700">
        <div className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
      <span className="text-xs text-dark-500 dark:text-dark-400">{value > 0 ? value.toFixed(2) : '—'}</span>
    </div>
  )
}

export default function PodsTab({ clusterId, subscriptionId }: PodsTabProps) {
  const [pods, setPods] = useState<Pod[]>([])
  const [summary, setSummary] = useState<PodSummary>({})
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [filter, setFilter] = useState('')
  const [nsFilter, setNsFilter] = useState('All')
  const [statusFilter, setStatusFilter] = useState('All')
  const [sortKey, setSortKey] = useState<SortKey>('name')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')

  const fetchData = useCallback(async (showRefresh = false) => {
    if (showRefresh) setRefreshing(true)
    else setLoading(true)
    try {
      const url = subscriptionId
        ? `/api/kubernetes/pods/${encodeURIComponent(clusterId)}/${encodeURIComponent(subscriptionId)}`
        : `/api/kubernetes/pods-by-cluster?cluster_id=${encodeURIComponent(clusterId)}`
      const data = await api.get<{ pods: Pod[]; summary?: PodSummary; total_count?: number }>(url)
      setPods(data.pods || [])
      setSummary(data.summary || {})
    } catch {
      setPods([])
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [clusterId, subscriptionId])

  useEffect(() => { fetchData() }, [fetchData])

  const handleSort = (key: SortKey) => {
    if (key === sortKey) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setSortDir('asc')
    }
  }

  const namespaces = useMemo(() => [...new Set(pods.map((p) => p.namespace))].sort(), [pods])
  const statuses = useMemo(() => [...new Set(pods.map((p) => p.status))].sort(), [pods])

  const sorted = useMemo(() => {
    const q = filter.toLowerCase()
    let list = pods.filter(
      (p) => p.name.toLowerCase().includes(q) || p.namespace.toLowerCase().includes(q),
    )
    if (nsFilter !== 'All') list = list.filter((p) => p.namespace === nsFilter)
    if (statusFilter !== 'All') list = list.filter((p) => p.status === statusFilter)
    return [...list].sort((a, b) => {
      let cmp = 0
      switch (sortKey) {
        case 'restarts': cmp = (a.restarts ?? 0) - (b.restarts ?? 0); break
        case 'cpu_request': cmp = parseCpuValue(a.cpu_request) - parseCpuValue(b.cpu_request); break
        case 'memory_request': cmp = parseMemoryValue(a.memory_request) - parseMemoryValue(b.memory_request); break
        default: cmp = String(a[sortKey] ?? '').localeCompare(String(b[sortKey] ?? ''))
      }
      return sortDir === 'desc' ? -cmp : cmp
    })
  }, [pods, filter, nsFilter, statusFilter, sortKey, sortDir])

  // Compute per-namespace CPU/Memory aggregation for area charts
  const nsCpuData = useMemo(() => {
    const nsMap: Record<string, number> = {}
    pods.forEach((p) => {
      nsMap[p.namespace] = (nsMap[p.namespace] || 0) + parseCpuValue(p.cpu_request)
    })
    return Object.entries(nsMap)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([ns, cpu]) => ({ namespace: ns, cpu: parseFloat(cpu.toFixed(3)) }))
  }, [pods])

  const nsMemData = useMemo(() => {
    const nsMap: Record<string, number> = {}
    pods.forEach((p) => {
      nsMap[p.namespace] = (nsMap[p.namespace] || 0) + parseMemoryValue(p.memory_request)
    })
    return Object.entries(nsMap)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([ns, mem]) => ({ namespace: ns, memory: parseFloat(mem.toFixed(3)) }))
  }, [pods])

  const maxCpu = useMemo(() => Math.max(...pods.map((p) => parseCpuValue(p.cpu_request)), 1), [pods])
  const maxMem = useMemo(() => Math.max(...pods.map((p) => parseMemoryValue(p.memory_request)), 1), [pods])

  const totalPods = pods.length
  const healthyCt = summary.healthy_count ?? pods.filter((p) => p.status === 'Running' || p.status === 'Succeeded').length
  const warningCt = summary.warning_count ?? pods.filter((p) => p.status === 'Pending').length
  const criticalCt = summary.critical_count ?? pods.filter((p) => p.status === 'Failed' || p.status === 'CrashLoopBackOff' || p.status === 'Error').length

  if (loading) return <Card padding={false}><TableSkeleton rows={8} /></Card>

  return (
    <div className="space-y-6">
      {/* ─── Header: Pods Overview ─── */}
      <div>
        <h2 className="text-lg font-semibold text-dark-900 dark:text-white">Pods Overview</h2>
        <div className="mt-2 flex flex-wrap items-center gap-3">
          <span className="rounded-full bg-gray-100 px-3 py-1 text-sm font-medium text-dark-700 dark:bg-dark-700 dark:text-dark-200">
            {totalPods} Total Pods
          </span>
          <span className="rounded-full bg-green-100 px-3 py-1 text-sm font-medium text-green-800 dark:bg-green-900/30 dark:text-green-400">
            {healthyCt} Healthy
          </span>
          {warningCt > 0 && (
            <span className="rounded-full bg-yellow-100 px-3 py-1 text-sm font-medium text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400">
              {warningCt} Warning
            </span>
          )}
          {criticalCt > 0 && (
            <span className="rounded-full bg-red-100 px-3 py-1 text-sm font-medium text-red-800 dark:bg-red-900/30 dark:text-red-400">
              {criticalCt} Critical
            </span>
          )}
        </div>
      </div>

      {/* ─── CPU & Memory Usage Charts ─── */}
      {pods.length > 0 && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Card>
            <h3 className="mb-3 text-sm font-medium text-dark-500 dark:text-dark-400">CPU Usage by Namespace</h3>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={nsCpuData} margin={{ top: 4, right: 12, bottom: 0, left: 0 }}>
                <defs>
                  <linearGradient id="cpuGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#7FB069" stopOpacity={0.5} />
                    <stop offset="100%" stopColor="#7FB069" stopOpacity={0.05} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="namespace" fontSize={10} tick={{ fill: '#6b7280' }} axisLine={false} tickLine={false} />
                <YAxis fontSize={10} tick={{ fill: '#6b7280' }} axisLine={false} tickLine={false} width={40} />
                <Tooltip
                  formatter={(v: number) => [`${v} cores`, 'CPU']}
                  contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: 8, color: '#e5e7eb', fontSize: 12 }}
                  itemStyle={{ color: '#d1d5db' }}
                  labelStyle={{ color: '#9ca3af' }}
                />
                <Area type="monotone" dataKey="cpu" stroke="#7FB069" strokeWidth={2} fill="url(#cpuGrad)" dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </Card>
          <Card>
            <h3 className="mb-3 text-sm font-medium text-dark-500 dark:text-dark-400">Memory Usage by Namespace</h3>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={nsMemData} margin={{ top: 4, right: 12, bottom: 0, left: 0 }}>
                <defs>
                  <linearGradient id="memGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#3a5c2d" stopOpacity={0.5} />
                    <stop offset="100%" stopColor="#3a5c2d" stopOpacity={0.05} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="namespace" fontSize={10} tick={{ fill: '#6b7280' }} axisLine={false} tickLine={false} />
                <YAxis fontSize={10} tick={{ fill: '#6b7280' }} axisLine={false} tickLine={false} width={40} tickFormatter={(v) => `${v}Gi`} />
                <Tooltip
                  formatter={(v: number) => [`${v.toFixed(2)} Gi`, 'Memory']}
                  contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: 8, color: '#e5e7eb', fontSize: 12 }}
                  itemStyle={{ color: '#d1d5db' }}
                  labelStyle={{ color: '#9ca3af' }}
                />
                <Area type="monotone" dataKey="memory" stroke="#3a5c2d" strokeWidth={2} fill="url(#memGrad)" dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </Card>
        </div>
      )}

      {/* ─── Filters ─── */}
      <Card padding={false}>
        <div className="flex flex-wrap items-center gap-3 border-b border-gray-200 p-4 dark:border-dark-700">
          <input
            type="text"
            placeholder="Search pods..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
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
            {statuses.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <button
            onClick={() => fetchData(true)}
            disabled={refreshing}
            className="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 px-3 py-2 text-sm text-dark-600 hover:bg-gray-50 dark:border-dark-600 dark:text-dark-300 dark:hover:bg-dark-800"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <span className="ml-auto text-sm text-dark-400">{sorted.length} pods</span>
        </div>

        {/* ─── Table ─── */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-gray-200 text-xs uppercase text-dark-500 dark:border-dark-700 dark:text-dark-400">
              <tr>
                <SortHeader label="Name" sortKey="name" active={sortKey === 'name'} direction={sortDir} onSort={handleSort} />
                <SortHeader label="Namespace" sortKey="namespace" active={sortKey === 'namespace'} direction={sortDir} onSort={handleSort} />
                <SortHeader label="Status" sortKey="status" active={sortKey === 'status'} direction={sortDir} onSort={handleSort} />
                <SortHeader label="Node" sortKey="node" active={sortKey === 'node'} direction={sortDir} onSort={handleSort} />
                <SortHeader label="Restarts" sortKey="restarts" active={sortKey === 'restarts'} direction={sortDir} onSort={handleSort} />
                <SortHeader label="CPU Request" sortKey="cpu_request" active={sortKey === 'cpu_request'} direction={sortDir} onSort={handleSort} />
                <SortHeader label="Memory Request" sortKey="memory_request" active={sortKey === 'memory_request'} direction={sortDir} onSort={handleSort} />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-dark-800">
              {sorted.map((pod, i) => {
                const restarts = pod.restarts ?? 0
                const cpuVal = parseCpuValue(pod.cpu_request)
                const memVal = parseMemoryValue(pod.memory_request)
                return (
                  <tr key={i} className="hover:bg-gray-50 dark:hover:bg-dark-800/50">
                    <td className="max-w-[200px] truncate px-4 py-2.5 font-medium text-dark-900 dark:text-white" title={pod.name}>{pod.name}</td>
                    <td className="px-4 py-2.5 text-dark-600 dark:text-dark-300">{pod.namespace}</td>
                    <td className="px-4 py-2.5">
                      <Badge variant={
                        pod.status === 'Running' || pod.status === 'Succeeded' ? 'green'
                          : pod.status === 'Pending' ? 'yellow'
                          : 'red'
                      }>
                        {pod.status}
                      </Badge>
                    </td>
                    <td className="max-w-[160px] truncate px-4 py-2.5 text-xs text-dark-500 dark:text-dark-400" title={pod.node}>{pod.node || '—'}</td>
                    <td className="px-4 py-2.5">
                      <span className={restarts > 0 ? 'font-medium text-red-600 dark:text-red-400' : 'text-dark-600 dark:text-dark-300'}>
                        {restarts}
                      </span>
                    </td>
                    <td className="px-4 py-2.5">
                      <MiniBar value={cpuVal} max={maxCpu} color="#7FB069" />
                    </td>
                    <td className="px-4 py-2.5">
                      <MiniBar value={memVal} max={maxMem} color="#3a5c2d" />
                    </td>
                  </tr>
                )
              })}
              {sorted.length === 0 && (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-dark-400">No pods found</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}
