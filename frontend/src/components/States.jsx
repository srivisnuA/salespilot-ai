export function Loading({ label = 'Loading…' }) {
  return (
    <div className="flex items-center justify-center py-16 text-slate-500">
      <svg className="animate-spin h-5 w-5 mr-3 text-brand-600" viewBox="0 0 24 24" fill="none">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
      </svg>
      {label}
    </div>
  )
}

export function ErrorState({ message, onRetry }) {
  return (
    <div className="card p-8 text-center">
      <div className="text-red-600 font-semibold mb-2">Something went wrong</div>
      <p className="text-slate-500 text-sm mb-4">{message}</p>
      {onRetry && (
        <button className="btn-secondary" onClick={onRetry}>Try again</button>
      )}
    </div>
  )
}

export function EmptyState({ title, hint, action }) {
  return (
    <div className="card p-10 text-center">
      <div className="text-4xl mb-3">🗂️</div>
      <div className="font-semibold text-slate-700">{title}</div>
      {hint && <p className="text-sm text-slate-500 mt-1">{hint}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}

export function Skeleton({ rows = 5 }) {
  return (
    <div className="space-y-3 p-4">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="h-10 bg-slate-100 rounded-lg animate-pulse" />
      ))}
    </div>
  )
}
