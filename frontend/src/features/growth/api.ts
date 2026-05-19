import { isAxiosError } from 'axios';
import { apiClient } from '@/api/client';
import type { GrowthProgressResponse, PromotionTestRequest, PromotionTestResponse } from './types';

export async function getGrowthProgress(): Promise<GrowthProgressResponse> {
  const response = await apiClient.get<GrowthProgressResponse>('/api/growth/me/progress');
  return response.data;
}

export async function submitPromotionTest(
  payload: PromotionTestRequest,
): Promise<PromotionTestResponse> {
  const response = await apiClient.post<PromotionTestResponse>(
    '/api/growth/promotion-test',
    payload,
  );
  return response.data;
}

export function getGrowthApiErrorMessage(error: unknown, fallback: string): string {
  if (isAxiosError<{ message?: string }>(error)) {
    return error.response?.data?.message ?? fallback;
  }

  return error instanceof Error ? error.message : fallback;
}
