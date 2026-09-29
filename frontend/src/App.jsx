import { Routes, Route, useLocation } from 'react-router-dom'
import { useEffect, useState } from 'react'
import Sidebar, { NAV } from './components/Sidebar.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Leads from './pages/Leads.jsx'
import LeadDetail from './pages/LeadDetail.jsx'
import Outreach from './pages/Outreach.jsx'
import Pipeline from './pages/Pipeline.jsx'
import Analytics from './pages/Analytics.jsx'
import Automations from './pages/Automations.jsx'
import Settings from './pages/Settings.jsx'

function pageTitle(pathname) {
  if (pathname.startsWith('/leads/')) return 'Lead Detail'
  const match = NAV.find((n) => n.to !== '/' && pathname.startsWith(n.to))
  return match ? match.label : 'Dashboard'
}

export default function App() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const { pathname } = useLocation()

  // Close drawer on navigation (safety net if a link is followed without onClick)
  useEffect(() => { setMobileOpen(false) }, [pathname])

  // Escape closes the drawer
  useEffect(() => {
    if (!mobileOpen) return
    const onKey = (e) => { if (e.key === 'Escape') setMobileOpen(false) }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [mobileOpen])

  // Prevent background scroll while drawer is open
  useEffect(() => {
    document.body.style.overflow = mobileOpen ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [mobileOpen])

  return (
    <div className="flex min-h-screen max-w-full overflow-x-hidden">
      <Sidebar mobileOpen={mobileOpen} onCloseMobile={() => setMobileOpen(false)} />

      {/* Mobile top bar */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-40 bg-slate-900 text-white flex items-center gap-3 px-3 h-12 shadow">
        <button
          className="h-10 w-10 -ml-1 flex items-center justify-center rounded-lg hover:bg-slate-800 text-xl leading-none"
          aria-label="Open menu"
          onClick={() => setMobileOpen(true)}
        >
          ☰
        </button>
        <div className="h-7 w-7 rounded-lg bg-brand-600 flex items-center justify-center text-white font-bold text-sm shrink-0">S</div>
        <span className="font-semibold truncate">SalesPilot AI</span>
        <span className="ml-auto text-sm text-slate-300 truncate max-w-[40vw] text-right">{pageTitle(pathname)}</span>
      </div>

      <main className="flex-1 min-w-0 p-4 md:p-6 overflow-x-hidden pt-16 md:pt-6">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/leads" element={<Leads />} />
          <Route path="/leads/:id" element={<LeadDetail />} />
          <Route path="/outreach" element={<Outreach />} />
          <Route path="/pipeline" element={<Pipeline />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/automations" element={<Automations />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  )
}
