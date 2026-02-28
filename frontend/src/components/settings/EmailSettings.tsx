import { useState, useEffect } from 'react'
import Card from '../common/Card'
import Button from '../common/Button'
import { getSettings, saveSetting } from '../../api/settings'
import { api } from '../../api/client'

export default function EmailSettings() {
  const [smtpHost, setSmtpHost] = useState('')
  const [smtpPort, setSmtpPort] = useState('587')
  const [smtpUser, setSmtpUser] = useState('')
  const [smtpPassword, setSmtpPassword] = useState('')
  const [recipientEmail, setRecipientEmail] = useState('')
  const [enabled, setEnabled] = useState(false)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    getSettings().then((data) => {
      const s = data.settings || {}
      setSmtpHost((s.smtp_host as string) || '')
      setSmtpPort(String(s.smtp_port || 587))
      setSmtpUser((s.smtp_user as string) || '')
      setRecipientEmail((s.email_recipient as string) || '')
      setEnabled(!!s.email_enabled)
    }).catch(() => {})
  }, [])

  const handleSave = async () => {
    setSaving(true)
    setMessage('')
    try {
      await Promise.all([
        saveSetting('smtp_host', smtpHost),
        saveSetting('smtp_port', parseInt(smtpPort)),
        saveSetting('smtp_user', smtpUser),
        saveSetting('email_recipient', recipientEmail),
        saveSetting('email_enabled', enabled),
        ...(smtpPassword ? [saveSetting('smtp_password', smtpPassword)] : []),
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
      const result = await api.post<{ success: boolean; message: string }>('/api/settings/test-email', {})
      setMessage(result.success ? 'Test email sent' : result.message)
    } catch {
      setMessage('Email test failed')
    } finally {
      setTesting(false)
    }
  }

  return (
    <Card>
      <h3 className="mb-4 text-lg font-semibold text-dark-900 dark:text-white">Email Notifications</h3>
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <input type="checkbox" id="email-enabled" checked={enabled} onChange={(e) => setEnabled(e.target.checked)}
            className="rounded border-gray-300 text-primary-600 dark:border-dark-600" />
          <label htmlFor="email-enabled" className="text-sm text-dark-700 dark:text-dark-300">Enable email notifications</label>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">SMTP Host</label>
            <input type="text" value={smtpHost} onChange={(e) => setSmtpHost(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-dark-600 dark:bg-dark-800 dark:text-white"
              placeholder="smtp.gmail.com" />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">SMTP Port</label>
            <input type="text" value={smtpPort} onChange={(e) => setSmtpPort(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-dark-600 dark:bg-dark-800 dark:text-white"
              placeholder="587" />
          </div>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">SMTP Username</label>
          <input type="text" value={smtpUser} onChange={(e) => setSmtpUser(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-dark-600 dark:bg-dark-800 dark:text-white" />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">SMTP Password</label>
          <input type="password" value={smtpPassword} onChange={(e) => setSmtpPassword(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-dark-600 dark:bg-dark-800 dark:text-white"
            placeholder="Enter to update" />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">Recipient Email</label>
          <input type="email" value={recipientEmail} onChange={(e) => setRecipientEmail(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-dark-600 dark:bg-dark-800 dark:text-white"
            placeholder="admin@company.com" />
        </div>

        {message && (
          <div className="rounded-lg bg-blue-50 px-3 py-2 text-sm text-blue-700 dark:bg-blue-900/20 dark:text-blue-400">{message}</div>
        )}

        <div className="flex gap-2 pt-2">
          <Button onClick={handleSave} disabled={saving} size="sm">{saving ? 'Saving...' : 'Save'}</Button>
          <Button variant="secondary" onClick={handleTest} disabled={testing || !smtpHost} size="sm">{testing ? 'Sending...' : 'Send Test'}</Button>
        </div>
      </div>
    </Card>
  )
}
