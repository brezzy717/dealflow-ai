import Head from 'next/head';
import Layout from '../components/Layout';

export default function Home() {
  return (
    <Layout>
      <Head>
        <title>DealFlow AI Dashboard</title>
      </Head>
      <section className="space-y-6">
        <header>
          <h1 className="text-3xl font-semibold">DealFlow AI Control Center</h1>
          <p className="text-stone-500">
            Monitor lead tiers, automate outreach cadences, and review broker outcomes in one place.
          </p>
        </header>
        <div className="rounded-xl border border-stone-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-medium">Next Steps</h2>
          <ul className="mt-4 list-disc space-y-2 pl-6 text-stone-600">
            <li>Connect to the backend API from `apps/backend`.</li>
            <li>Wire React Query to the scoring and assignment endpoints.</li>
            <li>Replace this placeholder card with live tier summaries and action widgets.</li>
          </ul>
        </div>
      </section>
    </Layout>
  );
}
