import { api } from './client'

export interface Alert {
  id: number
  name: string
  alert_type: string
  threshold: number | null
  cluster_id: string | null
  enabled: boolean
  status: string
  severity?: string
  description?: string
  metric_name?: string
  operator?: string
  frequency?: string
  notification_email?: string
  created_at: string
  updated_at: string
}

interface AlertsResponse {
  alerts: Alert[]
  total: number
}

export async function getAlerts(clusterId?: string): Promise<AlertsResponse> {
  const params = clusterId ? `?cluster_id=${encodeURIComponent(clusterId)}` : ''
  return api.get(`/api/alerts${params}`)
}

export async function createAlert(data: {
  name: string
  alert_type: string
  threshold?: number
  cluster_id?: string
  severity?: string
  description?: string
  metric_name?: string
  operator?: string
  frequency?: string
  notification_email?: string
}): Promise<Alert> {
  return api.post('/api/alerts', data)
}

export async function updateAlert(
  alertId: number,
  data: {
    name?: string
    threshold?: number
    enabled?: boolean
    status?: string
    severity?: string
    description?: string
    metric_name?: string
    operator?: string
    frequency?: string
    notification_email?: string
  },
): Promise<Alert> {
  return api.put(`/api/alerts/${alertId}`, data)
}

export async function deleteAlert(alertId: number): Promise<void> {
  return api.delete(`/api/alerts/${alertId}`)
}
