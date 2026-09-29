import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api, fmtPct, fmtDate, fmtDateTime, timeAgo, CLASS_STYLES } from '../lib/api.js'
import { ClassificationBadge, ScoreBadge, StatusBadge, StageBadge } from '../components/Badges.jsx'
import { Loading, ErrorState } from '../components/States.jsx'
import { useToast } from '../components/Toast.jsx'
import LeadForm from '../components/LeadForm.jsx'

const EVENT_TYPES = ['opened', 'link_clicked', 'reply', 'demo_requested', 'meeting_booked', 'follow_up_completed', 'website_visit']

export default function LeadDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const [lead, setLead] = useState(null)
  const [error, setError] = useState(null)
  const [editOpen, setEditOpen] = useState(false)
  const [generating, setGenerating] = useState(false)

  const load = () => {
    setError(null)
    api.get(`/leads/${id}`).then(setLead).catch((e) => setError(e.message))
  }
  useEffect(load, [id])

  if (error) return <ErrorState message={error} onRetry={load} />
  if (!lead) return <Loading label="Loading lead…" />

  const maxPoints = Math.max(...lead.score_factors.map((f) => f.max_points), 1)
  const deal = lead.deals[0]

  const recordEvent = async (eventType) => {
    try {
      const res = await api.post(`/emails/leads/${lead.id}/engagement`, { event_type: eventType })
      toast.success(`${eventType.replace('_', ' ')} recorded — score ${res.old_score} → ${res.new_score}`)
      load()
    } catch (e) { toast.error(e.message) }
  }

  const generateEmail = async () => {
    setGenerating(true)
    try {
      await api.post('/emails/generate', { lead_id: lead.id, tone: 'professional', length: 'medium' })
      toast.success('Outreach email draft generated')
      load()
    } catch (e) { toast.error(e.message) } finally { setGenerating(false) }
  }

  const deleteLead = async () => {
    if (!confirm(`Delete ${lead.name}? This also removes their emails, engagements and deals.`)) return
    try {
      await api.del(`/leads/${lead.id}`)
      toast.success('Lead deleted')
      navigate('/leads')
    } catch (e) { toast.error(e.message) }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between">
        <div>
          <Link to="/leads" className="text-sm text-brand-600 hover:underline">← Back to leads</Link>
          <h1 className="text-2xl font-bold mt-1">{lead.name}</h1>
          <p className="text-sm text-slate-500">{lead.job_title}{lead.job_title && ' · '}{lead.company_name} · {lead.industry}</p>
        </div>
        <div className="flex gap-2 shrink-0">
          <button className="btn-secondary" onClick={() => setEditOpen(true)}>Edit</button>
          <button className="btn-danger" onClick={deleteLead}>Delete</button>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        {/* Score card */}
        <div className="card p-5">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">AI Lead Score</h2>
            <ClassificationBadge classification={lead.classification} />
          </div>
          <div className="flex items-end gap-3 mt-3">
            <div className="text-5xl font-bold text-brand-700">{lead.score}</div>
            <div className="text-sm text-slate-500 pb-1">/ 100</div>
          </div>
          <div className="mt-2 text-sm text-slate-600">
            Conversion probability: <strong>{fmtPct(lead.conversion_probability * 100)}</strong>
          </div>
          <div className="h-2 bg-slate-100 rounded-full mt-3 overflow-hidden">
            <div className={`h-full ${lead.score >= 75 ? 'bg-red-500' : lead.score >= 50 ? 'bg-amber-500' : 'bg-sky-500'}`} style={{ width: `${lead.score}%` }} />
          </div>
          <h3 className="text-xs font-semibold text-slate-500 uppercase mt-5 mb-2">Score factors</h3>
          <div className="space-y-2">
            {lead.score_factors.map((f, i) => (
              <div key={i}>
                <div className="flex justify-between text-xs">
                  <span className="font-medium text-slate-700">{f.factor}</span>
                  <span className={f.points >= 0 ? 'text-emerald-600 font-semibold' : 'text-red-600 font-semibold'}>
                    {f.points >= 0 ? '+' : ''}{f.points}
                  </span>
                </div>
                <div className="h-1.5 bg-slate-100 rounded-full mt-1">
                  <div className={`h-full rounded-full ${f.points >= 0 ? 'bg-emerald-500' : 'bg-red-400'}`}
                    style={{ width: `${Math.min(100, Math.abs(f.points) / maxPoints * 100)}%` }} />
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5">{f.explanation}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Middle column: details + quick actions */}
        <div className="space-y-4">
          <div className="card p-5">
            <h2 className="font-semibold mb-3">Details</h2>
            <dl className="grid grid-cols-2 gap-y-2 text-sm">
              <dt className="text-slate-500">Email</dt><dd className="truncate">{lead.email}</dd>
              <dt className="text-slate-500">Company size</dt><dd>{lead.company_size || '—'}</dd>
              <dt className="text-slate-500">Revenue</dt><dd>{lead.annual_revenue ? `$${Number(lead.annual_revenue).toLocaleString()}` : '—'}</dd>
              <dt className="text-slate-500">Budget</dt><dd>{lead.budget ? `$${Number(lead.budget).toLocaleString()}` : '—'}</dd>
              <dt className="text-slate-500">Source</dt><dd>{lead.source.replace('_', ' ')}</dd>
              <dt className="text-slate-500">Timeline</dt><dd>{lead.buying_timeline}</dd>
              <dt className="text-slate-500">Intent score</dt><dd>{lead.intent_score}</dd>
              <dt className="text-slate-500">Created</dt><dd>{fmtDate(lead.created_at)}</dd>
            </dl>
            {lead.pain_point && (
              <>
                <h3 className="label mt-4">Pain point</h3>
                <p className="text-sm">{lead.pain_point}</p>
              </>
            )}
            {lead.notes && (
              <>
                <h3 className="label mt-3">Notes</h3>
                <p className="text-sm">{lead.notes}</p>
              </>
            )}
          </div>

          <div className="card p-5">
            <h2 className="font-semibold mb-3">Quick actions</h2>
            <button className="btn-primary w-full" onClick={generateEmail} disabled={generating}>
              {generating ? 'Generating…' : '✨ Generate outreach email'}
            </button>
            <div className="mt-3">
              <div className="label">Record engagement</div>
              <div className="flex flex-wrap gap-2">
                {EVENT_TYPES.map((t) => (
                  <button key={t} className="btn-secondary text-xs min-h-[40px]" onClick={() => recordEvent(t)}>
                    {t.replace('_', ' ')}
                  </button>
                ))}
              </div>
            </div>
            {deal && (
              <div className="mt-4 pt-4 border-t border-slate-100">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="label">Deal</div>
                    <div className="text-sm font-medium">{deal.name}</div>
                    <div className="text-xs text-slate-500">${Number(deal.value).toLocaleString()} · {deal.win_probability}% win · {deal.risk_level} risk</div>
                  </div>
                  <div className="text-right">
                    <StageBadge stage={deal.stage} />
                    <div><Link to="/pipeline" className="text-xs text-brand-600 hover:underline">open pipeline</Link></div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {lead.tasks.length > 0 && (
            <div className="card p-5">
              <h2 className="font-semibold mb-3">Tasks</h2>
              {lead.tasks.map((t) => (
                <div key={t.id} className="flex items-center justify-between py-1 text-sm">
                  <span>{t.status === 'done' ? '✅' : '⬜'} {t.title}</span>
                  <span className="text-xs text-slate-400">{t.due_date || ''}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right column: emails + timeline */}
        <div className="space-y-4">
          <div className="card p-5">
            <div className="flex items-center justify-between mb-3">
              <h2 className="font-semibold">Emails</h2>
              <Link to="/outreach" className="text-xs text-brand-600 hover:underline">outreach →</Link>
            </div>
            {lead.emails.length === 0 && <p className="text-sm text-slate-400">No emails yet — generate one above.</p>}
            <div className="space-y-3">
              {lead.emails.map((em) => (
                <div key={em.id} className="border border-slate-100 rounded-lg p-3">
                  <div className="flex items-center justify-between">
                    <StatusBadge status={em.status} />
                    <span className="text-xs text-slate-400">{timeAgo(em.created_at)}</span>
                  </div>
                  <div className="text-sm font-medium mt-1">{em.subject}</div>
                  <p className="text-xs text-slate-500 mt-1 line-clamp-3 whitespace-pre-line">{em.body}</p>
                  <div className="text-[11px] text-slate-400 mt-1">{em.tone} · {em.length} · generated by {em.generated_by}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="card p-5">
            <h2 className="font-semibold mb-3">Activity timeline</h2>
            <div className="space-y-0 max-h-96 overflow-y-auto">
              {[...lead.activities].sort((a, b) => new Date(b.created_at) - new Date(a.created_at)).map((a) => (
                <div key={a.id} className="flex gap-3 pb-3 last:pb-0">
                  <div className="flex flex-col items-center">
                    <span className="h-2 w-2 rounded-full bg-brand-500 mt-1.5" />
                    <span className="flex-1 w-px bg-slate-100" />
                  </div>
                  <div className="flex-1">
                    <div className="text-sm">{a.message}</div>
                    <div className="text-[11px] text-slate-400">{fmtDateTime(a.created_at)}</div>
                  </div>
                </div>
              ))}
              {lead.activities.length === 0 && <p className="text-sm text-slate-400">No activity yet.</p>}
            </div>
            {lead.engagement_events.length > 0 && (
              <div className="mt-3 pt-3 border-t border-slate-100 text-xs text-slate-500">
                Engagement: {lead.engagement_events.map((e) => e.event_type.replace('_', ' ')).join(', ')}
              </div>
            )}
          </div>
        </div>
      </div>

      {editOpen && <LeadForm lead={lead} onClose={() => setEditOpen(false)} onSaved={() => { setEditOpen(false); load() }} />}
    </div>
  )
}
