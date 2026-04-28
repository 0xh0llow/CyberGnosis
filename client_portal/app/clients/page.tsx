'use client';

import { useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { getAlerts, getHosts, getMetrics } from '@/lib/api';
import type { Alert, Host, Metric } from '@/lib/api';
import { Activity, Cpu, HardDrive, Loader2, MonitorSmartphone, RefreshCw } from 'lucide-react';

const POLL_MS = 10000;

export default function ClientsPage() {
  const [hosts, setHosts] = useState<Host[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [metrics, setMetrics] = useState<Metric[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastSync, setLastSync] = useState('');

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [nextHosts, nextAlerts, nextMetrics] = await Promise.all([
          getHosts(),
          getAlerts('limit=150'),
          getMetrics('limit=200'),
        ]);

        if (!cancelled) {
          setHosts(nextHosts);
          setAlerts(nextAlerts);
          setMetrics(nextMetrics);
          setLastSync(new Date().toLocaleTimeString('it-IT'));
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
  }, []);

  const latestMetricByHost = useMemo(() => {
    const map = new Map<string, Metric>();
    for (const metric of metrics) {
      if (!map.has(metric.host_id)) map.set(metric.host_id, metric);
    }
    return map;
  }, [metrics]);

  const openAlertsByHost = useMemo(() => {
    const map = new Map<string, number>();
    for (const alert of alerts) {
      if (alert.status !== 'open') continue;
      map.set(alert.host_id, (map.get(alert.host_id) ?? 0) + 1);
    }
    return map;
  }, [alerts]);

  return (
    <div className="space-y-6">
      <section className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-950">Client Monitorati</h2>
          <p className="text-sm text-slate-600">Stato live degli endpoint osservati dagli agenti CyberGnosis.</p>
        </div>
        <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-600 shadow-sm">
          <RefreshCw size={14} className="text-sky-700" />
          Ultima sincronizzazione: {lastSync || '--:--:--'}
        </div>
      </section>

      {loading ? (
        <div className="flex min-h-64 items-center justify-center gap-2 rounded-2xl border border-slate-200 bg-white text-slate-500 shadow-panel">
          <Loader2 size={18} className="animate-spin" />
          Caricamento client...
        </div>
      ) : hosts.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-16 text-center text-slate-500">
          Nessun client registrato. Avvia un agent per vedere i sistemi comparire qui.
        </div>
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {hosts.map((host) => {
            const metric = latestMetricByHost.get(host.host_id);
            const cpu = readMetric(metric, ['cpu_percent']);
            const memory = readMetric(metric, ['memory_percent', 'ram_percent']);
            const disk = readMetric(metric, ['disk_percent']);
            const openAlerts = openAlertsByHost.get(host.host_id) ?? 0;

            return (
              <article key={host.host_id} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-panel">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className={`h-2.5 w-2.5 rounded-full ${host.is_active ? 'bg-emerald-500' : 'bg-slate-300'}`} />
                      <h3 className="text-lg font-semibold text-slate-950">{host.host_id}</h3>
                    </div>
                    <p className="mt-2 text-sm text-slate-500">
                      Ultimo contatto: {formatDateTime(host.last_seen)}
                    </p>
                  </div>
                  <span className={`rounded-full px-3 py-1 text-xs font-semibold ${host.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-600'}`}>
                    {host.is_active ? 'online' : 'offline'}
                  </span>
                </div>

                <div className="mt-5 grid gap-3 sm:grid-cols-3">
                  <MetricCard icon={<Cpu size={16} />} label="CPU" value={cpu} />
                  <MetricCard icon={<Activity size={16} />} label="RAM" value={memory} />
                  <MetricCard icon={<HardDrive size={16} />} label="Disk" value={disk} />
                </div>

                <div className="mt-5 grid gap-3 sm:grid-cols-2">
                  <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
                    <div className="flex items-center gap-2 text-sm font-medium text-slate-700">
                      <MonitorSmartphone size={15} />
                      Alert aperti
                    </div>
                    <div className="mt-2 text-2xl font-bold text-slate-950">{openAlerts}</div>
                  </div>
                  <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
                    <div className="text-sm font-medium text-slate-700">OS / Hostname</div>
                    <div className="mt-2 text-sm text-slate-600">
                      {host.hostname || host.os_info || 'Non disponibile'}
                    </div>
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}

function MetricCard({ icon, label, value }: { icon: ReactNode; label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
      <div className="flex items-center gap-2 text-sm font-medium text-slate-700">
        {icon}
        {label}
      </div>
      <div className="mt-2 text-2xl font-bold text-slate-950">{value}</div>
    </div>
  );
}

function readMetric(metric: Metric | undefined, candidates: string[]) {
  if (!metric) return 'n/d';
  for (const key of candidates) {
    const value = metric.metrics[key];
    if (typeof value === 'number') return `${Math.round(value)}%`;
  }
  return 'n/d';
}

function formatDateTime(value?: string | null) {
  if (!value) return 'n/d';
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? 'n/d' : parsed.toLocaleString('it-IT');
}
