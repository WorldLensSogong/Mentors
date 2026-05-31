/**
 * 경제 지수 실시간 API 응답 타입.
 *
 * 백엔드 진실의 원천: backend/core/market_data/router.py
 * - /api/market/quotes (GET)
 */

export interface IndicatorQuote {
  name: string;        // 한글 지표명: "환율" | "금리" | "코스피" | "나스닥"
  symbol: string;      // Yahoo Finance 심볼: "USDKRW=X" | "^TNX" | "^KS11" | "^IXIC"
  value: number;       // 현재 시장 가격
  change: number;      // 전일 대비 변동 (절댓값)
  change_pct: number;  // 전일 대비 변동률 (%)
  is_up: boolean;      // 상승 여부
  history: number[];   // 5일 일봉 종가 배열 (sparkline 용)
  updated_at: string;  // ISO-8601
}

export interface MarketQuotesResponse {
  quotes: IndicatorQuote[];
  cached: boolean;
  cache_age_s: number;
}
