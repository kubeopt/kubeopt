import { useEffect, useMemo, useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { api } from '../../api/client'
import Card from '../common/Card'
import Badge from '../common/Badge'
import LoadingSpinner from '../common/LoadingSpinner'

interface WorkloadsTabProps {
  clusterId: string
  subscriptionId: string
}

interface Workload {
  name: string
  namespace: string
  type: string
  replicas?: number
  ready?: number
  hpa_enabled?: boolean
}

type SortKey = 'name' | 'namespace' | 'type' | 'replicas' | 'ready'
type TypeFilter = 'All' | 'Deployment' | 'StatefulSet' | 'DaemonSet'

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

export default function WorkloadsTab({ clusterId, subscriptionId }: WorkloadsTabProps) {
  const [workloads, setWorkloads] = useState<Workload[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState<TypeFilter>('All')
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
        const data = await api.get<{ deployments: Workload[]; statefulsets: Workload[]; daemonsets: Workload[] }>(
          `/api/kubernetes/workloads/${encodeURIComponent(clusterId)}/${encodeURIComponent(subscriptionId)}`
        )
        const all: Workload[] = [
          ...(data.deployments || []).map((w) => ({ ...w, type: 'Deployment' })),
          ...(data.statefulsets || []).map((w) => ({ ...w, type: 'StatefulSet' })),
          ...(data.daemonsets || []).map((w) => ({ ...w, type: 'DaemonSet' })),
        ]
        setWorkloads(all)
      } catch {
        setWorkloads([])
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

  const filtered = useMemo(() => {
    const q = search.toLowerCase()
    let list = workloads.filter(
      (w) => w.name.toLowerCase().includes(q) || w.namespace.toLowerCase().includes(q),
    )
    if (typeFilter !== 'All') list = list.filter((w) => w.type === typeFilter)
    return [...list].sort((a, b) => {
      let cmp = 0
      switch (sortKey) {
        case 'replicas': cmp = (a.replicas ?? 0) - (b.replicas ?? 0); break
        case 'ready': cmp = (a.ready ?? 0) - (b.ready ?? 0); break
        default: cmp = String(a[sortKey] ?? '').localeCompare(String(b[sortKey] ?? ''))
      }
      return sortDir === 'desc' ? -cmp : cmp
    })
  }, [workloads, search, typeFilter, sortKey, sortDir])

  if (loading) return <div className="flex justify-center py-12"><LoadingSpinner size="lg" /></div>

  return (
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
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value as TypeFilter)}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-dark-600 dark:bg-dark-800 dark:text-white"
        >
          <option value="All">All Types</option>
          <option value="Deployment">Deployment</option>
          <option value="StatefulSet">StatefulSet</option>
          <option value="DaemonSet">DaemonSet</option>
        </select>
        <span className="text-sm text-dark-400">{filtered.length} workloads</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-gray-200 text-xs uppercase text-dark-500 dark:border-dark-700 dark:text-dark-400">
            <tr>
              <SortHeader label="Name" sortKey="name" active={sortKey === 'name'} direction={sortDir} onSort={handleSort} />
              <SortHeader label="Namespace" sortKey="namespace" active={sortKey === 'namespace'} direction={sortDir} onSort={handleSort} />
              <SortHeader label="Type" sortKey="type" active={sortKey === 'type'} direction={sortDir} onSort={handleSort} />
              <SortHeader label="Replicas" sortKey="replicas" active={sortKey === 'replicas'} direction={sortDir} onSort={handleSort} />
              <SortHeader label="Ready" sortKey="ready" active={sortKey === 'ready'} direction={sortDir} onSort={handleSort} />
              <th className="px-4 py-3">HPA</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-dark-800">
            {filtered.map((w, i) => (
              <tr key={i} className="hover:bg-gray-50 dark:hover:bg-dark-800/50">
                <td className="px-4 py-2.5 font-medium text-dark-900 dark:text-white">{w.name}</td>
                <td className="px-4 py-2.5 text-dark-600 dark:text-dark-300">{w.namespace}</td>
                <td className="px-4 py-2.5 text-dark-600 dark:text-dark-300">{w.type}</td>
                <td className="px-4 py-2.5 text-dark-600 dark:text-dark-300">{w.replicas ?? '—'}</td>
                <td className="px-4 py-2.5 text-dark-600 dark:text-dark-300">{w.ready ?? '—'}</td>
                <td className="px-4 py-2.5">
                  <Badge variant={w.hpa_enabled ? 'green' : 'gray'}>
                    {w.hpa_enabled ? 'Active' : 'None'}
                  </Badge>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-dark-400">No workloads found</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </Card>
  )
}
