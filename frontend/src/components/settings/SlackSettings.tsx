import { useState, useEffect } from 'react'
import Card from '../common/Card'
import Button from '../common/Button'
import { getSettings, saveSetting } from '../../api/settings'
import { api } from '../../api/client'

export default function SlackSettings() {
  const [webhookUrl, setWebhookUrl] = useState('')
  const [channel, setChannel] = useState('')
  const [enabled, setEnabled] = useState(false)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    getSettings().then((data) => {
      const s = data.settings || {}
      setWebhookUrl((s.slack_webhook_url as string) || '')
      setChannel((s.slack_channel as string) || '')
      setEnabled(!!s.slack_enabled)
    }).catch(() => {})
  }, [])

  const handleSave = async () => {
    setSaving(true)
    setMessage('')
    try {
      await Promise.all([
        saveSetting('slack_webhook_url', webhookUrl),
        saveSetting('slack_channel', channel),
        saveSetting('slack_enabled', enabled),
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
    setMessage('')
    try {
      const result = await api.post<{ success: boolean; message: string }>('/api/settings/test-slack', {})
      setMessage(result.success ? 'Test message sent to Slack' : result.message)
    } catch {
      setMessage('Slack test failed')
    } finally {
      setTesting(false)
    }
  }

  return (
    <Card>
      <h3 className="mb-4 text-lg font-semibold text-dark-900 dark:text-white">Slack Integration</h3>
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <input type="checkbox" id="slack-enabled" checked={enabled} onChange={(e) => setEnabled(e.target.checked)}
            className="rounded border-gray-300 text-primary-600 dark:border-dark-600" />
          <label htmlFor="slack-enabled" className="text-sm text-dark-700 dark:text-dark-300">Enable Slack notifications</label>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">Webhook URL</label>
          <input type="text" value={webhookUrl} onChange={(e) => setWebhookUrl(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-dark-600 dark:bg-dark-800 dark:text-white"
            placeholder="https://hooks.slack.com/services/..." />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">Channel</label>
          <input type="text" value={channel} onChange={(e) => setChannel(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-dark-600 dark:bg-dark-800 dark:text-white"
            placeholder="#kubeopt-alerts" />
        </div>

        {message && (
          <div className="rounded-lg bg-blue-50 px-3 py-2 text-sm text-blue-700 dark:bg-blue-900/20 dark:text-blue-400">{message}</div>
        )}

        <div className="flex gap-2 pt-2">
          <Button onClick={handleSave} disabled={saving} size="sm">{saving ? 'Saving...' : 'Save'}</Button>
          <Button variant="secondary" onClick={handleTest} disabled={testing || !webhookUrl} size="sm">{testing ? 'Sending...' : 'Send Test'}</Button>
        </div>
      </div>
    </Card>
  )
}
