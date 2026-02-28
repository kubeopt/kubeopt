import { useEffect, useMemo, useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { api } from '../../api/client'
import { getChartData } from '../../api/analysis'
import Card from '../common/Card'
import Badge from '../common/Badge'
import LoadingSpinner from '../common/LoadingSpinner'
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
}

type SortKey = 'name' | 'vm_size' | 'cpu_cores' | 'memory_gb' | 'cpu_percent' | 'memory_percent'

function UtilBar({ value }: { value: number }) {
  const color = value > 80 ? 'bg-red-500' : value > 60 ? 'bg-yellow-500' : 'bg-primary-500'
  return (
    <div className="flex items-center gap-2">
      <div className="h-2 w-24 overflow-hidden rounded-full bg-gray-200 dark:bg-dark-700">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${Math.min(value, 100)}%` }} />
      </div>
      <span className="text-xs text-dark-500">{value.toFixed(0)}%</span>
    </div>
  )
}

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

interface NodeRecommendation {
  node_name: string
  current_vm: string
  recommended_vm: string
  monthly_savings: number
  avg_cpu_pct: number
  avg_memory_pct: number
  priority: string
}

export default function ResourcesTab({ clusterId, subscriptionId }: ResourcesTabProps) {
  const [nodes, setNodes] = useState<Node[]>([])
  const [recommendations, setRecommendations] = useState<NodeRecommendation[]>([])
  const [loading, setLoading] = useState(true)
  const [sortKey, setSortKey] = useState<SortKey>('name')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')

  useEffect(() => {
    async function fetch() {
      setLoading(true)
      try {
        const promises: [Promise<{ nodes: Node[] }> | null, Promise<unknown>] = [
          subscriptionId
            ? api.get<{ nodes: Node[] }>(
                `/api/kubernetes/resources/${encodeURIComponent(clusterId)}/${encodeURIComponent(subscriptionId)}`
              )
            : null,
          getChartData(clusterId),
        ]
        const [nodeData, chartData] = await Promise.all([
          promises[0] || Promise.resolve({ nodes: [] as Node[] }),
          promises[1],
        ])
        setNodes(nodeData.nodes || [])
        const cd = chartData as Record<string, unknown>
        const recs = (cd?.node_recommendations || []) as NodeRecommendation[]
        setRecommendations(recs)
      } catch {
        setNodes([])
      } finally {
        setLoading(false)
      }
    }
    fetch()
  }, [clusterId, subscriptionId])

  const handleSort = (key: SortKey) => {
    if (key === sortKey) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setSortDir('asc')
    }
  }

  const sorted = useMemo(() => {
    return [...nodes].sort((a, b) => {
      let cmp = 0
      const numericKeys: SortKey[] = ['cpu_cores', 'memory_gb', 'cpu_percent', 'memory_percent']
      if (numericKeys.includes(sortKey)) {
        cmp = (a[sortKey] as number ?? 0) - (b[sortKey] as number ?? 0)
      } else {
        cmp = String(a[sortKey] ?? '').localeCompare(String(b[sortKey] ?? ''))
      }
      return sortDir === 'desc' ? -cmp : cmp
    })
  }, [nodes, sortKey, sortDir])

  if (loading) return <div className="flex justify-center py-12"><LoadingSpinner size="lg" /></div>

  return (
    <div className="space-y-6">
      <Card padding={false}>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-gray-200 text-xs uppercase text-dark-500 dark:border-dark-700 dark:text-dark-400">
              <tr>
                <SortHeader label="Node" sortKey="name" active={sortKey === 'name'} direction={sortDir} onSort={handleSort} />
                <th className="px-4 py-3">Status</th>
                <SortHeader label="VM Size" sortKey="vm_size" active={sortKey === 'vm_size'} direction={sortDir} onSort={handleSort} />
                <SortHeader label="CPU (cores)" sortKey="cpu_cores" active={sortKey === 'cpu_cores'} direction={sortDir} onSort={handleSort} />
                <SortHeader label="Memory (GB)" sortKey="memory_gb" active={sortKey === 'memory_gb'} direction={sortDir} onSort={handleSort} />
                <SortHeader label="CPU Usage" sortKey="cpu_percent" active={sortKey === 'cpu_percent'} direction={sortDir} onSort={handleSort} />
                <SortHeader label="Memory Usage" sortKey="memory_percent" active={sortKey === 'memory_percent'} direction={sortDir} onSort={handleSort} />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-dark-800">
              {sorted.map((node, i) => (
                <tr key={i} className="hover:bg-gray-50 dark:hover:bg-dark-800/50">
                  <td className="px-4 py-2.5 font-medium text-dark-900 dark:text-white">{node.name}</td>
                  <td className="px-4 py-2.5">
                    <Badge variant={node.status === 'Ready' || !node.status ? 'green' : 'red'}>
                      {node.status || 'Ready'}
                    </Badge>
                  </td>
                  <td className="px-4 py-2.5 font-mono text-xs text-dark-600 dark:text-dark-300">{node.vm_size || '—'}</td>
                  <td className="px-4 py-2.5 text-dark-600 dark:text-dark-300">{node.cpu_cores ?? '—'}</td>
                  <td className="px-4 py-2.5 text-dark-600 dark:text-dark-300">{node.memory_gb?.toFixed(1) ?? '—'}</td>
                  <td className="px-4 py-2.5">{node.cpu_percent !== undefined ? <UtilBar value={node.cpu_percent} /> : '—'}</td>
                  <td className="px-4 py-2.5">{node.memory_percent !== undefined ? <UtilBar value={node.memory_percent} /> : '—'}</td>
                </tr>
              ))}
              {sorted.length === 0 && (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-dark-400">No nodes found</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Node Recommendations */}
      {recommendations.length > 0 && (
        <Card>
          <h3 className="mb-4 text-sm font-medium text-dark-500 dark:text-dark-400">Node Recommendations</h3>
          <NodeRecommendationsTable data={recommendations} />
        </Card>
      )}
    </div>
  )
}
