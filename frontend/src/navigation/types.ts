export type RootStackParamList = {
  Login: undefined;
  Onboarding: undefined;
  Home: undefined;
  PromotionTest: undefined;
};

declare global {
  namespace ReactNavigation {
    // eslint-disable-next-line @typescript-eslint/no-empty-object-type
    interface RootParamList extends RootStackParamList {}
  }
}
