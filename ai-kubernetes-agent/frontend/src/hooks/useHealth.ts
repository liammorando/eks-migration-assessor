import { useQuery } from '@tanstack/react-query';
import { healthCheck } from '@/services/api';
import { HealthResponse } from '@/types';

export function useHealth() {
  return useQuery<HealthResponse>({
    queryKey: ['health'],
    queryFn: healthCheck,
    refetchInterval: 30000,
  });
}