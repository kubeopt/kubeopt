import { useState, useEffect } from 'react'
import Card from '../common/Card'
import Badge from '../common/Badge'
import { api } from '../../api/client'

interface SystemStatus {
  status: string
  version?: string
  cloud_provider?: string
  uptime?: string
  python_version?: string
  environment?: string
}

export default function AdvancedSettings() {
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null)

  useEffect(() => {
    api.get<SystemStatus>('/api/system_status').then(setSystemStatus).catch(() => {})
  }, [])

  const envVars = [
    { key: 'CLOUD_PROVIDER', desc: 'Active cloud provider' },
    { key: 'PLAN_GENERATION_URL', desc: 'Plan generation service URL' },
    { key: 'LICENSE_API_URL', desc: 'License manager service URL' },
    { key: 'PYTHONPATH', desc: 'Python module path' },
  ]

  return (
    <div className="space-y-4">
      <Card>
        <h3 className="mb-4 text-lg font-semibold text-dark-900 dark:text-white">System Status</h3>
        {systemStatus ? (
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-dark-400">Status</span>
              <div className="mt-0.5 font-medium text-dark-800 dark:text-dark-200">
                <Badge variant={systemStatus.status === 'healthy' ? 'green' : 'red'}>{systemStatus.status}</Badge>
              </div>
            </div>
            {systemStatus.version && (
              <div>
                <span className="text-dark-400">Version</span>
                <div className="mt-0.5 font-medium text-dark-800 dark:text-dark-200">{systemStatus.version}</div>
              </div>
            )}
            {systemStatus.cloud_provider && (
              <div>
                <span className="text-dark-400">Cloud Provider</span>
                <div className="mt-0.5 font-medium text-dark-800 dark:text-dark-200">{systemStatus.cloud_provider}</div>
              </div>
            )}
            {systemStatus.environment && (
              <div>
                <span className="text-dark-400">Environment</span>
                <div className="mt-0.5 font-medium text-dark-800 dark:text-dark-200">{systemStatus.environment}</div>
              </div>
            )}
          </div>
        ) : (
          <p className="text-sm text-dark-400">Loading system status...</p>
        )}
      </Card>

      <Card>
        <h3 className="mb-4 text-lg font-semibold text-dark-900 dark:text-white">Service URLs</h3>
        <div className="space-y-2 text-sm">
          {envVars.map((v) => (
            <div key={v.key} className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2 dark:bg-dark-800">
              <div>
                <span className="font-mono text-xs text-dark-500 dark:text-dark-400">{v.key}</span>
                <span className="ml-2 text-dark-400">{v.desc}</span>
              </div>
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <h3 className="mb-4 text-lg font-semibold text-dark-900 dark:text-white">API Documentation</h3>
        <p className="text-sm text-dark-600 dark:text-dark-400">
          Interactive API documentation is available at{' '}
          <a href="/docs" target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline dark:text-primary-400">/docs</a>
          {' '}(Swagger UI) or{' '}
          <a href="/redoc" target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline dark:text-primary-400">/redoc</a>
          {' '}(ReDoc).
        </p>
      </Card>
    </div>
  )
}
