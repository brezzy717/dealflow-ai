import Head from 'next/head';
import Link from 'next/link';
import Layout from '../components/Layout';
import { useMetrics } from '../hooks/useDashboard';

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-xl border border-stone-200 bg-white p-5 shadow-sm">
      <div className="text-2xl font-semibold text-stone-900">{value}</div>
      <div className="mt-1 text-sm text-stone-500">{label}</div>
    </div>
  );
}

export default function Home() {
  const { data, isLoading, isError } = useMetrics();
  const pct = (n: number | undefined) => (n != null ? `${Math.round(n * 100)}%` : '—');

  return (
    <Layout>
      <Head>
        <title>DealFlow AI Dashboard</title>
      </Head>
      <section className="space-y-6">
        <header>
          <h1 className="text-2xl font-semibold">Welcome back</h1>
          <p className="text-sm text-stone-500">Your pipeline at a glance.</p>
        </header>

        {isError && (
          <p className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
            Sign in and start the API to load your metrics.
          </p>
        )}

        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <Stat label="Active prospects" value={isLoading ? '—' : data?.prospects ?? 0} />
          <Stat label="Clients" value={isLoading ? '—' : data?.clients ?? 0} />
          <Stat label="Appointments" value={isLoading ? '—' : data?.appointments ?? 0} />
          <Stat label="Closed deals" value={isLoading ? '—' : data?.closed_deals ?? 0} />
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Stat label="Prospect → appointment" value={pct(data?.prospect_to_appointment_rate)} />
          <Stat label="Appointment → close" value={pct(data?.appointment_to_close_rate)} />
        </div>

        <div className="rounded-xl border border-stone-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-medium">Jump in</h2>
          <ul className="mt-3 space-y-1 text-sm">
            <li>
              <Link href="/prospects" className="text-emerald-700 hover:underline">
                Work your prospects →
              </Link>
            </li>
            <li>
              <Link href="/appointments" className="text-emerald-700 hover:underline">
                Review upcoming appointments →
              </Link>
            </li>
            <li>
              <Link href="/reports" className="text-emerald-700 hover:underline">
                Drill into your reports →
              </Link>
            </li>
          </ul>
        </div>
      </section>
    </Layout>
  );
}
