import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, fmtMoney, fmtPct, timeAgo, fmtDateTime } from '../lib/api.js'
import { StatCard, ClassificationBadge, ScoreBadge } from '../components/Badges.jsx'
import { Loading, ErrorState } from '../components/States.jsx'
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, AreaChart, Area,
  CartesianGrid, PieChart, Pie, Cell, Legend,
} from 'recharts'

const FUNNEL_COLORS = ['#3b6ef6', '#4f80f7', '#6392f8', '#77a4f9', '#8bb6fa', '#9fc8fb', '#10b981']

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  const load = () => {
    setError(null)
    api.get('/analytics/dashboard').then(setData).catch((e) => setError(e.message))
  }
  useEffect(load, [])

  if (error) return <ErrorState message={error} onRetry={load} />
  if (!data) return <Loading label="Loading dashboard…" />

  const funnelData = data.funnel.map((f) => ({ name: f.stage, value: f.count }))
  const split = [
    { name: 'Hot', value: data.hot, color: '#ef4444' },
    { name: 'Warm', value: data.warm, color: '#f59e0b' },
    { name: 'Cold', value: data.cold, color: '#0ea5e9' },
  ].filter((s) => s.value > 0)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-sm text-slate-500">Live overview of your sales operation</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-5 gap-4">
        <StatCard label="Total Leads" value={data.total_leads} icon="👥" />
        <StatCard label="Hot Leads" value={data.hot} tone="red" sub={`${data.warm} warm · ${data.cold} cold`} icon="🔥" />
        <StatCard label="Avg Lead Score" value={data.avg_score} tone="brand" icon="⭐" />
        <StatCard label="Emails Sent" value={data.emails_sent} icon="✉️" />
        <StatCard label="Open Rate" value={fmtPct(Math.min(data.open_rate, 100))} sub={`${fmtPct(data.click_rate)} clicks`} icon="📬" />
        <StatCard label="Reply Rate" value={fmtPct(data.reply_rate)} tone="green" icon="💬" />
        <StatCard label="Conversion Rate" value={fmtPct(data.conversion_rate)} tone="green" icon="✅" />
        <StatCard label="Pipeline Value" value={fmtMoney(data.pipeline_value)} sub={`${data.open_deals} open deals`} icon="🎯" />
        <StatCard label="Predicted Revenue" value={fmtMoney(data.predicted_revenue)} tone="brand" sub="weighted by win probability" icon="🔮" />
        <StatCard label="Won Revenue" value={fmtMoney(data.won_revenue)} tone="green" icon="🏆" />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="card p-4 xl:col-span-2">
          <h2 className="font-semibold mb-3">Pipeline Funnel</h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={funnelData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="value" name="Leads" radius={[4, 4, 0, 0]}>
                {funnelData.map((_, i) => <Cell key={i} fill={FUNNEL_COLORS[i % FUNNEL_COLORS.length]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="card p-4">
          <h2 className="font-semibold mb-3">Lead Temperature</h2>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={split} dataKey="value" nameKey="name" innerRadius={60} outerRadius={90} paddingAngle={3}>
                {split.map((s, i) => <Cell key={i} fill={s.color} />)}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card p-4">
        <h2 className="font-semibold mb-3">Revenue Forecast (next 6 months, probability-weighted)</h2>
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={data.forecast.map((f) => ({ ...f, label: f.month }))}>
            <defs>
              <linearGradient id="fc" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b6ef6" stopOpacity={0.35} />
                <stop offset="95%" stopColor="#3b6ef6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="label" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
            <Tooltip formatter={(v) => fmtMoney(v)} />
            <Area type="monotone" dataKey="predicted" stroke="#3b6ef6" fill="url(#fc)" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="card p-4">
          <h2 className="font-semibold mb-3">High-Intent Leads</h2>
          <div className="space-y-2">
            {data.high_intent_leads.length === 0 && <p className="text-sm text-slate-400">No open leads yet.</p>}
            {data.high_intent_leads.map((l) => (
              <Link key={l.id} to={`/leads/${l.id}`} className="flex items-center justify-between rounded-lg border border-slate-100 px-3 py-2 hover:bg-slate-50">
                <div>
                  <div className="text-sm font-medium">{l.name}</div>
                  <div className="text-xs text-slate-500">{l.company}</div>
                </div>
                <div className="flex items-center gap-2">
                  <ClassificationBadge classification={l.classification} />
                  <ScoreBadge score={l.score} />
                </div>
              </Link>
            ))}
          </div>
        </div>
        <div className="card p-4 xl:col-span-2">
          <h2 className="font-semibold mb-3">Recent Activity</h2>
          <div className="space-y-1 max-h-80 overflow-y-auto">
            {data.recent_activity.length === 0 && <p className="text-sm text-slate-400">Nothing yet.</p>}
            {data.recent_activity.map((a) => (
              <div key={a.id} className="flex items-start gap-3 py-2 border-b border-slate-50 last:border-0">
                <span className="mt-0.5 text-sm">
                  {a.type === 'email' ? '✉️' : a.type === 'engagement' ? '👀' : a.type === 'score' ? '⭐' : a.type === 'automation' ? '⚡' : a.type === 'stage' ? '🎯' : '•'}
                </span>
                <div className="flex-1">
                  <div className="text-sm text-slate-700">{a.message}</div>
                  {a.lead_id && <Link to={`/leads/${a.lead_id}`} className="text-xs text-brand-600 hover:underline">view lead</Link>}
                </div>
                <span className="text-xs text-slate-400 whitespace-nowrap">{timeAgo(a.created_at)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
