'use client';

import { useEffect, useState } from 'react';
import { getHosts, simulateAttack } from '@/lib/api';
import type { Host } from '@/lib/api';
import { Target, Terminal, ShieldAlert, Cpu, Code, Loader2 } from 'lucide-react';

export default function DemoPage() {
  const [hosts, setHosts] = useState<Host[]>([]);
  const [selectedHost, setSelectedHost] = useState('');
  const [attacking, setAttacking] = useState<string | null>(null);
  const [logs, setLogs] = useState<{ time: string; msg: string }[]>([]);

  useEffect(() => {
    getHosts().then((h) => {
      setHosts(h);
      if (h.length > 0) setSelectedHost(h[0].host_id);
    }).catch(console.error);
  }, []);

  const addLog = (msg: string) =>
    setLogs((prev) => [...prev, { time: new Date().toLocaleTimeString('it-IT'), msg }]);

  const runAttack = async (attackId: string, attackName: string) => {
    if (!selectedHost) return;
    setAttacking(attackId);
    addLog(`[INIT] Avvio simulazione "${attackName}" su ${selectedHost}...`);

    try {
      setTimeout(() => addLog(`[ACTIVE] Iniezione payload all'agent su ${selectedHost}...`), 1200);
      setTimeout(() => addLog(`[DETECT] Il Server Centrale SOC ha rilevato un'anomalia.`), 2800);

      await simulateAttack(attackId);

      setTimeout(() => {
        addLog(`[ALERT] Alert registrato nel DB — controllalo nella sezione Overview.`);
        addLog(`[DONE] Simulazione completata.`);
        setAttacking(null);
      }, 3500);
    } catch {
      addLog(`[ERROR] Endpoint /api/simulate-attack non ancora implementato sul server.`);
      addLog(`[INFO] Aggiungi la rotta FastAPI per abilitare la demo reale.`);
      setAttacking(null);
    }
  };

  const attacks = [
    { id: 'malware',    name: 'Lancio Malware',       desc: 'Simula il rilascio di un file con firma sospetta.',         icon: <ShieldAlert size={20} className="text-red-500" /> },
    { id: 'bruteforce', name: 'Bruteforce SSH',        desc: 'Simula tentativi di login SSH falliti in rapida successione.', icon: <Terminal size={20} className="text-blue-500" /> },
    { id: 'cpu',        name: 'Picco CPU (Crypto)',    desc: 'Crea un picco artificiale di CPU per innescare il modello anomalie.', icon: <Cpu size={20} className="text-amber-500" /> },
    { id: 'sast',       name: 'Codice Vulnerabile',   desc: 'Rilascia un file con credenziali hardcoded per il code scanner.', icon: <Code size={20} className="text-emerald-500" /> },
  ];

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h2 className="text-2xl font-bold text-neutral-900">Demo Live / Simulatore</h2>
        <p className="text-neutral-500">Testa gli agent CyberGnosis simulando attacchi sui client connessi.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">

          {/* Step 1 — seleziona host reale */}
          <div className="bg-white border border-neutral-200 rounded-xl p-6 shadow-sm">
            <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
              <Target size={20} className="text-neutral-500" />
              Passo 1: Seleziona Host Destinazione
            </h3>
            {hosts.length === 0 ? (
              <p className="text-sm text-neutral-400">Nessun host registrato. Avvia un agente client per vedere gli host qui.</p>
            ) : (
              <select
                value={selectedHost}
                onChange={(e) => setSelectedHost(e.target.value)}
                className="w-full border border-neutral-300 rounded-lg px-4 py-3 outline-none focus:ring-2 focus:ring-blue-500 bg-neutral-50 text-neutral-900 font-medium"
              >
                {hosts.map((h) => (
                  <option key={h.host_id} value={h.host_id}>
                    {h.host_id} — {h.is_active ? '🟢 online' : '🔴 offline'}
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Step 2 — scegli attacco */}
          <div className="bg-white border border-neutral-200 rounded-xl p-6 shadow-sm">
            <h3 className="font-bold text-lg mb-4">Passo 2: Scegli Scenario di Attacco</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {attacks.map((attack) => (
                <div
                  key={attack.id}
                  className={`border rounded-xl p-4 flex flex-col justify-between transition-all ${
                    attacking === attack.id ? 'border-blue-500 bg-blue-50/50' : 'border-neutral-200 hover:border-blue-300 bg-white'
                  }`}
                >
                  <div>
                    <div className="flex items-center gap-3 mb-2">
                      <div className="p-2 bg-neutral-50 border border-neutral-100 rounded-lg">{attack.icon}</div>
                      <h4 className="font-bold text-neutral-900">{attack.name}</h4>
                    </div>
                    <p className="text-sm text-neutral-500 mb-4">{attack.desc}</p>
                  </div>
                  <button
                    disabled={attacking !== null || hosts.length === 0}
                    onClick={() => runAttack(attack.id, attack.name)}
                    className={`w-full py-2 rounded-lg font-medium flex items-center justify-center gap-2 transition-colors ${
                      attacking === attack.id
                        ? 'bg-blue-600 text-white'
                        : attacking !== null || hosts.length === 0
                        ? 'bg-neutral-100 text-neutral-400 cursor-not-allowed'
                        : 'bg-neutral-900 hover:bg-neutral-800 text-white'
                    }`}
                  >
                    {attacking === attack.id ? (
                      <><Loader2 size={16} className="animate-spin" /> Simulazione...</>
                    ) : 'Avvia Simulazione'}
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Console */}
        <div className="bg-neutral-900 rounded-xl overflow-hidden flex flex-col border border-neutral-800 shadow-lg h-[500px]">
          <div className="bg-neutral-950 px-4 py-3 border-b border-neutral-800 flex items-center gap-2">
            <Terminal size={16} className="text-neutral-400" />
            <span className="text-xs font-mono text-neutral-300 font-medium tracking-wider">ATTACK_CONSOLE // CYBERGNOSIS</span>
          </div>
          <div className="p-4 overflow-auto flex-1 font-mono text-xs text-green-400 space-y-2">
            {logs.length === 0 ? (
              <div className="text-neutral-600">In attesa dell'innesco della simulazione...</div>
            ) : (
              logs.map((log, i) => (
                <div key={i} className="leading-relaxed">
                  <span className="text-neutral-500">[{log.time}]</span> {log.msg}
                </div>
              ))
            )}
            {attacking && (
              <div className="flex items-center gap-2 text-neutral-500 animate-pulse mt-4">
                <span className="w-2 h-4 bg-neutral-500 inline-block" /> Esecuzione in corso
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
