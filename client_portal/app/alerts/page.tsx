'use client';

import { useEffect, useMemo, useState } from 'react';
import { getAlerts, getHosts, updateAlert } from '@/lib/api';
import type { Alert, Host } from '@/lib/api';
import { Loader2, Search, ShieldAlert } from 'lucide-react';

const POLL_MS = 15000;

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [hosts, setHosts] = useState<Host[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    severity: '',
    status: '',
    host_id: '',
  });

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const query = new URLSearchParams();
        query.set('limit', '100');
        if (filters.severity) query.set('severity', filters.severity);
        if (filters.status) query.set('status', filters.status);
        if (filters.host_id) query.set('host_id', filters.host_id);

        const [nextAlerts, nextHosts] = await Promise.all([
          getAlerts(query.toString()),
          getHosts(),
        ]);

        if (!cancelled) {
          setAlerts(nextAlerts);
          setHosts(nextHosts);
        }
      } catch (error) {
        console.error(error);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void load();
    const timer = window.setInterval(() => void load(), POLL_MS);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [filters.host_id, filters.severity, filters.status]);

  const grouped = useMemo(
    () => ({
      open: alerts.filter((alert) => alert.status === 'open').length,
      critical: alerts.filter((alert) => alert.severity === 'critical').length,
    }),
    [alerts],
  );

  async function handleStatusChange(alertId: number, status: Alert['status']) {
    const updated = await updateAlert(alertId, { status });
    setAlerts((current) => current.map((item) => (item.id === alertId ? updated : item)));
  }

  return (
    <div className="space-y-6">
      <section className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-950">Alert Security</h2>
          <p className="text-sm text-slate-600">Vista operativa sugli eventi inviati dagli agenti, con refresh automatico.</p>
        </div>
        <div className="flex gap-3 text-sm">
          <InfoPill label="Open" value={grouped.open} tone="amber" />
          <InfoPill label="Critical" value={grouped.critical} tone="red" />
        </div>
      </section>

      <section className="grid gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-panel sm:grid-cols-3">
        <FilterSelect
          label="Severity"
          value={filters.severity}
          onChange={(value) => setFilters((current) => ({ ...current, severity: value }))}
          options={['critical', 'high', 'medium', 'low']}
        />
        <FilterSelect
          label="Status"
          value={filters.status}
          onChange={(value) => setFilters((current) => ({ ...current, status: value }))}
          options={['open', 'investigating', 'resolved', 'false_positive']}
        />
        <label className="space-y-2 text-sm font-medium text-slate-700">
          <span>Client</span>
          <select
            value={filters.host_id}
            onChange={(event) => setFilters((current) => ({ ...current, host_id: event.target.value }))}
            className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-sky-400 focus:bg-white"
          >
            <option value="">Tutti i client</option>
            {hosts.map((host) => (
              <option key={host.host_id} value={host.host_id}>
                {host.host_id}
              </option>
            ))}
          </select>
        </label>
      </section>

      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-panel">
        <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
          <div className="flex items-center gap-2">
            <ShieldAlert size={18} className="text-sky-700" />
            <h3 className="font-semibold text-slate-950">Stream degli alert</h3>
          </div>
          <span className="text-xs font-medium uppercase tracking-[0.16em] text-slate-400">polling 15s</span>
        </div>

        {loading ? (
          <div className="flex items-center justify-center gap-2 px-6 py-16 text-slate-500">
            <Loader2 size={18} className="animate-spin" />
            Caricamento alert...
          </div>
        ) : alerts.length === 0 ? (
          <div className="px-6 py-16 text-center text-slate-500">Nessun alert con i filtri correnti.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
                <tr>
                  <th className="px-5 py-3">Alert</th>
                  <th className="px-5 py-3">Client</th>
                  <th className="px-5 py-3">Tipo</th>
                  <th className="px-5 py-3">Severity</th>
                  <th className="px-5 py-3">Stato</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {alerts.map((alert) => (
                  <tr key={alert.id} className="hover:bg-slate-50/80">
                    <td className="px-5 py-4">
                      <div className="font-medium text-slate-950">{alert.title}</div>
                      <div className="mt-1 line-clamp-2 text-xs text-slate-500">{alert.description}</div>
                      <div className="mt-2 text-xs text-slate-400">{formatDateTime(alert.created_at ?? alert.timestamp)}</div>
                    </td>
                    <td className="px-5 py-4 font-mono text-xs text-slate-700">{alert.host_id}</td>
                    <td className="px-5 py-4 text-slate-600">{alert.alert_type}</td>
                    <td className="px-5 py-4"><SeverityBadge severity={alert.severity} /></td>
                    <td className="px-5 py-4">
                      <select
                        value={alert.status}
                        onChange={(event) => void handleStatusChange(alert.id, event.target.value as Alert['status'])}
                        className="rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 outline-none focus:border-sky-400"
                      >
                        <option value="open">open</option>
                        <option value="investigating">investigating</option>
                        <option value="resolved">resolved</option>
                        <option value="false_positive">false_positive</option>
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

function FilterSelect({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: string[];
}) {
  return (
    <label className="space-y-2 text-sm font-medium text-slate-700">
      <span>{label}</span>
      <div className="relative">
        <Search size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <select
          value={value}
          onChange={(event) => onChange(event.target.value)}
          className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-9 pr-3 text-sm text-slate-900 outline-none transition focus:border-sky-400 focus:bg-white"
        >
          <option value="">Tutti</option>
          {options.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </div>
    </label>
  );
}

function SeverityBadge({ severity }: { severity: Alert['severity'] }) {
  const styles: Record<Alert['severity'], string> = {
    critical: 'bg-red-100 text-red-700',
    high: 'bg-orange-100 text-orange-700',
    medium: 'bg-amber-100 text-amber-700',
    low: 'bg-emerald-100 text-emerald-700',
  };

  return <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${styles[severity]}`}>{severity}</span>;
}

function InfoPill({ label, value, tone }: { label: string; value: number; tone: 'amber' | 'red' }) {
  const tones = {
    amber: 'bg-amber-100 text-amber-800',
    red: 'bg-red-100 text-red-800',
  };

  return (
    <div className={`rounded-full px-3 py-1.5 font-semibold ${tones[tone]}`}>
      {label}: {value}
    </div>
  );
}

function formatDateTime(value?: string | null) {
  if (!value) return 'n/d';
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? 'n/d' : parsed.toLocaleString('it-IT');
}
