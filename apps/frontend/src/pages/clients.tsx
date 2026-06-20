import Head from 'next/head';
import Layout from '../components/Layout';
import { useClients } from '../hooks/useDashboard';

export default function ClientsPage() {
  const { data, isLoading } = useClients();
  const clients = data ?? [];

  return (
    <Layout>
      <Head>
        <title>My Clients · DealFlow AI</title>
      </Head>
      <section className="space-y-5">
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">My Clients</h1>
            <p className="text-sm text-stone-500">Current and past clients.</p>
          </div>
          <a
            href={`${process.env.NEXT_PUBLIC_API_BASE_URL ?? ''}/api/export/prospects?format=csv`}
            className="rounded-md border border-stone-300 px-3 py-1.5 text-sm text-stone-700 hover:bg-stone-50"
          >
            Export CSV
          </a>
        </header>
        {isLoading && <p className="text-stone-500">Loading…</p>}
        {!isLoading && clients.length === 0 && (
          <p className="rounded-lg border border-stone-200 bg-white p-4 text-sm text-stone-500">
            No clients yet. Prospects appear here once you close them.
          </p>
        )}
        <ul className="space-y-3">
          {clients.map((c) => (
            <li key={c.assignment_id} className="rounded-lg border border-stone-200 bg-white p-4 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="font-medium">{c.business_name}</span>
                <span className="text-xs uppercase tracking-wide text-emerald-700">{c.status}</span>
              </div>
              <p className="mt-1 text-sm text-stone-500">
                {[c.industry, c.owner_name].filter(Boolean).join(' · ')}
              </p>
            </li>
          ))}
        </ul>
      </section>
    </Layout>
  );
}
