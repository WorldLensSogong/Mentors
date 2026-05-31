/**
 * 콘텐츠 동 API 응답 타입 — backend Pydantic schemas와 1:1 매칭.
 *
 * 백엔드 진실의 원천: backend/features/content/schemas.py
 *
 * owner: content 동 (5동) — backend
 */

export type MentorStrategy = 'value' | 'growth' | 'dividend' | 'momentum';
export type Sentiment = 'positive' | 'neutral' | 'negative';
export type InvestmentRelevance = 'high' | 'medium' | 'low';
export type ReliabilityLevel = 'very_high' | 'high' | 'medium' | 'low';

// ---------------------------------------------------------------------------
// 뉴스 기사
// ---------------------------------------------------------------------------

export interface NewsArticleResponse {
  id: number;
  title_original: string;
  title_translated: string | null;
  summary_ko: string | null;
  content: string | null;
  content_translated: string | null;
  original_url: string;
  source_name: string | null;
  image_url: string | null;
  language: string;
  published_at: string | null; // ISO 8601
  reliability_score: number;
  reliability_level: ReliabilityLevel;
  composite_score: number;
  strategies: MentorStrategy[];
  ai_sentiment: Sentiment | null;
  ai_investment_relevance: InvestmentRelevance | null;
  keywords: string[];
  display_title: string | null;
  display_summary: string | null;
}

export interface NewsListResponse {
  items: NewsArticleResponse[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export type NewsSortBy = 'latest' | 'reliability' | 'composite';

export interface ListNewsParams {
  page?: number;
  page_size?: number;
  sort?: NewsSortBy;
  strategy?: MentorStrategy | null;
  min_reliability?: number;
}

// ---------------------------------------------------------------------------
// RAG 시맨틱 검색
// ---------------------------------------------------------------------------

export interface SearchHit {
  article_id: number;
  score: number;
  title: string;
  summary: string | null;
  source_name: string | null;
  url: string;
  image_url: string | null;
  matched_chunk: string;
  published_at: string | null;
}

export interface SearchResponse {
  query: string;
  total: number;
  results: SearchHit[];
}

// ---------------------------------------------------------------------------
// 사용자 관심 키워드
// ---------------------------------------------------------------------------

export type UserKeywordSource = 'manual' | 'onboarding' | 'auto';

export interface UserKeywordResponse {
  id: number;
  keyword: string;
  language: string;
  source: UserKeywordSource;
  weight: number;
  master_keyword_id: number;
  created_at: string;
}

export interface UserKeywordListResponse {
  items: UserKeywordResponse[];
  total: number;
}

export interface UserKeywordCreateRequest {
  keyword: string;
  language?: string;
}

// ---------------------------------------------------------------------------
// 스크랩
// ---------------------------------------------------------------------------

export interface ScrapResponse {
  id: number;
  user_id: number;
  article_id: number;
  created_at: string;
}

export interface ScrapCreateRequest {
  article_id: number;
}

// ---------------------------------------------------------------------------
// RSS 직접 피드 — /api/content/news/top, /api/content/news/rss-search
// ---------------------------------------------------------------------------

export interface RssNewsItem {
  title: string;
  url: string;
  source_name: string | null;
  published_at: string | null; // ISO-8601 or null
  summary: string | null;
  keywords: string[];
}

// ---------------------------------------------------------------------------
// URL 즉석 AI 요약 — /api/content/news/summarize-url
// ---------------------------------------------------------------------------

export interface UrlSummarizeRequest {
  url: string;
  title?: string;
}

export interface UrlSummarizeResponse {
  title: string;
  ai_summary: string;
  image_url: string | null;
  original_url: string;
  // AI 분석 필드
  sentiment: 'positive' | 'neutral' | 'negative' | null;
  investment_relevance: 'high' | 'medium' | 'low' | null;
  strategies: string[];
  keywords: string[];
  reliability_score: number | null;
}

// ---------------------------------------------------------------------------
// Admin — AI retry
// ---------------------------------------------------------------------------

export interface RetryFailedSample {
  id: number;
  title: string;
  ai_error: string;
}

export interface RetryFailedResponse {
  reset: number;
  sample: RetryFailedSample[];
}
