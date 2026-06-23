import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import type { ProspectsResponse } from '../types/prospect';

export function useProspects() {
  return useQuery({
    queryKey: ['prospects'],
    queryFn: async (): Promise<ProspectsResponse> => {
      const { data } = await api.get<ProspectsResponse>('/api/prospects');
      return data;
    }
  });
}
