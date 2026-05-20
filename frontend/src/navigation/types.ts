export type RootStackParamList = {
  Home: undefined;
  Login: undefined;
};

declare global {
  namespace ReactNavigation {
    // React Navigation 공식 패턴 — 빈 interface로 전역 타입 확장
    // eslint-disable-next-line @typescript-eslint/no-empty-object-type
    interface RootParamList extends RootStackParamList {}
  }
}
