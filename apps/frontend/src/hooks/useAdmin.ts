import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';

export interface AdminHealth {
  tenants: number;
  users: number;
  raw_leads: number;
  predictions: number;
  assignments: number;
  queued_calls: number;
  unacknowledged_alerts: number;
}

export interface AdminNotification {
  id: string;
  level: string;
  source: string | null;
  message: string;
  acknowledged: boolean;
  created_at: string;
}

export interface AdminModel {
  id: string;
  model_name: string;
  version: string;
  is_active: boolean;
  metrics: Record<string, unknown>;
  trained_at: string | null;
}

export function useAdminHealth() {
  return useQuery({
    queryKey: ['admin-health'],
    queryFn: async (): Promise<AdminHealth> =>
      (await api.get<AdminHealth>('/api/admin/health')).data
  });
}

export function useAdminNotifications() {
  return useQuery({
    queryKey: ['admin-notifications'],
    queryFn: async (): Promise<AdminNotification[]> =>
      (await api.get<{ notifications: AdminNotification[] }>('/api/admin/notifications')).data
        .notifications
  });
}

export function useAdminModels() {
  return useQuery({
    queryKey: ['admin-models'],
    queryFn: async (): Promise<AdminModel[]> =>
      (await api.get<{ models: AdminModel[] }>('/api/admin/models')).data.models
  });
}
