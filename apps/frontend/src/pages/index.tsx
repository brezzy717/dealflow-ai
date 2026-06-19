import Head from 'next/head';
import Link from 'next/link';
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
          <h2 className="text-xl font-medium">Get started</h2>
          <ul className="mt-4 space-y-2 text-stone-600">
            <li>
              <Link href="/prospects" className="font-medium text-emerald-700 hover:underline">
                View your Prospects →
              </Link>{' '}
              scored, off-market leads assigned to you.
            </li>
          </ul>
        </div>
      </section>
    </Layout>
  );
}
