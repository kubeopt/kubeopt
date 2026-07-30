import { api } from './client'

export interface CollectorStatus {
  cluster_id: string
  collected_at: string
  is_fresh: boolean
  data_source: 'collector' | 'provider'
  nodes: number
  pods: number
  metrics_server_available: boolean
}

export async function getCollectorStatus(clusterId: string): Promise<CollectorStatus | null> {
  try {
    return await api.get(`/api/collector/report/${encodeURIComponent(clusterId)}`)
  } catch {
    return null
  }
}
