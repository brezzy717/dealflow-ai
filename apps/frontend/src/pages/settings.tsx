import Head from 'next/head';
import Layout from '../components/Layout';
import { useSettings, useUpdateSettings } from '../hooks/useSettings';

export default function SettingsPage() {
  const { data, isLoading, isError } = useSettings();
  const update = useUpdateSettings();

  const toggleOutreach = () => {
    if (!data) return;
    update.mutate({ ...data, warm_outreach_opt_in: !data.warm_outreach_opt_in });
  };

  return (
    <Layout>
      <Head>
        <title>Settings · DealFlow AI</title>
      </Head>
      <section className="space-y-6">
        <header>
          <h1 className="text-2xl font-semibold">Settings</h1>
          <p className="text-sm text-stone-500">Outreach preference and lead parameters.</p>
        </header>

        {isError && (
          <p className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
            Sign in to manage your settings.
          </p>
        )}
        {isLoading && <p className="text-stone-500">Loading…</p>}

        {data && (
          <>
            <div className="flex items-center justify-between rounded-xl border border-stone-200 bg-white p-5 shadow-sm">
              <div>
                <div className="font-medium">AI Calling Concierge</div>
                <div className="text-sm text-stone-500">
                  {data.warm_outreach_opt_in
                    ? 'On — we run warm outreach for you.'
                    : 'Off — you handle outreach manually.'}
                </div>
              </div>
              <button
                type="button"
                onClick={toggleOutreach}
                disabled={update.isPending}
                className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
              >
                {data.warm_outreach_opt_in ? 'Turn off' : 'Turn on'}
              </button>
            </div>

            <div className="rounded-xl border border-stone-200 bg-white p-5 shadow-sm">
              <h2 className="text-sm font-semibold uppercase tracking-wide text-stone-500">
                Assignment parameters
              </h2>
              <dl className="mt-3 grid grid-cols-2 gap-3 text-sm">
                <div>
                  <dt className="text-stone-500">Min years in business</dt>
                  <dd>{data.parameters.min_years_in_business ?? 'Any'}</dd>
                </div>
                <div>
                  <dt className="text-stone-500">Employees</dt>
                  <dd>
                    {data.parameters.min_employees ?? 'Any'} – {data.parameters.max_employees ?? 'Any'}
                  </dd>
                </div>
                <div>
                  <dt className="text-stone-500">Omitted industries</dt>
                  <dd>{data.parameters.omitted_industries.join(', ') || 'None'}</dd>
                </div>
                <div>
                  <dt className="text-stone-500">Omitted locations</dt>
                  <dd>{data.parameters.omitted_locations.join(', ') || 'None'}</dd>
                </div>
              </dl>
            </div>
          </>
        )}
      </section>
    </Layout>
  );
}
