const assert = require('node:assert/strict');

const {
  applyOptimisticSolvedQuizProgress,
  buildGrowthProgressQueryKey,
  buildPromotionTestPayload,
  didGrowthProgressAdvance,
  getGrowthStageCopy,
  getLearningRecordHintMessage,
  getLearningRecordSegments,
  getPromotionResultHeadline,
  getUnlockLabel,
  isPromotionTestComplete,
} = require('../../.tmp-harness-growth/_dev-harness/growth/logic.js');

const eligibleProgress = {
  current_tier: 'T1',
  next_tier: 'T2',
  progress_percent: 80,
  mastered_concepts: 4,
  total_concepts: 5,
  eligible_for_promotion: true,
  promotion_eligible_at: '2026-05-15T09:00:00Z',
  unlocked_features: [],
  next_unlocks: ['debate_arena'],
  promotion_test: {
    target_tier: 'T2',
    passing_score: 80,
    question_count: 2,
    questions: [
      {
        question_id: 't1-q1',
        prompt: 'Question 1',
        choices: [
          { choice_id: 'A', text: 'Choice A' },
          { choice_id: 'B', text: 'Choice B' },
        ],
      },
      {
        question_id: 't1-q2',
        prompt: 'Question 2',
        choices: [
          { choice_id: 'A', text: 'Choice A' },
          { choice_id: 'B', text: 'Choice B' },
        ],
      },
    ],
  },
};

assert.equal(
  isPromotionTestComplete(eligibleProgress.promotion_test.questions, { 't1-q1': 'A' }),
  false,
  'every question should need an answer before submit is enabled',
);

assert.equal(
  isPromotionTestComplete(eligibleProgress.promotion_test.questions, {
    't1-q1': 'A',
    't1-q2': 'B',
  }),
  true,
  'submit should unlock when all question ids have answers',
);

assert.deepEqual(
  buildPromotionTestPayload(eligibleProgress.promotion_test.questions, {
    't1-q2': 'B',
    't1-q1': 'A',
  }),
  {
    answers: [
      { question_id: 't1-q1', choice_id: 'A' },
      { question_id: 't1-q2', choice_id: 'B' },
    ],
  },
  'payload should preserve the server question order',
);

assert.equal(getUnlockLabel('debate_arena'), '멘토 토론 아레나');
assert.equal(getUnlockLabel('extra_mentors'), '추가 멘토 해금');
assert.equal(getUnlockLabel('mystery_feature'), 'mystery feature');

assert.deepEqual(getLearningRecordSegments({ reports: 3, quizzes: 5, arenas: 4 }), [
  { key: 'reports', label: '리포트 3' },
  { key: 'quizzes', label: '퀴즈 5' },
  { key: 'arenas', label: '아레나 4' },
]);

assert.equal(
  didGrowthProgressAdvance(eligibleProgress, {
    ...eligibleProgress,
    progress_percent: 80,
    mastered_concepts: 4,
  }),
  false,
  'unchanged growth snapshots should not stop the sync retry loop early',
);

assert.equal(
  didGrowthProgressAdvance(eligibleProgress, {
    ...eligibleProgress,
    progress_percent: 100,
    mastered_concepts: 5,
    eligible_for_promotion: true,
  }),
  true,
  'a higher mastered concept count should be treated as synced growth progress',
);

assert.deepEqual(
  applyOptimisticSolvedQuizProgress({
    ...eligibleProgress,
    progress_percent: 60,
    mastered_concepts: 3,
    promotion_test: null,
    eligible_for_promotion: false,
  }),
  {
    ...eligibleProgress,
    progress_percent: 80,
    mastered_concepts: 4,
    promotion_test: null,
    eligible_for_promotion: true,
  },
  'a newly solved quiz should immediately raise the local growth gauge without waiting for async event propagation',
);

assert.equal(
  getLearningRecordHintMessage('reports'),
  '이해도에 맞춘 리포트를 다시 열어보고, 놓친 흐름을 복기해 보세요.',
);
assert.equal(
  getLearningRecordHintMessage('quizzes'),
  '멘토 채팅 퀴즈와 개념 퀴즈 결과가 여기에서 함께 갱신돼요.',
);

assert.deepEqual(getGrowthStageCopy(eligibleProgress), {
  badge: '승급 가능',
  title: 'T2 승급시험을 볼 준비가 됐어요',
  description: '현재 티어 이해도 80%를 달성했어요. 지금 바로 승급시험을 시작할 수 있어요.',
});

assert.deepEqual(
  getGrowthStageCopy({
    ...eligibleProgress,
    progress_percent: 40,
    mastered_concepts: 2,
    eligible_for_promotion: false,
    promotion_test: null,
  }),
  {
    badge: '성장 진행 중',
    title: '현재 T1 이해도를 쌓는 중이에요',
    description: '개념 2/5개를 완료했어요. 승급시험까지 40%만 더 채우면 돼요.',
  },
);

assert.equal(
  getPromotionResultHeadline({
    previous_tier: 'T1',
    current_tier: 'T2',
    target_tier: 'T2',
    passed: true,
    score_percent: 80,
    correct_answers: 4,
    total_questions: 5,
    unlocked_features: ['debate_arena'],
    message: 'Promotion test passed.',
  }),
  'T2로 승급했어요',
);

assert.equal(
  getPromotionResultHeadline({
    previous_tier: 'T2',
    current_tier: 'T2',
    target_tier: 'T3',
    passed: false,
    score_percent: 60,
    correct_answers: 3,
    total_questions: 5,
    unlocked_features: ['debate_arena'],
    message: 'Promotion test not passed. You can retry immediately.',
  }),
  '이번에는 T2 유지예요',
);

assert.deepEqual(
  buildGrowthProgressQueryKey('token'),
  ['growth-progress', 'token'],
  'growth progress query keys should stay identical across screens so chat quiz submissions refresh the same gauge',
);

assert.deepEqual(
  buildGrowthProgressQueryKey(null),
  ['growth-progress', null],
  'growth progress query keys should also be stable before authentication is available',
);

console.log('growth logic tests passed');
