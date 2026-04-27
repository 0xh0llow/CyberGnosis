'use client';

import { useEffect, useState } from 'react';
import { getTickets, createTicket, getHosts } from '@/lib/api';
import type { Ticket, Host } from '@/lib/api';
import { MessageSquare, Plus, CheckCircle, Clock, Loader2 } from 'lucide-react';

export default function TicketsPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [hosts, setHosts] = useState<Host[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    Promise.all([getTickets(), getHosts()])
      .then(([t, h]) => { setTickets(t); setHosts(h); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleCreateTicket = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    const formData = new FormData(e.target as HTMLFormElement);
    try {
      const newTicket = await createTicket({
        title: formData.get('title') as string,
        description: formData.get('description') as string,
        priority: formData.get('priority') as 'low' | 'medium' | 'high',
        status: 'open',
      });
      setTickets((prev) => [newTicket, ...prev]);
      setIsModalOpen(false);
    } catch (err) {
      console.error('Errore creazione ticket:', err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-neutral-900">Ticket di Supporto</h2>
          <p className="text-neutral-500">Contatta i nostri esperti di sicurezza per ricevere assistenza.</p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
        >
          <Plus size={18} /> Apri Nuovo Ticket
        </button>
      </div>

      <div className="bg-white border border-neutral-200 rounded-xl overflow-hidden shadow-sm">
        <div className="divide-y divide-neutral-200">
          {loading && (
            <div className="p-8 text-center text-neutral-400 flex items-center justify-center gap-2">
              <Loader2 size={18} className="animate-spin" /> Caricamento ticket...
            </div>
          )}
          {!loading && tickets.length === 0 && (
            <div className="p-8 text-center text-neutral-500">Nessun ticket trovato. Aprине uno se hai bisogno di aiuto.</div>
          )}
          {tickets.map((ticket) => (
            <div key={ticket.id} className="p-5 flex items-center justify-between hover:bg-neutral-50 transition-colors">
              <div className="flex flex-col gap-1 text-sm text-neutral-500">
                <span className="font-medium text-neutral-900 text-base">{ticket.title}</span>
                <div className="flex items-center gap-4">
                  <span>{ticket.id}</span>
                  <span>Aperto il {new Date(ticket.created_at).toLocaleDateString('it-IT')}</span>
                </div>
              </div>
              <div className="flex items-center gap-3 text-sm font-medium">
                {ticket.priority === 'high' ? (
                  <span className="px-2.5 py-1 bg-red-100 text-red-700 rounded-full">Alta Priorità</span>
                ) : (
                  <span className="px-2.5 py-1 bg-neutral-100 text-neutral-700 rounded-full">Standard</span>
                )}
                {ticket.status === 'open' || ticket.status === 'in_progress' ? (
                  <span className="flex items-center gap-1.5 text-amber-600"><Clock size={16} /> Aperto</span>
                ) : (
                  <span className="flex items-center gap-1.5 text-emerald-600"><CheckCircle size={16} /> Risolto</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
            <h3 className="text-xl font-bold mb-4">Apri un Ticket</h3>
            <form onSubmit={handleCreateTicket} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-1">Titolo</label>
                <input
                  required name="title" type="text"
                  className="w-full border border-neutral-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
                  placeholder="es. Il server Database è lento"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-1">Host (Opzionale)</label>
                <select name="host_id" className="w-full border border-neutral-300 rounded-lg px-3 py-2 bg-white outline-none">
                  <option value="">-- Seleziona Host --</option>
                  {hosts.map((h) => (
                    <option key={h.host_id} value={h.host_id}>{h.host_id}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-1">Priorità</label>
                <select name="priority" className="w-full border border-neutral-300 rounded-lg px-3 py-2 bg-white outline-none">
                  <option value="low">Standard</option>
                  <option value="high">Alta (Urgente)</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-1">Descrizione</label>
                <textarea
                  required name="description" rows={4}
                  className="w-full border border-neutral-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
                  placeholder="Descrivi cosa sta succedendo..."
                />
              </div>
              <div className="flex gap-3 justify-end mt-6">
                <button type="button" onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-lg text-neutral-600 hover:bg-neutral-100 font-medium transition-colors">
                  Annulla
                </button>
                <button type="submit" disabled={submitting}
                  className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 font-medium transition-colors flex items-center gap-2 disabled:opacity-60">
                  {submitting && <Loader2 size={16} className="animate-spin" />}
                  Invia Ticket
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
