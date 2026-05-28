/**
 * 콘텐츠 동 순수 함수 — UI에서 사용하는 라벨/포맷 헬퍼.
 *
 * owner: content 동 (5동) — backend
 */

import type {
  MentorStrategy,
  ReliabilityLevel,
  Sentiment,
  InvestmentRelevance,
} from './types';

// 멘토 전략 한국어 라벨
export const STRATEGY_LABEL: Record<MentorStrategy, string> = {
  value: '가치',
  growth: '성장',
  dividend: '배당',
  momentum: '모멘텀',
};

// 신뢰도 레벨 라벨
export const RELIABILITY_LABEL: Record<ReliabilityLevel, string> = {
  very_high: '매우 높음',
  high: '높음',
  medium: '보통',
  low: '낮음',
};

// 신뢰도 레벨 컬러 키 (constants/colors와 매칭)
export const RELIABILITY_COLOR_KEY: Record<ReliabilityLevel, 'success' | 'accent' | 'muted' | 'rose'> = {
  very_high: 'success',
  high: 'success',
  medium: 'accent',
  low: 'rose',
};

// sentiment 라벨
export const SENTIMENT_LABEL: Record<Sentiment, string> = {
  positive: '긍정',
  neutral: '중립',
  negative: '부정',
};

// 투자 관련성 라벨
export const RELEVANCE_LABEL: Record<InvestmentRelevance, string> = {
  high: '높음',
  medium: '보통',
  low: '낮음',
};

/**
 * 발행 시각 → "방금 전" / "10분 전" / "오늘" / "2일 전" / "yyyy.MM.dd"
 */
export function formatPublishedAt(iso: string | null, now: Date = new Date()): string {
  if (!iso) return '발행 시각 미상';
  const t = new Date(iso);
  if (Number.isNaN(t.getTime())) return '발행 시각 미상';
  const diffSec = Math.floor((now.getTime() - t.getTime()) / 1000);
  if (diffSec < 60) return '방금 전';
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)}분 전`;
  if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}시간 전`;
  if (diffSec < 86400 * 7) return `${Math.floor(diffSec / 86400)}일 전`;
  const y = t.getFullYear();
  const m = String(t.getMonth() + 1).padStart(2, '0');
  const d = String(t.getDate()).padStart(2, '0');
  return `${y}.${m}.${d}`;
}

/**
 * 신뢰도 점수 → 레벨 변환 (백엔드와 동일 규칙)
 */
export function reliabilityLevelFromScore(score: number): ReliabilityLevel {
  if (score >= 90) return 'very_high';
  if (score >= 70) return 'high';
  if (score >= 50) return 'medium';
  return 'low';
}

/**
 * 기사의 표시 제목 — translated 우선, original fallback
 */
export function pickDisplayTitle(article: {
  title_translated: string | null;
  title_original: string;
}): string {
  return article.title_translated || article.title_original;
}
