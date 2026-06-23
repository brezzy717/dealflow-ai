import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';

export interface Metrics {
  prospects: number;
  clients: number;
  appointments: number;
  closed_deals: number;
  prospect_to_appointment_rate: number;
  appointment_to_close_rate: number;
  ytd_commissions: number | null;
}

export interface Appointment {
  id: string;
  source: string;
  scheduled_at: string;
  status: string;
}

export interface Client {
  assignment_id: string;
  status: string;
  business_name: string;
  industry: string | null;
  owner_name: string | null;
}

export interface Task {
  id: string;
  title: string;
  description: string | null;
  status: string;
  due_at: string | null;
}

export interface ReportSummary {
  by_tier: Record<string, number>;
  top_industries: Record<string, number>;
  outcomes: Record<string, number>;
}

export function useMetrics() {
  return useQuery({
    queryKey: ['metrics'],
    queryFn: async (): Promise<Metrics> => (await api.get<Metrics>('/api/metrics')).data
  });
}

export function useAppointments() {
  return useQuery({
    queryKey: ['appointments'],
    queryFn: async (): Promise<Appointment[]> =>
      (await api.get<{ appointments: Appointment[] }>('/api/appointments')).data.appointments
  });
}

export function useClients() {
  return useQuery({
    queryKey: ['clients'],
    queryFn: async (): Promise<Client[]> =>
      (await api.get<{ clients: Client[] }>('/api/clients')).data.clients
  });
}

export function useTasks() {
  return useQuery({
    queryKey: ['tasks'],
    queryFn: async (): Promise<Task[]> =>
      (await api.get<{ tasks: Task[] }>('/api/tasks')).data.tasks
  });
}

export function useCreateTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (title: string) => (await api.post('/api/tasks', { title })).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tasks'] })
  });
}

export function useReports() {
  return useQuery({
    queryKey: ['reports'],
    queryFn: async (): Promise<ReportSummary> =>
      (await api.get<ReportSummary>('/api/reports/summary')).data
  });
}
