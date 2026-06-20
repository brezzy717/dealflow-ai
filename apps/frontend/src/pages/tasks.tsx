import Head from 'next/head';
import { useState } from 'react';
import Layout from '../components/Layout';
import { useCreateTask, useTasks } from '../hooks/useDashboard';

export default function TasksPage() {
  const { data, isLoading } = useTasks();
  const createTask = useCreateTask();
  const [title, setTitle] = useState('');
  const tasks = data ?? [];

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    createTask.mutate(title.trim());
    setTitle('');
  };

  return (
    <Layout>
      <Head>
        <title>Tasks · DealFlow AI</title>
      </Head>
      <section className="space-y-5">
        <header>
          <h1 className="text-2xl font-semibold">Task Manager</h1>
          <p className="text-sm text-stone-500">To-dos and prospects awaiting action.</p>
        </header>

        <form onSubmit={submit} className="flex gap-2">
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Add a to-do…"
            className="flex-1 rounded-md border border-stone-300 px-3 py-2 text-sm"
          />
          <button
            type="submit"
            disabled={createTask.isPending}
            className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
          >
            Add
          </button>
        </form>

        {isLoading && <p className="text-stone-500">Loading…</p>}
        <ul className="space-y-2">
          {tasks.map((t) => (
            <li key={t.id} className="rounded-lg border border-stone-200 bg-white p-3 text-sm shadow-sm">
              <div className="flex items-center justify-between">
                <span>{t.title}</span>
                <span className="text-xs uppercase tracking-wide text-stone-500">{t.status}</span>
              </div>
            </li>
          ))}
        </ul>
      </section>
    </Layout>
  );
}
