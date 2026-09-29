const BASE = '/api'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    let detail = `Request failed (${res.status})`
    try {
      const body = await res.json()
      detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail || body)
    } catch { /* keep default */ }
    throw new Error(detail)
  }
  return res.json()
}

export const api = {
  get: (p) => request(p),
  post: (p, body) => request(p, { method: 'POST', body: JSON.stringify(body) }),
  patch: (p, body) => request(p, { method: 'PATCH', body: JSON.stringify(body) }),
  put: (p, body) => request(p, { method: 'PUT', body: JSON.stringify(body) }),
  del: (p) => request(p, { method: 'DELETE' }),
}

export const fmtMoney = (n) =>
  n == null ? '—' : '$' + Number(n).toLocaleString('en-US', { maximumFractionDigits: 0 })
export const fmtMoney2 = (n) =>
  n == null ? '—' : '$' + Number(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
export const fmtPct = (n) => (n == null ? '—' : `${Number(n).toFixed(1)}%`)
export const fmtDate = (s) => (s ? new Date(s).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : '—')
export const fmtDateTime = (s) => (s ? new Date(s).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }) : '—')
export const timeAgo = (s) => {
  if (!s) return '—'
  const diff = (Date.now() - new Date(s).getTime()) / 1000
  if (diff < 60) return 'just now'
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

export const CLASS_STYLES = {
  hot: 'bg-red-100 text-red-700',
  warm: 'bg-amber-100 text-amber-700',
  cold: 'bg-sky-100 text-sky-700',
}
