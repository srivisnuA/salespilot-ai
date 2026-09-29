import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, fmtDate, CLASS_STYLES } from '../lib/api.js'
import { ClassificationBadge, ScoreBadge } from '../components/Badges.jsx'
import { Loading, ErrorState, EmptyState, Skeleton } from '../components/States.jsx'
import LeadForm from '../components/LeadForm.jsx'

const INDUSTRIES = ['', 'SaaS', 'FinTech', 'Healthcare', 'E-commerce', 'Manufacturing', 'Technology']

export default function Leads() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({ q: '', classification: '', industry: '', source: '', sort: 'score', direction: 'desc' })
  const [page, setPage] = useState(1)
  const [showForm, setShowForm] = useState(false)

  const load = (f = filters, p = page) => {
    setLoading(true)
    setError(null)
    const params = new URLSearchParams()
    Object.entries(f).forEach(([k, v]) => v && params.set(k, v))
    params.set('page', p)
    params.set('page_size', 20)
    api.get(`/leads?${params}`)
      .then((d) => { setData(d); setLoading(false) })
      .catch((e) => { setError(e.message); setLoading(false) })
  }

  useEffect(() => { load() }, []) // eslint-disable-line

  const setF = (k, v) => {
    const next = { ...filters, [k]: v }
    setFilters(next)
    setPage(1)
    load(next, 1)
  }

  const sortBy = (col) => {
    const dir = filters.sort === col && filters.direction === 'desc' ? 'asc' : 'desc'
    const next = { ...filters, sort: col, direction: dir }
    setFilters(next)
    load(next, page)
  }

  const arrow = (col) => (filters.sort === col ? (filters.direction === 'desc' ? ' ↓' : ' ↑') : '')

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">Leads</h1>
          <p className="text-sm text-slate-500">{data ? `${data.total} leads` : ' '}</p>
        </div>
        <button className="btn-primary shrink-0" onClick={() => setShowForm(true)}>+ New Lead</button>
      </div>

      <div className="card p-3 grid grid-cols-1 sm:flex sm:flex-wrap gap-2">
        <input className="input w-full sm:max-w-xs" placeholder="Search name, company, email…" value={filters.q}
          onChange={(e) => setF('q', e.target.value)} />
        <select className="input w-full sm:max-w-[140px]" value={filters.classification} onChange={(e) => setF('classification', e.target.value)}>
          <option value="">All temperatures</option><option value="hot">Hot</option><option value="warm">Warm</option><option value="cold">Cold</option>
        </select>
        <select className="input w-full sm:max-w-[160px]" value={filters.industry} onChange={(e) => setF('industry', e.target.value)}>
          {INDUSTRIES.map((i) => <option key={i} value={i}>{i || 'All industries'}</option>)}
        </select>
        <select className="input w-full sm:max-w-[150px]" value={filters.source} onChange={(e) => setF('source', e.target.value)}>
          <option value="">All sources</option>
          {['website', 'referral', 'linkedin', 'webinar', 'cold_outreach', 'inbound', 'event', 'partner'].map((s) => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
        </select>
      </div>

      {error && <ErrorState message={error} onRetry={() => load()} />}
      {loading && <div className="card"><Skeleton rows={8} /></div>}

      {!loading && !error && data && data.items.length === 0 && (
        <EmptyState title="No leads match" hint="Try clearing filters or create a new lead."
          action={<button className="btn-primary" onClick={() => setShowForm(true)}>+ New Lead</button>} />
      )}

      {!loading && !error && data && data.items.length > 0 && (
        <div className="card overflow-x-auto">
          <table className="w-full sm:min-w-[760px]">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="th cursor-pointer" onClick={() => sortBy('name')}>Name{arrow('name')}</th>
                <th className="th cursor-pointer" onClick={() => sortBy('company')}>Company{arrow('company')}</th>
                <th className="th hidden sm:table-cell">Industry</th>
                <th className="th hidden md:table-cell">Source</th>
                <th className="th hidden md:table-cell">Budget</th>
                <th className="th hidden lg:table-cell cursor-pointer" onClick={() => sortBy('created')}>Created{arrow('created')}</th>
                <th className="th cursor-pointer" onClick={() => sortBy('score')}>Score{arrow('score')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.items.map((l) => (
                <tr key={l.id} className="hover:bg-slate-50">
                  <td className="td">
                    <Link to={`/leads/${l.id}`} className="font-medium text-brand-700 hover:underline">{l.name}</Link>
                    <div className="text-xs text-slate-400">{l.email}</div>
                  </td>
                  <td className="td">
                    <div>{l.company_name}</div>
                    <div className="text-xs text-slate-400">{l.job_title}</div>
                  </td>
                  <td className="td hidden sm:table-cell">{l.industry}</td>
                  <td className="td hidden md:table-cell">{l.source.replace('_', ' ')}</td>
                  <td className="td hidden md:table-cell">{l.budget ? `$${Number(l.budget).toLocaleString()}` : '—'}</td>
                  <td className="td hidden lg:table-cell">{fmtDate(l.created_at)}</td>
                  <td className="td">
                    <div className="flex items-center gap-2">
                      <ScoreBadge score={l.score} />
                      <ClassificationBadge classification={l.classification} />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="flex items-center justify-between px-4 py-3 border-t border-slate-100 text-sm">
            <span className="text-slate-500">Page {data.page} of {Math.max(1, Math.ceil(data.total / data.page_size))}</span>
            <div className="flex gap-2">
              <button className="btn-secondary" disabled={page <= 1} onClick={() => { const p = page - 1; setPage(p); load(filters, p) }}>Previous</button>
              <button className="btn-secondary" disabled={page >= Math.ceil(data.total / data.page_size)} onClick={() => { const p = page + 1; setPage(p); load(filters, p) }}>Next</button>
            </div>
          </div>
        </div>
      )}

      {showForm && <LeadForm onClose={() => setShowForm(false)} onSaved={() => { setShowForm(false); load() }} />}
    </div>
  )
}
