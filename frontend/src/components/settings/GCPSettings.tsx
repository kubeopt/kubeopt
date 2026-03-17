import { useState, useEffect } from 'react'
import Card from '../common/Card'
import Button from '../common/Button'
import Badge from '../common/Badge'
import { getSettings, saveSetting, testGCPConnection } from '../../api/settings'

export default function GCPSettings() {
  const [projectId, setProjectId] = useState('')
  const [zone, setZone] = useState('us-central1-a')
  const [serviceAccountKey, setServiceAccountKey] = useState('')
  const [billingApi, setBillingApi] = useState(true)
  const [billingDataset, setBillingDataset] = useState('')
  const [billingAccountId, setBillingAccountId] = useState('')
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<{ connected: boolean; message: string } | null>(null)
  const [message, setMessage] = useState('')

  useEffect(() => {
    getSettings().then((data) => {
      const s = data.settings || {}
      setProjectId((s.gcp_project_id as string) || '')
      setZone((s.gcp_zone as string) || 'us-central1-a')
      setBillingApi(s.gcp_billing_api !== false)
      setBillingDataset((s.gcp_billing_dataset as string) || '')
      setBillingAccountId((s.gcp_billing_account_id as string) || '')
    }).catch(() => {})
  }, [])

  const handleSave = async () => {
    setSaving(true)
    setMessage('')
    try {
      await Promise.all([
        saveSetting('gcp_project_id', projectId),
        saveSetting('gcp_zone', zone),
        saveSetting('gcp_billing_api', billingApi),
        ...(billingDataset ? [saveSetting('gcp_billing_dataset', billingDataset)] : []),
        ...(billingAccountId ? [saveSetting('gcp_billing_account_id', billingAccountId)] : []),
        ...(serviceAccountKey ? [saveSetting('gcp_service_account_key', serviceAccountKey)] : []),
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
      const result = await testGCPConnection({
        project_id: projectId,
        service_account_json: serviceAccountKey || undefined,
        zone,
      })
      setTestResult(result)
    } catch {
      setTestResult({ connected: false, message: 'Connection test failed' })
    } finally {
      setTesting(false)
    }
  }

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = (ev) => {
      setServiceAccountKey(ev.target?.result as string)
    }
    reader.readAsText(file)
  }

  return (
    <Card>
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-dark-900 dark:text-white">GCP Configuration</h3>
        <Badge variant="red">GKE</Badge>
      </div>

      <div className="space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">Project ID</label>
          <input type="text" value={projectId} onChange={(e) => setProjectId(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-dark-600 dark:bg-dark-800 dark:text-white"
            placeholder="my-project-123" />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">Default Zone</label>
          <select value={zone} onChange={(e) => setZone(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-dark-600 dark:bg-dark-800 dark:text-white">
            {['us-central1-a', 'us-central1-b', 'us-east1-b', 'us-west1-a', 'europe-west1-b', 'asia-east1-a'].map((z) => (
              <option key={z} value={z}>{z}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">Service Account Key (JSON)</label>
          <input type="file" accept=".json" onChange={handleFileUpload}
            className="w-full text-sm text-dark-600 file:mr-3 file:rounded-lg file:border-0 file:bg-primary-50 file:px-3 file:py-2 file:text-sm file:font-medium file:text-primary-700 hover:file:bg-primary-100 dark:text-dark-400" />
          {serviceAccountKey && <p className="mt-1 text-xs text-green-600">Key file loaded</p>}
        </div>
        <div className="flex items-center gap-2">
          <input type="checkbox" id="billing-api" checked={billingApi} onChange={(e) => setBillingApi(e.target.checked)}
            className="rounded border-gray-300 text-primary-600 dark:border-dark-600" />
          <label htmlFor="billing-api" className="text-sm text-dark-700 dark:text-dark-300">Enable Billing API integration</label>
        </div>
        {billingApi && (
          <>
            <div>
              <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">BigQuery Billing Dataset</label>
              <input type="text" value={billingDataset} onChange={(e) => setBillingDataset(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-dark-600 dark:bg-dark-800 dark:text-white"
                placeholder="billing_export" />
              <p className="mt-1 text-xs text-dark-500 dark:text-dark-400">Dataset name from BigQuery billing export</p>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">Billing Account ID</label>
              <input type="text" value={billingAccountId} onChange={(e) => setBillingAccountId(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-dark-600 dark:bg-dark-800 dark:text-white"
                placeholder="01F983-976921-D42BB2" />
              <p className="mt-1 text-xs text-dark-500 dark:text-dark-400">From GCP Console &gt; Billing &gt; Account ID</p>
            </div>
          </>
        )}

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
