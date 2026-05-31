import type { CompletedOnboardingProfile } from '../onboarding/types';

export type LearningChatMentorId = 1 | 2 | 3 | 4;

export type LearningChatRole = 'user' | 'assistant';

export interface LearningChatMentorProfile {
  id: LearningChatMentorId;
  label: string;
  shortLabel: string;
  description: string;
  focusLabel: string;
  accentColor: string;
  avatarTint: string;
}

export interface LearningChatSession {
  id: number;
  mentor_id: LearningChatMentorId;
  title: string | null;
  created_at: string;
}

export interface LearningChatMessage {
  id: number;
  session_id: number;
  role: LearningChatRole;
  content: string;
  created_at: string;
}

export interface LearningChatSessionListResponse {
  sessions: LearningChatSession[];
}

export interface LearningChatMessageListResponse {
  messages: LearningChatMessage[];
}

export interface CreateLearningChatSessionRequest {
  mentor_id: LearningChatMentorId;
}

export interface ChatStreamRequest {
  session_id: number;
  content: string;
}

export interface LearningChatStreamChunk {
  delta: string;
  done: boolean;
  usage?: Record<string, unknown> | null;
  citations?: Record<string, unknown>[];
}

export interface LearningChatFollowUpQuizOption {
  index: number;
  text: string;
}

export interface LearningChatFollowUpQuiz {
  concept_id: number;
  concept_name: string;
  quiz_index: number;
  question: string;
  options: LearningChatFollowUpQuizOption[];
}

export type LearningChatStreamEvent =
  | {
      type: 'delta';
      chunk: LearningChatStreamChunk;
    }
  | {
      type: 'follow_up_quiz';
      quiz: LearningChatFollowUpQuiz;
    };

export interface LearningChatHistoryCard {
  sessionId: number;
  mentor: LearningChatMentorProfile;
  title: string;
  preview: string;
  createdAtLabel: string;
  messageCount: number;
}

export interface LearningChatScreenSeed {
  mentorId: LearningChatMentorId;
  profile: CompletedOnboardingProfile | null;
}
