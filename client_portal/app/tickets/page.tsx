'use client';

import { useEffect, useState } from 'react';
import { getTickets, createTicket, getHosts, updateTicket } from '@/lib/api';
import type { Ticket, Host } from '@/lib/api';
import { Plus, CheckCircle, Clock, Loader2, MessageCircleReply, XCircle } from 'lucide-react';

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
        host_id: (formData.get('host_id') as string) || null,
        priority: formData.get('priority') as 'low' | 'medium' | 'high',
        status: 'open',
        customer_name: (formData.get('customer_name') as string) || null,
        customer_email: (formData.get('customer_email') as string) || null,
        support_response: null,
        internal_notes: null,
        closed_at: null,
        alert_id: null,
      });
      setTickets((prev) => [newTicket, ...prev]);
      setIsModalOpen(false);
    } catch (err) {
      console.error('Errore creazione ticket:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleCloseTicket = async (ticketId: number) => {
    try {
      const updated = await updateTicket(ticketId, { status: 'closed' });
      setTickets((current) => current.map((ticket) => (ticket.id === ticketId ? updated : ticket)));
    } catch (err) {
      console.error('Errore chiusura ticket:', err);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-neutral-900">Ticket di Supporto</h2>
          <p className="text-neutral-500">Apri richieste, leggi le risposte del team e chiudi il ticket quando il problema è risolto.</p>
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
            <div className="p-8 text-center text-neutral-500">Nessun ticket trovato. Aprine uno se hai bisogno di aiuto.</div>
          )}
          {tickets.map((ticket) => (
            <div key={ticket.id} className="p-5 hover:bg-neutral-50 transition-colors">
              <div className="flex items-start justify-between gap-4">
              <div className="flex flex-col gap-1 text-sm text-neutral-500">
                <span className="font-medium text-neutral-900 text-base">{ticket.title}</span>
                <div className="flex items-center gap-4">
                  <span>#{ticket.id}</span>
                  {ticket.host_id && <span>Host: {ticket.host_id}</span>}
                  <span>Aperto il {new Date(ticket.created_at).toLocaleDateString('it-IT')}</span>
                  {ticket.customer_name && <span>Cliente: {ticket.customer_name}</span>}
                </div>
                {ticket.customer_email && <div>{ticket.customer_email}</div>}
              </div>
              <div className="flex items-center gap-3 text-sm font-medium">
                {ticket.priority === 'high' ? (
                  <span className="px-2.5 py-1 bg-red-100 text-red-700 rounded-full">Alta Priorità</span>
                ) : ticket.priority === 'medium' ? (
                  <span className="px-2.5 py-1 bg-amber-100 text-amber-700 rounded-full">Media Priorità</span>
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
              <div className="mt-4 grid gap-3 md:grid-cols-[1fr_auto] md:items-start">
                <div className="rounded-xl border border-neutral-200 bg-neutral-50 px-4 py-3 text-sm text-neutral-700">
                  <div className="font-medium text-neutral-900">La tua richiesta</div>
                  <p className="mt-2 mb-0">{ticket.description}</p>
                  <div className="mt-4 flex items-center gap-2 font-medium text-blue-700">
                    <MessageCircleReply size={16} />
                    Risposta del supporto
                  </div>
                  <p className="mt-2 mb-0 text-neutral-600">{ticket.support_response || 'Nessuna risposta ancora. Il team ti aggiornerà qui.'}</p>
                </div>
                {ticket.status !== 'closed' && (
                  <button
                    onClick={() => void handleCloseTicket(ticket.id)}
                    className="inline-flex items-center gap-2 rounded-lg border border-neutral-300 px-3 py-2 text-sm font-medium text-neutral-700 transition hover:bg-neutral-100"
                  >
                    <XCircle size={16} />
                    Chiudi ticket
                  </button>
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
                <label className="block text-sm font-medium text-neutral-700 mb-1">Nome cliente</label>
                <input
                  name="customer_name" type="text"
                  className="w-full border border-neutral-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
                  placeholder="es. Mario Rossi"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-1">Email cliente</label>
                <input
                  name="customer_email" type="email"
                  className="w-full border border-neutral-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
                  placeholder="es. mario@azienda.it"
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
                  <option value="medium">Media</option>
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
