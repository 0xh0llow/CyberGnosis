'use client';

import { useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { getAlerts, getHosts, simulateAttack } from '@/lib/api';
import type { Alert, Host } from '@/lib/api';
import {
  Activity,
  Bug,
  ChevronRight,
  Cpu,
  Loader2,
  Radar,
  Server,
  ShieldAlert,
  Terminal,
} from 'lucide-react';

type ScenarioId = 'malware' | 'bruteforce' | 'cpu' | 'sast';
type ScenarioSeverity = 'critical' | 'high' | 'medium';

type Scenario = {
  id: ScenarioId;
  name: string;
  headline: string;
  description: string;
  severity: ScenarioSeverity;
  impact: string;
  expectedSignal: string;
  durationLabel: string;
};

type ConsoleEntry = {
  id: number;
  tone: 'info' | 'success' | 'warning' | 'error';
  time: string;
  msg: string;
};

const scenarios: Scenario[] = [
  {
    id: 'malware',
    name: 'Malware Drop',
    headline: 'Payload sospetto sul client',
    description: 'Genera un alert malware dimostrativo ad alta severita` per verificare il triage del SOC.',
    severity: 'critical',
    impact: 'Convalida routing alert, Telegram e presa in carico del team.',
    expectedSignal: 'Alert malware critico con provenance demo nel backend.',
    durationLabel: '20s playbook',
  },
  {
    id: 'bruteforce',
    name: 'SSH Bruteforce',
    headline: 'Burst di autenticazioni fallite',
    description: 'Simula una raffica di tentativi SSH respinti senza eseguire accessi reali sul sistema.',
    severity: 'high',
    impact: 'Verifica visualizzazione IDS e correlazione sugli host monitorati.',
    expectedSignal: 'Alert IDS high con traccia demo associata al client.',
    durationLabel: '15s playbook',
  },
  {
    id: 'cpu',
    name: 'CPU Overload',
    headline: 'Picco anomalo di risorse',
    description: 'Inietta un evento di saturazione CPU sintetico per testare anomaly detection e osservabilita`.',
    severity: 'high',
    impact: 'Ottimo per demo cliente e controllo pannello metriche.',
    expectedSignal: 'Alert performance high visibile in alerts e overview.',
    durationLabel: '12s playbook',
  },
  {
    id: 'sast',
    name: 'Weak Code Signal',
    headline: 'Pattern di codice vulnerabile',
    description: 'Produce un alert di code scanning per mostrare credenziali hardcoded o pratiche insicure.',
    severity: 'medium',
    impact: 'Dimostra la catena dal code scanner al ticket operativo.',
    expectedSignal: 'Alert code con metadata demo consultabile dal portale.',
    durationLabel: '18s playbook',
  },
];

export default function DemoPage() {
  const [hosts, setHosts] = useState<Host[]>([]);
  const [selectedHost, setSelectedHost] = useState('');
  const [activeScenario, setActiveScenario] = useState<ScenarioId>('malware');
  const [runningScenario, setRunningScenario] = useState<ScenarioId | null>(null);
  const [loading, setLoading] = useState(true);
  const [demoAlerts, setDemoAlerts] = useState<Alert[]>([]);
  const [logs, setLogs] = useState<ConsoleEntry[]>([]);
  const [banner, setBanner] = useState('');

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [nextHosts, nextAlerts] = await Promise.all([
          getHosts(),
          getAlerts('limit=40'),
        ]);

        if (cancelled) return;
        setHosts(nextHosts);
        if (nextHosts.length > 0) {
          setSelectedHost((current) => current || nextHosts[0].host_id);
        }
        setDemoAlerts(
          nextAlerts.filter((alert) => alert.alert_metadata?.source === 'demo').slice(0, 8),
        );
      } catch (error) {
        console.error(error);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const selectedScenario = scenarios.find((scenario) => scenario.id === activeScenario) ?? scenarios[0];
  const selectedHostLabel = selectedHost || 'demo-host automatico';

  function addLog(msg: string, tone: ConsoleEntry['tone'] = 'info') {
    setLogs((prev) => [
      ...prev,
      {
        id: prev.length + 1,
        tone,
        time: new Date().toLocaleTimeString('it-IT'),
        msg,
      },
    ]);
  }

  async function refreshDemoAlerts() {
    try {
      const nextAlerts = await getAlerts('limit=40');
      setDemoAlerts(
        nextAlerts.filter((alert) => alert.alert_metadata?.source === 'demo').slice(0, 8),
      );
    } catch (error) {
      console.error(error);
    }
  }

  function wait(ms: number) {
    return new Promise((resolve) => window.setTimeout(resolve, ms));
  }

  async function runScenario(scenario: Scenario) {
    setRunningScenario(scenario.id);
    setBanner('');
    addLog(`[ARM] Scenario ${scenario.name} preparato per host ${selectedHostLabel}.`);
    try {
      addLog('[SAFE] Modalita` demo: vengono creati eventi sintetici, non attivita` offensive reali.');
      await wait(500);
      addLog(`[SYNC] Invio playbook ${scenario.id} verso il central server...`);
      await wait(700);

      const result = await simulateAttack(scenario.id, selectedHost || undefined);

      addLog(`[DETECT] Alert ${result.alert.id} creato con severity ${result.alert.severity}.`, 'success');
      await wait(600);
      addLog(`[ROUTE] Host ${result.host_id} aggiornato e pronto per triage in /alerts.`, 'success');
      setBanner(`Scenario ${scenario.name} eseguito su ${result.host_id}.`);
      await refreshDemoAlerts();
    } catch (error) {
      console.error(error);
      addLog('[FAIL] Simulazione non riuscita. Controlla central_server e token del proxy.', 'error');
      setBanner('Esecuzione fallita: verifica API e connettivita` del backend.');
    } finally {
      setRunningScenario(null);
    }
  }

  return (
    <div className="space-y-6">
      <section className="overflow-hidden rounded-[28px] border border-slate-200 bg-[linear-gradient(135deg,_rgba(15,23,42,0.98)_0%,_rgba(30,41,59,0.96)_50%,_rgba(12,74,110,0.9)_100%)] p-6 text-white shadow-panel">
        <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.22em] text-sky-100">
              <Radar size={14} />
              Demo Lab
            </div>
            <div>
              <h2 className="text-3xl font-bold tracking-tight">Pagina separata per simulare incidenti client</h2>
              <p className="mt-3 max-w-2xl text-sm text-slate-200">
                Qui pilotiamo scenari demo come malware, overload CPU e SSH bruteforce in modo controllato:
                il backend genera alert sintetici per mostrare detection, ticketing e notifiche senza eseguire attivita` offensive reali.
              </p>
            </div>
            <div className="flex flex-wrap gap-3 text-sm">
              <StatusPill icon={<ShieldAlert size={14} />} label="Alert demo reali nel DB" />
              <StatusPill icon={<Server size={14} />} label={`Target: ${selectedHostLabel}`} />
              <StatusPill icon={<Activity size={14} />} label={`${demoAlerts.length} alert demo recenti`} />
            </div>
          </div>

          <div className="rounded-3xl border border-white/12 bg-white/10 p-5 backdrop-blur">
            <div className="text-sm font-semibold text-sky-100">Host di destinazione</div>
            <p className="mt-2 text-sm text-slate-200">
              Seleziona un client monitorato. Se la lista e` vuota, il server usera` un host demo di fallback.
            </p>

            {loading ? (
              <div className="mt-5 inline-flex items-center gap-2 text-sm text-slate-200">
                <Loader2 size={16} className="animate-spin" />
                Caricamento host...
              </div>
            ) : (
              <select
                value={selectedHost}
                onChange={(event) => setSelectedHost(event.target.value)}
                className="mt-5 w-full rounded-2xl border border-white/15 bg-slate-950/50 px-4 py-3 text-sm text-white outline-none transition focus:border-sky-400"
              >
                <option value="">Usa host demo automatico</option>
                {hosts.map((host) => (
                  <option key={host.host_id} value={host.host_id}>
                    {host.host_id} · {host.is_active ? 'online' : 'offline'}
                  </option>
                ))}
              </select>
            )}

            {banner ? (
              <div className="mt-4 rounded-2xl border border-emerald-400/25 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-100">
                {banner}
              </div>
            ) : (
              <div className="mt-4 rounded-2xl border border-white/10 bg-slate-950/35 px-4 py-3 text-sm text-slate-200">
                Playbook attivo: <span className="font-semibold text-white">{selectedScenario.name}</span>
              </div>
            )}
          </div>
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-6">
          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-panel">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div>
                <h3 className="text-lg font-semibold text-slate-950">Scenari disponibili</h3>
                <p className="text-sm text-slate-500">Ogni azione crea un alert demo lato server e aggiorna il portale.</p>
              </div>
              {runningScenario ? (
                <span className="inline-flex items-center gap-2 rounded-full bg-sky-100 px-3 py-1 text-xs font-semibold text-sky-800">
                  <Loader2 size={13} className="animate-spin" />
                  In esecuzione
                </span>
              ) : null}
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              {scenarios.map((scenario) => {
                const selected = scenario.id === activeScenario;
                const running = scenario.id === runningScenario;
                return (
                  <article
                    key={scenario.id}
                    className={`rounded-2xl border p-4 transition ${
                      selected
                        ? 'border-sky-300 bg-sky-50'
                        : 'border-slate-200 bg-slate-50 hover:border-slate-300'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className={`rounded-2xl p-3 ${iconWrapClass(scenario.id)}`}>
                        {scenarioIcon(scenario.id)}
                      </div>
                      <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${severityBadgeClass(scenario.severity)}`}>
                        {scenario.severity}
                      </span>
                    </div>

                    <div className="mt-4">
                      <h4 className="text-base font-semibold text-slate-950">{scenario.name}</h4>
                      <p className="mt-1 text-sm font-medium text-slate-700">{scenario.headline}</p>
                      <p className="mt-3 text-sm leading-6 text-slate-500">{scenario.description}</p>
                    </div>

                    <div className="mt-4 space-y-2 text-sm text-slate-600">
                      <div><span className="font-semibold text-slate-800">Segnale atteso:</span> {scenario.expectedSignal}</div>
                      <div><span className="font-semibold text-slate-800">Uso:</span> {scenario.impact}</div>
                    </div>

                    <div className="mt-5 flex flex-wrap items-center justify-between gap-3">
                      <span className="inline-flex items-center gap-2 rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-600">
                        <ChevronRight size={12} />
                        {scenario.durationLabel}
                      </span>
                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={() => setActiveScenario(scenario.id)}
                          className={`rounded-xl px-3 py-2 text-sm font-semibold transition ${
                            selected
                              ? 'bg-white text-slate-950 shadow-sm'
                              : 'bg-transparent text-slate-600 hover:bg-white'
                          }`}
                        >
                          Dettagli
                        </button>
                        <button
                          type="button"
                          disabled={runningScenario !== null}
                          onClick={() => void runScenario(scenario)}
                          className={`inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition ${
                            running
                              ? 'bg-sky-600 text-white'
                              : runningScenario !== null
                              ? 'cursor-not-allowed bg-slate-200 text-slate-400'
                              : 'bg-slate-950 text-white hover:bg-slate-800'
                          }`}
                        >
                          {running ? <Loader2 size={15} className="animate-spin" /> : scenarioIcon(scenario.id)}
                          Esegui
                        </button>
                      </div>
                    </div>
                  </article>
                );
              })}
            </div>
          </section>

          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-panel">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div>
                <h3 className="text-lg font-semibold text-slate-950">Scenario selezionato</h3>
                <p className="text-sm text-slate-500">Vista rapida del playbook che andra` in esecuzione.</p>
              </div>
              <span className={`rounded-full px-3 py-1 text-xs font-semibold ${severityBadgeClass(selectedScenario.severity)}`}>
                {selectedScenario.severity}
              </span>
            </div>

            <div className="grid gap-4 lg:grid-cols-[0.95fr_1.05fr]">
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
                <div className={`inline-flex rounded-2xl p-3 ${iconWrapClass(selectedScenario.id)}`}>
                  {scenarioIcon(selectedScenario.id)}
                </div>
                <h4 className="mt-4 text-xl font-semibold text-slate-950">{selectedScenario.name}</h4>
                <p className="mt-2 text-sm text-slate-600">{selectedScenario.headline}</p>
                <p className="mt-4 text-sm leading-6 text-slate-500">{selectedScenario.description}</p>
              </div>

              <div className="grid gap-3">
                <InfoCard title="Host target" value={selectedHostLabel} />
                <InfoCard title="Segnale atteso" value={selectedScenario.expectedSignal} />
                <InfoCard title="Valore demo" value={selectedScenario.impact} />
                <InfoCard title="Modalita`" value="Simulazione controllata con alert sintetico creato dal central_server." />
              </div>
            </div>
          </section>
        </div>

        <div className="space-y-6">
          <section className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-950 shadow-panel">
            <div className="flex items-center gap-2 border-b border-slate-800 bg-slate-950 px-4 py-3">
              <Terminal size={16} className="text-slate-400" />
              <span className="text-xs font-mono font-semibold uppercase tracking-[0.18em] text-slate-300">
                demo_console // client attack lab
              </span>
            </div>
            <div className="h-[360px] space-y-2 overflow-auto p-4 font-mono text-xs">
              {logs.length === 0 ? (
                <div className="text-slate-500">Nessuna simulazione avviata. Premi Esegui su uno scenario.</div>
              ) : (
                logs.map((log) => (
                  <div key={log.id} className={`leading-6 ${logToneClass(log.tone)}`}>
                    <span className="text-slate-500">[{log.time}]</span> {log.msg}
                  </div>
                ))
              )}
            </div>
          </section>

          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-panel">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div>
                <h3 className="text-lg font-semibold text-slate-950">Alert demo recenti</h3>
                <p className="text-sm text-slate-500">Cronologia sintetica degli ultimi eventi creati da questa pagina.</p>
              </div>
              <button
                type="button"
                onClick={() => void refreshDemoAlerts()}
                className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-100"
              >
                Aggiorna
              </button>
            </div>

            {demoAlerts.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-4 py-8 text-center text-sm text-slate-500">
                Nessun alert demo ancora presente.
              </div>
            ) : (
              <div className="space-y-3">
                {demoAlerts.map((alert) => (
                  <article key={alert.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="font-semibold text-slate-950">{alert.title}</div>
                        <div className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-500">
                          {alert.host_id} · {alert.alert_type}
                        </div>
                      </div>
                      <span className={`rounded-full px-3 py-1 text-xs font-semibold ${severityBadgeClass(alert.severity)}`}>
                        {alert.severity}
                      </span>
                    </div>
                    <p className="mt-3 text-sm text-slate-600">{alert.description}</p>
                    <div className="mt-3 text-xs text-slate-500">
                      {formatDateTime(alert.created_at)} · source: {String(alert.alert_metadata?.source ?? 'n/d')}
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>
        </div>
      </section>
    </div>
  );
}

function InfoCard({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
      <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{title}</div>
      <div className="mt-2 text-sm font-medium text-slate-900">{value}</div>
    </div>
  );
}

function StatusPill({ icon, label }: { icon: ReactNode; label: string }) {
  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/10 px-3 py-1.5 text-xs font-medium text-slate-100">
      {icon}
      {label}
    </span>
  );
}

function scenarioIcon(id: ScenarioId) {
  switch (id) {
    case 'malware':
      return <Bug size={18} />;
    case 'bruteforce':
      return <Terminal size={18} />;
    case 'cpu':
      return <Cpu size={18} />;
    case 'sast':
      return <ShieldAlert size={18} />;
  }
}

function iconWrapClass(id: ScenarioId) {
  switch (id) {
    case 'malware':
      return 'bg-red-100 text-red-700';
    case 'bruteforce':
      return 'bg-sky-100 text-sky-700';
    case 'cpu':
      return 'bg-amber-100 text-amber-700';
    case 'sast':
      return 'bg-emerald-100 text-emerald-700';
  }
}

function severityBadgeClass(severity: Alert['severity'] | ScenarioSeverity) {
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

function logToneClass(tone: ConsoleEntry['tone']) {
  switch (tone) {
    case 'success':
      return 'text-emerald-300';
    case 'warning':
      return 'text-amber-300';
    case 'error':
      return 'text-red-300';
    default:
      return 'text-sky-200';
  }
}

function formatDateTime(value?: string | null) {
  if (!value) return 'n/d';
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? 'n/d' : parsed.toLocaleString('it-IT');
}
