import { isAxiosError } from 'axios';
import { apiClient } from '@/api/client';
import { useUserStore } from '@/store/userStore';
import { parseLearningChatEventBuffer } from './logic';
import type {
  ChatStreamRequest,
  CreateLearningChatSessionRequest,
  LearningChatMessageListResponse,
  LearningChatSession,
  LearningChatSessionListResponse,
  LearningChatStreamEvent,
} from './types';

const apiBaseUrl = process.env.EXPO_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

export async function listLearningChatSessions(): Promise<LearningChatSessionListResponse> {
  const response = await apiClient.get<LearningChatSessionListResponse>('/api/learning/sessions');
  return response.data;
}

export async function createLearningChatSession(
  payload: CreateLearningChatSessionRequest,
): Promise<LearningChatSession> {
  const response = await apiClient.post<LearningChatSession>('/api/learning/sessions', payload);
  return response.data;
}

export async function listLearningChatMessages(
  sessionId: number,
): Promise<LearningChatMessageListResponse> {
  const response = await apiClient.get<LearningChatMessageListResponse>(
    `/api/learning/sessions/${sessionId}/messages`,
  );
  return response.data;
}

export async function streamLearningChat({
  payload,
  signal,
  onEvent,
}: {
  payload: ChatStreamRequest;
  signal?: AbortSignal;
  onEvent: (event: LearningChatStreamEvent) => void;
}): Promise<void> {
  const accessToken = useUserStore.getState().accessToken;
  const response = await fetch(`${apiBaseUrl}/api/learning/chat/stream`, {
    method: 'POST',
    headers: {
      Accept: 'text/event-stream',
      'Content-Type': 'application/json',
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
    },
    body: JSON.stringify(payload),
    signal,
  });

  if (response.status === 401) {
    useUserStore.getState().clearToken();
    throw new Error('세션이 만료되었습니다. 다시 로그인해 주세요.');
  }

  if (!response.ok) {
    let message = '멘토 답변을 불러오지 못했습니다.';

    try {
      const body = (await response.json()) as { detail?: string; message?: string };
      message = body.message ?? body.detail ?? message;
    } catch {
      try {
        const raw = await response.text();
        if (raw.trim()) {
          message = raw.trim();
        }
      } catch {
        // Ignore text parsing errors and keep the fallback message.
      }
    }

    throw new Error(message);
  }

  const reader = response.body?.getReader?.();

  if (!reader) {
    const raw = await response.text();
    const parsed = parseLearningChatEventBuffer(`${raw}\n\n`);
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
    const parsed = parseLearningChatEventBuffer(remainder);
    remainder = parsed.remainder;
    parsed.events.forEach(onEvent);
  }

  const trailingText = remainder + decoder.decode();
  if (trailingText.trim()) {
    const parsed = parseLearningChatEventBuffer(`${trailingText}\n\n`);
    parsed.events.forEach(onEvent);
  }
}

export function getLearningChatApiErrorMessage(error: unknown, fallback: string): string {
  if (isAxiosError<{ message?: string }>(error)) {
    return error.response?.data?.message ?? fallback;
  }

  return error instanceof Error ? error.message : fallback;
}
