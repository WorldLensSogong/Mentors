export interface MainTabBarMetricsInput {
  bottomInset: number;
  platform: 'android' | 'ios' | 'web';
}

export interface MainTabBarMetrics {
  height: number;
  paddingBottom: number;
  paddingTop: number;
  marginBottom: number;
  marginHorizontal: number;
  borderRadius: number;
}

/**
 * 하단 탭바 지표 — 바닥에서 살짝 띄운 둥근 플로팅 카드.
 * - marginBottom: 하단 safe area 위로 살짝(6px) 띄움
 * - marginHorizontal: 좌우 여백으로 카드처럼 분리
 * - height/padding: 카드 내부 높이/여백
 *
 * 탭바는 flex 흐름에 있으므로 margin 만큼 scene 높이가 줄어들어,
 * 각 화면의 하단 입력/버튼이 카드 위에 정상적으로 자리한다.
 */
export function buildMainTabBarMetrics({
  bottomInset,
}: MainTabBarMetricsInput): MainTabBarMetrics {
  return {
    height: 58,
    paddingBottom: 8,
    paddingTop: 8,
    marginBottom: bottomInset + 6,
    marginHorizontal: 10,
    borderRadius: 22,
  };
}
