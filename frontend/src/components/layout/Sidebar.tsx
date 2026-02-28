import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Settings, Server } from 'lucide-react'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Portfolio' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

export default function Sidebar() {
  return (
    <aside className="hidden w-64 flex-shrink-0 border-r border-gray-200 bg-white dark:border-dark-700 dark:bg-dark-900 lg:block">
      <div className="flex h-16 items-center gap-2 border-b border-gray-200 px-6 dark:border-dark-700">
        <Server className="h-7 w-7 text-primary-500" />
        <span className="text-xl font-bold text-dark-900 dark:text-white">KubeOpt</span>
      </div>
      <nav className="mt-4 space-y-1 px-3">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-primary-50 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400'
                  : 'text-dark-600 hover:bg-gray-100 dark:text-dark-400 dark:hover:bg-dark-800'
              }`
            }
          >
            <item.icon className="h-5 w-5" />
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
