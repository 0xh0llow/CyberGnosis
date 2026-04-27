/**
 * api.ts — wrapper centralizzato per tutte le chiamate al backend FastAPI.
 * Usato sia da Server Components (fetch diretto) che da Client Components.
 *
 * In produzione Docker i rewrites di next.config.ts instradano /api/* → central_server:8000/api/*
 * In sviluppo locale funziona ugualmente grazie al proxy Next.js.
 */

const API_TOKEN = process.env.API_TOKEN ?? ''

function authHeaders(): HeadersInit {
  return {
    'Content-Type': 'application/json',
    ...(API_TOKEN ? { Authorization: `Bearer ${API_TOKEN}` } : {}),
  }
}

// ── Types ────────────────────────────────────────────────────────────────────

export interface Host {
  host_id: string
  last_seen: string
  is_active: boolean
  metadata?: Record<string, unknown>
}

export interface Alert {
  id: string
  alert_type: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  title: string
  description: string
  status: 'open' | 'investigating' | 'resolved' | 'false_positive'
  host_id: string
  created_at: string
  alert_metadata?: Record<string, unknown>
}

export interface Metric {
  id: string
  host_id: string
  metric_type: string
  data: Record<string, unknown>
  timestamp: string
}

export interface Stats {
  total_alerts: number
  open_alerts: number
  total_hosts: number
  active_hosts: number
  total_metrics: number
  alerts_by_severity: Record<string, number>
}

export interface Ticket {
  id: string
  title: string
  description: string
  status: 'open' | 'in_progress' | 'closed'
  priority: 'low' | 'medium' | 'high'
  created_at: string
  updated_at: string
  alert_id?: string
}

// ── Helpers ──────────────────────────────────────────────────────────────────

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const base =
    typeof window === 'undefined'
      ? (process.env.CENTRAL_SERVER_URL ?? 'http://central_server:8000')
      : ''
  const res = await fetch(`${base}${path}`, {
    ...init,
    headers: { ...authHeaders(), ...(init?.headers ?? {}) },
    next: { revalidate: 30 }, // ISR 30s per i Server Components
  })
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`)
  return res.json() as Promise<T>
}

// ── API calls ────────────────────────────────────────────────────────────────

export const getStats    = () => apiFetch<Stats>('/api/stats')
export const getHosts    = () => apiFetch<Host[]>('/api/hosts')
export const getAlerts   = (params?: string) => apiFetch<Alert[]>(`/api/alerts${params ? '?' + params : ''}`)
export const getAlert    = (id: string) => apiFetch<Alert>(`/api/alerts/${id}`)
export const updateAlert = (id: string, body: Partial<Alert>) =>
  apiFetch<Alert>(`/api/alerts/${id}`, { method: 'PATCH', body: JSON.stringify(body) })

export const getTickets  = () => apiFetch<Ticket[]>('/api/tickets')
export const createTicket = (body: Omit<Ticket, 'id' | 'created_at' | 'updated_at'>) =>
  apiFetch<Ticket>('/api/tickets', { method: 'POST', body: JSON.stringify(body) })
export const updateTicket = (id: string, body: Partial<Ticket>) =>
  apiFetch<Ticket>(`/api/tickets/${id}`, { method: 'PATCH', body: JSON.stringify(body) })

export const searchSimilarAlerts = (query: string) =>
  apiFetch('/api/search/similar-alerts', {
    method: 'POST',
    body: JSON.stringify({ query, n_results: 5 }),
  })

export const simulateAttack = (type: string) =>
  apiFetch('/api/simulate-attack', {
    method: 'POST',
    body: JSON.stringify({ attack_type: type }),
  })

export const saveTelegramConfig = (chat_id: string) =>
  apiFetch('/api/notifications/telegram', {
    method: 'POST',
    body: JSON.stringify({ chat_id }),
  })
