interface AnomalyData {
  total_anomalies: number
  average_severity: number
  highest_severity: number
  categories: Record<string, number>
  anomalies: { type: string; severity: number; workload_name?: string }[]
}

interface AnomalyDetectionProps {
  data: AnomalyData
}

const TYPE_LABELS: Record<string, string> = {
  memory_leak: 'Memory Leak',
  cpu_spike: 'CPU Spike',
  resource_drift: 'Resource Drift',
  unusual_pattern: 'Unusual Pattern',
  cost_spike: 'Cost Spike',
}

export default function AnomalyDetectionChart({ data }: AnomalyDetectionProps) {
  // Zero anomalies — green "all clear" banner
  if (!data?.total_anomalies) {
    return (
      <div className="flex items-center gap-3 rounded-lg bg-green-50 px-4 py-3 dark:bg-green-900/20">
        <svg className="h-5 w-5 flex-shrink-0 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
        <span className="text-sm font-medium text-green-800 dark:text-green-300">
          All systems running normally
        </span>
        <span className="ml-auto rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700 dark:bg-green-800/40 dark:text-green-300">
          0 anomalies
        </span>
      </div>
    )
  }

  // Has anomalies — warning/danger banner + category list
  const isHigh = data.highest_severity >= 0.7
  const bannerBg = isHigh ? 'bg-red-50 dark:bg-red-900/20' : 'bg-yellow-50 dark:bg-yellow-900/20'
  const bannerText = isHigh ? 'text-red-800 dark:text-red-300' : 'text-yellow-800 dark:text-yellow-300'
  const badgeBg = isHigh
    ? 'bg-red-100 text-red-700 dark:bg-red-800/40 dark:text-red-300'
    : 'bg-yellow-100 text-yellow-700 dark:bg-yellow-800/40 dark:text-yellow-300'
  const iconColor = isHigh ? 'text-red-500' : 'text-yellow-500'

  const categories = Object.entries(data.categories || {})
    .filter(([, v]) => v > 0)
    .sort(([, a], [, b]) => b - a)

  return (
    <div className="space-y-2">
      <div className={`flex items-center gap-3 rounded-lg px-4 py-3 ${bannerBg}`}>
        <svg className={`h-5 w-5 flex-shrink-0 ${iconColor}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <span className={`text-sm font-medium ${bannerText}`}>
          {data.total_anomalies} anomal{data.total_anomalies === 1 ? 'y' : 'ies'} detected
        </span>
        <span className={`ml-auto rounded-full px-2 py-0.5 text-xs font-medium ${badgeBg}`}>
          Severity: {(data.highest_severity * 100).toFixed(0)}%
        </span>
      </div>

      {categories.length > 0 && (
        <div className="grid grid-cols-2 gap-1.5 sm:grid-cols-3">
          {categories.map(([type, count]) => (
            <div key={type} className="flex items-center justify-between rounded border border-gray-100 px-2.5 py-1.5 text-xs dark:border-dark-700">
              <span className="text-dark-600 dark:text-dark-300">
                {TYPE_LABELS[type] || type.replace(/_/g, ' ')}
              </span>
              <span className="ml-2 font-semibold text-dark-800 dark:text-dark-200">{count}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
