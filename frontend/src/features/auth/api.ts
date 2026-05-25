import { isAxiosError } from 'axios';
import { apiClient } from '@/api/client';

export interface DevAccessTokenRequest {
  email?: string;
  nickname?: string;
}

export interface DevAccessTokenUser {
  id: number;
  email: string;
  nickname: string;
  status: string;
}

export interface DevAccessTokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  created: boolean;
  user: DevAccessTokenUser;
}

export async function issueDevAccessToken(
  payload: DevAccessTokenRequest = {},
): Promise<DevAccessTokenResponse> {
  const response = await apiClient.post<DevAccessTokenResponse>('/auth/dev-token', payload);
  return response.data;
}

export async function getCurrentUser(): Promise<DevAccessTokenUser> {
  const response = await apiClient.get<DevAccessTokenUser>('/auth/me');
  return response.data;
}

export async function deleteCurrentUser(): Promise<void> {
  await apiClient.delete('/auth/me');
}

export function getAuthApiErrorMessage(error: unknown, fallback: string): string {
  if (isAxiosError<{ message?: string }>(error)) {
    return error.response?.data?.message ?? fallback;
  }

  return error instanceof Error ? error.message : fallback;
}
