import { create } from 'zustand'

interface User {
  username: string
  role: string
}

interface AuthState {
  token: string | null
  user: User | null
  licenseTier: string
  isAuthenticated: boolean
  setAuth: (token: string, user: User) => void
  setLicenseTier: (tier: string) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem('kubeopt_token'),
  user: JSON.parse(localStorage.getItem('kubeopt_user') || 'null'),
  licenseTier: 'FREE',
  isAuthenticated: !!localStorage.getItem('kubeopt_token'),

  setAuth: (token, user) => {
    localStorage.setItem('kubeopt_token', token)
    localStorage.setItem('kubeopt_user', JSON.stringify(user))
    set({ token, user, isAuthenticated: true })
  },

  setLicenseTier: (tier) => set({ licenseTier: tier }),

  logout: () => {
    localStorage.removeItem('kubeopt_token')
    localStorage.removeItem('kubeopt_user')
    set({ token: null, user: null, isAuthenticated: false, licenseTier: 'FREE' })
  },
}))
