import { NavLink, useLocation } from 'react-router-dom'
import { useEffect } from 'react'

const NAV = [
  { to: '/', label: 'Dashboard', icon: '📊' },
  { to: '/leads', label: 'Leads', icon: '👥' },
  { to: '/outreach', label: 'Outreach', icon: '✉️' },
  { to: '/pipeline', label: 'Pipeline', icon: '🎯' },
  { to: '/analytics', label: 'Analytics', icon: '📈' },
  { to: '/automations', label: 'Automations', icon: '⚡' },
  { to: '/settings', label: 'Settings', icon: '⚙️' },
]

// Shared nav list used by both the desktop sidebar and the mobile drawer.
export function SidebarNav({ onNavigate }) {
  const { pathname } = useLocation()
  return (
    <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
      {NAV.map((n) => {
        const active = n.to === '/' ? pathname === '/' : pathname.startsWith(n.to)
        return (
          <NavLink
            key={n.to}
            to={n.to}
            onClick={onNavigate}
            className={`flex items-center gap-3 rounded-lg px-3 py-3 text-sm font-medium transition md:py-2 ${
              active ? 'bg-brand-600 text-white' : 'hover:bg-slate-800 hover:text-white'
            }`}
          >
            <span>{n.icon}</span>
            {n.label}
          </NavLink>
        )
      })}
    </nav>
  )
}

function Brand({ compact }) {
  return (
    <div className="px-5 py-5 flex items-center gap-2 border-b border-slate-800">
      <div className="h-8 w-8 rounded-lg bg-brand-600 flex items-center justify-center text-white font-bold">S</div>
      <div>
        <div className="font-bold text-white leading-tight">SalesPilot AI</div>
        {!compact && <div className="text-[10px] text-slate-500 uppercase tracking-wider">Sales Automation</div>}
      </div>
    </div>
  )
}

export default function Sidebar({ mobileOpen, onCloseMobile }) {
  return (
    <>
      {/* Desktop sidebar — unchanged behavior, hidden below md */}
      <aside className="hidden md:flex w-60 shrink-0 bg-slate-900 text-slate-300 flex-col min-h-screen">
        <Brand />
        <SidebarNav />
        <div className="px-5 py-4 border-t border-slate-800 text-xs text-slate-500">
          Demo workspace · seeded data
        </div>
      </aside>

      {/* Mobile drawer — overlay below md, rendered only when open */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden" role="dialog" aria-modal="true" aria-label="Navigation menu">
          {/* backdrop */}
          <div className="absolute inset-0 bg-black/50" onClick={onCloseMobile} />
          <aside className="absolute left-0 top-0 bottom-0 w-72 max-w-[85vw] bg-slate-900 text-slate-300 flex flex-col shadow-xl">
            <div className="flex items-center justify-between pr-3">
              <Brand />
              <button
                className="btn-secondary h-10 w-10 !p-0 shrink-0"
                aria-label="Close menu"
                onClick={onCloseMobile}
              >
                ✕
              </button>
            </div>
            <SidebarNav onNavigate={onCloseMobile} />
            <div className="px-5 py-4 border-t border-slate-800 text-xs text-slate-500">
              Demo workspace · seeded data
            </div>
          </aside>
        </div>
      )}
    </>
  )
}

export { NAV }
