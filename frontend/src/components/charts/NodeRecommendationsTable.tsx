import Badge from '../common/Badge'

interface NodeRecommendation {
  node_name: string
  current_vm: string
  recommended_vm: string
  monthly_savings: number
  avg_cpu_pct: number
  avg_memory_pct: number
  priority: string
  reasoning?: string
}

function UtilizationBar({ value, label }: { value: number; label: string }) {
  const color = value < 30 ? 'bg-red-400' : value < 60 ? 'bg-yellow-400' : 'bg-green-400'
  return (
    <div className="flex items-center gap-2">
      <div className="h-2 w-20 rounded-full bg-gray-200 dark:bg-dark-700">
        <div className={`h-2 rounded-full ${color}`} style={{ width: `${Math.min(value, 100)}%` }} />
      </div>
      <span className="text-xs text-dark-500 dark:text-dark-400">{value.toFixed(0)}% {label}</span>
    </div>
  )
}

export default function NodeRecommendationsTable({ data }: { data: NodeRecommendation[] }) {
  if (!data.length) return <p className="py-8 text-center text-sm text-dark-400">No node recommendations available</p>

  const sorted = [...data].sort((a, b) => b.monthly_savings - a.monthly_savings)

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="border-b border-gray-200 text-xs uppercase text-dark-500 dark:border-dark-700 dark:text-dark-400">
          <tr>
            <th className="px-3 py-2">Node</th>
            <th className="px-3 py-2">Current</th>
            <th className="px-3 py-2">Recommended</th>
            <th className="px-3 py-2">Utilization</th>
            <th className="px-3 py-2">Savings</th>
            <th className="px-3 py-2">Priority</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 dark:divide-dark-800">
          {sorted.map((node, i) => (
            <tr key={i} className="hover:bg-gray-50 dark:hover:bg-dark-800/50">
              <td className="px-3 py-2 font-medium text-dark-900 dark:text-white">{node.node_name}</td>
              <td className="px-3 py-2 font-mono text-xs text-dark-600 dark:text-dark-300">{node.current_vm}</td>
              <td className="px-3 py-2 font-mono text-xs text-green-600 dark:text-green-400">{node.recommended_vm}</td>
              <td className="px-3 py-2">
                <UtilizationBar value={node.avg_cpu_pct} label="CPU" />
                <UtilizationBar value={node.avg_memory_pct} label="Mem" />
              </td>
              <td className="px-3 py-2 font-medium text-green-600">${node.monthly_savings.toFixed(0)}/mo</td>
              <td className="px-3 py-2">
                <Badge variant={node.priority === 'high' ? 'red' : node.priority === 'medium' ? 'yellow' : 'green'}>
                  {node.priority}
                </Badge>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
