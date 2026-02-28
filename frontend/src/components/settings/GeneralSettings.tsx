import { useState, useEffect } from 'react'
import Card from '../common/Card'
import Button from '../common/Button'
import Badge from '../common/Badge'
import { getSettings, saveSetting } from '../../api/settings'

export default function GeneralSettings() {
  const [autoAnalysis, setAutoAnalysis] = useState(false)
  const [analysisInterval, setAnalysisInterval] = useState('24')
  const [licenseKey, setLicenseKey] = useState('')
  const [licenseTier, setLicenseTier] = useState('FREE')
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    getSettings().then((data) => {
      const s = data.settings || {}
      setAutoAnalysis(!!s.auto_analysis_enabled)
      setAnalysisInterval(String(s.auto_analysis_interval_hours || 24))
      setLicenseKey((s.license_key as string) || '')
      setLicenseTier((s.license_tier as string) || 'FREE')
    }).catch(() => {})
  }, [])

  const handleSave = async () => {
    setSaving(true)
    setMessage('')
    try {
      await Promise.all([
        saveSetting('auto_analysis_enabled', autoAnalysis),
        saveSetting('auto_analysis_interval_hours', parseInt(analysisInterval)),
        ...(licenseKey ? [saveSetting('license_key', licenseKey)] : []),
      ])
      setMessage('Settings saved')
    } catch {
      setMessage('Failed to save settings')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-4">
      <Card>
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-dark-900 dark:text-white">License</h3>
          <Badge variant={licenseTier === 'ENTERPRISE' ? 'blue' : licenseTier === 'PRO' ? 'green' : 'gray'}>{licenseTier}</Badge>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">License Key</label>
          <input type="text" value={licenseKey} onChange={(e) => setLicenseKey(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-mono dark:border-dark-600 dark:bg-dark-800 dark:text-white"
            placeholder="KUBEOPT-XXXX-XXXX-XXXX" />
        </div>
      </Card>

      <Card>
        <h3 className="mb-4 text-lg font-semibold text-dark-900 dark:text-white">Auto Analysis</h3>
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <input type="checkbox" id="auto-analysis" checked={autoAnalysis} onChange={(e) => setAutoAnalysis(e.target.checked)}
              className="rounded border-gray-300 text-primary-600 dark:border-dark-600" />
            <label htmlFor="auto-analysis" className="text-sm text-dark-700 dark:text-dark-300">Enable scheduled automatic analysis</label>
          </div>
          {autoAnalysis && (
            <div>
              <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">Interval (hours)</label>
              <select value={analysisInterval} onChange={(e) => setAnalysisInterval(e.target.value)}
                className="w-48 rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-dark-600 dark:bg-dark-800 dark:text-white">
                {['6', '12', '24', '48', '72'].map((h) => (
                  <option key={h} value={h}>Every {h} hours</option>
                ))}
              </select>
            </div>
          )}
        </div>
      </Card>

      {message && (
        <div className="rounded-lg bg-blue-50 px-3 py-2 text-sm text-blue-700 dark:bg-blue-900/20 dark:text-blue-400">{message}</div>
      )}

      <div className="flex gap-2">
        <Button onClick={handleSave} disabled={saving} size="sm">{saving ? 'Saving...' : 'Save'}</Button>
      </div>
    </div>
  )
}
