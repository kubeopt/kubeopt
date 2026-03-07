import { api } from './client'

export async function getSettings() {
  return api.get<{ settings: Record<string, unknown>; cloud_provider: string }>('/api/settings')
}

export async function saveSetting(key: string, value: unknown) {
  return api.post('/api/settings/save', { key, value })
}

export async function testAzureConnection() {
  return api.post<{ connected: boolean; message: string }>('/api/settings/test-azure', {})
}

export async function testAWSConnection() {
  return api.post<{ connected: boolean; message: string }>('/api/settings/test-aws', {})
}

export async function testGCPConnection(opts?: { project_id?: string; service_account_json?: string; zone?: string }) {
  return api.post<{ connected: boolean; message: string }>('/api/settings/test-gcp', opts || {})
}
