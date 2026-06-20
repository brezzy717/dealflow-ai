import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';

export interface BrokerParameters {
  min_years_in_business: number | null;
  min_employees: number | null;
  max_employees: number | null;
  min_revenue_millions: number | null;
  max_revenue_millions: number | null;
  omitted_industries: string[];
  omitted_locations: string[];
}

export interface BrokerSettings {
  warm_outreach_opt_in: boolean;
  parameters: BrokerParameters;
}

export function useSettings() {
  return useQuery({
    queryKey: ['settings'],
    queryFn: async (): Promise<BrokerSettings> =>
      (await api.get<BrokerSettings>('/api/settings')).data
  });
}

export function useUpdateSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: BrokerSettings) => {
      const payload = { ...body.parameters, warm_outreach_opt_in: body.warm_outreach_opt_in };
      return (await api.put('/api/settings', payload)).data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['settings'] })
  });
}
