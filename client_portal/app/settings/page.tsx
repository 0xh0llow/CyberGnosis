'use client';

import { useEffect, useState } from 'react';
import { getTelegramConfigs, saveTelegramConfig } from '@/lib/api';
import type { TelegramConfig } from '@/lib/api';
import { BellRing, Loader2, MessageSquareShare, Save } from 'lucide-react';

export default function SettingsPage() {
  const [chatId, setChatId] = useState('');
  const [items, setItems] = useState<TelegramConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [botConfigured, setBotConfigured] = useState(false);

  useEffect(() => {
    void loadConfigs();
  }, []);

  async function loadConfigs() {
    try {
      const response = await getTelegramConfigs();
      setItems(response.items);
      setBotConfigured(response.bot_token_configured);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setMessage('');

    try {
      const response = await saveTelegramConfig(chatId);
      setMessage(response.bot_token_configured
        ? 'Chat salvata. Le notifiche Telegram sugli alert ora sono attive.'
        : 'Chat salvata, ma manca TELEGRAM_BOT_TOKEN nel server.');
      setChatId('');
      await loadConfigs();
    } catch (error) {
      console.error(error);
      setMessage('Salvataggio non riuscito. Controlla il formato del chat_id.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-panel">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-sky-100 p-3 text-sky-700">
            <BellRing size={20} />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-slate-950">Notifiche Telegram</h2>
            <p className="text-sm text-slate-600">Salva uno o piu` `chat_id` per ricevere alert e aggiornamenti operativi con messaggi Telegram piu` ricchi.</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <label className="block space-y-2 text-sm font-medium text-slate-700">
            <span>Chat ID</span>
            <input
              required
              value={chatId}
              onChange={(event) => setChatId(event.target.value)}
              placeholder="es. 123456789 o -100..."
              className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-sky-400 focus:bg-white"
            />
          </label>

          <div className="flex flex-wrap items-center gap-3">
            <button
              type="submit"
              disabled={saving}
              className="inline-flex items-center gap-2 rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:opacity-60"
            >
              {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
              Salva destinazione
            </button>
            <span className={`rounded-full px-3 py-1 text-xs font-semibold ${botConfigured ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>
              {botConfigured ? 'Bot configurato' : 'Bot non configurato'}
            </span>
          </div>

          {message && <p className="text-sm text-slate-600">{message}</p>}
        </form>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-panel">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-slate-100 p-3 text-slate-700">
            <MessageSquareShare size={20} />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-slate-950">Destinazioni attive</h3>
            <p className="text-sm text-slate-600">Queste chat verranno usate per le notifiche degli alert.</p>
          </div>
        </div>

        {loading ? (
          <div className="mt-8 flex items-center gap-2 text-sm text-slate-500">
            <Loader2 size={16} className="animate-spin" />
            Caricamento configurazione...
          </div>
        ) : items.length === 0 ? (
          <div className="mt-8 rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-8 text-center text-sm text-slate-500">
            Nessun chat_id configurato.
          </div>
        ) : (
          <div className="mt-6 space-y-3">
            {items.map((item) => (
              <div key={item.id} className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
                <div className="font-mono text-sm text-slate-900">{item.chat_id}</div>
                <div className="mt-1 text-xs text-slate-500">Salvato il {new Date(item.created_at).toLocaleString('it-IT')}</div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
