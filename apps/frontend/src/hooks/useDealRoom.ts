import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';

// Constrain + encode the user-derived room id before it enters a request path
// (must be a UUID; prevents path/host injection — CodeQL request-forgery).
const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const enc = (id: string): string => {
  if (!UUID_RE.test(id)) {
    throw new Error('Invalid deal room id');
  }
  return encodeURIComponent(id);
};

export const STAGES = [
  'buyer_matching',
  'loi_nda',
  'due_diligence',
  'negotiation',
  'docs_signed',
  'funded'
] as const;
export type Stage = (typeof STAGES)[number];

export interface Deal {
  id: string;
  stage: Stage;
  status: string;
  business_name: string;
}

export interface DealMessage {
  id: string;
  sender: string;
  body: string | null;
  attachment_uri: string | null;
  sent_at: string;
}

export interface DealRoom {
  id: string;
  stage: Stage;
  status: string;
  messages: DealMessage[];
}

export function usePipeline() {
  return useQuery({
    queryKey: ['pipeline'],
    queryFn: async (): Promise<Deal[]> =>
      (await api.get<{ deals: Deal[] }>('/api/pipeline')).data.deals
  });
}

export function useAdvanceStage() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ roomId, stage }: { roomId: string; stage: Stage }) =>
      (await api.post(`/api/deal-rooms/${enc(roomId)}/stage`, { stage })).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['pipeline'] })
  });
}

export function useDealRoom(roomId: string | undefined) {
  return useQuery({
    queryKey: ['deal-room', roomId],
    enabled: Boolean(roomId),
    queryFn: async (): Promise<DealRoom> =>
      (await api.get<DealRoom>(`/api/deal-rooms/${enc(roomId as string)}`)).data
  });
}

export function usePostMessage(roomId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: string) =>
      (await api.post(`/api/deal-rooms/${enc(roomId as string)}/messages`, { sender: 'broker', body }))
        .data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['deal-room', roomId] })
  });
}
