import type { NavigatorScreenParams } from '@react-navigation/native';
import type { LearningChatMentorId } from '@/features/chat/types';

export type MainTabParamList = {
  LearningRecord: undefined;
  MentorChat:
    | {
        sessionId?: number;
        mentorId?: LearningChatMentorId;
      }
    | undefined;
};

export type RootStackParamList = {
  Login: undefined;
  Onboarding: undefined;
  Home: NavigatorScreenParams<MainTabParamList> | undefined;
  PromotionTest: undefined;
  Settings: undefined;
  InterestSettings: undefined;
  ChatHistory: undefined;
};

declare global {
  namespace ReactNavigation {
    // eslint-disable-next-line @typescript-eslint/no-empty-object-type
    interface RootParamList extends RootStackParamList {}
  }
}
