import { isAxiosError } from 'axios';
import { apiClient } from '@/api/client';
import type {
  SubmitLearningQuizRequest,
  SubmitLearningQuizResponse,
  TierQuizCatalogResponse,
  TodayOpenerResponse,
} from './types';

export async function getCurrentTierQuizzes(): Promise<TierQuizCatalogResponse> {
  const response = await apiClient.get<TierQuizCatalogResponse>('/api/learning/me/quizzes');
  return response.data;
}

export async function submitLearningQuiz(
  payload: SubmitLearningQuizRequest,
): Promise<SubmitLearningQuizResponse> {
  const response = await apiClient.post<SubmitLearningQuizResponse>(
    '/api/learning/quizzes/submit',
    payload,
  );
  return response.data;
}

export async function getTodayOpener(mentorId: number): Promise<TodayOpenerResponse> {
  const response = await apiClient.get<TodayOpenerResponse>(
    `/api/learning/mentors/${mentorId}/today-opener`,
  );
  return response.data;
}

export function getLearningApiErrorMessage(error: unknown, fallback: string): string {
  if (isAxiosError<{ message?: string }>(error)) {
    return error.response?.data?.message ?? fallback;
  }

  return error instanceof Error ? error.message : fallback;
}
