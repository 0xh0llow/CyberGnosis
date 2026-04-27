/**
 * Overview page — Server Component.
 * Dati reali da FastAPI via api.ts (niente mock).
 */
import { getStats, getHosts, getAlerts } from '@/lib/api'

export const revalidate = 30

export default async function OverviewPage() {
  const [stats, hosts, alerts] = await Promise.all([
    getStats(),
    getHosts(),
    getAlerts('status=open&limit=10'),
  ])

  const activeHosts = hosts.filter((h) => h.is_active)
  const criticalAlerts = alerts.filter((a) => a.severity === 'critical')

  return (
    <main className="p-6 space-y-8">
      <h1 className="text-2xl font-bold">Overview</h1>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KpiCard label="Alert aperti"     value={stats.open_alerts}    accent="red" />
        <KpiCard label="Host attivi"      value={stats.active_hosts}   accent="green" />
        <KpiCard label="Alert critici"    value={criticalAlerts.length} accent="orange" />
        <KpiCard label="Host monitorati" value={stats.total_hosts}     accent="blue" />
      </div>

      {/* Alert recenti */}
      <section>
        <h2 className="text-lg font-semibold mb-3">Alert recenti (open)</h2>
        <div className="rounded-lg border overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-muted text-muted-foreground">
              <tr>
                <th className="px-4 py-2 text-left">Titolo</th>
                <th className="px-4 py-2 text-left">Host</th>
                <th className="px-4 py-2 text-left">Severity</th>
                <th className="px-4 py-2 text-left">Tipo</th>
              </tr>
            </thead>
            <tbody>
              {alerts.length === 0 && (
                <tr><td colSpan={4} className="px-4 py-6 text-center text-muted-foreground">Nessun alert aperto 🎉</td></tr>
              )}
              {alerts.map((a) => (
                <tr key={a.id} className="border-t hover:bg-muted/40 transition-colors">
                  <td className="px-4 py-2 font-medium">{a.title}</td>
                  <td className="px-4 py-2 text-muted-foreground">{a.host_id}</td>
                  <td className="px-4 py-2">
                    <SeverityBadge severity={a.severity} />
                  </td>
                  <td className="px-4 py-2 text-muted-foreground">{a.alert_type}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Host */}
      <section>
        <h2 className="text-lg font-semibold mb-3">Host ({activeHosts.length} attivi)</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {hosts.map((h) => (
            <div key={h.host_id} className="rounded-lg border p-4 flex items-center gap-3">
              <span className={`w-2.5 h-2.5 rounded-full ${h.is_active ? 'bg-green-500' : 'bg-gray-400'}`} />
              <div>
                <p className="font-medium text-sm">{h.host_id}</p>
                <p className="text-xs text-muted-foreground">
                  Ultimo contatto: {new Date(h.last_seen).toLocaleString('it-IT')}
                </p>
              </div>
            </div>
          ))}
        </div>
      </section>
    </main>
  )
}

function KpiCard({ label, value, accent }: { label: string; value: number; accent: string }) {
  const colors: Record<string, string> = {
    red: 'border-red-500/30 bg-red-50 dark:bg-red-950/20',
    green: 'border-green-500/30 bg-green-50 dark:bg-green-950/20',
    orange: 'border-orange-500/30 bg-orange-50 dark:bg-orange-950/20',
    blue: 'border-blue-500/30 bg-blue-50 dark:bg-blue-950/20',
  }
  return (
    <div className={`rounded-xl border p-5 ${colors[accent] ?? ''}`}>
      <p className="text-3xl font-bold tabular-nums">{value}</p>
      <p className="text-sm text-muted-foreground mt-1">{label}</p>
    </div>
  )
}

function SeverityBadge({ severity }: { severity: string }) {
  const styles: Record<string, string> = {
    critical: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400',
    high:     'bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-400',
    medium:   'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-400',
    low:      'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400',
  }
  return (
    <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${styles[severity] ?? 'bg-gray-100'}`}>
      {severity}
    </span>
  )
}
