import { useState } from 'react'
import Card from '../common/Card'
import Button from '../common/Button'
import { useAuthStore } from '../../store/authStore'
import { api } from '../../api/client'

export default function UserProfileSettings() {
  const { user } = useAuthStore()
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setMessage('')

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match')
      return
    }
    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters')
      return
    }

    setSaving(true)
    try {
      await api.post('/api/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      })
      setMessage('Password updated')
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update password')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-4">
      <Card>
        <h3 className="mb-4 text-lg font-semibold text-dark-900 dark:text-white">User Profile</h3>
        <div className="space-y-3">
          <div>
            <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">Username</label>
            <input type="text" value={user?.username || ''} disabled
              className="w-full rounded-lg border border-gray-300 bg-gray-50 px-3 py-2 text-sm text-dark-500 dark:border-dark-600 dark:bg-dark-800 dark:text-dark-400" />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">Role</label>
            <input type="text" value={user?.role || ''} disabled
              className="w-full rounded-lg border border-gray-300 bg-gray-50 px-3 py-2 text-sm text-dark-500 dark:border-dark-600 dark:bg-dark-800 dark:text-dark-400" />
          </div>
        </div>
      </Card>

      <Card>
        <h3 className="mb-4 text-lg font-semibold text-dark-900 dark:text-white">Change Password</h3>
        <form onSubmit={handleChangePassword} className="space-y-3">
          <div>
            <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">Current Password</label>
            <input type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} required
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-dark-600 dark:bg-dark-800 dark:text-white" />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">New Password</label>
            <input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-dark-600 dark:bg-dark-800 dark:text-white" />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">Confirm New Password</label>
            <input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-dark-600 dark:bg-dark-800 dark:text-white" />
          </div>

          {error && (
            <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-400">{error}</div>
          )}
          {message && (
            <div className="rounded-lg bg-green-50 px-3 py-2 text-sm text-green-700 dark:bg-green-900/20 dark:text-green-400">{message}</div>
          )}

          <Button type="submit" disabled={saving} size="sm">{saving ? 'Updating...' : 'Update Password'}</Button>
        </form>
      </Card>
    </div>
  )
}
