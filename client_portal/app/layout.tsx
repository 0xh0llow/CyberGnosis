import type { Metadata } from 'next';
import Link from 'next/link';
import type { ReactNode } from 'react';
import { Shield, Activity, BellRing, LifeBuoy, Radar } from 'lucide-react';
import { NavLink } from '@/components/nav-link';
import './globals.css';

const appName = process.env.NEXT_PUBLIC_APP_NAME ?? 'CyberGnosis';

export const metadata: Metadata = {
  title: `${appName} Portal`,
  description: 'Portale clienti CyberGnosis per aprire ticket e seguire le risposte del supporto.',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="it">
      <body className="min-h-screen bg-slate-100 text-slate-950 antialiased">
        <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(14,165,233,0.12),_transparent_38%),linear-gradient(180deg,_#f8fafc_0%,_#eef2ff_100%)]">
          <header className="border-b border-slate-200/80 bg-white/80 backdrop-blur">
            <div className="mx-auto flex max-w-6xl items-center justify-between gap-6 px-4 py-4 sm:px-6">
              <Link href="/" className="flex items-center gap-3 text-slate-950">
                <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-slate-950 text-white shadow-sm">
                  <Shield size={20} />
                </span>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-sky-700">Client Portal</p>
                  <h1 className="text-lg font-semibold">{appName}</h1>
                </div>
              </Link>

              <nav className="flex flex-wrap items-center gap-2 rounded-2xl border border-slate-200 bg-white/90 p-1.5 shadow-sm">
                <NavLink href="/" label="Overview" icon={<Activity size={16} />} />
                <NavLink href="/demo" label="Demo Lab" icon={<Radar size={16} />} />
                <NavLink href="/tickets" label="Tickets" icon={<LifeBuoy size={16} />} />
                <NavLink href="/settings" label="Telegram" icon={<BellRing size={16} />} />
              </nav>
            </div>
          </header>

          <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
