import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';

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
      (await api.post(`/api/deal-rooms/${roomId}/stage`, { stage })).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['pipeline'] })
  });
}

export function useDealRoom(roomId: string | undefined) {
  return useQuery({
    queryKey: ['deal-room', roomId],
    enabled: Boolean(roomId),
    queryFn: async (): Promise<DealRoom> =>
      (await api.get<DealRoom>(`/api/deal-rooms/${roomId}`)).data
  });
}

export function usePostMessage(roomId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: string) =>
      (await api.post(`/api/deal-rooms/${roomId}/messages`, { sender: 'broker', body })).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['deal-room', roomId] })
  });
}
