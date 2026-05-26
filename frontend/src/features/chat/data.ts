import type { CompletedOnboardingProfile, InterestTag } from '../onboarding/types';
import type { LearningChatMentorId, LearningChatMentorProfile } from './types';

export const learningChatMentors: LearningChatMentorProfile[] = [
  {
    id: 1,
    label: '가치 멘토',
    shortLabel: '가치',
    description: '기업 가치와 재무제표를 중심으로 차분하게 개념을 정리해 줍니다.',
    focusLabel: '수익성 · 현금흐름 · 장기 관점',
    accentColor: '#2D6A4F',
    avatarTint: '#E1F5EE',
  },
  {
    id: 2,
    label: '성장 멘토',
    shortLabel: '성장',
    description: '시장 크기와 매출 성장, 기술 경쟁력을 빠르게 짚어 줍니다.',
    focusLabel: '시장 규모 · 매출 성장 · 연구개발',
    accentColor: '#2F6FED',
    avatarTint: '#EAF1FF',
  },
  {
    id: 3,
    label: '배당 멘토',
    shortLabel: '배당',
    description: '현금흐름과 배당 지속 가능성을 안정적으로 설명해 줍니다.',
    focusLabel: '배당 성향 · 현금흐름 · 방어주',
    accentColor: '#B26A00',
    avatarTint: '#FFF2D8',
  },
  {
    id: 4,
    label: '모멘텀 멘토',
    shortLabel: '모멘텀',
    description: '추세와 리스크 관리를 중심으로 빠르게 흐름을 정리해 줍니다.',
    focusLabel: '추세 강도 · 거래량 · 손절 기준',
    accentColor: '#A4435B',
    avatarTint: '#FCE8EE',
  },
];

const growthInterestTags: InterestTag[] = ['tech', 'it', 'ai', 'bio', 'us-stock', 'semiconductor'];
const momentumInterestTags: InterestTag[] = ['crypto', 'battery', 'defense', 'entertainment-media'];

function includesAnyInterest(interests: InterestTag[], candidates: InterestTag[]): boolean {
  return candidates.some((candidate) => interests.includes(candidate));
}

export function getLearningChatMentorById(
  mentorId: LearningChatMentorId,
): LearningChatMentorProfile {
  return learningChatMentors.find((mentor) => mentor.id === mentorId) ?? learningChatMentors[0];
}

export function resolveSuggestedLearningMentorId(
  profile: CompletedOnboardingProfile | null,
): LearningChatMentorId {
  if (!profile) {
    return 1;
  }

  if (profile.selectedMentorId === 1 || profile.selectedMentorId === 2) {
    return profile.selectedMentorId;
  }

  if (profile.interests.includes('dividend') || profile.riskProfile === 'steady') {
    return 3;
  }

  if (
    includesAnyInterest(profile.interests, momentumInterestTags) ||
    profile.riskProfile === 'bold'
  ) {
    return 4;
  }

  if (includesAnyInterest(profile.interests, growthInterestTags)) {
    return 2;
  }

  return 1;
}
