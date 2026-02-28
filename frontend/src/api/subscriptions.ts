import { api } from './client'

interface Subscription {
  subscription_id: string
  subscription_name: string
  tenant_id?: string
  state: string
  is_default: boolean
}

export interface DropdownSubscription {
  id: string
  name: string
  is_default: boolean
}

export async function getSubscriptions(): Promise<{ subscriptions: Subscription[]; total: number }> {
  return api.get('/api/subscriptions')
}

export async function getSubscriptionDropdown(provider: string = 'azure'): Promise<{ subscriptions: DropdownSubscription[] }> {
  return api.get(`/api/subscriptions/dropdown?provider=${encodeURIComponent(provider)}`)
}

export async function validateSubscription(subscriptionId: string) {
  return api.post(`/api/subscriptions/${encodeURIComponent(subscriptionId)}/validate`)
}
