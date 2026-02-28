import { useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { login as apiLogin, getLicenseStatus } from '../api/auth'

export function useAuth() {
  const { setAuth, setLicenseTier, logout: storeLogout, isAuthenticated, user } = useAuthStore()
  const navigate = useNavigate()

  const login = useCallback(async (username: string, password: string) => {
    const res = await apiLogin(username, password)
    setAuth(res.token, res.user || { username, role: 'admin' })

    // Fetch license status after login
    try {
      const license = await getLicenseStatus()
      setLicenseTier(license.tier)
    } catch {
      // Ignore license check failure
    }

    navigate('/')
  }, [setAuth, setLicenseTier, navigate])

  const logout = useCallback(() => {
    storeLogout()
    navigate('/login')
  }, [storeLogout, navigate])

  return { login, logout, isAuthenticated, user }
}
