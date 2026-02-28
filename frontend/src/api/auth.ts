import { api } from './client'

interface LoginResponse {
  token: string
  token_type: string
  expires_in: number
  user?: { username: string; role: string }
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  return api.post('/api/auth/login', { username, password })
}

export async function refreshToken(): Promise<{ token: string }> {
  return api.post('/api/auth/refresh-token')
}

export async function getLicenseStatus(): Promise<{ valid: boolean; tier: string; features: string[] }> {
  return api.get('/api/auth/license/status')
}
