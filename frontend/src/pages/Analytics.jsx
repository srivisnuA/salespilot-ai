import { useEffect, useState } from 'react'
import { api, fmtMoney, fmtPct } from '../lib/api.js'
import { Loading, ErrorState } from '../components/States.jsx'
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid,
  PieChart, Pie, Cell, Legend, FunnelChart, Funnel, LabelList, RadialBarChart, RadialBar,
} from 'recharts'

const COLORS = ['#3b6ef6', '#6090fa', '#93b4fd', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#0ea5e9']

export default function Analytics() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  const load = () => {
    setError(null)
    api.get('/analytics/overview').then(setData).catch((e) => setError(e.message))
  }
  useEffect(load, [])

  if (error) return <ErrorState message={error} onRetry={load} />
  if (!data) return <Loading label="Crunching analytics…" />

  const roi = data.overall_roi

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Analytics</h1>
        <p className="text-sm text-slate-500">Performance, forecasting and ROI</p>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-6 gap-4">
        {[
          ['Win rate', fmtPct(data.win_rate)],
          ['Loss rate', fmtPct(data.loss_rate)],
          ['Avg deal value', fmtMoney(data.avg_deal_value)],
          ['Sales cycle', `${data.sales_cycle_days} days`],
          ['Pipeline velocity', fmtMoney(data.pipeline_velocity) + '/day'],
          ['Predicted revenue', fmtMoney(data.predicted_revenue)],
        ].map(([l, v]) => (
          <div key={l} className="card p-4">
            <div className="text-xs text-slate-500">{l}</div>
            <div className="text-xl font-bold mt-1">{v}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card p-4">
          <div className="text-xs text-slate-500">Won revenue</div>
          <div className="text-2xl font-bold text-emerald-600">{fmtMoney(data.won_revenue)}</div>
        </div>
        <div className="card p-4">
          <div className="text-xs text-slate-500">Open pipeline</div>
          <div className="text-2xl font-bold">{fmtMoney(data.open_pipeline)}</div>
        </div>
        <div className="card p-4">
          <div className="text-xs text-slate-500">Weighted pipeline</div>
          <div className="text-2xl font-bold text-brand-600">{fmtMoney(data.weighted_pipeline)}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <div className="card p-4">
          <h2 className="font-semibold mb-3">Lead sources</h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={data.sources} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis type="number" tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey="source" width={100} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="count" name="Leads" fill="#3b6ef6" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="card p-4">
          <h2 className="font-semibold mb-3">Score distribution</h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={data.score_distribution}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="bucket" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="count" name="Leads" radius={[4, 4, 0, 0]}>
                {data.score_distribution.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <div className="card p-4">
          <h2 className="font-semibold mb-3">Industry performance</h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={data.industry_performance}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="industry" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Legend />
              <Bar dataKey="leads" name="Leads" fill="#3b6ef6" radius={[4, 4, 0, 0]} />
              <Bar dataKey="won" name="Won deals" fill="#10b981" radius={[4, 4, 0, 0]} />
              <Bar dataKey="avg_score" name="Avg score" fill="#f59e0b" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="card p-4">
          <h2 className="font-semibold mb-3">Email engagement</h2>
          <div className="grid grid-cols-3 gap-3 mb-4">
            <div className="rounded-lg bg-slate-50 p-3 text-center">
              <div className="text-xs text-slate-500">Open rate</div>
              <div className="text-xl font-bold">{fmtPct(Math.min(data.email.open_rate, 100))}</div>
            </div>
            <div className="rounded-lg bg-slate-50 p-3 text-center">
              <div className="text-xs text-slate-500">Click rate</div>
              <div className="text-xl font-bold">{fmtPct(Math.min(data.email.click_rate, 100))}</div>
            </div>
            <div className="rounded-lg bg-slate-50 p-3 text-center">
              <div className="text-xs text-slate-500">Reply rate</div>
              <div className="text-xl font-bold">{fmtPct(Math.min(data.email.reply_rate, 100))}</div>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={170}>
            <BarChart data={[
              { name: 'Sent', value: data.email.emails_sent },
              { name: 'Opens', value: data.email.opens },
              { name: 'Clicks', value: data.email.clicks },
              { name: 'Replies', value: data.email.replies },
            ]}>
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="value" name="Count" fill="#6090fa" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <div className="card p-4">
          <h2 className="font-semibold mb-3">Funnel conversion</h2>
          <ResponsiveContainer width="100%" height={280}>
            <FunnelChart>
              <Tooltip />
              <Funnel dataKey="count" data={data.funnel} isAnimationActive>
                <LabelList position="right" fill="#334155" stroke="none" dataKey="stage" fontSize={11} />
                <LabelList position="inside" fill="#fff" stroke="none" dataKey="count" fontSize={12} />
              </Funnel>
            </FunnelChart>
          </ResponsiveContainer>
          <div className="text-xs text-slate-500 mt-2 space-y-0.5">
            {data.funnel_conversion.map((c) => (
              <div key={c.to}>{c.from} → {c.to}: <strong>{c.rate}%</strong></div>
            ))}
          </div>
        </div>
        <div className="card p-4">
          <h2 className="font-semibold mb-3">Win / loss</h2>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={[
                  { name: 'Won', value: Math.round(data.win_rate), fill: '#10b981' },
                  { name: 'Lost', value: Math.round(data.loss_rate), fill: '#ef4444' },
                ]}
                dataKey="value" nameKey="name" innerRadius={70} outerRadius={110} paddingAngle={2}>
              </Pie>
              <Tooltip formatter={(v) => `${v}%`} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ROI */}
      <div className="card p-4">
        <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
          <h2 className="font-semibold">Campaign ROI</h2>
          <div className="text-sm">
            Cost: <strong>{fmtMoney(data.total_campaign_cost)}</strong> · Revenue:{' '}
            <strong className="text-emerald-600">{fmtMoney(data.total_campaign_revenue)}</strong> · ROI:{' '}
            <strong className={roi >= 0 ? 'text-emerald-600' : 'text-red-600'}>
              {roi == null ? '—' : `${roi}%`}
            </strong>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[600px]">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr><th className="th">Campaign</th><th className="th">Channel</th><th className="th">Cost</th><th className="th">Revenue generated</th><th className="th">ROI</th></tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.campaigns_roi.map((c) => (
                <tr key={c.id}>
                  <td className="td font-medium">{c.name}</td>
                  <td className="td">{c.channel}</td>
                  <td className="td">{fmtMoney(c.cost)}</td>
                  <td className="td text-emerald-700">{fmtMoney(c.revenue)}</td>
                  <td className={`td font-semibold ${c.roi >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                    {c.roi == null ? '—' : `${c.roi}%`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-slate-400 mt-2">ROI = ((Revenue Generated − Campaign Cost) / Campaign Cost) × 100</p>
      </div>
    </div>
  )
}
