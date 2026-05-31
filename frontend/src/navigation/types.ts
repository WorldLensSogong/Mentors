import type { NavigatorScreenParams } from '@react-navigation/native';
import type { LearningChatMentorId } from '@/features/chat/types';

export type MainTabParamList = {
  Search: undefined;
  MentorChat:
    | {
        sessionId?: number;
        mentorId?: LearningChatMentorId;
      }
    | undefined;
  DebateArena:
    | {
        replaySessionId?: number;
        replayStreamUrl?: string;
        replayTopic?: string;
        replayPersonaAName?: string;
        replayPersonaBName?: string;
      }
    | undefined;
};

export type AppStackParamList = {
  Login: undefined;
  Signup: undefined;
  Onboarding: undefined;
  MainTabs: NavigatorScreenParams<MainTabParamList> | undefined;
  LearningRecord: undefined;
  PromotionTest: undefined;
  PromotionResult: undefined;
  InterestSettings: undefined;
  ChatHistory: undefined;
  DebateHistory: undefined;
  DebateSessionDetail: { sessionId: number };
  SearchResult: { query: string };
  RssArticleSummary: {
    title: string;
    url: string;
    source_name: string | null;
    published_at: string | null;
  };
  Settings: undefined;
  NotificationSettings: undefined;
  AccountSettings: undefined;
  NewsDetail: {
    newsId: number;
  };
};

declare global {
  namespace ReactNavigation {
    // eslint-disable-next-line @typescript-eslint/no-empty-object-type
    interface RootParamList extends AppStackParamList {}
  }
}
