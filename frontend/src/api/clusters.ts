import { api } from './client'
import type { Cluster, PortfolioSummary } from '../store/clusterStore'

interface ClusterListResponse {
  clusters: Cluster[]
  total: number
}

export async function getClusters(): Promise<ClusterListResponse> {
  return api.get('/api/clusters')
}

export async function addCluster(data: {
  cluster_name: string
  cloud_provider: string
  subscription_id?: string
  resource_group?: string
  account_id?: string
  region?: string
  project_id?: string
  zone?: string
}): Promise<Cluster> {
  return api.post('/api/clusters', data)
}

export async function removeCluster(clusterId: string): Promise<void> {
  return api.delete(`/api/cluster/${encodeURIComponent(clusterId)}/remove`)
}

export async function analyzeCluster(clusterId: string): Promise<{ session_key: string; status: string }> {
  return api.post(`/api/clusters/${encodeURIComponent(clusterId)}/analyze`)
}

export async function getClusterInfo(clusterId: string): Promise<Record<string, unknown>> {
  return api.get(`/api/cluster/${encodeURIComponent(clusterId)}/info`)
}

export async function getAnalysisStatus(clusterId: string): Promise<{
  status: string
  progress?: number
  current_phase?: string
  message?: string
}> {
  return api.get(`/api/clusters/${encodeURIComponent(clusterId)}/analysis-status`)
}

export async function getPortfolioSummary(): Promise<PortfolioSummary> {
  return api.get('/api/portfolio/summary')
}
