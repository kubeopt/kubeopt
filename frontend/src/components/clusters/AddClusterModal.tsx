import { useState, useEffect } from 'react'
import { clsx } from 'clsx'
import Modal from '../common/Modal'
import Button from '../common/Button'
import { addCluster } from '../../api/clusters'
import { getSubscriptionDropdown, type DropdownSubscription } from '../../api/subscriptions'

interface AddClusterModalProps {
  open: boolean
  onClose: () => void
  onAdded: () => void
}

type Provider = 'azure' | 'aws' | 'gcp'

export default function AddClusterModal({ open, onClose, onAdded }: AddClusterModalProps) {
  const [provider, setProvider] = useState<Provider>('azure')
  const [clusterName, setClusterName] = useState('')
  const [subscriptionId, setSubscriptionId] = useState('')
  const [resourceGroup, setResourceGroup] = useState('')
  const [accessKeyId, setAccessKeyId] = useState('')
  const [region, setRegion] = useState('')
  const [projectId, setProjectId] = useState('')
  const [zone, setZone] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // Subscription dropdown state
  const [subscriptions, setSubscriptions] = useState<DropdownSubscription[]>([])
  const [subsLoading, setSubsLoading] = useState(false)

  // Fetch subscriptions/accounts when modal opens (Azure or AWS)
  useEffect(() => {
    if (!open || (provider !== 'azure' && provider !== 'aws')) {
      setSubscriptions([])
      return
    }
    setSubsLoading(true)
    getSubscriptionDropdown(provider)
      .then((res) => {
        setSubscriptions(res.subscriptions || [])
        // Auto-select default for Azure, or first account for AWS
        if (provider === 'azure' && !subscriptionId) {
          const defaultSub = res.subscriptions?.find((s) => s.is_default)
          if (defaultSub) setSubscriptionId(defaultSub.id)
        } else if (provider === 'aws' && !accessKeyId && res.subscriptions?.length) {
          setAccessKeyId(res.subscriptions[0].id)
        }
      })
      .catch(() => setSubscriptions([]))
      .finally(() => setSubsLoading(false))
  }, [open, provider])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await addCluster({
        cluster_name: clusterName,
        cloud_provider: provider,
        subscription_id: provider === 'azure' ? subscriptionId : undefined,
        resource_group: provider === 'azure' ? resourceGroup : undefined,
        account_id: provider === 'aws' ? accessKeyId : undefined,
        region: provider !== 'azure' ? region : undefined,
        project_id: provider === 'gcp' ? projectId : undefined,
        zone: provider === 'gcp' ? zone : undefined,
      })
      onAdded()
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add cluster')
    } finally {
      setLoading(false)
    }
  }

  const providers: { id: Provider; label: string }[] = [
    { id: 'azure', label: 'Azure AKS' },
    { id: 'aws', label: 'AWS EKS' },
    { id: 'gcp', label: 'GCP GKE' },
  ]

  return (
    <Modal open={open} onClose={onClose} title="Add Cluster">
      {/* Provider tabs */}
      <div className="mb-4 flex gap-1 rounded-lg bg-gray-100 p-1 dark:bg-dark-800">
        {providers.map((p) => (
          <button
            key={p.id}
            onClick={() => setProvider(p.id)}
            className={clsx(
              'flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
              provider === p.id
                ? 'bg-white text-dark-900 shadow dark:bg-dark-700 dark:text-white'
                : 'text-dark-500 dark:text-dark-400',
            )}
          >
            {p.label}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="space-y-3">
        {error && (
          <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-400">{error}</div>
        )}

        <div>
          <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">Cluster Name</label>
          <input
            type="text"
            value={clusterName}
            onChange={(e) => setClusterName(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-dark-600 dark:bg-dark-800 dark:text-white"
            required
          />
        </div>

        {provider === 'azure' && (
          <>
            <div>
              <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">Subscription</label>
              {subsLoading ? (
                <div className="rounded-lg border border-gray-300 px-3 py-2 text-sm text-dark-400 dark:border-dark-600 dark:bg-dark-800">
                  Loading subscriptions...
                </div>
              ) : subscriptions.length > 0 ? (
                <select
                  value={subscriptionId}
                  onChange={(e) => setSubscriptionId(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-dark-600 dark:bg-dark-800 dark:text-white"
                >
                  <option value="">Select a subscription</option>
                  {subscriptions.map((sub) => (
                    <option key={sub.id} value={sub.id}>
                      {sub.name} ({sub.id.slice(0, 8)}...)
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  type="text"
                  value={subscriptionId}
                  onChange={(e) => setSubscriptionId(e.target.value)}
                  placeholder="Enter subscription ID"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-dark-600 dark:bg-dark-800 dark:text-white"
                />
              )}
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">
                Resource Group <span className="text-dark-400 dark:text-dark-500">(auto-detected if blank)</span>
              </label>
              <input type="text" value={resourceGroup} onChange={(e) => setResourceGroup(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-dark-600 dark:bg-dark-800 dark:text-white" />
            </div>
          </>
        )}

        {provider === 'aws' && (
          <>
            <div>
              <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">AWS Account</label>
              {subsLoading ? (
                <div className="rounded-lg border border-gray-300 px-3 py-2 text-sm text-dark-400 dark:border-dark-600 dark:bg-dark-800">
                  Loading accounts...
                </div>
              ) : subscriptions.length > 0 ? (
                <select
                  value={accessKeyId}
                  onChange={(e) => setAccessKeyId(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-dark-600 dark:bg-dark-800 dark:text-white"
                >
                  <option value="">Select an account</option>
                  {subscriptions.map((sub) => (
                    <option key={sub.id} value={sub.id}>
                      {sub.name || sub.id} ({sub.id})
                    </option>
                  ))}
                </select>
              ) : (
                <input type="text" value={accessKeyId} onChange={(e) => setAccessKeyId(e.target.value)}
                  placeholder="Enter AWS account ID"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-dark-600 dark:bg-dark-800 dark:text-white" />
              )}
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">Region</label>
              <input type="text" value={region} onChange={(e) => setRegion(e.target.value)} placeholder="us-east-1"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-dark-600 dark:bg-dark-800 dark:text-white" />
            </div>
          </>
        )}

        {provider === 'gcp' && (
          <>
            <div>
              <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">Project ID</label>
              <input type="text" value={projectId} onChange={(e) => setProjectId(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-dark-600 dark:bg-dark-800 dark:text-white" />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">Zone</label>
              <input type="text" value={zone} onChange={(e) => setZone(e.target.value)} placeholder="us-central1-a"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-dark-600 dark:bg-dark-800 dark:text-white" />
            </div>
          </>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <Button variant="secondary" onClick={onClose} type="button">Cancel</Button>
          <Button type="submit" disabled={loading}>{loading ? 'Adding...' : 'Add Cluster'}</Button>
        </div>
      </form>
    </Modal>
  )
}
