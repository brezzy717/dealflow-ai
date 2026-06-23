import Link from 'next/link';
import { useRouter } from 'next/router';
import { PropsWithChildren } from 'react';

const NAV: { href: string; label: string }[] = [
  { href: '/', label: 'Home' },
  { href: '/prospects', label: 'Prospects' },
  { href: '/appointments', label: 'Appointments' },
  { href: '/clients', label: 'My Clients' },
  { href: '/deal-room', label: 'Deal Room' },
  { href: '/pipeline', label: 'PipeDeal' },
  { href: '/tasks', label: 'Tasks' },
  { href: '/vault', label: 'Vault' },
  { href: '/reports', label: 'Reports' },
  { href: '/settings', label: 'Settings' }
];

export default function Layout({ children }: PropsWithChildren) {
  const router = useRouter();
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <div className="flex">
        <aside className="hidden min-h-screen w-56 shrink-0 border-r border-stone-200 bg-white px-4 py-6 md:block">
          <div className="px-2 text-lg font-bold tracking-tight text-emerald-700">DealFlow AI</div>
          <nav className="mt-8 space-y-1">
            {NAV.map((item) => {
              const active = router.pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`block rounded-md px-3 py-2 text-sm font-medium ${
                    active
                      ? 'bg-emerald-50 text-emerald-800'
                      : 'text-stone-600 hover:bg-stone-50 hover:text-stone-900'
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </aside>
        <main className="mx-auto w-full max-w-5xl px-6 py-10">{children}</main>
      </div>
      {/* Aria assistant widget (placeholder; wired in a later phase). */}
      <button
        type="button"
        aria-label="Open Aria assistant"
        className="fixed bottom-6 left-6 h-12 w-12 rounded-full bg-emerald-600 text-white shadow-lg hover:bg-emerald-700"
      >
        ✦
      </button>
    </div>
  );
}
