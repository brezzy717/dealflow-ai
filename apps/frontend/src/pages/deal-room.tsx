import Head from 'next/head';
import { useRouter } from 'next/router';
import { useState } from 'react';
import Layout from '../components/Layout';
import { useDealRoom, usePostMessage } from '../hooks/useDealRoom';

export default function DealRoomPage() {
  const router = useRouter();
  const roomId = typeof router.query.room === 'string' ? router.query.room : undefined;
  const { data, isLoading } = useDealRoom(roomId);
  const postMessage = usePostMessage(roomId);
  const [text, setText] = useState('');

  const send = (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) return;
    postMessage.mutate(text.trim());
    setText('');
  };

  return (
    <Layout>
      <Head>
        <title>Deal Room · DealFlow AI</title>
      </Head>
      <section className="space-y-5">
        <header>
          <h1 className="text-2xl font-semibold">Deal Room</h1>
          {data && (
            <p className="text-sm text-stone-500">
              Stage: <span className="font-medium capitalize">{data.stage.replace('_', ' ')}</span> ·{' '}
              {data.status}
            </p>
          )}
        </header>

        {!roomId && (
          <p className="rounded-lg border border-stone-200 bg-white p-4 text-sm text-stone-500">
            Open a deal from the <span className="font-medium">PipeDeal</span> board to enter its room.
          </p>
        )}
        {isLoading && roomId && <p className="text-stone-500">Loading…</p>}

        {data && (
          <>
            <div className="space-y-2 rounded-lg border border-stone-200 bg-white p-4">
              {data.messages.length === 0 && (
                <p className="text-sm text-stone-400">No messages yet.</p>
              )}
              {data.messages.map((m) => (
                <div key={m.id} className="text-sm">
                  <span className="font-medium text-stone-700">{m.sender}:</span>{' '}
                  <span className="text-stone-600">{m.body}</span>
                </div>
              ))}
            </div>
            <form onSubmit={send} className="flex gap-2">
              <input
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Message the room…"
                className="flex-1 rounded-md border border-stone-300 px-3 py-2 text-sm"
              />
              <button
                type="submit"
                disabled={postMessage.isPending}
                className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
              >
                Send
              </button>
            </form>
          </>
        )}
      </section>
    </Layout>
  );
}
