import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, fmtDateTime, CLASS_STYLES } from '../lib/api.js'
import { StatusBadge, ClassificationBadge } from '../components/Badges.jsx'
import { Loading, ErrorState, EmptyState } from '../components/States.jsx'
import { useToast } from '../components/Toast.jsx'

const TONES = ['professional', 'friendly', 'concise', 'consultative']
const LENGTHS = ['short', 'medium', 'detailed']

function ComposeModal({ onClose, onSent }) {
  const toast = useToast()
  const [leads, setLeads] = useState([])
  const [leadId, setLeadId] = useState('')
  const [tone, setTone] = useState('professional')
  const [length, setLength] = useState('medium')
  const [email, setEmail] = useState(null)
  const [busy, setBusy] = useState(false)
  const [q, setQ] = useState('')
  const [filtered, setFiltered] = useState([])
  const [leadMap, setLeadMap] = useState({})

  useEffect(() => {
    api.get('/leads?page_size=100&sort=score&direction=desc').then((d) => {
      setLeads(d.items)
      setFiltered(d.items.slice(0, 12))
      const m = {}
      d.items.forEach((l) => (m[l.id] = l))
      setLeadMap(m)
    })
  }, [])

  useEffect(() => {
    const f = leads.filter((l) =>
      !q || l.name.toLowerCase().includes(q.toLowerCase()) || l.company_name.toLowerCase().includes(q.toLowerCase()))
    setFiltered(f.slice(0, 12))
  }, [q, leads])

  const generate = async (regen = false) => {
    if (!leadId) return toast.error('Pick a lead first')
    setBusy(true)
    try {
      const res = await api.post('/emails/generate', { lead_id: Number(leadId), tone, length })
      setEmail(res)
      toast.success(regen ? 'New variant generated' : 'Email generated')
    } catch (e) { toast.error(e.message) } finally { setBusy(false) }
  }

  const save = async (status) => {
    setBusy(true)
    try {
      await api.patch(`/emails/${email.id}`, { subject: email.subject, body: email.body, status })
      if (status === 'sent') {
        await api.post(`/emails/${email.id}/send`)
        toast.success('Email sent (simulated) — engagement recorded')
      } else {
        toast.success(status === 'approved' ? 'Email approved' : 'Draft saved')
      }
      onSent()
    } catch (e) { toast.error(e.message) } finally { setBusy(false) }
  }

  const lead = leadMap[leadId]

  return (
    <div className="fixed inset-0 z-40 bg-black/40 flex items-start justify-center overflow-y-auto p-6" onClick={onClose}>
      <div className="card w-full max-w-3xl p-6 space-y-4" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold">Compose with AI</h2>
          <button className="btn-secondary" onClick={onClose}>Close</button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <div className="md:col-span-2">
            <label className="label">Lead</label>
            <input className="input" placeholder="Search leads…" value={q} onChange={(e) => setQ(e.target.value)} />
            <select className="input mt-2" value={leadId} onChange={(e) => { setLeadId(e.target.value); setEmail(null) }}>
              <option value="">— select a lead —</option>
              {filtered.map((l) => (
                <option key={l.id} value={l.id}>{l.name} · {l.company_name} ({l.score})</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Tone</label>
            <select className="input" value={tone} onChange={(e) => setTone(e.target.value)}>
              {TONES.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Length</label>
            <select className="input" value={length} onChange={(e) => setLength(e.target.value)}>
              {LENGTHS.map((l) => <option key={l} value={l}>{l}</option>)}
            </select>
          </div>
        </div>

        {lead && (
          <div className="rounded-lg bg-slate-50 border border-slate-100 p-3 text-xs text-slate-600">
            <strong>{lead.name}</strong> · {lead.job_title || 'unknown role'} at {lead.company_name} · {lead.industry}
            {lead.pain_point && <> · pain: “{lead.pain_point}”</>}
            {lead.buying_timeline !== 'unknown' && <> · timeline: {lead.buying_timeline}</>}
          </div>
        )}

        <div className="flex gap-2">
          <button className="btn-primary" onClick={() => generate(false)} disabled={busy || !leadId}>
            {busy ? 'Working…' : email ? 'Generate' : '✨ Generate'}
          </button>
          {email && <button className="btn-secondary" onClick={() => generate(true)} disabled={busy}>🔄 Regenerate</button>}
        </div>

        {email && (
          <div className="space-y-3">
            <div>
              <label className="label">Subject (editable)</label>
              <input className="input" value={email.subject} onChange={(e) => setEmail({ ...email, subject: e.target.value })} />
            </div>
            <div>
              <label className="label">Body (editable)</label>
              <textarea className="input font-mono text-xs" rows={10} value={email.body}
                onChange={(e) => setEmail({ ...email, body: e.target.value })} />
            </div>
            <div className="flex flex-wrap gap-2 justify-end">
              <button className="btn-secondary" onClick={() => save('draft')} disabled={busy}>Save draft</button>
              <button className="btn-secondary" onClick={() => save('approved')} disabled={busy}>Approve</button>
              <button className="btn-primary" onClick={() => save('sent')} disabled={busy}>🚀 Send (simulate)</button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default function Outreach() {
  const toast = useToast()
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [statusFilter, setStatusFilter] = useState('')
  const [composeOpen, setComposeOpen] = useState(false)
  const [expanded, setExpanded] = useState(null)

  const load = (s = statusFilter) => {
    setError(null)
    api.get(`/emails${s ? `?status=${s}` : ''}`).then(setData).catch((e) => setError(e.message))
  }
  useEffect(() => { load() }, []) // eslint-disable-line

  const act = async (email, action) => {
    try {
      if (action === 'approve') {
        await api.patch(`/emails/${email.id}`, { status: 'approved' })
        toast.success('Email approved')
      } else if (action === 'send') {
        await api.post(`/emails/${email.id}/send`)
        toast.success('Email sent (simulated) — engagement recorded')
      }
      load()
    } catch (e) { toast.error(e.message) }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div className="min-w-0">
          <h1 className="text-2xl font-bold">Outreach</h1>
          <p className="text-sm text-slate-500">AI-personalized email campaigns</p>
        </div>
        <button className="btn-primary shrink-0" onClick={() => setComposeOpen(true)}>✨ Compose with AI</button>
      </div>

      <div className="flex flex-wrap gap-2">
        {['', 'draft', 'approved', 'sent'].map((s) => (
          <button key={s} className={s === statusFilter ? 'btn-primary' : 'btn-secondary'}
            onClick={() => { setStatusFilter(s); load(s) }}>
            {s || 'all'}
          </button>
        ))}
      </div>

      {error && <ErrorState message={error} onRetry={() => load()} />}
      {!data && !error && <Loading label="Loading outreach…" />}
      {data && data.items.length === 0 && (
        <EmptyState title="No emails yet" hint="Compose your first AI-personalized email."
          action={<button className="btn-primary" onClick={() => setComposeOpen(true)}>✨ Compose with AI</button>} />
      )}

      {data && data.items.length > 0 && (
        <div className="space-y-2">
          {data.items.map((em) => (
            <div key={em.id} className="card p-4">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <StatusBadge status={em.status} />
                    <Link to={`/leads/${em.lead_id}`} className="text-sm font-semibold text-brand-700 hover:underline">
                      {em.lead_name} · {em.lead_company}
                    </Link>
                    {em.status === 'sent' && (
                      <span className="text-xs text-slate-400">
                        {em.opens} opens · {em.clicks} clicks {em.replied ? '· 💬 replied' : ''}
                      </span>
                    )}
                  </div>
                  <div className="text-sm font-medium mt-1 truncate">{em.subject}</div>
                  <div className="text-[11px] text-slate-400 mt-0.5">
                    {em.tone} · {em.length} · by {em.generated_by} · {fmtDateTime(em.created_at)}
                  </div>
                </div>
                <div className="flex flex-wrap gap-2 sm:shrink-0">
                  {em.status !== 'sent' && (
                    <>
                      <button className="btn-secondary text-xs" onClick={() => act(em, 'approve')}>Approve</button>
                      {em.status === 'approved' && <button className="btn-primary text-xs" onClick={() => act(em, 'send')}>Send</button>}
                    </>
                  )}
                  <button className="btn-secondary text-xs" onClick={() => setExpanded(expanded === em.id ? null : em.id)}>
                    {expanded === em.id ? 'Hide' : 'View'}
                  </button>
                </div>
              </div>
              {expanded === em.id && (
                <div className="mt-3 border-t border-slate-100 pt-3">
                  <div className="text-sm font-medium">{em.subject}</div>
                  <pre className="text-xs text-slate-600 whitespace-pre-wrap font-sans mt-2">{em.body}</pre>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {composeOpen && <ComposeModal onClose={() => setComposeOpen(false)} onSent={() => { setComposeOpen(false); load() }} />}
    </div>
  )
}
