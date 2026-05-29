import { isAxiosError } from 'axios';
import { apiClient } from '@/api/client';
import { useUserStore } from '@/store/userStore';
import { parseDebateEventBuffer } from './logic';
import type {
  DebateEligibility,
  DebatePersona,
  DebateStartRequest,
  DebateStartResponse,
  DebateStreamEvent,
} from './types';

const apiBaseUrl = process.env.EXPO_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

export async function getDebateEligibility(): Promise<DebateEligibility> {
  const response = await apiClient.get<DebateEligibility>('/api/debate/eligibility');
  return response.data;
}

export async function listDebatePersonas(): Promise<DebatePersona[]> {
  const response = await apiClient.get<DebatePersona[]>('/api/debate/personas');
  return response.data.filter((persona) => persona.is_public);
}

export async function startDebate(payload: DebateStartRequest): Promise<DebateStartResponse> {
  const response = await apiClient.post<DebateStartResponse>('/api/debate/start', payload);
  return response.data;
}

export async function streamDebate({
  streamUrl,
  signal,
  onEvent,
}: {
  streamUrl: string;
  signal?: AbortSignal;
  onEvent: (event: DebateStreamEvent) => void;
}): Promise<void> {
  const accessToken = useUserStore.getState().accessToken;
  const response = await fetch(`${apiBaseUrl}${streamUrl}`, {
    method: 'GET',
    headers: {
      Accept: 'text/event-stream',
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
    },
    signal,
  });

  if (response.status === 401) {
    useUserStore.getState().clearToken();
    throw new Error('세션이 만료되었습니다. 다시 로그인해 주세요.');
  }

  if (!response.ok) {
    throw new Error(await readDebateError(response));
  }

  const reader = response.body?.getReader?.();

  if (!reader) {
    const raw = await response.text();
    const parsed = parseDebateEventBuffer(`${raw}\n\n`);
    parsed.events.forEach(onEvent);
    return;
  }

  const decoder = new TextDecoder();
  let remainder = '';

  while (true) {
    const result = await reader.read();
    if (result.done) {
      break;
    }

    remainder += decoder.decode(result.value, { stream: true });
    const parsed = parseDebateEventBuffer(remainder);
    remainder = parsed.remainder;
    parsed.events.forEach(onEvent);
  }

  const trailingText = remainder + decoder.decode();
  if (trailingText.trim()) {
    const parsed = parseDebateEventBuffer(`${trailingText}\n\n`);
    parsed.events.forEach(onEvent);
  }
}

export function getDebateApiErrorMessage(error: unknown, fallback: string): string {
  if (isAxiosError<{ detail?: string; message?: string }>(error)) {
    return error.response?.data?.message ?? error.response?.data?.detail ?? fallback;
  }

  return error instanceof Error ? error.message : fallback;
}

async function readDebateError(response: Response): Promise<string> {
  const fallback = '토론을 시작하지 못했습니다. 잠시 후 다시 시도해 주세요.';

  try {
    const body = (await response.json()) as { detail?: string; message?: string };
    return body.message ?? body.detail ?? fallback;
  } catch {
    try {
      const raw = await response.text();
      return raw.trim() || fallback;
    } catch {
      return fallback;
    }
  }
}
