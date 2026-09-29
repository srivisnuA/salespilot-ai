export function StatCard({ label, value, sub, tone = 'default', icon }) {
  const tones = {
    default: 'text-slate-900',
    green: 'text-emerald-600',
    red: 'text-red-600',
    amber: 'text-amber-600',
    sky: 'text-sky-600',
    brand: 'text-brand-600',
  }
  return (
    <div className="card p-4">
      <div className="flex items-center justify-between">
        <div className="text-xs font-medium text-slate-500">{label}</div>
        {icon && <span className="text-lg">{icon}</span>}
      </div>
      <div className={`text-2xl font-bold mt-1 ${tones[tone]}`}>{value}</div>
      {sub && <div className="text-xs text-slate-400 mt-1">{sub}</div>}
    </div>
  )
}

export function ScoreBadge({ score }) {
  const color = score >= 75 ? 'bg-red-500' : score >= 50 ? 'bg-amber-500' : 'bg-sky-500'
  return (
    <span className={`badge ${score >= 75 ? 'bg-red-100 text-red-700' : score >= 50 ? 'bg-amber-100 text-amber-700' : 'bg-sky-100 text-sky-700'}`}>
      {score}
    </span>
  )
}

export function ClassificationBadge({ classification }) {
  const map = { hot: 'Hot 🔥', warm: 'Warm', cold: 'Cold' }
  const cls = { hot: 'bg-red-100 text-red-700', warm: 'bg-amber-100 text-amber-700', cold: 'bg-sky-100 text-sky-700' }
  return <span className={`badge ${cls[classification] || 'bg-slate-100 text-slate-600'}`}>{map[classification] || classification}</span>
}

export function RiskBadge({ risk }) {
  const cls = { low: 'bg-emerald-100 text-emerald-700', medium: 'bg-amber-100 text-amber-700', high: 'bg-red-100 text-red-700' }
  return <span className={`badge ${cls[risk] || ''}`}>{risk} risk</span>
}

export function StageBadge({ stage }) {
  return <span className="badge bg-brand-50 text-brand-700 border border-brand-100">{stage}</span>
}

export function StatusBadge({ status }) {
  const cls = {
    draft: 'bg-slate-100 text-slate-600',
    approved: 'bg-violet-100 text-violet-700',
    sent: 'bg-emerald-100 text-emerald-700',
  }
  return <span className={`badge ${cls[status] || ''}`}>{status}</span>
}
