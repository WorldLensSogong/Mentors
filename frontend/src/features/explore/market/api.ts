/**
 * 경제 지수 실시간 API wrapper.
 *
 * 백엔드 라우터: backend/core/market_data/router.py
 * - GET /api/market/quotes  →  환율·금리·코스피·나스닥 현재가 + 5일 히스토리
 */

import { apiClient } from '@/api/client';
import type { MarketQuotesResponse } from './types';

export async function getMarketQuotes(): Promise<MarketQuotesResponse> {
  const response = await apiClient.get<MarketQuotesResponse>('/api/market/quotes');
  return response.data;
}
