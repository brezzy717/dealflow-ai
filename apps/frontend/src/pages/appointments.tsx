import Head from 'next/head';
import Layout from '../components/Layout';
import { useAppointments } from '../hooks/useDashboard';

export default function AppointmentsPage() {
  const { data, isLoading } = useAppointments();
  const appointments = data ?? [];

  return (
    <Layout>
      <Head>
        <title>Appointments · DealFlow AI</title>
      </Head>
      <section className="space-y-5">
        <header>
          <h1 className="text-2xl font-semibold">Appointments</h1>
          <p className="text-sm text-stone-500">Discovery calls and meetings on your calendar.</p>
        </header>
        {isLoading && <p className="text-stone-500">Loading…</p>}
        {!isLoading && appointments.length === 0 && (
          <p className="rounded-lg border border-stone-200 bg-white p-4 text-sm text-stone-500">
            No appointments yet.
          </p>
        )}
        <ul className="space-y-3">
          {appointments.map((a) => (
            <li key={a.id} className="rounded-lg border border-stone-200 bg-white p-4 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="font-medium">{new Date(a.scheduled_at).toLocaleString()}</span>
                <span className="text-xs uppercase tracking-wide text-stone-500">{a.source}</span>
              </div>
              <p className="mt-1 text-sm text-stone-500">{a.status}</p>
            </li>
          ))}
        </ul>
      </section>
    </Layout>
  );
}
