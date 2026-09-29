import { useState } from 'react'
import { api } from '../lib/api.js'
import { useToast } from './Toast.jsx'

const INDUSTRIES = ['SaaS', 'FinTech', 'Healthcare', 'E-commerce', 'Manufacturing', 'Technology']
const SIZES = ['1-10', '11-50', '51-200', '201-1000', '1000+']
const SOURCES = ['website', 'referral', 'linkedin', 'webinar', 'cold_outreach', 'inbound', 'event', 'partner']
const TIMELINES = ['immediate', 'this quarter', '6 months', '1 year', 'unknown']

const EMPTY = {
  name: '', email: '', company_name: '', job_title: '', industry: 'SaaS',
  company_size: '11-50', annual_revenue: 0, source: 'website', budget: 0,
  buying_timeline: 'unknown', pain_point: '', notes: '',
}

export default function LeadForm({ lead, onClose, onSaved }) {
  const toast = useToast()
  const [form, setForm] = useState(lead ? {
    name: lead.name, email: lead.email, company_name: lead.company_name,
    job_title: lead.job_title, industry: lead.industry, company_size: lead.company_size,
    annual_revenue: lead.annual_revenue || 0, source: lead.source,
    budget: lead.budget || 0, buying_timeline: lead.buying_timeline,
    pain_point: lead.pain_point, notes: lead.notes,
  } : EMPTY)
  const [errors, setErrors] = useState({})
  const [saving, setSaving] = useState(false)

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  const validate = () => {
    const e = {}
    if (!form.name.trim()) e.name = 'Name is required'
    if (!form.email.trim()) e.email = 'Email is required'
    else if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(form.email)) e.email = 'Invalid email address'
    if (form.budget !== '' && Number(form.budget) < 0) e.budget = 'Must be non-negative'
    if (form.annual_revenue !== '' && Number(form.annual_revenue) < 0) e.annual_revenue = 'Must be non-negative'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const submit = async (ev) => {
    ev.preventDefault()
    if (!validate()) return
    setSaving(true)
    try {
      const payload = {
        ...form,
        annual_revenue: Number(form.annual_revenue) || 0,
        budget: Number(form.budget) || 0,
      }
      if (lead) await api.patch(`/leads/${lead.id}`, payload)
      else await api.post('/leads', payload)
      toast.success(lead ? 'Lead updated' : 'Lead created')
      onSaved()
    } catch (err) {
      toast.error(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-40 bg-black/40 flex items-start justify-center overflow-y-auto p-6" onClick={onClose}>
      <form className="card w-full max-w-2xl p-6 space-y-4" onClick={(e) => e.stopPropagation()} onSubmit={submit}>
        <h2 className="text-lg font-bold">{lead ? 'Edit Lead' : 'New Lead'}</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Name *</label>
            <input className="input" value={form.name} onChange={(e) => set('name', e.target.value)} />
            {errors.name && <p className="text-xs text-red-600 mt-1">{errors.name}</p>}
          </div>
          <div>
            <label className="label">Email *</label>
            <input className="input" value={form.email} onChange={(e) => set('email', e.target.value)} />
            {errors.email && <p className="text-xs text-red-600 mt-1">{errors.email}</p>}
          </div>
          <div>
            <label className="label">Company</label>
            <input className="input" value={form.company_name} onChange={(e) => set('company_name', e.target.value)} />
          </div>
          <div>
            <label className="label">Job Title</label>
            <input className="input" value={form.job_title} onChange={(e) => set('job_title', e.target.value)} />
          </div>
          <div>
            <label className="label">Industry</label>
            <select className="input" value={form.industry} onChange={(e) => set('industry', e.target.value)}>
              {INDUSTRIES.map((i) => <option key={i}>{i}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Company Size</label>
            <select className="input" value={form.company_size} onChange={(e) => set('company_size', e.target.value)}>
              {SIZES.map((s) => <option key={s}>{s}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Annual Company Revenue ($)</label>
            <input type="number" min="0" className="input" value={form.annual_revenue} onChange={(e) => set('annual_revenue', e.target.value)} />
            {errors.annual_revenue && <p className="text-xs text-red-600 mt-1">{errors.annual_revenue}</p>}
          </div>
          <div>
            <label className="label">Budget ($)</label>
            <input type="number" min="0" className="input" value={form.budget} onChange={(e) => set('budget', e.target.value)} />
            {errors.budget && <p className="text-xs text-red-600 mt-1">{errors.budget}</p>}
          </div>
          <div>
            <label className="label">Source</label>
            <select className="input" value={form.source} onChange={(e) => set('source', e.target.value)}>
              {SOURCES.map((s) => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Buying Timeline</label>
            <select className="input" value={form.buying_timeline} onChange={(e) => set('buying_timeline', e.target.value)}>
              {TIMELINES.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
        </div>
        <div>
          <label className="label">Pain Point</label>
          <textarea className="input" rows={2} value={form.pain_point} onChange={(e) => set('pain_point', e.target.value)} />
        </div>
        <div>
          <label className="label">Notes</label>
          <textarea className="input" rows={2} value={form.notes} onChange={(e) => set('notes', e.target.value)} />
        </div>
        <div className="flex justify-end gap-2">
          <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
          <button type="submit" className="btn-primary" disabled={saving}>{saving ? 'Saving…' : lead ? 'Save changes' : 'Create lead'}</button>
        </div>
      </form>
    </div>
  )
}
