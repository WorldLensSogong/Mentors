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

export function getGrowthStageCopy(progress: GrowthProgressResponse): GrowthStageCopy {
  if (progress.eligible_for_promotion && progress.next_tier) {
    return {
      badge: '승급 가능',
      title: `${progress.next_tier} 승급시험에 도전할 수 있어요`,
      description: `현재 티어 이해도 ${progress.progress_percent}%를 달성했어요. 지금 바로 시험을 시작할 수 있어요.`,
    };
  }

  if (!progress.next_tier) {
    return {
      badge: '최고 티어',
      title: `${progress.current_tier} 최종 티어에 도달했어요`,
      description: '이미 최종 티어예요. 열려 있는 기능을 충분히 활용해 보세요.',
    };
  }

  const remaining = Math.max(0, 80 - progress.progress_percent);
  return {
    badge: '성장 진행 중',
    title: `현재 ${progress.current_tier} 이해도를 쌓는 중이에요`,
    description: `개념 ${progress.mastered_concepts}/${progress.total_concepts}개를 완료했어요. 승급시험까지 ${remaining}% 더 채우면 됩니다.`,
  };
}

export function getPromotionResultHeadline(result: PromotionTestResponse): string {
  if (result.passed) {
    return `${result.current_tier}로 승급했어요`;
  }

  return `이번에는 ${result.previous_tier} 유지예요`;
}
