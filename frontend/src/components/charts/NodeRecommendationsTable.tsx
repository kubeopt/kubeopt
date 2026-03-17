import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'
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
  current_cost?: number
  recommended_cost?: number
  cpu_cores?: number
  memory_gb?: number
  recommended_cpu_cores?: number
  recommended_memory_gb?: number
  is_cost_increase?: boolean
  recommendation_type?: string
}

function UtilizationBar({ value, label }: { value: number; label: string }) {
  const v = value ?? 0
  const color = v < 30 ? 'bg-red-400' : v < 60 ? 'bg-yellow-400' : 'bg-green-400'
  return (
    <div className="flex items-center gap-2">
      <div className="h-2 w-20 rounded-full" style={{ backgroundColor: 'var(--border-subtle)' }}>
        <div className={`h-2 rounded-full ${color}`} style={{ width: `${Math.min(v, 100)}%` }} />
      </div>
      <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{v.toFixed(0)}% {label}</span>
    </div>
  )
}

export default function NodeRecommendationsTable({ data }: { data: NodeRecommendation[] }) {
  const [expandedRow, setExpandedRow] = useState<number | null>(null)

  if (!data.length) return <p className="py-8 text-center text-sm" style={{ color: 'var(--text-muted)' }}>No node recommendations available</p>

  const sorted = [...data].sort((a, b) => b.monthly_savings - a.monthly_savings)

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="border-b text-xs uppercase" style={{ borderColor: 'var(--border-subtle)', color: 'var(--text-muted)' }}>
          <tr>
            <th className="w-8 px-2 py-2" />
            <th className="px-3 py-2">Node</th>
            <th className="px-3 py-2">Current</th>
            <th className="px-3 py-2">Recommended</th>
            <th className="px-3 py-2">Utilization</th>
            <th className="px-3 py-2">Impact</th>
            <th className="px-3 py-2">Priority</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((node, i) => {
            const isExpanded = expandedRow === i
            return (
              <><tr
                  key={i}
                  onClick={() => setExpandedRow(isExpanded ? null : i)}
                  className="cursor-pointer border-b transition-colors hover:opacity-80"
                  style={{ borderColor: 'var(--border-subtle)' }}
                >
                  <td className="px-2 py-2">
                    {isExpanded
                      ? <ChevronDown className="h-4 w-4" style={{ color: 'var(--text-muted)' }} />
                      : <ChevronRight className="h-4 w-4" style={{ color: 'var(--text-muted)' }} />}
                  </td>
                  <td className="px-3 py-2 font-medium" style={{ color: 'var(--text-primary)' }}>{node.node_name}</td>
                  <td className="px-3 py-2 font-mono text-xs" style={{ color: 'var(--text-secondary)' }}>{node.current_vm}</td>
                  <td className="px-3 py-2 font-mono text-xs text-green-600 dark:text-green-400">{node.recommended_vm}</td>
                  <td className="px-3 py-2">
                    <UtilizationBar value={node.avg_cpu_pct} label="CPU" />
                    <UtilizationBar value={node.avg_memory_pct} label="Mem" />
                  </td>
                  <td className={`px-3 py-2 font-medium ${node.monthly_savings >= 0 ? 'text-green-600' : 'text-amber-600'}`}>
                    {node.monthly_savings >= 0
                      ? `$${node.monthly_savings.toFixed(0)}/mo`
                      : `+$${Math.abs(node.monthly_savings).toFixed(0)}/mo`}
                  </td>
                  <td className="px-3 py-2">
                    <Badge variant={node.priority === 'high' ? 'red' : node.priority === 'medium' ? 'yellow' : 'green'}>
                      {node.priority}
                    </Badge>
                  </td>
                </tr>
                {isExpanded && (
                  <tr key={`${i}-detail`} className="border-b" style={{ borderColor: 'var(--border-subtle)' }}>
                    <td colSpan={7} className="px-4 py-3">
                      <div className="rounded-lg p-4" style={{ backgroundColor: 'var(--bg-surface)' }}>
                        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                          {/* Utilization Details */}
                          <div>
                            <h5 className="mb-2 text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
                              Current Utilization
                            </h5>
                            <div className="space-y-1.5">
                              <div className="flex justify-between text-sm">
                                <span style={{ color: 'var(--text-secondary)' }}>CPU Usage</span>
                                <span className={`font-medium ${node.avg_cpu_pct < 30 ? 'text-red-500' : node.avg_cpu_pct < 60 ? 'text-yellow-500' : 'text-green-500'}`}>
                                  {node.avg_cpu_pct.toFixed(1)}%
                                </span>
                              </div>
                              <div className="flex justify-between text-sm">
                                <span style={{ color: 'var(--text-secondary)' }}>Memory Usage</span>
                                <span className={`font-medium ${node.avg_memory_pct < 30 ? 'text-red-500' : node.avg_memory_pct < 60 ? 'text-yellow-500' : 'text-green-500'}`}>
                                  {node.avg_memory_pct.toFixed(1)}%
                                </span>
                              </div>
                              {node.cpu_cores != null && (
                                <div className="flex justify-between text-sm">
                                  <span style={{ color: 'var(--text-secondary)' }}>CPU Cores</span>
                                  <span style={{ color: 'var(--text-primary)' }}>{node.cpu_cores}</span>
                                </div>
                              )}
                              {node.memory_gb != null && (
                                <div className="flex justify-between text-sm">
                                  <span style={{ color: 'var(--text-secondary)' }}>Memory</span>
                                  <span style={{ color: 'var(--text-primary)' }}>{node.memory_gb} GB</span>
                                </div>
                              )}
                            </div>
                          </div>

                          {/* Cost Comparison */}
                          <div>
                            <h5 className="mb-2 text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
                              Cost Comparison
                            </h5>
                            <div className="space-y-1.5">
                              <div className="flex justify-between text-sm">
                                <span style={{ color: 'var(--text-secondary)' }}>Current VM</span>
                                <span className="font-mono text-xs" style={{ color: 'var(--text-primary)' }}>{node.current_vm}</span>
                              </div>
                              <div className="flex justify-between text-sm">
                                <span style={{ color: 'var(--text-secondary)' }}>Recommended VM</span>
                                <span className="font-mono text-xs text-green-600 dark:text-green-400">{node.recommended_vm}</span>
                              </div>
                              {node.current_cost != null && (
                                <div className="flex justify-between text-sm">
                                  <span style={{ color: 'var(--text-secondary)' }}>Current Cost</span>
                                  <span style={{ color: 'var(--text-primary)' }}>${node.current_cost.toFixed(2)}/mo</span>
                                </div>
                              )}
                              {node.recommended_cost != null && (
                                <div className="flex justify-between text-sm">
                                  <span style={{ color: 'var(--text-secondary)' }}>Recommended Cost</span>
                                  <span className={node.monthly_savings >= 0 ? 'text-green-600' : 'text-amber-600'}>
                                    ${node.recommended_cost.toFixed(2)}/mo
                                  </span>
                                </div>
                              )}
                              <div className="flex justify-between text-sm">
                                <span style={{ color: 'var(--text-secondary)' }}>
                                  {node.monthly_savings >= 0 ? 'Monthly Savings' : 'Monthly Cost Increase'}
                                </span>
                                <span className={`font-semibold ${node.monthly_savings >= 0 ? 'text-green-600' : 'text-amber-600'}`}>
                                  {node.monthly_savings >= 0
                                    ? `$${node.monthly_savings.toFixed(2)}/mo`
                                    : `+$${Math.abs(node.monthly_savings).toFixed(2)}/mo`}
                                </span>
                              </div>
                            </div>
                          </div>

                          {/* Reasoning */}
                          {node.reasoning && (
                            <div>
                              <h5 className="mb-2 text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
                                Reasoning
                              </h5>
                              <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
                                {node.reasoning}
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
