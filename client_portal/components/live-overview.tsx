'use client';

import { useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import Link from 'next/link';
import { getAlerts, getHosts, getMetrics, getStats, getTelegramConfigs } from '@/lib/api';
import type { Alert, Host, Metric, Stats } from '@/lib/api';
import { Activity, BellRing, Cpu, HardDrive, LifeBuoy, Loader2, Radar, Server, ShieldAlert } from 'lucide-react';

const POLL_MS = 10000;

export function LiveOverview() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [hosts, setHosts] = useState<Host[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [metrics, setMetrics] = useState<Metric[]>([]);
  const [botConfigured, setBotConfigured] = useState(false);
  const [loading, setLoading] = useState(true);
  const [lastSync, setLastSync] = useState('');

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [nextStats, nextHosts, nextAlerts, nextMetrics, telegram] = await Promise.all([
          getStats(),
          getHosts(),
          getAlerts('status=open&limit=12'),
          getMetrics('limit=120'),
          getTelegramConfigs(),
        ]);

        if (!cancelled) {
          setStats(nextStats);
          setHosts(nextHosts);
          setAlerts(nextAlerts);
          setMetrics(nextMetrics);
          setBotConfigured(telegram.bot_token_configured && telegram.items.length > 0);
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

  if (loading && !stats) {
    return (
      <div className="flex min-h-80 items-center justify-center gap-2 rounded-2xl border border-slate-200 bg-white text-slate-500 shadow-panel">
        <Loader2 size={18} className="animate-spin" />
        Caricamento dashboard live...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <section className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-950">Control Center</h2>
          <p className="text-sm text-slate-600">Monitoraggio live di client, alert aperti, ticket e canali di notifica.</p>
        </div>
        <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-600 shadow-sm">
          <Activity size={15} className="text-sky-700" />
          Ultimo aggiornamento: {lastSync || '--:--:--'}
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard icon={<ShieldAlert size={18} />} label="Alert aperti" value={stats?.open_alerts ?? 0} tone="red" />
        <KpiCard icon={<Server size={18} />} label="Client attivi" value={stats?.active_hosts ?? 0} tone="blue" />
        <KpiCard icon={<Cpu size={18} />} label="Metriche raccolte" value={stats?.total_metrics ?? 0} tone="amber" />
        <KpiCard icon={<BellRing size={18} />} label="Telegram" value={botConfigured ? 'online' : 'setup'} tone="emerald" />
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="space-y-6">
          <Panel title="Client in tempo reale" actionHref="/clients" actionLabel="Apri gestione client">
            <div className="grid gap-3">
              {hosts.slice(0, 6).map((host) => {
                const metric = latestMetricByHost.get(host.host_id);
                return (
                  <div key={host.host_id} className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className={`h-2.5 w-2.5 rounded-full ${host.is_active ? 'bg-emerald-500' : 'bg-slate-300'}`} />
                        <span className="font-semibold text-slate-950">{host.host_id}</span>
                      </div>
                      <div className="mt-1 text-xs text-slate-500">Ultimo contatto: {formatDateTime(host.last_seen)}</div>
                    </div>
                    <div className="flex flex-wrap gap-2 text-xs font-semibold">
                      <StatTag icon={<Cpu size={12} />} text={`CPU ${readMetric(metric, ['cpu_percent'])}`} />
                      <StatTag icon={<Activity size={12} />} text={`RAM ${readMetric(metric, ['memory_percent', 'ram_percent'])}`} />
                      <StatTag icon={<HardDrive size={12} />} text={`Disk ${readMetric(metric, ['disk_percent'])}`} />
                    </div>
                  </div>
                );
              })}
            </div>
          </Panel>

          <Panel title="Alert recenti" actionHref="/alerts" actionLabel="Apri triage alert">
            <div className="space-y-3">
              {alerts.length === 0 ? (
                <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-8 text-center text-slate-500">
                  Nessun alert aperto in questo momento.
                </div>
              ) : (
                alerts.map((alert) => (
                  <div key={alert.id} className="rounded-xl border border-slate-200 bg-white px-4 py-4">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <div className="font-semibold text-slate-950">{alert.title}</div>
                        <div className="mt-1 text-sm text-slate-600">{alert.host_id} · {alert.alert_type}</div>
                      </div>
                      <span className={`rounded-full px-3 py-1 text-xs font-semibold ${severityStyle(alert.severity)}`}>
                        {alert.severity}
                      </span>
                    </div>
                    <p className="mt-3 text-sm text-slate-500">{alert.description}</p>
                  </div>
                ))
              )}
            </div>
          </Panel>
        </div>

        <div className="space-y-6">
          <Panel title="Azioni rapide">
            <div className="grid gap-3">
              <QuickLink href="/demo" icon={<Radar size={18} />} title="Demo Live Attacco" description="Simula brute force SSH, malware o scenario CPU anomalo." />
              <QuickLink href="/tickets" icon={<LifeBuoy size={18} />} title="Ticket di assistenza" description="Apri richieste operative per il SOC o per il supporto." />
              <QuickLink href="/settings" icon={<BellRing size={18} />} title="Telegram" description="Configura i chat_id che devono ricevere gli alert." />
            </div>
          </Panel>

          <Panel title="Stato notifiche">
            <div className={`rounded-xl px-4 py-4 ${botConfigured ? 'bg-emerald-50 text-emerald-900' : 'bg-amber-50 text-amber-900'}`}>
              <div className="font-semibold">{botConfigured ? 'Telegram attivo' : 'Telegram da configurare'}</div>
              <p className="mt-2 text-sm opacity-80">
                {botConfigured
                  ? 'Gli alert creati dal backend vengono inoltrati ai chat_id salvati.'
                  : 'Salva almeno un chat_id e verifica TELEGRAM_BOT_TOKEN sul server.'}
              </p>
            </div>
          </Panel>
        </div>
      </section>
    </div>
  );
}

function Panel({
  title,
  children,
  actionHref,
  actionLabel,
}: {
  title: string;
  children: ReactNode;
  actionHref?: string;
  actionLabel?: string;
}) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-panel">
      <div className="mb-4 flex items-center justify-between gap-3">
        <h3 className="text-lg font-semibold text-slate-950">{title}</h3>
        {actionHref && actionLabel ? (
          <Link href={actionHref} className="text-sm font-semibold text-sky-700 hover:text-sky-800">
            {actionLabel}
          </Link>
        ) : null}
      </div>
      {children}
    </section>
  );
}

function KpiCard({
  icon,
  label,
  value,
  tone,
}: {
  icon: ReactNode;
  label: string;
  value: number | string;
  tone: 'red' | 'blue' | 'amber' | 'emerald';
}) {
  const tones = {
    red: 'bg-red-50 text-red-900 border-red-100',
    blue: 'bg-sky-50 text-sky-900 border-sky-100',
    amber: 'bg-amber-50 text-amber-900 border-amber-100',
    emerald: 'bg-emerald-50 text-emerald-900 border-emerald-100',
  };

  return (
    <article className={`rounded-2xl border p-5 shadow-sm ${tones[tone]}`}>
      <div className="flex items-center justify-between gap-3">
        <div className="rounded-xl bg-white/70 p-2">{icon}</div>
        <div className="text-right">
          <div className="text-3xl font-bold">{value}</div>
          <div className="mt-1 text-sm font-medium opacity-80">{label}</div>
        </div>
      </div>
    </article>
  );
}

function QuickLink({
  href,
  icon,
  title,
  description,
}: {
  href: string;
  icon: ReactNode;
  title: string;
  description: string;
}) {
  return (
    <Link href={href} className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-4 transition hover:border-sky-200 hover:bg-sky-50">
      <div className="flex items-center gap-3 text-slate-950">
        <div className="rounded-xl bg-white p-2 text-sky-700 shadow-sm">{icon}</div>
        <div className="font-semibold">{title}</div>
      </div>
      <p className="mt-3 text-sm text-slate-500">{description}</p>
    </Link>
  );
}

function StatTag({ icon, text }: { icon: ReactNode; text: string }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-slate-950 px-2.5 py-1 text-white">
      {icon}
      {text}
    </span>
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

function severityStyle(severity: Alert['severity']) {
  switch (severity) {
    case 'critical':
      return 'bg-red-100 text-red-700';
    case 'high':
      return 'bg-orange-100 text-orange-700';
    case 'medium':
      return 'bg-amber-100 text-amber-700';
    default:
      return 'bg-emerald-100 text-emerald-700';
  }
}
