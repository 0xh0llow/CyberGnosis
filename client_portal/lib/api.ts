/**
 * api.ts — wrapper centralizzato per tutte le chiamate al backend FastAPI.
 * Usato sia da Server Components (fetch diretto) che da Client Components.
 *
 * In Docker e in locale le chiamate passano da /api/* del portale Next,
 * che fa da proxy runtime verso il central_server.
 */

function authHeaders(): HeadersInit {
  return {
    'Content-Type': 'application/json',
  }
}

// ── Types ────────────────────────────────────────────────────────────────────

export interface Host {
  id?: number
  host_id: string
  hostname?: string | null
  os_info?: string | null
  last_seen: string | null
  is_active: boolean
  registered_at?: string | null
  metadata?: Record<string, unknown>
}

export interface Alert {
  id: number
  alert_type: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  title: string
  description: string
  status: 'open' | 'investigating' | 'resolved' | 'false_positive'
  host_id: string
  created_at: string
  updated_at?: string | null
  timestamp?: string | null
  alert_metadata?: Record<string, unknown>
}

export interface Metric {
  id: number
  host_id: string
  metrics: Record<string, unknown>
  timestamp: string
}

export interface Stats {
  total_alerts: number
  open_alerts: number
  total_hosts: number
  active_hosts: number
  total_metrics: number
  total_tickets: number
  open_tickets: number
  tickets_by_status: Record<string, number>
  alerts_by_severity: Record<string, number>
}

export interface Ticket {
  id: number
  title: string
  description: string
  customer_name?: string | null
  customer_email?: string | null
  status: 'open' | 'in_progress' | 'closed'
  priority: 'low' | 'medium' | 'high'
  created_at: string
  updated_at: string | null
  host_id?: string | null
  alert_id?: number | null
  support_response?: string | null
  internal_notes?: string | null
  closed_at?: string | null
}

export interface TelegramConfig {
  id: number
  chat_id: string
  is_active: boolean
  created_at: string
  updated_at: string | null
}

export interface SimulationResult {
  status: string
  host_id: string
  alert: Alert
}

interface AlertsResponse {
  alerts: Alert[]
}

interface TicketsResponse {
  tickets: Ticket[]
}

interface TelegramConfigsResponse {
  items: TelegramConfig[]
  bot_token_configured: boolean
}

interface TelegramSaveResponse extends TelegramConfig {
  bot_token_configured: boolean
}

// ── Helpers ──────────────────────────────────────────────────────────────────

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const fetchInit: RequestInit = {
    ...init,
    headers: { ...authHeaders(), ...(init?.headers ?? {}) },
    cache: 'no-store',
  }

  const res = await fetch(path, fetchInit)
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`)
  return res.json() as Promise<T>
}

function normalizeAlert(alert: Partial<Alert> & { metadata?: Record<string, unknown> }): Alert {
  return {
    id: Number(alert.id),
    alert_type: String(alert.alert_type ?? ''),
    severity: (alert.severity ?? 'low') as Alert['severity'],
    title: String(alert.title ?? ''),
    description: String(alert.description ?? ''),
    status: (alert.status ?? 'open') as Alert['status'],
    host_id: String(alert.host_id ?? ''),
    created_at: String(alert.created_at ?? alert.timestamp ?? ''),
    updated_at: (alert.updated_at as string | null | undefined) ?? null,
    timestamp: (alert.timestamp as string | null | undefined) ?? null,
    alert_metadata: (alert.alert_metadata as Record<string, unknown> | undefined)
      ?? (alert.metadata as Record<string, unknown> | undefined)
      ?? {},
  }
}

function normalizeTicket(ticket: Partial<Ticket>): Ticket {
  return {
    id: Number(ticket.id),
    title: String(ticket.title ?? ''),
    description: String(ticket.description ?? ''),
    customer_name: (ticket.customer_name as string | null | undefined) ?? null,
    customer_email: (ticket.customer_email as string | null | undefined) ?? null,
    status: (ticket.status ?? 'open') as Ticket['status'],
    priority: (ticket.priority ?? 'medium') as Ticket['priority'],
    created_at: String(ticket.created_at ?? ''),
    updated_at: (ticket.updated_at as string | null | undefined) ?? null,
    host_id: (ticket.host_id as string | null | undefined) ?? null,
    alert_id: (ticket.alert_id as number | null | undefined) ?? null,
    support_response: (ticket.support_response as string | null | undefined) ?? null,
    internal_notes: (ticket.internal_notes as string | null | undefined) ?? null,
    closed_at: (ticket.closed_at as string | null | undefined) ?? null,
  }
}

function normalizeStats(stats: Partial<Stats>): Stats {
  return {
    total_alerts: stats.total_alerts ?? 0,
    open_alerts: stats.open_alerts ?? 0,
    total_hosts: stats.total_hosts ?? stats.active_hosts ?? 0,
    active_hosts: stats.active_hosts ?? 0,
    total_metrics: stats.total_metrics ?? 0,
    total_tickets: stats.total_tickets ?? 0,
    open_tickets: stats.open_tickets ?? 0,
    tickets_by_status: stats.tickets_by_status ?? {},
    alerts_by_severity: stats.alerts_by_severity ?? {},
  }
}

// ── API calls ────────────────────────────────────────────────────────────────

export const getStats = async () => normalizeStats(await apiFetch<Stats>('/api/stats'))
export const getHosts = () => apiFetch<Host[]>('/api/hosts')
export const getMetrics = (params?: string) => apiFetch<Metric[]>(`/api/metrics${params ? '?' + params : ''}`)
export const getAlerts = async (params?: string) => {
  const response = await apiFetch<Alert[] | AlertsResponse>(`/api/alerts${params ? '?' + params : ''}`)
  const alerts = Array.isArray(response) ? response : response.alerts
  return alerts.map((alert) => normalizeAlert(alert))
}
export const getAlert = async (id: string | number) =>
  normalizeAlert(await apiFetch<Alert>(`/api/alerts/${id}`))
export const updateAlert = async (id: string | number, body: Partial<Alert>) =>
  normalizeAlert(await apiFetch<Alert>(`/api/alerts/${id}`, { method: 'PATCH', body: JSON.stringify(body) }))

export const getTickets = async () => {
  const response = await apiFetch<Ticket[] | TicketsResponse>('/api/tickets')
  const tickets = Array.isArray(response) ? response : response.tickets
  return tickets.map((ticket) => normalizeTicket(ticket))
}
export const getTicket = async (id: string | number) =>
  normalizeTicket(await apiFetch<Ticket>(`/api/tickets/${id}`))
export const createTicket = async (
  body: Omit<Ticket, 'id' | 'created_at' | 'updated_at'>,
) => normalizeTicket(
  await apiFetch<Ticket>('/api/tickets', { method: 'POST', body: JSON.stringify(body) }),
)
export const updateTicket = async (id: string | number, body: Partial<Ticket>) =>
  normalizeTicket(
    await apiFetch<Ticket>(`/api/tickets/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  )

export const searchSimilarAlerts = (query: string) =>
  apiFetch('/api/search/similar-alerts', {
    method: 'POST',
    body: JSON.stringify({ query, top_k: 5 }),
  })

export const simulateAttack = (type: string, host_id?: string) =>
  apiFetch<SimulationResult>('/api/simulate-attack', {
    method: 'POST',
    body: JSON.stringify({ attack_type: type, host_id }),
  })

export const saveTelegramConfig = (chat_id: string) =>
  apiFetch<TelegramSaveResponse>('/api/notifications/telegram', {
    method: 'POST',
    body: JSON.stringify({ chat_id }),
  })

export const getTelegramConfigs = () =>
  apiFetch<TelegramConfigsResponse>('/api/notifications/telegram')
