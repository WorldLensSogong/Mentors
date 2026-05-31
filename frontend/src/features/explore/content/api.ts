/**
 * 콘텐츠 동 API endpoint wrapper.
 *
 * 백엔드 라우터: backend/features/content/router.py
 * - /api/content/news               (GET, paged + filters)
 * - /api/content/news/search        (GET, RAG semantic)
 * - /api/content/news/{id}          (GET, detail)
 * - /api/content/scraps             (POST/GET/DELETE)
 * - /api/content/keywords           (POST/GET/DELETE)
 * - /api/content/admin/retry-failed (POST)
 *
 * owner: content 동 (5동) — backend
 */

import { apiClient } from '@/api/client';
import type {
  ListNewsParams,
  NewsArticleResponse,
  NewsListResponse,
  RetryFailedResponse,
  RssNewsItem,
  ScrapCreateRequest,
  ScrapResponse,
  SearchResponse,
  UrlSummarizeRequest,
  UrlSummarizeResponse,
  UserKeywordCreateRequest,
  UserKeywordListResponse,
  UserKeywordResponse,
} from './types';

// ---------------------------------------------------------------------------
// 뉴스 피드
// ---------------------------------------------------------------------------

export async function listNews(params: ListNewsParams = {}): Promise<NewsListResponse> {
  const response = await apiClient.get<NewsListResponse>('/api/content/news', { params });
  return response.data;
}

export async function getNewsDetail(newsId: number): Promise<NewsArticleResponse> {
  const response = await apiClient.get<NewsArticleResponse>(`/api/content/news/${newsId}`);
  return response.data;
}

export async function searchNews(query: string, topK = 10): Promise<SearchResponse> {
  const response = await apiClient.get<SearchResponse>('/api/content/news/search', {
    params: { q: query, top_k: topK },
  });
  return response.data;
}

// ---------------------------------------------------------------------------
// 사용자 관심 키워드 CRUD
// ---------------------------------------------------------------------------

export async function listMyKeywords(): Promise<UserKeywordListResponse> {
  const response = await apiClient.get<UserKeywordListResponse>('/api/content/keywords');
  return response.data;
}

export async function addMyKeyword(
  payload: UserKeywordCreateRequest,
): Promise<UserKeywordResponse> {
  const response = await apiClient.post<UserKeywordResponse>('/api/content/keywords', payload);
  return response.data;
}

export async function removeMyKeyword(userKeywordId: number): Promise<void> {
  await apiClient.delete(`/api/content/keywords/${userKeywordId}`);
}

// ---------------------------------------------------------------------------
// 스크랩
// ---------------------------------------------------------------------------

export async function addScrap(payload: ScrapCreateRequest): Promise<ScrapResponse> {
  const response = await apiClient.post<ScrapResponse>('/api/content/scraps', payload);
  return response.data;
}

export async function listMyScraps(limit = 50): Promise<ScrapResponse[]> {
  const response = await apiClient.get<ScrapResponse[]>('/api/content/scraps', {
    params: { limit },
  });
  return response.data;
}

export async function removeScrap(scrapId: number): Promise<void> {
  await apiClient.delete(`/api/content/scraps/${scrapId}`);
}

// ---------------------------------------------------------------------------
// RSS 직접 피드 (DB 파이프라인 불필요 — 실시간 Google News RSS)
// ---------------------------------------------------------------------------

/** 주요 금융 뉴스 (기본 키워드 검색) */
export async function getTopNews(limit = 8): Promise<RssNewsItem[]> {
  const response = await apiClient.get<RssNewsItem[]>('/api/content/news/top', {
    params: { limit },
  });
  return response.data;
}

/** Google News RSS 키워드 검색 */
export async function rssSearchNews(query: string, limit = 10): Promise<RssNewsItem[]> {
  const response = await apiClient.get<RssNewsItem[]>('/api/content/news/rss-search', {
    params: { q: query, limit },
  });
  return response.data;
}

/**
 * RSS 기사 URL을 받아 본문 추출 + LLM 한국어 요약을 생성합니다.
 * 기사 이미지(og:image 등)도 함께 반환됩니다.
 */
export async function summarizeNewsUrl(
  payload: UrlSummarizeRequest,
): Promise<UrlSummarizeResponse> {
  const response = await apiClient.post<UrlSummarizeResponse>(
    '/api/content/news/summarize-url',
    payload,
  );
  return response.data;
}

// ---------------------------------------------------------------------------
// Admin — AI 실패 재처리
// ---------------------------------------------------------------------------

export async function retryFailedAi(limit = 100): Promise<RetryFailedResponse> {
  const response = await apiClient.post<RetryFailedResponse>(
    '/api/content/admin/retry-failed',
    null,
    { params: { limit } },
  );
  return response.data;
}
