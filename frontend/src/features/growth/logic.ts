import type {
  GrowthProgressResponse,
  GrowthStageCopy,
  PromotionTestQuestion,
  PromotionTestRequest,
  PromotionTestResponse,
} from './types';

const unlockLabels: Record<string, string> = {
  debate_arena: '멘토 토론 아레나',
  extra_mentors: '추가 멘토 해금',
};

export type LearningRecordSegmentKey = 'reports' | 'quizzes' | 'arenas';

export function buildGrowthProgressQueryKey(
  accessToken: string | null,
): ['growth-progress', string | null] {
  return ['growth-progress', accessToken];
}

export function getLearningRecordSegments(counts: {
  reports: number;
  quizzes: number;
  arenas: number;
}): { key: LearningRecordSegmentKey; label: string }[] {
  return [
    { key: 'reports', label: `리포트 ${counts.reports}` },
    { key: 'quizzes', label: `퀴즈 ${counts.quizzes}` },
    { key: 'arenas', label: `아레나 ${counts.arenas}` },
  ];
}

export function getLearningRecordHintMessage(segment: LearningRecordSegmentKey): string {
  switch (segment) {
    case 'reports':
      return '이해도에 맞춘 리포트를 다시 열어보고, 놓친 흐름을 복기해 보세요.';
    case 'quizzes':
      return '멘토 채팅 퀴즈와 개념 퀴즈 결과가 여기에서 함께 갱신돼요.';
    case 'arenas':
      return '토론 기록을 열면 멘토별 주장과 내 답변 흐름을 다시 확인할 수 있어요.';
    default:
      return '';
  }
}

export function isPromotionTestComplete(
  questions: PromotionTestQuestion[],
  answersByQuestionId: Record<string, string>,
): boolean {
  return (
    questions.length > 0 &&
    questions.every((question) => Boolean(answersByQuestionId[question.question_id]))
  );
}

export function buildPromotionTestPayload(
  questions: PromotionTestQuestion[],
  answersByQuestionId: Record<string, string>,
): PromotionTestRequest {
  return {
    answers: questions.flatMap((question) => {
      const choiceId = answersByQuestionId[question.question_id];
      if (!choiceId) {
        return [];
      }

      return [
        {
          question_id: question.question_id,
          choice_id: choiceId,
        },
      ];
    }),
  };
}

export function getUnlockLabel(code: string): string {
  return unlockLabels[code] ?? code.replace(/_/g, ' ');
}

export function didGrowthProgressAdvance(
  previous: GrowthProgressResponse | null,
  next: GrowthProgressResponse | null,
): boolean {
  if (!previous || !next) {
    return false;
  }

  return (
    next.current_tier !== previous.current_tier ||
    next.mastered_concepts > previous.mastered_concepts ||
    next.progress_percent > previous.progress_percent ||
    (!previous.eligible_for_promotion && next.eligible_for_promotion)
  );
}

export function applyOptimisticSolvedQuizProgress(
  progress: GrowthProgressResponse | null,
): GrowthProgressResponse | null {
  if (!progress) {
    return null;
  }

  if (progress.total_concepts <= 0) {
    return progress;
  }

  const nextMasteredConcepts = Math.min(progress.total_concepts, progress.mastered_concepts + 1);
  if (nextMasteredConcepts === progress.mastered_concepts) {
    return progress;
  }

  const nextProgressPercent = Math.floor((nextMasteredConcepts / progress.total_concepts) * 100);

  return {
    ...progress,
    mastered_concepts: nextMasteredConcepts,
    progress_percent: nextProgressPercent,
    eligible_for_promotion: Boolean(progress.next_tier) && nextProgressPercent >= 80,
  };
}

export function getGrowthStageCopy(progress: GrowthProgressResponse): GrowthStageCopy {
  if (progress.eligible_for_promotion && progress.next_tier) {
    return {
      badge: '승급 가능',
      title: `${progress.next_tier} 승급시험을 볼 준비가 됐어요`,
      description: `현재 티어 이해도 ${progress.progress_percent}%를 달성했어요. 지금 바로 승급시험을 시작할 수 있어요.`,
    };
  }

  if (!progress.next_tier) {
    return {
      badge: '최종 티어',
      title: `${progress.current_tier} 최종 티어에 도달했어요`,
      description: '이미 마지막 티어예요. 열려 있는 기능을 충분히 활용해 보세요.',
    };
  }

  const remaining = Math.max(0, 80 - progress.progress_percent);
  return {
    badge: '성장 진행 중',
    title: `현재 ${progress.current_tier} 이해도를 쌓는 중이에요`,
    description: `개념 ${progress.mastered_concepts}/${progress.total_concepts}개를 완료했어요. 승급시험까지 ${remaining}%만 더 채우면 돼요.`,
  };
}

export function getPromotionResultHeadline(result: PromotionTestResponse): string {
  if (result.passed) {
    return `${result.current_tier}로 승급했어요`;
  }

  return `이번에는 ${result.previous_tier} 유지예요`;
}
