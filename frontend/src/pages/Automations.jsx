import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, fmtDateTime } from '../lib/api.js'
import { Loading, ErrorState, EmptyState } from '../components/States.jsx'
import { useToast } from '../components/Toast.jsx'

const TRIGGER_LABELS = {
  score_above_threshold: 'Lead score above threshold',
  email_opened_multiple: 'Email opened multiple times',
  no_response_days: 'No response for N days',
  demo_requested: 'Demo requested',
  lead_created: 'Lead created',
}

function ActionChips({ actions }) {
  return (
    <div className="flex flex-wrap gap-1">
      {(actions || []).map((a, i) => (
        <span key={i} className="badge bg-slate-100 text-slate-600">{a.type.replace(/_/g, ' ')}</span>
      ))}
    </div>
  )
}

export default function Automations() {
  const toast = useToast()
  const [items, setItems] = useState(null)
  const [runs, setRuns] = useState(null)
  const [error, setError] = useState(null)
  const [selected, setSelected] = useState(null)

  const load = () => {
    setError(null)
    Promise.all([api.get('/automations'), api.get('/automations/runs/recent')])
      .then(([a, r]) => { setItems(a.items); setRuns(r.items) })
      .catch((e) => setError(e.message))
  }
  useEffect(load, [])

  const toggle = async (a) => {
    try {
      await api.patch(`/automations/${a.id}`, { enabled: !a.enabled })
      toast.success(`${a.name} ${a.enabled ? 'disabled' : 'enabled'}`)
      load()
    } catch (e) { toast.error(e.message) }
  }

  const runNow = async (a) => {
    try {
      const res = await api.post(`/automations/${a.id}/run`, {})
      toast.success(res.executed != null ? `Sweep complete — ${res.executed} execution(s)` : 'Automation executed')
      load()
    } catch (e) { toast.error(e.message) }
  }

  const viewRuns = async (a) => {
    setSelected(a)
    try {
      const r = await api.get(`/automations/${a.id}/runs`)
      setRuns(r.items)
    } catch (e) { toast.error(e.message) }
  }

  if (error) return <ErrorState message={error} onRetry={load} />
  if (!items) return <Loading label="Loading automations…" />

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold">Automations</h1>
        <p className="text-sm text-slate-500">Trigger → action rules that run on their own</p>
      </div>

      <div className="space-y-3">
        {items.map((a) => (
          <div key={a.id} className={`card p-4 ${!a.enabled ? 'opacity-60' : ''}`}>
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <h2 className="font-semibold">{a.name}</h2>
                  <span className={`badge ${a.enabled ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-200 text-slate-500'}`}>
                    {a.enabled ? 'active' : 'paused'}
                  </span>
                </div>
                <p className="text-sm text-slate-500 mt-1">{a.description}</p>
                <div className="flex flex-wrap items-center gap-2 mt-2 text-xs">
                  <span className="badge bg-brand-50 text-brand-700">IF {TRIGGER_LABELS[a.trigger_type] || a.trigger_type}
                    {a.conditions?.threshold != null && ` (${a.conditions.threshold}+)`}
                    {a.conditions?.opens != null && ` (${a.conditions.opens}+)`}
                    {a.conditions?.days != null && ` (${a.conditions.days} days)`}
                  </span>
                  <span className="text-slate-400">THEN</span>
                  <ActionChips actions={a.actions} />
                </div>
                <div className="text-[11px] text-slate-400 mt-2">
                  {a.run_count} execution(s){a.last_run_at ? ` · last run ${fmtDateTime(a.last_run_at)}` : ''}
                </div>
              </div>
              <div className="flex flex-row flex-wrap sm:flex-col gap-2 sm:shrink-0">
                <button className="btn-secondary text-xs" onClick={() => toggle(a)}>{a.enabled ? 'Disable' : 'Enable'}</button>
                <button className="btn-secondary text-xs" onClick={() => runNow(a)}>Run now</button>
                <button className="btn-secondary text-xs" onClick={() => viewRuns(a)}>History</button>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="card p-4">
        <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
          <h2 className="font-semibold">Execution history{selected ? ` — ${selected.name}` : ' (all rules)'}</h2>
          {selected && <button className="btn-secondary text-xs" onClick={() => { setSelected(null); api.get('/automations/runs/recent').then((r) => setRuns(r.items)) }}>Show all</button>}
        </div>
        {!runs || runs.length === 0 ? (
          <EmptyState title="No executions yet" hint="Automations fire automatically as leads engage — or use Run now." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[680px]">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr><th className="th">When</th><th className="th">Rule</th><th className="th">Lead</th><th className="th">Trigger</th><th className="th">Result</th></tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {runs.map((r) => (
                  <tr key={r.id}>
                    <td className="td whitespace-nowrap">{fmtDateTime(r.ran_at)}</td>
                    <td className="td font-medium">{r.automation}</td>
                    <td className="td">{r.lead ? <Link className="text-brand-600 hover:underline" to={`/leads/${r.lead_id}`}>{r.lead}</Link> : '—'}</td>
                    <td className="td text-xs">{r.trigger_summary}</td>
                    <td className="td text-xs">{r.result}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
