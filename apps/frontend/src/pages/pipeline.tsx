import Head from 'next/head';
import Link from 'next/link';
import Layout from '../components/Layout';
import { Deal, STAGES, Stage, usePipeline } from '../hooks/useDealRoom';

const STAGE_LABELS: Record<Stage, string> = {
  buyer_matching: 'Buyer Matching',
  loi_nda: 'LOI / NDA',
  due_diligence: 'Due Diligence',
  negotiation: 'Negotiation',
  docs_signed: 'Docs Signed',
  funded: 'Funded'
};

export default function PipelinePage() {
  const { data, isLoading } = usePipeline();
  const deals = data ?? [];
  const byStage = (stage: Stage): Deal[] => deals.filter((d) => d.stage === stage);

  return (
    <Layout>
      <Head>
        <title>PipeDeal · DealFlow AI</title>
      </Head>
      <section className="space-y-5">
        <header>
          <h1 className="text-2xl font-semibold">PipeDeal</h1>
          <p className="text-sm text-stone-500">Move deals from buyer matching to funded.</p>
        </header>
        {isLoading && <p className="text-stone-500">Loading…</p>}
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-6">
          {STAGES.map((stage) => (
            <div key={stage} className="rounded-lg border border-stone-200 bg-stone-50 p-2">
              <h2 className="px-1 pb-2 text-xs font-semibold uppercase tracking-wide text-stone-500">
                {STAGE_LABELS[stage]}
              </h2>
              <div className="space-y-2">
                {byStage(stage).map((deal) => (
                  <Link
                    key={deal.id}
                    href={`/deal-room?room=${deal.id}`}
                    className="block rounded-md border border-stone-200 bg-white p-2 text-sm shadow-sm hover:border-emerald-300"
                  >
                    {deal.business_name}
                    {deal.status === 'closed' && (
                      <span className="ml-1 text-xs text-emerald-600">✓</span>
                    )}
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>
    </Layout>
  );
}
