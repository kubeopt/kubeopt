import { Sun, Moon, LogOut, User, Menu } from 'lucide-react'
import { useTheme } from '../../hooks/useTheme'
import { useAuth } from '../../hooks/useAuth'

interface HeaderProps {
  onMenuToggle: () => void
}

export default function Header({ onMenuToggle }: HeaderProps) {
  const { isDark, toggleTheme } = useTheme()
  const { logout, user } = useAuth()

  return (
    <header
      className="flex h-16 items-center justify-between px-6"
      style={{ backgroundColor: 'var(--bg-header)' }}
    >
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuToggle}
          className="rounded-lg p-2 transition-colors hover:bg-primary-50 dark:hover:bg-dark-800 lg:hidden"
          style={{ color: 'var(--text-muted)' }}
          title="Menu"
        >
          <Menu className="h-5 w-5" />
        </button>
        <span className="text-xs font-medium tracking-wide" style={{ color: 'var(--text-muted)' }}>
          Intelligent. Insightful. Illuminating.
        </span>
      </div>
      <div className="flex items-center gap-3">
        <button
          onClick={toggleTheme}
          className="rounded-lg p-2 transition-colors hover:bg-primary-50 dark:hover:bg-dark-800"
          style={{ color: 'var(--text-muted)' }}
          title={isDark ? 'Light mode' : 'Dark mode'}
        >
          {isDark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
        </button>
        {user && (
          <span className="flex items-center gap-1.5 text-sm" style={{ color: 'var(--text-secondary)' }}>
            <User className="h-4 w-4" />
            {user.username}
          </span>
        )}
        <button
          onClick={logout}
          className="rounded-lg p-2 transition-colors hover:bg-primary-50 dark:hover:bg-dark-800"
          style={{ color: 'var(--text-muted)' }}
          title="Logout"
        >
          <LogOut className="h-5 w-5" />
        </button>
      </div>
    </header>
  )
}
