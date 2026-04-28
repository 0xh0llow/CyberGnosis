'use client';

import type { ReactNode } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export function NavLink({
  href,
  label,
  icon,
}: {
  href: string;
  label: string;
  icon: ReactNode;
}) {
  const pathname = usePathname();
  const isActive = href === '/' ? pathname === href : pathname.startsWith(href);

  return (
    <Link
      href={href}
      aria-current={isActive ? 'page' : undefined}
      className={[
        'inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium transition-colors',
        isActive
          ? 'bg-slate-950 text-white shadow-sm'
          : 'text-slate-600 hover:bg-slate-100 hover:text-slate-950',
      ].join(' ')}
    >
      {icon}
      {label}
    </Link>
  );
}
