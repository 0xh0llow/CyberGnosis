import { getStats, getHosts, getAlerts } from '@/lib/api';
import { Server, Activity, ShieldAlert, Cpu, HardDrive, CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';
import Link from 'next/link';

export const revalidate = 30;

export default async function OverviewPage() {
  const [stats, hosts, alerts] = await Promise.all([
    getStats(),
    getHosts(),
    getAlerts('status=open&limit=10'),
  ]);

  const openAlerts = alerts.filter((a) => a.status === 'open');
  const criticalCount = alerts.filter((a) => a.severity === 'critical' || a.severity === 'high').length;

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h2 className="text-2xl font-bold text-neutral-900">Panoramica del tuo Ambiente</h2>
        <p className="text-neutral-500">Una vista semplificata dei tuoi server protetti e delle attività recenti.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatusCard
          title="Stato Generale"
          value={criticalCount === 0 ? 'Protetto' : 'Attenzione'}
          icon={<ShieldAlert className={criticalCount === 0 ? 'text-emerald-500' : 'text-red-500'} size={24} />}
          description="Tutti i sistemi monitorati"
          status={criticalCount === 0 ? 'good' : 'warning'}
        />
        <StatusCard
          title="Host Attivi"
          value={stats.active_hosts.toString()}
          icon={<Server className="text-blue-500" size={24} />}
          description={`${stats.total_hosts} host monitorati in totale`}
        />
        <StatusCard
          title="Avvisi Attivi"
          value={stats.open_alerts.toString()}
          icon={<Activity className="text-amber-500" size={24} />}
          description="Azione potrebbe essere richiesta"
          status={stats.open_alerts > 0 ? 'warning' : 'good'}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Hosts List */}
        <div className="bg-white border border-neutral-200 rounded-xl overflow-hidden">
          <div className="p-4 border-b border-neutral-200 bg-neutral-50 flex justify-between items-center">
            <h3 className="font-semibold text-neutral-800 flex items-center gap-2">
              <Server size={18} className="text-neutral-500" />
              Host Monitorati
            </h3>
          </div>
          <div className="divide-y divide-neutral-100">
            {hosts.length === 0 && (
              <div className="p-6 text-center text-neutral-400">Nessun host registrato.</div>
            )}
            {hosts.map((host) => (
              <div key={host.host_id} className="p-4 flex items-center justify-between hover:bg-neutral-50 transition-colors">
                <div className="flex items-center gap-4">
                  {host.is_active ? (
                    <CheckCircle2 className="text-emerald-500" size={20} />
                  ) : (
                    <XCircle className="text-red-500" size={20} />
                  )}
                  <div>
                    <p className="font-medium text-neutral-900">{host.host_id}</p>
                    <div className="flex items-center gap-3 text-xs text-neutral-500 mt-1">
                      <span className="flex items-center gap-1">
                        <HardDrive size={12} />
                        Ultimo contatto: {new Date(host.last_seen).toLocaleString('it-IT')}
                      </span>
                    </div>
                  </div>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                  host.is_active
                    ? 'bg-emerald-100 text-emerald-700'
                    : 'bg-neutral-100 text-neutral-500'
                }`}>
                  {host.is_active ? 'online' : 'offline'}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Alerts List */}
        <div className="bg-white border border-neutral-200 rounded-xl overflow-hidden">
          <div className="p-4 border-b border-neutral-200 bg-neutral-50 flex justify-between items-center">
            <h3 className="font-semibold text-neutral-800 flex items-center gap-2">
              <Activity size={18} className="text-neutral-500" />
              Avvisi Recenti
            </h3>
            <Link href="/tickets" className="text-sm text-blue-600 font-medium hover:underline">
              Chiedi a un Esperto
            </Link>
          </div>
          <div className="divide-y divide-neutral-100">
            {openAlerts.length === 0 && (
              <div className="p-6 text-center text-neutral-400">Nessun avviso aperto 🎉</div>
            )}
            {openAlerts.map((alert) => (
              <div key={alert.id} className="p-4 flex items-start gap-3 hover:bg-neutral-50 transition-colors">
                <div className={`mt-0.5 p-1.5 rounded-full ${
                  alert.severity === 'critical' || alert.severity === 'high'
                    ? 'bg-red-100 text-red-600'
                    : 'bg-amber-100 text-amber-600'
                }`}>
                  <ShieldAlert size={14} />
                </div>
                <div>
                  <p className="font-medium text-neutral-900">{alert.title}</p>
                  <p className="text-sm text-neutral-500 mt-0.5">{alert.host_id}</p>
                  <p className="text-xs text-neutral-400 mt-2">
                    {new Date(alert.created_at).toLocaleString('it-IT')}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function StatusCard({ title, value, icon, description, status }: {
  title: string; value: string; icon: React.ReactNode;
  description: string; status?: string;
}) {
  return (
    <div className="bg-white p-5 rounded-xl border border-neutral-200 shadow-sm flex flex-col justify-between">
      <div className="flex justify-between items-start">
        <div>
          <p className="text-sm font-medium text-neutral-500">{title}</p>
          <h3 className="text-3xl font-bold text-neutral-900 mt-2">{value}</h3>
        </div>
        <div className="p-2 bg-neutral-50 rounded-lg">{icon}</div>
      </div>
      <div className="mt-4 flex items-center gap-2 text-sm text-neutral-600">
        {status === 'good' && <div className="w-2 h-2 rounded-full bg-emerald-500" />}
        {status === 'warning' && <div className="w-2 h-2 rounded-full bg-amber-500" />}
        {description}
      </div>
    </div>
  );
}
