import { api } from './client'

export async function getPlan(clusterId: string) {
  return api.get(`/api/clusters/${encodeURIComponent(clusterId)}/plan`)
}

export async function generatePlan(clusterId: string, strategy = 'balanced', force = false) {
  return api.post(`/api/clusters/${encodeURIComponent(clusterId)}/plan/generate`, { strategy, force_regenerate: force })
}

export async function getPlanHistory(clusterId: string) {
  return api.get(`/api/clusters/${encodeURIComponent(clusterId)}/plans`)
}
