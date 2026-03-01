import { useCallback, useEffect, useMemo, useState } from 'react'
import { ChevronDown, ChevronUp, RefreshCw, LayoutGrid, List, FolderTree } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, PieChart, Pie } from 'recharts'
import { api } from '../../api/client'
import { getChartData } from '../../api/analysis'
import Card from '../common/Card'
import Badge from '../common/Badge'
import { TableSkeleton } from '../common/Skeleton'
import NodeRecommendationsTable from '../charts/NodeRecommendationsTable'

interface ResourcesTabProps {
  clusterId: string
  subscriptionId: string
}

interface Node {
  name: string
  vm_size?: string
  cpu_cores?: number
  memory_gb?: number
  cpu_percent?: number
  memory_percent?: number
  status?: string
  os_image?: string
  kubelet_version?: string
  node_pool?: string
}

interface Namespace {
  name: string
  pod_count?: number
  service_count?: number
}

interface StorageItem {
  namespace?: string
  name: string
  type?: string
  status?: string
  size?: string
  storage_class?: string
  kind?: string
}

interface NetworkInfo {
  public_ip_count?: number
  load_balancer_count?: number
  public_ip_cost?: number
  load_balancer_cost?: number
}

interface NodeRecommendation {
  node_name: string
  current_vm: string
  recommended_vm: string
  monthly_savings: number
  avg_cpu_pct: number
  avg_memory_pct: number
  priority: string
}

type SortKey = 'name' | 'vm_size' | 'cpu_cores' | 'memory_gb' | 'cpu_percent' | 'memory_percent' | 'node_pool'
type NsView = 'compact' | 'cards' | 'explorer'

const NS_CATEGORIES: Record<string, string[]> = {
  'System': ['kube-system', 'kube-public', 'kube-node-lease', 'default', 'local-path-storage'],
  'Infra': ['ingress-nginx', 'cert-manager', 'istio-system', 'linkerd', 'traefik', 'metallb-system', 'calico-system', 'tigera-operator'],
  'Monitor': ['monitoring', 'prometheus', 'grafana', 'elastic-system', 'logging', 'datadog', 'newrelic', 'observability'],
}

function categorizeNamespace(ns: string): string {
  for (const [cat, patterns] of Object.entries(NS_CATEGORIES)) {
    if (patterns.some((p) => ns === p || ns.startsWith(p))) return cat
  }
  return 'Apps'
}

function UtilBar({ value }: { value: number }) {
  const color = value > 80 ? 'bg-red-500' : value > 60 ? 'bg-yellow-500' : 'bg-primary-500'
  return (
    <div className="flex items-center gap-2">
      <div className="h-2 w-24 overflow-hidden rounded-full" style={{ backgroundColor: 'var(--border-subtle)' }}>
        <div className={`h-full rounded-full ${color}`} style={{ width: `${Math.min(value, 100)}%` }} />
      </div>
      <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{value.toFixed(0)}%</span>
    </div>
  )
}

function SortHeader({
  label, sortKey, active, direction, onSort,
}: {
  label: string; sortKey: SortKey; active: boolean; direction: 'asc' | 'desc'; onSort: (key: SortKey) => void
}) {
  return (
    <th className="cursor-pointer select-none px-4 py-3" style={{ color: 'var(--text-muted)' }} onClick={() => onSort(sortKey)}>
      <span className="inline-flex items-center gap-1">
        {label}
        {active && (direction === 'asc' ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />)}
      </span>
    </th>
  )
}

const DARK_TOOLTIP = {
  contentStyle: { backgroundColor: '#1f2937', border: 'none', borderRadius: 8, color: '#e5e7eb', fontSize: 12 },
  itemStyle: { color: '#d1d5db' },
  labelStyle: { color: '#9ca3af' },
}

export default function ResourcesTab({ clusterId, subscriptionId }: ResourcesTabProps) {
  const [nodes, setNodes] = useState<Node[]>([])
  const [namespaces, setNamespaces] = useState<Namespace[]>([])
  const [storage, setStorage] = useState<StorageItem[]>([])
  const [network, setNetwork] = useState<NetworkInfo>({})
  const [recommendations, setRecommendations] = useState<NodeRecommendation[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [sortKey, setSortKey] = useState<SortKey>('name')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')
  const [nsView, setNsView] = useState<NsView>('compact')
  const [search, setSearch] = useState('')
  const [poolFilter, setPoolFilter] = useState('All')

  const fetchData = useCallback(async (showRefresh = false) => {
    if (showRefresh) setRefreshing(true)
    else setLoading(true)
    try {
      const nodeUrl = subscriptionId
        ? `/api/kubernetes/resources/${encodeURIComponent(clusterId)}/${encodeURIComponent(subscriptionId)}`
        : `/api/kubernetes/resources-by-cluster?cluster_id=${encodeURIComponent(clusterId)}`
      const results = await Promise.allSettled([
        api.get<{
          nodes?: Node[]
          namespaces?: Namespace[]
          storage?: StorageItem[]
          network?: NetworkInfo
        }>(nodeUrl),
        getChartData(clusterId),
      ])
      if (results[0].status === 'fulfilled') {
        const nodeData = results[0].value
        setNodes(nodeData.nodes || [])
        setNamespaces(nodeData.namespaces || [])
        setStorage(nodeData.storage || [])
        setNetwork(nodeData.network || {})
      }
      if (results[1].status === 'fulfilled') {
        const cd = results[1].value as Record<string, unknown>
        setRecommendations((cd?.node_recommendations || []) as NodeRecommendation[])
      }
    } catch {
      setNodes([])
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

  const nodePools = useMemo(() => [...new Set(nodes.map((n) => n.node_pool || 'default').filter(Boolean))].sort(), [nodes])

  const filtered = useMemo(() => {
    const q = search.toLowerCase()
    let list = nodes.filter(
      (n) => n.name.toLowerCase().includes(q) || (n.vm_size || '').toLowerCase().includes(q),
    )
    if (poolFilter !== 'All') list = list.filter((n) => (n.node_pool || 'default') === poolFilter)
    return [...list].sort((a, b) => {
      let cmp = 0
      const numericKeys: SortKey[] = ['cpu_cores', 'memory_gb', 'cpu_percent', 'memory_percent']
      if (numericKeys.includes(sortKey)) {
        cmp = (a[sortKey] as number ?? 0) - (b[sortKey] as number ?? 0)
      } else {
        cmp = String(a[sortKey] ?? '').localeCompare(String(b[sortKey] ?? ''))
      }
      return sortDir === 'desc' ? -cmp : cmp
    })
  }, [nodes, search, poolFilter, sortKey, sortDir])

  const categorized = useMemo(() => {
    const groups: Record<string, Namespace[]> = { Apps: [], Infra: [], Monitor: [], System: [] }
    namespaces.forEach((ns) => {
      const cat = categorizeNamespace(ns.name)
      if (!groups[cat]) groups[cat] = []
      groups[cat].push(ns)
    })
    return groups
  }, [namespaces])

  const avgCpu = nodes.length ? nodes.reduce((s, n) => s + (n.cpu_percent ?? 0), 0) / nodes.length : 0
  const avgMem = nodes.length ? nodes.reduce((s, n) => s + (n.memory_percent ?? 0), 0) / nodes.length : 0
  const totalCores = nodes.reduce((s, n) => s + (n.cpu_cores ?? 0), 0)
  const totalMemGb = nodes.reduce((s, n) => s + (n.memory_gb ?? 0), 0)

  // Chart data: Node CPU distribution
  const cpuDistData = useMemo(() => {
    const low = nodes.filter((n) => (n.cpu_percent ?? 0) < 30).length
    const mid = nodes.filter((n) => (n.cpu_percent ?? 0) >= 30 && (n.cpu_percent ?? 0) < 70).length
    const high = nodes.filter((n) => (n.cpu_percent ?? 0) >= 70).length
    return [
      { name: 'Low (<30%)', value: low, color: '#ef4444' },
      { name: 'Medium (30-70%)', value: mid, color: '#eab308' },
      { name: 'Optimal (>70%)', value: high, color: '#7FB069' },
    ].filter((d) => d.value > 0)
  }, [nodes])

  // Chart data: VM Size distribution
  const vmDistData = useMemo(() => {
    const vmMap: Record<string, number> = {}
    nodes.forEach((n) => { const vm = n.vm_size || 'Unknown'; vmMap[vm] = (vmMap[vm] || 0) + 1 })
    return Object.entries(vmMap)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 6)
      .map(([vm, count]) => ({ vm, count }))
  }, [nodes])

  // Chart data: Storage class distribution
  const storageClassData = useMemo(() => {
    const classMap: Record<string, number> = {}
    storage.forEach((s) => { const sc = s.storage_class || 'default'; classMap[sc] = (classMap[sc] || 0) + 1 })
    return Object.entries(classMap).map(([name, value]) => ({ name, value }))
  }, [storage])

  const resetFilters = () => { setSearch(''); setPoolFilter('All') }

  if (loading) return <Card padding={false}><TableSkeleton rows={6} /></Card>

  return (
    <div className="space-y-6">
      {/* ─── Header ─── */}
      <div>
        <h2 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>Infrastructure Resources</h2>
        <div className="mt-2 flex flex-wrap items-center gap-3">
          <span className="rounded-full px-3 py-1 text-sm font-medium" style={{ backgroundColor: 'var(--bg-surface)', color: 'var(--text-secondary)' }}>
            {nodes.length} Nodes
          </span>
          <span className="rounded-full px-3 py-1 text-sm font-medium" style={{ backgroundColor: 'var(--bg-surface)', color: 'var(--text-secondary)' }}>
            {totalCores} Cores / {totalMemGb.toFixed(0)} GB RAM
          </span>
          <span className={`rounded-full px-3 py-1 text-sm font-medium ${avgCpu >= 60 ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' : avgCpu >= 40 ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400' : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'}`}>
            CPU: {avgCpu.toFixed(0)}% / Mem: {avgMem.toFixed(0)}%
          </span>
        </div>
      </div>

      {/* ─── 3 Charts Row ─── */}
      {nodes.length > 0 && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* CPU Utilization Distribution */}
          <Card>
            <h3 className="mb-3 text-sm font-medium" style={{ color: 'var(--text-muted)' }}>CPU Utilization Distribution</h3>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={cpuDistData} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
                <XAxis dataKey="name" fontSize={10} tick={{ fill: '#6b7280' }} axisLine={false} tickLine={false} />
                <YAxis fontSize={11} tick={{ fill: '#6b7280' }} axisLine={false} tickLine={false} allowDecimals={false} />
                <Tooltip {...DARK_TOOLTIP} />
                <Bar dataKey="value" name="Nodes" radius={[4, 4, 0, 0]} barSize={32}>
                  {cpuDistData.map((d, i) => <Cell key={i} fill={d.color} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Card>

          {/* VM Size Distribution */}
          <Card>
            <h3 className="mb-3 text-sm font-medium" style={{ color: 'var(--text-muted)' }}>VM Size Distribution</h3>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={vmDistData} layout="vertical" margin={{ top: 4, right: 12, bottom: 4, left: 4 }}>
                <XAxis type="number" fontSize={11} tick={{ fill: '#6b7280' }} axisLine={false} tickLine={false} allowDecimals={false} />
                <YAxis type="category" dataKey="vm" width={100} fontSize={9} tick={{ fill: '#6b7280' }} axisLine={false} tickLine={false} />
                <Tooltip {...DARK_TOOLTIP} />
                <Bar dataKey="count" name="Nodes" fill="#5f9548" radius={[0, 4, 4, 0]} barSize={16} />
              </BarChart>
            </ResponsiveContainer>
          </Card>

          {/* Storage Classes */}
          <Card>
            <h3 className="mb-3 text-sm font-medium" style={{ color: 'var(--text-muted)' }}>
              {storage.length > 0 ? 'Storage Class Distribution' : 'Network Resources'}
            </h3>
            {storage.length > 0 && storageClassData.length > 0 ? (
              <ResponsiveContainer width="100%" height={180}>
                <PieChart>
                  <Pie data={storageClassData} cx="50%" cy="50%" innerRadius={40} outerRadius={70} dataKey="value" stroke="none" label={({ name, value }) => `${name} (${value})`}>
                    {storageClassData.map((_, i) => <Cell key={i} fill={['#7FB069', '#5f9548', '#3a5c2d', '#9ec88d', '#4a7737'][i % 5]} />)}
                  </Pie>
                  <Tooltip {...DARK_TOOLTIP} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-[180px] flex-col items-center justify-center gap-2">
                <div className="grid grid-cols-2 gap-4 text-center">
                  <div>
                    <div className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>{network.public_ip_count ?? 0}</div>
                    <div className="text-xs" style={{ color: 'var(--text-muted)' }}>Public IPs</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>{network.load_balancer_count ?? 0}</div>
                    <div className="text-xs" style={{ color: 'var(--text-muted)' }}>Load Balancers</div>
                  </div>
                </div>
              </div>
            )}
          </Card>
        </div>
      )}

      {/* ─── Filters + Nodes Table ─── */}
      <Card padding={false}>
        <div className="flex flex-wrap items-center gap-3 border-b p-4" style={{ borderColor: 'var(--border-subtle)' }}>
          <input
            type="text"
            placeholder="Search nodes..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full max-w-xs rounded-lg border px-3 py-2 text-sm focus:outline-none"
            style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--bg-surface)', color: 'var(--text-primary)' }}
          />
          {nodePools.length > 1 && (
            <select
              value={poolFilter}
              onChange={(e) => setPoolFilter(e.target.value)}
              className="rounded-lg border px-3 py-2 text-sm"
              style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--bg-surface)', color: 'var(--text-primary)' }}
            >
              <option value="All">All Node Pools</option>
              {nodePools.map((np) => <option key={np} value={np}>{np}</option>)}
            </select>
          )}
          <button onClick={resetFilters} className="rounded-lg border px-3 py-2 text-sm" style={{ borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }}>
            Reset
          </button>
          <button
            onClick={() => fetchData(true)}
            disabled={refreshing}
            className="inline-flex items-center gap-1.5 rounded-lg border px-3 py-2 text-sm"
            style={{ borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }}
          >
            <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <span className="ml-auto text-sm" style={{ color: 'var(--text-muted)' }}>{filtered.length} nodes</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b text-xs uppercase" style={{ borderColor: 'var(--border-subtle)', color: 'var(--text-muted)' }}>
              <tr>
                <SortHeader label="Node" sortKey="name" active={sortKey === 'name'} direction={sortDir} onSort={handleSort} />
                <th className="px-4 py-3">Status</th>
                <SortHeader label="Node Pool" sortKey="node_pool" active={sortKey === 'node_pool'} direction={sortDir} onSort={handleSort} />
                <SortHeader label="VM Size" sortKey="vm_size" active={sortKey === 'vm_size'} direction={sortDir} onSort={handleSort} />
                <SortHeader label="CPU" sortKey="cpu_cores" active={sortKey === 'cpu_cores'} direction={sortDir} onSort={handleSort} />
                <SortHeader label="Memory" sortKey="memory_gb" active={sortKey === 'memory_gb'} direction={sortDir} onSort={handleSort} />
                <SortHeader label="CPU Usage" sortKey="cpu_percent" active={sortKey === 'cpu_percent'} direction={sortDir} onSort={handleSort} />
                <SortHeader label="Memory Usage" sortKey="memory_percent" active={sortKey === 'memory_percent'} direction={sortDir} onSort={handleSort} />
              </tr>
            </thead>
            <tbody>
              {filtered.map((node, i) => (
                <tr key={i} className="border-b transition-colors hover:opacity-80" style={{ borderColor: 'var(--border-subtle)' }}>
                  <td className="px-4 py-2.5 font-medium" style={{ color: 'var(--text-primary)' }}>{node.name}</td>
                  <td className="px-4 py-2.5">
                    <Badge variant={node.status === 'Ready' || !node.status ? 'green' : 'red'}>
                      {node.status || 'Ready'}
                    </Badge>
                  </td>
                  <td className="px-4 py-2.5 text-xs" style={{ color: 'var(--text-secondary)' }}>{node.node_pool || 'default'}</td>
                  <td className="px-4 py-2.5 font-mono text-xs" style={{ color: 'var(--text-secondary)' }}>{node.vm_size || '—'}</td>
                  <td className="px-4 py-2.5" style={{ color: 'var(--text-secondary)' }}>{node.cpu_cores ?? '—'}</td>
                  <td className="px-4 py-2.5" style={{ color: 'var(--text-secondary)' }}>{node.memory_gb?.toFixed(1) ?? '—'} GB</td>
                  <td className="px-4 py-2.5">{node.cpu_percent !== undefined ? <UtilBar value={node.cpu_percent} /> : '—'}</td>
                  <td className="px-4 py-2.5">{node.memory_percent !== undefined ? <UtilBar value={node.memory_percent} /> : '—'}</td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr><td colSpan={8} className="px-4 py-8 text-center" style={{ color: 'var(--text-muted)' }}>No nodes found</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* ─── Namespaces Section ─── */}
      {namespaces.length > 0 && (
        <Card>
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>Namespaces ({namespaces.length})</h3>
            <div className="flex rounded-lg border" style={{ borderColor: 'var(--border-color)' }}>
              {([
                { view: 'compact' as NsView, icon: List, label: 'Compact' },
                { view: 'cards' as NsView, icon: LayoutGrid, label: 'Cards' },
                { view: 'explorer' as NsView, icon: FolderTree, label: 'Explorer' },
              ]).map(({ view, icon: Icon, label }) => (
                <button
                  key={view}
                  onClick={() => setNsView(view)}
                  className={`inline-flex items-center gap-1 px-3 py-1.5 text-xs ${
                    nsView === view ? 'bg-primary-500 text-white' : ''
                  } ${view === 'compact' ? 'rounded-l-lg' : view === 'explorer' ? 'rounded-r-lg' : ''}`}
                  style={nsView !== view ? { color: 'var(--text-muted)' } : undefined}
                >
                  <Icon className="h-3.5 w-3.5" />
                  {label}
                </button>
              ))}
            </div>
          </div>

          <div className="mb-4 flex flex-wrap gap-2">
            {Object.entries(categorized).map(([cat, nsList]) => (
              nsList.length > 0 && (
                <span key={cat} className="rounded-full px-3 py-1 text-xs font-medium" style={{ backgroundColor: 'var(--bg-surface)', color: 'var(--text-secondary)' }}>
                  {cat}: {nsList.length}
                </span>
              )
            ))}
          </div>

          {nsView === 'compact' && (
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
              {namespaces.map((ns) => (
                <div key={ns.name} className="flex items-center justify-between rounded-lg border px-3 py-2" style={{ borderColor: 'var(--border-subtle)' }}>
                  <span className="truncate text-sm" style={{ color: 'var(--text-secondary)' }}>{ns.name}</span>
                  {ns.pod_count !== undefined && (
                    <span className="ml-2 flex-shrink-0 text-xs" style={{ color: 'var(--text-muted)' }}>{ns.pod_count} pods</span>
                  )}
                </div>
              ))}
            </div>
          )}

          {nsView === 'cards' && (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {namespaces.map((ns) => (
                <div key={ns.name} className="rounded-lg border p-3" style={{ borderColor: 'var(--border-subtle)' }}>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>{ns.name}</span>
                    <Badge variant={categorizeNamespace(ns.name) === 'System' ? 'gray' : categorizeNamespace(ns.name) === 'Monitor' ? 'blue' : categorizeNamespace(ns.name) === 'Infra' ? 'yellow' : 'green'}>
                      {categorizeNamespace(ns.name)}
                    </Badge>
                  </div>
                  <div className="mt-2 flex gap-4 text-xs" style={{ color: 'var(--text-muted)' }}>
                    {ns.pod_count !== undefined && <span>{ns.pod_count} pods</span>}
                    {ns.service_count !== undefined && <span>{ns.service_count} services</span>}
                  </div>
                </div>
              ))}
            </div>
          )}

          {nsView === 'explorer' && (
            <div className="space-y-4">
              {Object.entries(categorized).map(([cat, nsList]) => (
                nsList.length > 0 && (
                  <div key={cat}>
                    <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>{cat} ({nsList.length})</h4>
                    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
                      {nsList.map((ns) => (
                        <div
                          key={ns.name}
                          className={`flex items-center justify-between rounded-lg border px-3 py-2 ${
                            cat === 'Apps' ? 'border-green-200 bg-green-50/50 dark:border-green-900/30 dark:bg-green-900/10'
                              : cat === 'Infra' ? 'border-yellow-200 bg-yellow-50/50 dark:border-yellow-900/30 dark:bg-yellow-900/10'
                              : cat === 'Monitor' ? 'border-blue-200 bg-blue-50/50 dark:border-blue-900/30 dark:bg-blue-900/10'
                              : 'border-gray-200 bg-gray-50/50 dark:border-dark-700 dark:bg-dark-800/50'
                          }`}
                        >
                          <span className="truncate text-sm" style={{ color: 'var(--text-secondary)' }}>{ns.name}</span>
                          {ns.pod_count !== undefined && (
                            <span className="ml-2 flex-shrink-0 text-xs" style={{ color: 'var(--text-muted)' }}>{ns.pod_count} pods</span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )
              ))}
            </div>
          )}
        </Card>
      )}

      {/* ─── Storage Volumes ─── */}
      {storage.length > 0 && (
        <Card padding={false}>
          <div className="border-b p-4" style={{ borderColor: 'var(--border-subtle)' }}>
            <h3 className="text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>Storage Volumes ({storage.length})</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b text-xs uppercase" style={{ borderColor: 'var(--border-subtle)', color: 'var(--text-muted)' }}>
                <tr>
                  <th className="px-4 py-3">Name</th>
                  <th className="px-4 py-3">Namespace</th>
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Size</th>
                  <th className="px-4 py-3">Storage Class</th>
                </tr>
              </thead>
              <tbody>
                {storage.map((vol, i) => (
                  <tr key={i} className="border-b transition-colors hover:opacity-80" style={{ borderColor: 'var(--border-subtle)' }}>
                    <td className="px-4 py-2.5 font-medium" style={{ color: 'var(--text-primary)' }}>{vol.name}</td>
                    <td className="px-4 py-2.5" style={{ color: 'var(--text-secondary)' }}>{vol.namespace || '—'}</td>
                    <td className="px-4 py-2.5" style={{ color: 'var(--text-secondary)' }}>{vol.kind || vol.type || '—'}</td>
                    <td className="px-4 py-2.5">
                      <Badge variant={vol.status === 'Bound' ? 'green' : vol.status === 'Available' ? 'blue' : vol.status === 'Released' ? 'yellow' : 'gray'}>
                        {vol.status || '—'}
                      </Badge>
                    </td>
                    <td className="px-4 py-2.5" style={{ color: 'var(--text-secondary)' }}>{vol.size || '—'}</td>
                    <td className="px-4 py-2.5 font-mono text-xs" style={{ color: 'var(--text-muted)' }}>{vol.storage_class || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* ─── Network Resources ─── */}
      {(network.public_ip_count || network.load_balancer_count) ? (
        <Card>
          <h3 className="mb-3 text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>Network Resources</h3>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div>
              <div className="text-xs" style={{ color: 'var(--text-muted)' }}>Public IPs</div>
              <div className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>{network.public_ip_count ?? 0}</div>
              {network.public_ip_cost ? <div className="text-xs" style={{ color: 'var(--text-muted)' }}>${network.public_ip_cost.toFixed(2)}/mo</div> : null}
            </div>
            <div>
              <div className="text-xs" style={{ color: 'var(--text-muted)' }}>Load Balancers</div>
              <div className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>{network.load_balancer_count ?? 0}</div>
              {network.load_balancer_cost ? <div className="text-xs" style={{ color: 'var(--text-muted)' }}>${network.load_balancer_cost.toFixed(2)}/mo</div> : null}
            </div>
          </div>
        </Card>
      ) : null}

      {/* ─── Node Recommendations ─── */}
      {recommendations.length > 0 && (
        <Card>
          <h3 className="mb-4 text-sm font-medium" style={{ color: 'var(--text-muted)' }}>
            Node Recommendations ({recommendations.length})
          </h3>
          <NodeRecommendationsTable data={recommendations} />
        </Card>
      )}
    </div>
  )
}
