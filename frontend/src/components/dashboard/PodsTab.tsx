import { useEffect, useMemo, useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { api } from '../../api/client'
import Card from '../common/Card'
import LoadingSpinner from '../common/LoadingSpinner'
import Badge from '../common/Badge'

interface PodsTabProps {
  clusterId: string
  subscriptionId: string
}

interface Pod {
  name: string
  namespace: string
  status: string
  cpu_request?: string
  memory_request?: string
  node?: string
  restarts?: number
}

type SortKey = 'name' | 'namespace' | 'status' | 'cpu_request' | 'memory_request' | 'restarts'

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

export default function PodsTab({ clusterId, subscriptionId }: PodsTabProps) {
  const [pods, setPods] = useState<Pod[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('')
  const [sortKey, setSortKey] = useState<SortKey>('name')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')

  useEffect(() => {
    async function fetch() {
      if (!subscriptionId) {
        setLoading(false)
        return
      }
      setLoading(true)
      try {
        const data = await api.get<{ pods: Pod[] }>(
          `/api/kubernetes/pods/${encodeURIComponent(clusterId)}/${encodeURIComponent(subscriptionId)}`
        )
        setPods(data.pods || [])
      } catch {
        setPods([])
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
    const q = filter.toLowerCase()
    const list = pods.filter(
      (p) => p.name.toLowerCase().includes(q) || p.namespace.toLowerCase().includes(q),
    )
    return [...list].sort((a, b) => {
      let cmp = 0
      switch (sortKey) {
        case 'restarts': cmp = (a.restarts ?? 0) - (b.restarts ?? 0); break
        default: cmp = String(a[sortKey] ?? '').localeCompare(String(b[sortKey] ?? ''))
      }
      return sortDir === 'desc' ? -cmp : cmp
    })
  }, [pods, filter, sortKey, sortDir])

  if (loading) return <div className="flex justify-center py-12"><LoadingSpinner size="lg" /></div>

  return (
    <Card padding={false}>
      <div className="border-b border-gray-200 p-4 dark:border-dark-700">
        <input
          type="text"
          placeholder="Filter pods..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="w-full max-w-sm rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none dark:border-dark-600 dark:bg-dark-800 dark:text-white"
        />
        <span className="ml-3 text-sm text-dark-400">{sorted.length} pods</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-gray-200 text-xs uppercase text-dark-500 dark:border-dark-700 dark:text-dark-400">
            <tr>
              <SortHeader label="Name" sortKey="name" active={sortKey === 'name'} direction={sortDir} onSort={handleSort} />
              <SortHeader label="Namespace" sortKey="namespace" active={sortKey === 'namespace'} direction={sortDir} onSort={handleSort} />
              <SortHeader label="Status" sortKey="status" active={sortKey === 'status'} direction={sortDir} onSort={handleSort} />
              <SortHeader label="CPU" sortKey="cpu_request" active={sortKey === 'cpu_request'} direction={sortDir} onSort={handleSort} />
              <SortHeader label="Memory" sortKey="memory_request" active={sortKey === 'memory_request'} direction={sortDir} onSort={handleSort} />
              <SortHeader label="Restarts" sortKey="restarts" active={sortKey === 'restarts'} direction={sortDir} onSort={handleSort} />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-dark-800">
            {sorted.map((pod, i) => (
              <tr key={i} className="hover:bg-gray-50 dark:hover:bg-dark-800/50">
                <td className="px-4 py-2.5 font-medium text-dark-900 dark:text-white">{pod.name}</td>
                <td className="px-4 py-2.5 text-dark-600 dark:text-dark-300">{pod.namespace}</td>
                <td className="px-4 py-2.5">
                  <Badge variant={pod.status === 'Running' ? 'green' : pod.status === 'Pending' ? 'yellow' : 'red'}>
                    {pod.status}
                  </Badge>
                </td>
                <td className="px-4 py-2.5 text-dark-600 dark:text-dark-300">{pod.cpu_request || '—'}</td>
                <td className="px-4 py-2.5 text-dark-600 dark:text-dark-300">{pod.memory_request || '—'}</td>
                <td className="px-4 py-2.5 text-dark-600 dark:text-dark-300">{pod.restarts ?? 0}</td>
              </tr>
            ))}
            {sorted.length === 0 && (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-dark-400">No pods found</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </Card>
  )
}
