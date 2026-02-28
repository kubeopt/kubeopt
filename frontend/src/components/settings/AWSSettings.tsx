import { useState, useEffect } from 'react'
import Card from '../common/Card'
import Button from '../common/Button'
import Badge from '../common/Badge'
import { getSettings, saveSetting, testAWSConnection } from '../../api/settings'

export default function AWSSettings() {
  const [accessKeyId, setAccessKeyId] = useState('')
  const [secretAccessKey, setSecretAccessKey] = useState('')
  const [region, setRegion] = useState('us-east-1')
  const [costExplorer, setCostExplorer] = useState(true)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<{ connected: boolean; message: string } | null>(null)
  const [message, setMessage] = useState('')

  useEffect(() => {
    getSettings().then((data) => {
      const s = data.settings || {}
      setAccessKeyId((s.aws_access_key_id as string) || '')
      setRegion((s.aws_region as string) || 'us-east-1')
      setCostExplorer(s.aws_cost_explorer !== false)
    }).catch(() => {})
  }, [])

  const handleSave = async () => {
    setSaving(true)
    setMessage('')
    try {
      await Promise.all([
        saveSetting('aws_access_key_id', accessKeyId),
        saveSetting('aws_region', region),
        saveSetting('aws_cost_explorer', costExplorer),
        ...(secretAccessKey ? [saveSetting('aws_secret_access_key', secretAccessKey)] : []),
      ])
      setMessage('Settings saved')
    } catch {
      setMessage('Failed to save settings')
    } finally {
      setSaving(false)
    }
  }

  const handleTest = async () => {
    setTesting(true)
    setTestResult(null)
    try {
      const result = await testAWSConnection()
      setTestResult(result)
    } catch {
      setTestResult({ connected: false, message: 'Connection test failed' })
    } finally {
      setTesting(false)
    }
  }

  return (
    <Card>
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-dark-900 dark:text-white">AWS Configuration</h3>
        <Badge variant="yellow">EKS</Badge>
      </div>

      <div className="space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">Access Key ID</label>
          <input type="text" value={accessKeyId} onChange={(e) => setAccessKeyId(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-dark-600 dark:bg-dark-800 dark:text-white"
            placeholder="AKIAIOSFODNN7EXAMPLE" />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">Secret Access Key</label>
          <input type="password" value={secretAccessKey} onChange={(e) => setSecretAccessKey(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-dark-600 dark:bg-dark-800 dark:text-white"
            placeholder="Enter to update (leave empty to keep current)" />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">Default Region</label>
          <select value={region} onChange={(e) => setRegion(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-dark-600 dark:bg-dark-800 dark:text-white">
            {['us-east-1', 'us-east-2', 'us-west-1', 'us-west-2', 'eu-west-1', 'eu-central-1', 'ap-southeast-1', 'ap-northeast-1'].map((r) => (
              <option key={r} value={r}>{r}</option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <input type="checkbox" id="cost-explorer" checked={costExplorer} onChange={(e) => setCostExplorer(e.target.checked)}
            className="rounded border-gray-300 text-primary-600 dark:border-dark-600" />
          <label htmlFor="cost-explorer" className="text-sm text-dark-700 dark:text-dark-300">Enable Cost Explorer integration</label>
        </div>

        {testResult && (
          <div className={`rounded-lg px-3 py-2 text-sm ${testResult.connected ? 'bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-400' : 'bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-400'}`}>
            {testResult.message}
          </div>
        )}
        {message && (
          <div className="rounded-lg bg-blue-50 px-3 py-2 text-sm text-blue-700 dark:bg-blue-900/20 dark:text-blue-400">{message}</div>
        )}

        <div className="flex gap-2 pt-2">
          <Button onClick={handleSave} disabled={saving} size="sm">{saving ? 'Saving...' : 'Save'}</Button>
          <Button variant="secondary" onClick={handleTest} disabled={testing} size="sm">{testing ? 'Testing...' : 'Test Connection'}</Button>
        </div>
      </div>
    </Card>
  )
}
