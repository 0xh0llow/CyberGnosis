'use client';

import { useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import Link from 'next/link';
import { BellRing, LifeBuoy, Loader2, MessageCircleReply, Sparkles } from 'lucide-react';
import { getStats, getTelegramConfigs, getTickets } from '@/lib/api';
import type { Stats, Ticket } from '@/lib/api';

export function ClientOverview() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [botConfigured, setBotConfigured] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [statsPayload, ticketsPayload, telegram] = await Promise.all([
          getStats(),
          getTickets(),
          getTelegramConfigs(),
        ]);

        if (!cancelled) {
          setStats(statsPayload);
          setTickets(ticketsPayload);
          setBotConfigured(telegram.bot_token_configured && telegram.items.length > 0);
        }
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

  const recentTickets = useMemo(() => tickets.slice(0, 5), [tickets]);

  if (loading && !stats) {
    return (
      <div className="flex min-h-80 items-center justify-center gap-2 rounded-2xl border border-slate-200 bg-white text-slate-500 shadow-panel">
        <Loader2 size={18} className="animate-spin" />
        Caricamento portale cliente...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <section className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-950">Portale Clienti</h2>
          <p className="text-sm text-slate-600">Apri ticket, leggi le risposte del supporto e tieni traccia dello stato delle richieste.</p>
        </div>
        <Link href="/tickets" className="inline-flex items-center gap-2 rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800">
          <LifeBuoy size={16} />
          Apri o segui i ticket
        </Link>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <KpiCard icon={<LifeBuoy size={18} />} label="Ticket totali" value={stats?.total_tickets ?? tickets.length} tone="blue" />
        <KpiCard icon={<MessageCircleReply size={18} />} label="Ticket aperti" value={stats?.open_tickets ?? tickets.filter((ticket) => ticket.status !== 'closed').length} tone="amber" />
        <KpiCard icon={<BellRing size={18} />} label="Telegram" value={botConfigured ? 'attivo' : 'da configurare'} tone="emerald" />
      </section>

      <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-panel">
          <div className="mb-4 flex items-center justify-between gap-3">
            <h3 className="text-lg font-semibold text-slate-950">Ultime richieste</h3>
            <Link href="/tickets" className="text-sm font-semibold text-sky-700 hover:text-sky-800">
              Vedi tutto
            </Link>
          </div>

          {recentTickets.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-8 text-center text-slate-500">
              Nessun ticket ancora aperto. Usa il portale per contattare il supporto.
            </div>
          ) : (
            <div className="space-y-3">
              {recentTickets.map((ticket) => (
                <div key={ticket.id} className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <div className="font-semibold text-slate-950">#{ticket.id} · {ticket.title}</div>
                      <div className="mt-1 text-sm text-slate-600">{ticket.customer_name || 'Richiesta cliente'} · {ticket.priority}</div>
                    </div>
                    <span className={`rounded-full px-3 py-1 text-xs font-semibold ${ticket.status === 'closed' ? 'bg-emerald-100 text-emerald-700' : ticket.status === 'in_progress' ? 'bg-sky-100 text-sky-700' : 'bg-amber-100 text-amber-700'}`}>
                      {ticket.status}
                    </span>
                  </div>
                  <p className="mt-3 text-sm text-slate-500">{ticket.support_response || ticket.description}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="space-y-6">
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-panel">
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-sky-100 p-3 text-sky-700">
                <Sparkles size={20} />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-slate-950">Come funziona</h3>
                <p className="text-sm text-slate-600">Il supporto usa una dashboard admin separata per prendere in carico, rispondere e chiudere i ticket.</p>
              </div>
            </div>
          </div>

          <div className={`rounded-2xl border p-5 shadow-panel ${botConfigured ? 'border-emerald-200 bg-emerald-50 text-emerald-900' : 'border-amber-200 bg-amber-50 text-amber-900'}`}>
            <div className="font-semibold">{botConfigured ? 'Telegram configurato' : 'Telegram non configurato'}</div>
            <p className="mt-2 text-sm opacity-90">
              {botConfigured
                ? 'Riceverai notifiche più ricche quando arrivano alert o quando il supporto aggiorna il flusso operativo.'
                : 'Salva almeno un chat_id per ricevere aggiornamenti rapidi via Telegram.'}
            </p>
          </div>
        </div>
      </section>
    </div>
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
  tone: 'blue' | 'amber' | 'emerald';
}) {
  const tones = {
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
