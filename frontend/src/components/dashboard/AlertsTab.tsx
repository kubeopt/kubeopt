import { useCallback, useEffect, useState } from 'react'
import { Pause, Play, Plus, Trash2 } from 'lucide-react'
import { getAlerts, createAlert, updateAlert, deleteAlert, type Alert } from '../../api/alerts'
import { useAutoRefresh } from '../../hooks/useAutoRefresh'
import Card from '../common/Card'
import Badge from '../common/Badge'
import Button from '../common/Button'
import Modal from '../common/Modal'

interface AlertsTabProps {
  clusterId: string
}

const STATUS_BADGE: Record<string, 'green' | 'yellow' | 'red' | 'gray'> = {
  active: 'green',
  paused: 'gray',
  triggered: 'red',
}

const SEVERITY_BADGE: Record<string, 'red' | 'yellow' | 'blue' | 'gray'> = {
  critical: 'red',
  warning: 'yellow',
  info: 'blue',
}

const inputCls = 'w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-dark-600 dark:bg-dark-800 dark:text-white'

export default function AlertsTab({ clusterId }: AlertsTabProps) {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [editAlert, setEditAlert] = useState<Alert | null>(null)
  const [confirmDelete, setConfirmDelete] = useState<Alert | null>(null)

  // Form state
  const [formName, setFormName] = useState('')
  const [formType, setFormType] = useState('cost_threshold')
  const [formThreshold, setFormThreshold] = useState('')
  const [formSeverity, setFormSeverity] = useState('warning')
  const [formDescription, setFormDescription] = useState('')
  const [formMetric, setFormMetric] = useState('cost')
  const [formOperator, setFormOperator] = useState('>')
  const [formFrequency, setFormFrequency] = useState('hourly')
  const [formEmail, setFormEmail] = useState('')

  const fetchAlerts = useCallback(async () => {
    try {
      const data = await getAlerts(clusterId)
      setAlerts(data.alerts || [])
    } catch {
      // handled
    } finally {
      setLoading(false)
    }
  }, [clusterId])

  useEffect(() => { fetchAlerts() }, [fetchAlerts])
  useAutoRefresh(fetchAlerts, { intervalMs: 60_000 })

  const resetForm = () => {
    setFormName('')
    setFormType('cost_threshold')
    setFormThreshold('')
    setFormSeverity('warning')
    setFormDescription('')
    setFormMetric('cost')
    setFormOperator('>')
    setFormFrequency('hourly')
    setFormEmail('')
  }

  const handleCreate = async () => {
    await createAlert({
      name: formName,
      alert_type: formType,
      threshold: formThreshold ? parseFloat(formThreshold) : undefined,
      cluster_id: clusterId,
      severity: formSeverity,
      description: formDescription || undefined,
      metric_name: formMetric,
      operator: formOperator,
      frequency: formFrequency,
      notification_email: formEmail || undefined,
    })
    setShowCreate(false)
    resetForm()
    await fetchAlerts()
  }

  const handleUpdate = async () => {
    if (!editAlert) return
    await updateAlert(editAlert.id, {
      name: formName,
      threshold: formThreshold ? parseFloat(formThreshold) : undefined,
      severity: formSeverity,
      description: formDescription || undefined,
      metric_name: formMetric,
      operator: formOperator,
      frequency: formFrequency,
      notification_email: formEmail || undefined,
    })
    setEditAlert(null)
    resetForm()
    await fetchAlerts()
  }

  const handleTogglePause = async (alert: Alert) => {
    await updateAlert(alert.id, {
      enabled: !alert.enabled,
      status: alert.enabled ? 'paused' : 'active',
    })
    await fetchAlerts()
  }

  const handleDelete = async () => {
    if (!confirmDelete) return
    await deleteAlert(confirmDelete.id)
    setConfirmDelete(null)
    await fetchAlerts()
  }

  const openEdit = (alert: Alert) => {
    setFormName(alert.name)
    setFormType(alert.alert_type)
    setFormThreshold(alert.threshold?.toString() || '')
    setFormSeverity(alert.severity || 'warning')
    setFormDescription(alert.description || '')
    setFormMetric(alert.metric_name || 'cost')
    setFormOperator(alert.operator || '>')
    setFormFrequency(alert.frequency || 'hourly')
    setFormEmail(alert.notification_email || '')
    setEditAlert(alert)
  }

  if (loading) {
    return (
      <Card className="py-8 text-center text-dark-400">
        Loading alerts...
      </Card>
    )
  }

  const formFields = (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">Name</label>
          <input value={formName} onChange={(e) => setFormName(e.target.value)} className={inputCls} placeholder="Alert name" />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">Severity</label>
          <select value={formSeverity} onChange={(e) => setFormSeverity(e.target.value)} className={inputCls}>
            <option value="info">Info</option>
            <option value="warning">Warning</option>
            <option value="critical">Critical</option>
          </select>
        </div>
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">Description</label>
        <textarea
          value={formDescription}
          onChange={(e) => setFormDescription(e.target.value)}
          className={inputCls}
          rows={2}
          placeholder="Optional description"
        />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">Type</label>
          <select value={formType} onChange={(e) => setFormType(e.target.value)} className={inputCls}>
            <option value="cost_threshold">Cost Threshold</option>
            <option value="cpu_monitoring">CPU Monitoring</option>
            <option value="memory_monitoring">Memory Monitoring</option>
            <option value="pod_restart">Pod Restart</option>
          </select>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">Metric</label>
          <select value={formMetric} onChange={(e) => setFormMetric(e.target.value)} className={inputCls}>
            <option value="cost">Cost ($)</option>
            <option value="cpu_percent">CPU %</option>
            <option value="memory_percent">Memory %</option>
            <option value="pod_restarts">Pod Restarts</option>
            <option value="node_count">Node Count</option>
          </select>
        </div>
      </div>
      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">Operator</label>
          <select value={formOperator} onChange={(e) => setFormOperator(e.target.value)} className={inputCls}>
            <option value=">">&gt; Greater than</option>
            <option value=">=">&gt;= Greater or equal</option>
            <option value="<">&lt; Less than</option>
            <option value="<=">&lt;= Less or equal</option>
            <option value="==">== Equal</option>
          </select>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">Threshold</label>
          <input
            type="number"
            value={formThreshold}
            onChange={(e) => setFormThreshold(e.target.value)}
            className={inputCls}
            placeholder="e.g. 1000"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">Frequency</label>
          <select value={formFrequency} onChange={(e) => setFormFrequency(e.target.value)} className={inputCls}>
            <option value="realtime">Real-time</option>
            <option value="hourly">Hourly</option>
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
          </select>
        </div>
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium text-dark-700 dark:text-dark-300">Notification Email</label>
        <input
          type="email"
          value={formEmail}
          onChange={(e) => setFormEmail(e.target.value)}
          className={inputCls}
          placeholder="user@example.com (optional)"
        />
      </div>
    </div>
  )

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-dark-900 dark:text-white">Alerts</h3>
        <Button size="sm" onClick={() => { resetForm(); setShowCreate(true) }}>
          <Plus className="mr-1.5 h-4 w-4" />
          Create Alert
        </Button>
      </div>

      {alerts.length === 0 ? (
        <Card className="py-8 text-center text-dark-400">
          No alerts configured. Create one to start monitoring.
        </Card>
      ) : (
        <div className="space-y-3">
          {alerts.map((alert) => (
            <Card key={alert.id} className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => openEdit(alert)}
                    className="font-medium text-dark-800 hover:underline dark:text-dark-200"
                  >
                    {alert.name}
                  </button>
                  <Badge variant={STATUS_BADGE[alert.status] || 'gray'}>
                    {alert.status}
                  </Badge>
                  {alert.severity && (
                    <Badge variant={SEVERITY_BADGE[alert.severity] || 'gray'}>
                      {alert.severity}
                    </Badge>
                  )}
                </div>
                <p className="mt-0.5 text-xs text-dark-400">
                  {alert.alert_type.replace(/_/g, ' ')}
                  {alert.metric_name && ` · ${alert.metric_name}`}
                  {alert.operator && alert.threshold != null && ` ${alert.operator} ${alert.threshold}`}
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handleTogglePause(alert)}
                  className="rounded p-1.5 text-dark-400 hover:bg-gray-100 dark:hover:bg-dark-800"
                  title={alert.enabled ? 'Pause' : 'Activate'}
                >
                  {alert.enabled ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                </button>
                <button
                  onClick={() => setConfirmDelete(alert)}
                  className="rounded p-1.5 text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
                  title="Delete"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Create modal */}
      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Create Alert">
        {formFields}
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="secondary" size="sm" onClick={() => setShowCreate(false)}>Cancel</Button>
          <Button size="sm" onClick={handleCreate} disabled={!formName}>Create</Button>
        </div>
      </Modal>

      {/* Edit modal */}
      <Modal open={!!editAlert} onClose={() => setEditAlert(null)} title="Edit Alert">
        {formFields}
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="secondary" size="sm" onClick={() => setEditAlert(null)}>Cancel</Button>
          <Button size="sm" onClick={handleUpdate} disabled={!formName}>Save</Button>
        </div>
      </Modal>

      {/* Delete confirmation */}
      <Modal open={!!confirmDelete} onClose={() => setConfirmDelete(null)} title="Delete Alert">
        <p className="text-sm text-dark-600 dark:text-dark-300">
          Are you sure you want to delete <strong>{confirmDelete?.name}</strong>? This cannot be undone.
        </p>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="secondary" size="sm" onClick={() => setConfirmDelete(null)}>Cancel</Button>
          <Button variant="danger" size="sm" onClick={handleDelete}>Delete</Button>
        </div>
      </Modal>
    </div>
  )
}
