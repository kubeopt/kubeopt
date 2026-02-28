import { useState, useEffect } from 'react'
import Card from '../common/Card'
import Button from '../common/Button'
import Badge from '../common/Badge'
import { getSettings, saveSetting, testAzureConnection } from '../../api/settings'

export default function AzureSettings() {
  const [subscriptionId, setSubscriptionId] = useState('')
  const [resourceGroup, setResourceGroup] = useState('')
  const [tenantId, setTenantId] = useState('')
  const [clientId, setClientId] = useState('')
  const [clientSecret, setClientSecret] = useState('')
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<{ connected: boolean; message: string } | null>(null)
  const [message, setMessage] = useState('')

  useEffect(() => {
    getSettings().then((data) => {
      const s = data.settings || {}
      setSubscriptionId((s.azure_subscription_id as string) || '')
      setResourceGroup((s.azure_resource_group as string) || '')
      setTenantId((s.azure_tenant_id as string) || '')
      setClientId((s.azure_client_id as string) || '')
    }).catch(() => {})
  }, [])

  const handleSave = async () => {
    setSaving(true)
    setMessage('')
    try {
      await Promise.all([
        saveSetting('azure_subscription_id', subscriptionId),
        saveSetting('azure_resource_group', resourceGroup),
        saveSetting('azure_tenant_id', tenantId),
        saveSetting('azure_client_id', clientId),
        ...(clientSecret ? [saveSetting('azure_client_secret', clientSecret)] : []),
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
      const result = await testAzureConnection()
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
        <h3 className="text-lg font-semibold text-dark-900 dark:text-white">Azure Configuration</h3>
        <Badge variant="blue">AKS</Badge>
      </div>

      <div className="space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">Subscription ID</label>
          <input type="text" value={subscriptionId} onChange={(e) => setSubscriptionId(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-dark-600 dark:bg-dark-800 dark:text-white"
            placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">Resource Group</label>
          <input type="text" value={resourceGroup} onChange={(e) => setResourceGroup(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-dark-600 dark:bg-dark-800 dark:text-white" />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">Tenant ID</label>
          <input type="text" value={tenantId} onChange={(e) => setTenantId(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-dark-600 dark:bg-dark-800 dark:text-white" />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">Client ID</label>
          <input type="text" value={clientId} onChange={(e) => setClientId(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-dark-600 dark:bg-dark-800 dark:text-white" />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">Client Secret</label>
          <input type="password" value={clientSecret} onChange={(e) => setClientSecret(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-dark-600 dark:bg-dark-800 dark:text-white"
            placeholder="Enter to update (leave empty to keep current)" />
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
