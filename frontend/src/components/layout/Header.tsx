import { Sun, Moon, LogOut, User } from 'lucide-react'
import { useTheme } from '../../hooks/useTheme'
import { useAuth } from '../../hooks/useAuth'

export default function Header() {
  const { isDark, toggleTheme } = useTheme()
  const { logout, user } = useAuth()

  return (
    <header className="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-6 dark:border-dark-700 dark:bg-dark-900">
      <div className="text-sm text-dark-500 dark:text-dark-400">
        Multi-Cloud Kubernetes Cost Optimizer
      </div>
      <div className="flex items-center gap-3">
        <button
          onClick={toggleTheme}
          className="rounded-lg p-2 text-dark-500 hover:bg-gray-100 dark:text-dark-400 dark:hover:bg-dark-800"
          title={isDark ? 'Light mode' : 'Dark mode'}
        >
          {isDark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
        </button>
        {user && (
          <span className="flex items-center gap-1.5 text-sm text-dark-600 dark:text-dark-300">
            <User className="h-4 w-4" />
            {user.username}
          </span>
        )}
        <button
          onClick={logout}
          className="rounded-lg p-2 text-dark-500 hover:bg-gray-100 dark:text-dark-400 dark:hover:bg-dark-800"
          title="Logout"
        >
          <LogOut className="h-5 w-5" />
        </button>
      </div>
    </header>
  )
}
