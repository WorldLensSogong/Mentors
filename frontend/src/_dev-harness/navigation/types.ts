export type RootStackParamList = {
  Login: undefined;
  Onboarding: undefined;
  Home: undefined;
  PromotionTest: undefined;
  InterestSettings: undefined;
};

export type MainTabParamList = {
  LearningRecord: undefined;
  Settings: undefined;
};

declare global {
  namespace ReactNavigation {
    // eslint-disable-next-line @typescript-eslint/no-empty-object-type
    interface RootParamList extends RootStackParamList {}
  }
}
