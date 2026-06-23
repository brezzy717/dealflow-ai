import Head from 'next/head';
import Layout from './Layout';

export default function Placeholder({ title, note }: { title: string; note: string }) {
  return (
    <Layout>
      <Head>
        <title>{title} · DealFlow AI</title>
      </Head>
      <section className="space-y-4">
        <h1 className="text-2xl font-semibold">{title}</h1>
        <p className="rounded-lg border border-stone-200 bg-white p-4 text-sm text-stone-500">{note}</p>
      </section>
    </Layout>
  );
}
