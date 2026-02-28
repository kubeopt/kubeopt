import { api } from './client'

export async function getChartData(clusterId?: string, chartType?: string) {
  const params = new URLSearchParams()
  if (clusterId) params.set('cluster_id', clusterId)
  if (chartType) params.set('chart_type', chartType)
  return api.get(`/api/chart-data?${params}`)
}

export async function getDashboardOverview(clusterId?: string) {
  const params = clusterId ? `?cluster_id=${encodeURIComponent(clusterId)}` : ''
  return api.get(`/api/dashboard/overview${params}`)
}

export async function getCPUPlan(clusterId: string) {
  return api.get(`/api/clusters/${encodeURIComponent(clusterId)}/cpu-optimization-plan`)
}

export async function getAnalysisStatus(clusterId: string) {
  return api.get(`/api/clusters/${encodeURIComponent(clusterId)}/analysis-status`)
}
