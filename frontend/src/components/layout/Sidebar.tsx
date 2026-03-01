import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Settings, ChevronsLeft, ChevronsRight, X } from 'lucide-react'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Portfolio' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

interface SidebarProps {
  collapsed: boolean
  onToggle: () => void
  mobileOpen: boolean
  onMobileClose: () => void
}

export default function Sidebar({ collapsed, onToggle, mobileOpen, onMobileClose }: SidebarProps) {
  const width = collapsed ? 'w-[68px]' : 'w-64'

  return (
    <>
      {/* Desktop sidebar */}
      <aside
        className={`hidden flex-shrink-0 transition-all duration-200 lg:flex lg:flex-col ${width}`}
        style={{ backgroundColor: 'var(--bg-sidebar)' }}
      >
        <SidebarContent collapsed={collapsed} onToggle={onToggle} />
      </aside>

      {/* Mobile sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-64 transition-transform duration-200 lg:hidden ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        style={{ backgroundColor: 'var(--bg-sidebar)' }}
      >
        <div className="px-4 pb-3 pt-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <img src="/kubeopt_eyecon.png" alt="KubeOpt" className="h-8 w-8 animate-spin-slow" />
              <span className="text-xl font-bold" style={{ color: 'var(--text-primary)' }}>KubeOpt</span>
            </div>
            <button onClick={onMobileClose} className="rounded-lg p-1.5 transition-colors hover:bg-primary-50 dark:hover:bg-dark-800" style={{ color: 'var(--text-muted)' }}>
              <X className="h-5 w-5" />
            </button>
          </div>
          <p className="mt-1.5 pl-10 text-[11px] leading-tight italic" style={{ color: 'var(--text-muted)' }}>
            Your third eye for kubernetes costs
          </p>
        </div>
        <nav className="mt-4 space-y-1 px-3">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              onClick={onMobileClose}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400'
                    : 'hover:bg-primary-50 dark:hover:bg-dark-800'
                }`
              }
              style={({ isActive }) => ({ color: isActive ? undefined : 'var(--text-secondary)' })}
            >
              <item.icon className="h-5 w-5" />
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
    </>
  )
}

function SidebarContent({ collapsed, onToggle }: { collapsed: boolean; onToggle: () => void }) {
  return (
    <>
      <div className={`px-4 ${collapsed ? 'py-4' : 'pb-3 pt-5'}`}>
        <div className={`flex items-center gap-2 ${collapsed ? 'justify-center' : ''}`}>
          <img src="/kubeopt_eyecon.png" alt="KubeOpt" className="h-8 w-8 animate-spin-slow" />
          {!collapsed && <span className="text-xl font-bold" style={{ color: 'var(--text-primary)' }}>KubeOpt</span>}
        </div>
        {!collapsed && (
          <p className="mt-1.5 pl-10 text-[11px] leading-tight italic" style={{ color: 'var(--text-muted)' }}>
            Your third eye for kubernetes costs
          </p>
        )}
      </div>
      <nav className="mt-4 flex-1 space-y-1 px-3">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `flex items-center rounded-lg text-sm font-medium transition-colors ${
                collapsed ? 'justify-center px-2 py-2.5' : 'gap-3 px-3 py-2.5'
              } ${
                isActive
                  ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400'
                  : 'hover:bg-primary-50 dark:hover:bg-dark-800'
              }`
            }
            style={({ isActive }) => ({ color: isActive ? undefined : 'var(--text-secondary)' })}
            title={collapsed ? item.label : undefined}
          >
            <item.icon className="h-5 w-5 flex-shrink-0" />
            {!collapsed && item.label}
          </NavLink>
        ))}
      </nav>
      <div className="p-3">
        <button
          onClick={onToggle}
          className="flex w-full items-center justify-center rounded-lg p-2 transition-colors hover:bg-primary-50 dark:hover:bg-dark-800"
          style={{ color: 'var(--text-muted)' }}
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronsRight className="h-4 w-4" /> : <ChevronsLeft className="h-4 w-4" />}
        </button>
      </div>
    </>
  )
}
