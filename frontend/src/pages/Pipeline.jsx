import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, fmtMoney, fmtDate, timeAgo } from '../lib/api.js'
import { ClassificationBadge, RiskBadge, ScoreBadge } from '../components/Badges.jsx'
import { Loading, ErrorState } from '../components/States.jsx'
import { useToast } from '../components/Toast.jsx'

const STAGES = ['NEW', 'QUALIFIED', 'CONTACTED', 'ENGAGED', 'DEMO', 'NEGOTIATION', 'WON', 'LOST']

function NewDealModal({ onClose, onCreated }) {
  const toast = useToast()
  const [leads, setLeads] = useState([])
  const [form, setForm] = useState({ lead_id: '', value: '', expected_close_date: '' })
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    api.get('/leads?page_size=100&sort=score&direction=desc').then((d) => setLeads(d.items))
  }, [])

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    try {
      await api.post('/deals', {
        lead_id: Number(form.lead_id),
        value: Number(form.value),
        expected_close_date: form.expected_close_date || null,
      })
      toast.success('Deal created')
      onCreated()
    } catch (err) { toast.error(err.message) } finally { setBusy(false) }
  }

  return (
    <div className="fixed inset-0 z-40 bg-black/40 flex items-center justify-center p-6" onClick={onClose}>
      <form className="card w-full max-w-md p-6 space-y-4" onClick={(ev) => ev.stopPropagation()} onSubmit={submit}>
        <h2 className="text-lg font-bold">New deal</h2>
        <div>
          <label className="label">Lead *</label>
          <select className="input" required value={form.lead_id} onChange={(e) => setForm({ ...form, lead_id: e.target.value })}>
            <option value="">— select —</option>
            {leads.map((l) => <option key={l.id} value={l.id}>{l.name} · {l.company_name} ({l.score})</option>)}
          </select>
        </div>
        <div>
          <label className="label">Deal value ($) *</label>
          <input type="number" min="1" required className="input" value={form.value}
            onChange={(e) => setForm({ ...form, value: e.target.value })} />
        </div>
        <div>
          <label className="label">Expected close date</label>
          <input type="date" className="input" value={form.expected_close_date}
            onChange={(e) => setForm({ ...form, expected_close_date: e.target.value })} />
        </div>
        <div className="flex justify-end gap-2">
          <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn-primary" disabled={busy}>{busy ? 'Creating…' : 'Create deal'}</button>
        </div>
      </form>
    </div>
  )
}

function DealCard({ deal, onDragStart, onOpen }) {
  return (
    <div draggable onDragStart={(e) => onDragStart(e, deal)}
      onClick={() => onOpen(deal)}
      className="card p-3 cursor-grab active:cursor-grabbing hover:shadow-md transition">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="text-sm font-semibold truncate">{deal.company}</div>
          <div className="text-xs text-slate-500 truncate">{deal.contact}</div>
        </div>
        <ScoreBadge score={deal.lead_score} />
      </div>
      <div className="mt-2 flex items-center justify-between">
        <span className="text-sm font-bold">{fmtMoney(deal.value)}</span>
        <span className="text-xs text-slate-500">{Math.round(deal.win_probability)}% win</span>
      </div>
      <div className="mt-2 flex items-center justify-between text-xs">
        <RiskBadge risk={deal.risk_level} />
        <span className="text-slate-400">{deal.expected_close_date ? fmtDate(deal.expected_close_date) : 'no close date'}</span>
      </div>
      {deal.last_activity && (
        <div className="mt-2 text-[11px] text-slate-400 border-t border-slate-50 pt-1">
          {deal.last_activity.type.replace('_', ' ')} · {timeAgo(deal.last_activity.at)}
        </div>
      )}
    </div>
  )
}

function PredictionModal({ dealId, onClose }) {
  const [pred, setPred] = useState(null)
  const [error, setError] = useState(null)
  useEffect(() => {
    api.get(`/deals/${dealId}/prediction`).then(setPred).catch((e) => setError(e.message))
  }, [dealId])

  return (
    <div className="fixed inset-0 z-40 bg-black/40 flex items-start justify-center overflow-y-auto p-6" onClick={onClose}>
      <div className="card w-full max-w-2xl p-6 space-y-4" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold">Deal prediction</h2>
          <button className="btn-secondary" onClick={onClose}>Close</button>
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        {!pred && !error && <Loading />}
        {pred && (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="card p-4 text-center">
                <div className="text-xs text-slate-500">Win probability</div>
                <div className="text-3xl font-bold text-brand-700">{pred.win_probability}%</div>
              </div>
              <div className="card p-4 text-center">
                <div className="text-xs text-slate-500">Deal value</div>
                <div className="text-2xl font-bold">{fmtMoney(pred.value)}</div>
              </div>
              <div className="card p-4 text-center">
                <div className="text-xs text-slate-500">Expected revenue</div>
                <div className="text-2xl font-bold text-emerald-600">{fmtMoney(pred.expected_revenue)}</div>
                <div className="text-[11px] text-slate-400">value × probability</div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <RiskBadge risk={pred.risk_level} />
              <span className="text-xs text-slate-400">stage {pred.stage}</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h3 className="text-sm font-semibold text-emerald-700 mb-2">▲ Positive factors</h3>
                <div className="space-y-2">
                  {pred.positive_factors.map((f, i) => (
                    <div key={i} className="rounded-lg bg-emerald-50 border border-emerald-100 p-2 text-xs">
                      <div className="font-semibold">{f.factor} <span className="text-emerald-600">+{f.impact}</span></div>
                      <div className="text-slate-500">{f.explanation}</div>
                    </div>
                  ))}
                  {pred.positive_factors.length === 0 && <p className="text-xs text-slate-400">None</p>}
                </div>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-red-700 mb-2">▼ Risk factors</h3>
                <div className="space-y-2">
                  {pred.negative_factors.map((f, i) => (
                    <div key={i} className="rounded-lg bg-red-50 border border-red-100 p-2 text-xs">
                      <div className="font-semibold">{f.factor} <span className="text-red-600">{f.impact}</span></div>
                      <div className="text-slate-500">{f.explanation}</div>
                    </div>
                  ))}
                  {pred.negative_factors.length === 0 && <p className="text-xs text-slate-400">None — healthy deal</p>}
                </div>
              </div>
            </div>
            <div>
              <h3 className="text-sm font-semibold mb-2">Stage history</h3>
              <div className="text-xs text-slate-500 space-y-1">
                {pred.stage_history.map((h, i) => (
                  <div key={i}>{h.from_stage || '•'} → <strong>{h.to_stage}</strong> · {fmtDate(h.changed_at)}</div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default function Pipeline() {
  const toast = useToast()
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [dragging, setDragging] = useState(null)
  const [dragOver, setDragOver] = useState(null)
  const [newOpen, setNewOpen] = useState(false)
  const [predDeal, setPredDeal] = useState(null)

  const load = () => {
    setError(null)
    api.get('/deals').then(setData).catch((e) => setError(e.message))
  }
  useEffect(load, [])

  const drop = async (stage) => {
    setDragOver(null)
    const deal = dragging
    setDragging(null)
    if (!deal || deal.stage === stage) return
    try {
      await api.patch(`/deals/${deal.id}`, { stage })
      toast.success(`Deal moved to ${stage}`)
      load()
    } catch (e) { toast.error(e.message) }
  }

  if (error) return <ErrorState message={error} onRetry={load} />
  if (!data) return <Loading label="Loading pipeline…" />

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div className="min-w-0">
          <h1 className="text-2xl font-bold">Pipeline</h1>
          <p className="text-sm text-slate-500">
            Open: <strong>{fmtMoney(data.summary.open_value)}</strong> · Weighted:{' '}
            <strong>{fmtMoney(data.summary.weighted_value)}</strong> · Won:{' '}
            <strong className="text-emerald-600">{fmtMoney(data.summary.won_value)}</strong>
          </p>
        </div>
        <button className="btn-primary shrink-0" onClick={() => setNewOpen(true)}>+ New deal</button>
      </div>

      {/* Kanban scrolls horizontally within its own container only — page never overflows */}
      <div className="flex gap-3 overflow-x-auto -mx-4 px-4 pb-4" style={{ WebkitOverflowScrolling: 'touch' }}>
        {STAGES.map((stage) => {
          const deals = data.columns[stage] || []
          const stageValue = deals.reduce((s, d) => s + Number(d.value), 0)
          return (
            <div key={stage}
              className={`w-64 max-w-[78vw] shrink-0 rounded-xl p-2 ${dragOver === stage ? 'bg-brand-50 ring-2 ring-brand-300' : 'bg-slate-200/60'}`}
              onDragOver={(e) => { e.preventDefault(); setDragOver(stage) }}
              onDragLeave={() => setDragOver(null)}
              onDrop={() => drop(stage)}>
              <div className="flex items-center justify-between px-2 py-1.5">
                <span className="text-xs font-bold uppercase tracking-wide text-slate-600">{stage}</span>
                <span className="text-xs text-slate-500">{deals.length} · {fmtMoney(stageValue)}</span>
              </div>
              <div className="space-y-2 min-h-[80px]">
                {deals.map((d) => (
                  <DealCard key={d.id} deal={d} onDragStart={(e, deal) => setDragging(deal)} onOpen={setPredDeal} />
                ))}
                {deals.length === 0 && (
                  <div className="text-center text-xs text-slate-400 py-6 border-2 border-dashed border-slate-300/70 rounded-lg">
                    drop here
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {newOpen && <NewDealModal onClose={() => setNewOpen(false)} onCreated={() => { setNewOpen(false); load() }} />}
      {predDeal && <PredictionModal dealId={predDeal.id} onClose={() => setPredDeal(null)} />}
    </div>
  )
}
