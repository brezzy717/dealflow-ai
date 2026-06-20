import Head from 'next/head';
import Layout from '../components/Layout';
import { useReports } from '../hooks/useDashboard';

function Breakdown({ title, data }: { title: string; data: Record<string, number> }) {
  const entries = Object.entries(data);
  return (
    <div className="rounded-xl border border-stone-200 bg-white p-5 shadow-sm">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-stone-500">{title}</h2>
      {entries.length === 0 ? (
        <p className="mt-2 text-sm text-stone-400">No data yet.</p>
      ) : (
        <ul className="mt-3 space-y-1 text-sm">
          {entries.map(([k, v]) => (
            <li key={k} className="flex items-center justify-between">
              <span className="capitalize text-stone-700">{k}</span>
              <span className="font-medium">{v}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function ReportsPage() {
  const { data, isLoading } = useReports();

  return (
    <Layout>
      <Head>
        <title>Reports · DealFlow AI</title>
      </Head>
      <section className="space-y-5">
        <header>
          <h1 className="text-2xl font-semibold">Reports</h1>
          <p className="text-sm text-stone-500">Conversion, tier mix, and sector breakdowns.</p>
        </header>
        {isLoading && <p className="text-stone-500">Loading…</p>}
        {data && (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <Breakdown title="By tier" data={data.by_tier} />
            <Breakdown title="Top industries" data={data.top_industries} />
            <Breakdown title="Deal outcomes" data={data.outcomes} />
          </div>
        )}
      </section>
    </Layout>
  );
}
