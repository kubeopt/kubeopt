import { api } from './client'

export async function getRecommendations(clusterId: string) {
  return api.get(`/api/clusters/${encodeURIComponent(clusterId)}/recommendations`)
}
