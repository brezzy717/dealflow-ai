import Head from 'next/head';
import Link from 'next/link';
import { useState } from 'react';
import Layout from '../components/Layout';
import { useProspects } from '../hooks/useProspects';
import type { Prospect, Tier } from '../types/prospect';

const TIER_STYLES: Record<Tier, string> = {
  green: 'bg-emerald-100 text-emerald-800 border-emerald-300',
  yellow: 'bg-amber-100 text-amber-800 border-amber-300',
  red: 'bg-rose-100 text-rose-800 border-rose-300',
  monitor: 'bg-stone-100 text-stone-600 border-stone-300'
};

function TierBadge({ tier, score }: { tier: Tier; score: number | null }) {
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium ${TIER_STYLES[tier]}`}>
      {tier.toUpperCase()}
      {score !== null && <span className="font-semibold">· {Math.round(score)}</span>}
    </span>
  );
}

function ProspectRow({ prospect }: { prospect: Prospect }) {
  const [open, setOpen] = useState(false);
  return (
    <li className="rounded-lg border border-stone-200 bg-white p-4 shadow-sm">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-start justify-between gap-4 text-left"
      >
        <div>
          <div className="flex items-center gap-3">
            <span className="font-semibold text-stone-900">{prospect.business_name}</span>
            <TierBadge tier={prospect.tier} score={prospect.score} />
          </div>
          <p className="mt-1 text-sm text-stone-500">
            {[prospect.industry, prospect.city && prospect.state && `${prospect.city}, ${prospect.state}`]
              .filter(Boolean)
              .join(' · ')}
          </p>
          <p className="mt-1 text-xs text-stone-400">
            {prospect.employee_count ?? '—'} employees ·{' '}
            {prospect.revenue_millions !== null ? `$${prospect.revenue_millions}M ARR` : '— ARR'} ·{' '}
            {prospect.years_in_business ?? '—'} yrs
          </p>
        </div>
        <span className="text-sm text-stone-400">{open ? 'Hide' : 'Why?'}</span>
      </button>

      {open && (
        <div className="mt-3 border-t border-stone-100 pt-3 text-sm">
          {prospect.explanation && <p className="text-stone-700">{prospect.explanation}</p>}
          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">Sell signals</p>
              <ul className="mt-1 list-disc pl-5 text-stone-600">
                {prospect.top_positive.length === 0 && <li className="list-none text-stone-400">None</li>}
                {prospect.top_positive.map((a) => (
                  <li key={a.feature}>{a.label}</li>
                ))}
              </ul>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-stone-500">Mitigating factors</p>
              <ul className="mt-1 list-disc pl-5 text-stone-600">
                {prospect.top_negative.length === 0 && <li className="list-none text-stone-400">None</li>}
                {prospect.top_negative.map((a) => (
                  <li key={a.feature}>{a.label}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </li>
  );
}

export default function ProspectsPage() {
  const { data, isLoading, isError } = useProspects();
  const prospects = data?.prospects ?? [];

  return (
    <Layout>
      <Head>
        <title>Prospects · DealFlow AI</title>
      </Head>
      <section className="space-y-5">
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Prospects</h1>
            <p className="text-sm text-stone-500">Scored, off-market leads assigned to you.</p>
          </div>
          <Link href="/" className="text-sm text-stone-500 hover:text-stone-800">
            ← Home
          </Link>
        </header>

        {isLoading && <p className="text-stone-500">Loading prospects…</p>}
        {isError && (
          <p className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
            Could not load prospects. Sign in and ensure the API is running.
          </p>
        )}
        {!isLoading && !isError && prospects.length === 0 && (
          <p className="rounded-lg border border-stone-200 bg-white p-4 text-sm text-stone-500">
            No prospects yet. Your weekly drop will appear here.
          </p>
        )}

        <ul className="space-y-3">
          {prospects.map((prospect) => (
            <ProspectRow key={prospect.assignment_id} prospect={prospect} />
          ))}
        </ul>
      </section>
    </Layout>
  );
}
