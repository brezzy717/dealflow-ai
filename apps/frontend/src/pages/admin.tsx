import Head from 'next/head';
import { useAdminHealth, useAdminModels, useAdminNotifications } from '../hooks/useAdmin';

function Card({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-lg border border-stone-200 bg-white p-4 shadow-sm">
      <div className="text-xl font-semibold">{value}</div>
      <div className="mt-1 text-xs uppercase tracking-wide text-stone-500">{label}</div>
    </div>
  );
}

export default function AdminPage() {
  const health = useAdminHealth();
  const notifications = useAdminNotifications();
  const models = useAdminModels();

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <Head>
        <title>Admin · DealFlow AI</title>
      </Head>
      <header className="border-b border-stone-200 bg-white px-8 py-4">
        <h1 className="text-lg font-bold text-emerald-700">DealFlow AI · Admin</h1>
      </header>
      <main className="mx-auto max-w-6xl space-y-8 px-8 py-8">
        {health.isError && (
          <p className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
            Admin access required (sign in with an admin role).
          </p>
        )}

        <section>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-stone-500">
            Platform health
          </h2>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4 lg:grid-cols-7">
            <Card label="Tenants" value={health.data?.tenants ?? '—'} />
            <Card label="Users" value={health.data?.users ?? '—'} />
            <Card label="Leads" value={health.data?.raw_leads ?? '—'} />
            <Card label="Predictions" value={health.data?.predictions ?? '—'} />
            <Card label="Assignments" value={health.data?.assignments ?? '—'} />
            <Card label="Queued calls" value={health.data?.queued_calls ?? '—'} />
            <Card label="Alerts" value={health.data?.unacknowledged_alerts ?? '—'} />
          </div>
        </section>

        <section>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-stone-500">
            Error feed
          </h2>
          <div className="space-y-2">
            {(notifications.data ?? []).length === 0 && (
              <p className="text-sm text-stone-400">No alerts.</p>
            )}
            {(notifications.data ?? []).map((n) => (
              <div key={n.id} className="rounded-lg border border-stone-200 bg-white p-3 text-sm shadow-sm">
                <span className="mr-2 font-medium uppercase text-rose-600">{n.level}</span>
                {n.message}
              </div>
            ))}
          </div>
        </section>

        <section>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-stone-500">
            Models
          </h2>
          <div className="space-y-2">
            {(models.data ?? []).length === 0 && (
              <p className="text-sm text-stone-400">No model versions yet.</p>
            )}
            {(models.data ?? []).map((m) => (
              <div key={m.id} className="flex items-center justify-between rounded-lg border border-stone-200 bg-white p-3 text-sm shadow-sm">
                <span>
                  {m.model_name} <span className="text-stone-400">{m.version}</span>
                </span>
                {m.is_active && <span className="text-xs font-medium text-emerald-600">ACTIVE</span>}
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
