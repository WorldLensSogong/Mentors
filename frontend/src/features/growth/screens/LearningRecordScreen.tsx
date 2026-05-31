import { useEffect, useRef, useState } from 'react';
import { useNavigation, type NavigationProp } from '@react-navigation/native';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { colors } from '@/constants/colors';
import { getGrowthApiErrorMessage, getGrowthProgress } from '@/features/growth/api';
import type { GrowthProgressResponse } from '@/features/growth/types';
import {
  getCurrentTierQuizzes,
  getLearningApiErrorMessage,
  submitLearningQuiz,
} from '@/features/learning/api';
import type {
  LearningQuiz,
  SubmitLearningQuizRequest,
  SubmitLearningQuizResponse,
} from '@/features/learning/types';
import { useUserStore } from '@/store/userStore';
import {
  buildGrowthProgressQueryKey,
  didGrowthProgressAdvance,
  getLearningRecordHintMessage,
  getLearningRecordSegments,
  type LearningRecordSegmentKey,
} from '@/features/growth/logic';
import type { AppStackParamList } from '@/navigation/types';

// ──────────────────────────────────────────────
// Types & Helpers
// ──────────────────────────────────────────────
type QuizResultTone = 'correct' | 'incorrect' | 'review';

interface QuizSubmissionState {
  correct: boolean;
  explanation: string;
  syncState: 'idle' | 'syncing' | 'synced' | 'delayed';
  message: string | null;
}

function wait(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function getQuizResultState(
  quiz: LearningQuiz,
  submissionState: QuizSubmissionState | undefined,
): { label: string; tone: QuizResultTone } {
  if (submissionState) {
    // 정답이면 즉시 완료로 표시
    if (submissionState.correct) {
      return { label: '정답 완료', tone: 'correct' };
    }
    return { label: '다시 도전', tone: 'incorrect' };
  }
  if (quiz.solved) return { label: '정답 완료', tone: 'correct' };
  if (quiz.attempted) {
    return {
      label: quiz.last_result_correct === false ? '다시 도전' : '풀이 기록',
      tone: quiz.last_result_correct === false ? 'incorrect' : 'review',
    };
  }
  return { label: '미응시', tone: 'review' };
}

// ──────────────────────────────────────────────
// Sub Components
// ──────────────────────────────────────────────
function QuizResultChip({ label, tone }: { label: string; tone: QuizResultTone }) {
  const chipStyle =
    tone === 'correct'
      ? styles.chipCorrect
      : tone === 'incorrect'
        ? styles.chipIncorrect
        : styles.chipReview;
  const textStyle =
    tone === 'correct'
      ? styles.chipTextCorrect
      : tone === 'incorrect'
        ? styles.chipTextIncorrect
        : styles.chipTextReview;
  return (
    <View style={[styles.quizResultChip, chipStyle]}>
      <Text style={[styles.quizResultChipText, textStyle]}>{label}</Text>
    </View>
  );
}

function QuizCard({
  quiz,
  tierLabel,
  expanded,
  selectedAnswerIndex,
  submissionState,
  errorMessage,
  isSubmitting,
  onToggle,
  onSelectAnswer,
  onSubmit,
}: {
  quiz: LearningQuiz;
  tierLabel: string;
  expanded: boolean;
  selectedAnswerIndex: number | undefined;
  submissionState: QuizSubmissionState | undefined;
  errorMessage: string | undefined;
  isSubmitting: boolean;
  onToggle: () => void;
  onSelectAnswer: (i: number) => void;
  onSubmit: () => void;
}) {
  const resultState = getQuizResultState(quiz, submissionState);
  return (
    <View style={[styles.card, styles.quizCard, expanded && styles.quizCardExpanded]}>
      <Pressable onPress={onToggle} style={styles.quizCardToggle}>
        <View style={styles.quizIndicator}>
          <Text style={styles.quizIndicatorText}>Q</Text>
        </View>
        <View style={styles.quizBody}>
          <Text style={styles.quizMeta}>{tierLabel}</Text>
          <Text style={styles.quizConcept}>{quiz.concept_name}</Text>
          <Text style={styles.quizQuestion}>{quiz.question}</Text>
          <QuizResultChip label={resultState.label} tone={resultState.tone} />
        </View>
        <Text style={styles.quizArrow}>{expanded ? '⌃' : '⌄'}</Text>
      </Pressable>

      {expanded ? (
        <View style={styles.quizDetail}>
          <View style={styles.quizOptionList}>
            {quiz.options.map((option) => {
              const selected = selectedAnswerIndex === option.index;
              return (
                <Pressable
                  key={option.index}
                  onPress={() => onSelectAnswer(option.index)}
                  style={({ pressed }) => [
                    styles.quizOptionButton,
                    selected ? styles.quizOptionButtonSelected : styles.quizOptionButtonIdle,
                    pressed && styles.quizOptionButtonPressed,
                  ]}
                >
                  <Text style={[styles.quizOptionIndex, selected && styles.quizOptionIndexSelected]}>
                    {option.index + 1}
                  </Text>
                  <Text style={[styles.quizOptionText, selected && styles.quizOptionTextSelected]}>
                    {option.text}
                  </Text>
                </Pressable>
              );
            })}
          </View>
          {errorMessage ? <Text style={styles.quizErrorText}>{errorMessage}</Text> : null}
          {submissionState ? (
            <View style={styles.quizExplanationBox}>
              <Text style={styles.quizExplanationTitle}>
                {submissionState.correct ? '정답 해설' : '오답 해설'}
              </Text>
              <Text style={styles.quizExplanationText}>{submissionState.explanation}</Text>
              {submissionState.message ? (
                <Text style={styles.quizSyncText}>{submissionState.message}</Text>
              ) : null}
            </View>
          ) : null}
          <Pressable
            onPress={onSubmit}
            disabled={selectedAnswerIndex == null || isSubmitting}
            style={({ pressed }) => [
              styles.quizSubmitButton,
              (selectedAnswerIndex == null || isSubmitting) && styles.quizSubmitButtonDisabled,
              pressed && selectedAnswerIndex != null && !isSubmitting && styles.quizSubmitButtonPressed,
            ]}
          >
            <Text style={styles.quizSubmitButtonText}>
              {isSubmitting ? '채점 중...' : '정답 제출하기'}
            </Text>
          </Pressable>
        </View>
      ) : null}
    </View>
  );
}

function InfoCard({ title, description }: { title: string; description: string }) {
  return (
    <View style={[styles.card, styles.infoCard]}>
      <Text style={styles.infoTitle}>{title}</Text>
      <Text style={styles.infoDescription}>{description}</Text>
    </View>
  );
}

// 리포트 탭 (모크 데이터)
function ReportTab({ onNavigateToDebate }: { onNavigateToDebate: () => void }) {
  const reports = [
    {
      id: '1',
      date: '2026-05-30',
      title: '금리 인하 기대와 성장주의 관계',
      mentor: '가치투자 멘토',
      summary: '미 연준의 금리 정책 변화가 성장주 밸류에이션에 미치는 영향을 분석했습니다.',
    },
    {
      id: '2',
      date: '2026-05-29',
      title: '안전마진을 활용한 저평가 기업 발굴',
      mentor: '모멘텀 멘토',
      summary: '내재가치 대비 충분한 안전마진을 가진 종목을 찾는 방법을 정리했습니다.',
    },
  ];

  if (reports.length === 0) {
    return (
      <InfoCard
        title="아직 저장된 리포트가 없어요"
        description="멘토 채팅을 하면 대화 내용 기반으로 리포트가 생성될 예정이에요."
      />
    );
  }

  return (
    <>
      {reports.map((report) => (
        <Pressable
          key={report.id}
          style={({ pressed }) => [styles.card, styles.reportCard, pressed && { opacity: 0.9 }]}
        >
          <View style={styles.reportHeader}>
            <Text style={styles.reportMentor}>{report.mentor}</Text>
            <Text style={styles.reportDate}>{report.date}</Text>
          </View>
          <Text style={styles.reportTitle}>{report.title}</Text>
          <Text style={styles.reportSummary} numberOfLines={2}>{report.summary}</Text>
        </Pressable>
      ))}
    </>
  );
}

// 투기장 탭 (모크 데이터)
function ArenaTab({ onNavigateToArena }: { onNavigateToArena: () => void }) {
  const records = [
    {
      id: '1',
      date: '2026-05-28',
      topic: '금리 인상기에 성장주 vs 가치주 어느 쪽이 유리한가',
      mentorA: '가치투자',
      mentorB: '모멘텀',
    },
  ];

  if (records.length === 0) {
    return (
      <InfoCard
        title="아직 투기장 기록이 없어요"
        description="투기장 탭에서 두 멘토의 토론을 시작해 보세요."
      />
    );
  }

  return (
    <>
      {records.map((record) => (
        <Pressable
          key={record.id}
          onPress={onNavigateToArena}
          style={({ pressed }) => [styles.card, styles.arenaCard, pressed && { opacity: 0.9 }]}
        >
          <View style={styles.arenaHeader}>
            <View style={styles.arenaVsRow}>
              <Text style={styles.arenaMentor}>{record.mentorA}</Text>
              <Text style={styles.arenaVs}>⚔️</Text>
              <Text style={styles.arenaMentor}>{record.mentorB}</Text>
            </View>
            <Text style={styles.reportDate}>{record.date}</Text>
          </View>
          <Text style={styles.arenaTopic}>{record.topic}</Text>
          <Text style={styles.arenaLink}>기록 보기 →</Text>
        </Pressable>
      ))}
    </>
  );
}

// ──────────────────────────────────────────────
// Main Screen
// ──────────────────────────────────────────────
export function LearningRecordScreen() {
  const navigation = useNavigation<NavigationProp<AppStackParamList>>();
  const accessToken = useUserStore((state) => state.accessToken);
  const queryClient = useQueryClient();

  const [selectedSegment, setSelectedSegment] = useState<LearningRecordSegmentKey>('quizzes');
  const [expandedQuizConceptId, setExpandedQuizConceptId] = useState<number | null>(null);
  const [selectedAnswerByConceptId, setSelectedAnswerByConceptId] = useState<Record<number, number | undefined>>({});
  const [quizSubmissionByConceptId, setQuizSubmissionByConceptId] = useState<Record<number, QuizSubmissionState>>({});
  const [quizErrorByConceptId, setQuizErrorByConceptId] = useState<Record<number, string>>({});

  const growthQueryKey = buildGrowthProgressQueryKey(accessToken);
  const learningQuizzesQueryKey = ['learning-quizzes', accessToken] as const;
  const prevTierRef = useRef<string | null>(null);

  const growthProgressQuery = useQuery({
    queryKey: growthQueryKey,
    queryFn: getGrowthProgress,
    enabled: Boolean(accessToken),
    retry: 0,
  });

  const learningQuizzesQuery = useQuery({
    queryKey: learningQuizzesQueryKey,
    queryFn: getCurrentTierQuizzes,
    enabled: Boolean(accessToken),
    retry: 0,
  });

  // 티어 변경 감지 → 퀴즈 목록 갱신
  useEffect(() => {
    const currentTier = growthProgressQuery.data?.current_tier ?? null;
    if (currentTier === null) return;
    if (prevTierRef.current !== null && prevTierRef.current !== currentTier) {
      setExpandedQuizConceptId(null);
      setSelectedAnswerByConceptId({});
      setQuizSubmissionByConceptId({});
      setQuizErrorByConceptId({});
      void queryClient.invalidateQueries({ queryKey: learningQuizzesQueryKey });
    }
    prevTierRef.current = currentTier;
  }, [growthProgressQuery.data?.current_tier, queryClient, learningQuizzesQueryKey]);

  const submitQuizMutation = useMutation<
    SubmitLearningQuizResponse,
    unknown,
    SubmitLearningQuizRequest,
    { previousGrowthProgress: GrowthProgressResponse | null }
  >({
    mutationFn: submitLearningQuiz,
    onMutate: (variables) => {
      setQuizErrorByConceptId((current) => ({ ...current, [variables.concept_id]: '' }));
      return { previousGrowthProgress: growthProgressQuery.data ?? null };
    },
    onSuccess: async (result, variables, context) => {
      // 정답 여부에 따라 즉시 로컬 상태 업데이트
      const initialState: QuizSubmissionState = {
        correct: result.correct,
        explanation: result.explanation,
        syncState: result.correct ? 'syncing' : 'idle',
        message: result.correct
          ? '정답이에요. 성장치에 반영하고 있어요.'
          : '오답이에요. 해설을 확인하고 다시 도전해 보세요.',
      };
      setQuizSubmissionByConceptId((current) => ({
        ...current,
        [variables.concept_id]: initialState,
      }));

      if (accessToken) {
        try {
          await queryClient.invalidateQueries({ queryKey: learningQuizzesQueryKey });
          await queryClient.fetchQuery({ queryKey: learningQuizzesQueryKey, queryFn: getCurrentTierQuizzes });
        } catch { /* ignore */ }
      }

      if (!result.correct) return;

      let nextState: QuizSubmissionState = {
        ...initialState,
        syncState: 'delayed',
        message: '정답이 저장됐어요. 성장치 반영 중...',
      };

      try {
        const prev = context?.previousGrowthProgress ?? null;
        if (!prev) {
          await queryClient.invalidateQueries({ queryKey: growthQueryKey });
          nextState = { ...initialState, syncState: 'synced', message: '성장치가 갱신됐어요.' };
        } else {
          for (let attempt = 0; attempt < 3; attempt += 1) {
            const next = await queryClient.fetchQuery({ queryKey: growthQueryKey, queryFn: getGrowthProgress });
            if (didGrowthProgressAdvance(prev, next)) {
              nextState = { ...initialState, syncState: 'synced', message: '이해도 게이지가 갱신됐어요.' };
              break;
            }
            await wait(450);
          }
          await queryClient.invalidateQueries({ queryKey: growthQueryKey });
        }
      } catch {
        await queryClient.invalidateQueries({ queryKey: growthQueryKey });
      }

      setQuizSubmissionByConceptId((current) => ({ ...current, [variables.concept_id]: nextState }));
    },
    onError: (error, variables) => {
      setQuizErrorByConceptId((current) => ({
        ...current,
        [variables.concept_id]: getLearningApiErrorMessage(error, '퀴즈 제출에 실패했어요.'),
      }));
    },
  });

  const learningErrorMessage = learningQuizzesQuery.error
    ? getLearningApiErrorMessage(learningQuizzesQuery.error, '현재 티어 퀴즈를 불러오지 못했어요.')
    : null;
  const quizCount = learningQuizzesQuery.data?.quizzes.length ?? 0;

  const segmentLabels = [
    { key: 'reports' as LearningRecordSegmentKey, label: '리포트' },
    { key: 'quizzes' as LearningRecordSegmentKey, label: `퀴즈 ${quizCount > 0 ? quizCount : ''}` },
    { key: 'arenas' as LearningRecordSegmentKey, label: '투기장' },
  ];

  function handleQuizSubmit(conceptId: number) {
    const answerIndex = selectedAnswerByConceptId[conceptId];
    if (answerIndex == null) {
      setQuizErrorByConceptId((current) => ({ ...current, [conceptId]: '보기 하나를 고른 뒤 제출해 주세요.' }));
      return;
    }
    submitQuizMutation.mutate({ concept_id: conceptId, answer_index: answerIndex });
  }

  return (
    <SafeAreaView style={styles.screen}>
      <View style={styles.header}>
        <View style={styles.headerRow}>
          <Pressable onPress={() => navigation.goBack()} style={styles.backButton}>
            <Text style={styles.backArrow}>←</Text>
          </Pressable>
          <View style={styles.headerTextGroup}>
            <Text style={styles.headerTitle}>나의 학습 기록</Text>
          </View>
          <Pressable
            onPress={() => navigation.navigate('PromotionTest')}
            style={({ pressed }) => [styles.headerActionButton, pressed && styles.headerActionButtonPressed]}
          >
            <Text style={styles.headerActionButtonText}>승급시험</Text>
          </Pressable>
        </View>
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {/* 세그먼트 컨트롤 */}
        <View style={styles.segmentControl}>
          {segmentLabels.map((segment) => {
            const selected = selectedSegment === segment.key;
            return (
              <Pressable
                key={segment.key}
                onPress={() => setSelectedSegment(segment.key)}
                style={[styles.segmentButton, selected && styles.segmentButtonSelected]}
              >
                <Text style={[styles.segmentButtonText, selected && styles.segmentButtonTextSelected]}>
                  {segment.label}
                </Text>
              </Pressable>
            );
          })}
        </View>

        {/* 힌트 배너 */}
        <View style={styles.hintBanner}>
          <Text style={styles.hintIcon}>ⓘ</Text>
          <Text style={styles.hintText}>{getLearningRecordHintMessage(selectedSegment)}</Text>
        </View>

        {/* 리포트 탭 */}
        {selectedSegment === 'reports' ? (
          <ReportTab onNavigateToDebate={() => navigation.navigate('MainTabs', { screen: 'DebateArena' })} />
        ) : null}

        {/* 퀴즈 탭 */}
        {selectedSegment === 'quizzes' && !accessToken ? (
          <InfoCard title="로그인하면 퀴즈를 풀 수 있어요" description="현재 티어 퀴즈를 풀면 정답 여부와 이해도가 계정과 함께 저장돼요." />
        ) : null}
        {selectedSegment === 'quizzes' && accessToken && learningQuizzesQuery.isLoading ? (
          <View style={styles.loadingBox}><ActivityIndicator color={colors.primary} /></View>
        ) : null}
        {selectedSegment === 'quizzes' && accessToken && !learningQuizzesQuery.isLoading && learningErrorMessage ? (
          <InfoCard title="퀴즈를 불러오지 못했어요" description={learningErrorMessage} />
        ) : null}
        {selectedSegment === 'quizzes' && accessToken && !learningQuizzesQuery.isLoading && !learningErrorMessage && quizCount === 0 ? (
          <InfoCard title="아직 열린 퀴즈가 없어요" description="현재 티어에서 풀 수 있는 퀴즈가 준비되면 여기서 바로 볼 수 있어요." />
        ) : null}
        {selectedSegment === 'quizzes' && learningQuizzesQuery.data
          ? learningQuizzesQuery.data.quizzes.map((quiz) => {
              const isSubmitting =
                submitQuizMutation.isPending && submitQuizMutation.variables?.concept_id === quiz.concept_id;
              return (
                <QuizCard
                  key={quiz.concept_id}
                  quiz={quiz}
                  tierLabel={`${learningQuizzesQuery.data?.tier ?? 'T1'} 개념 퀴즈`}
                  expanded={expandedQuizConceptId === quiz.concept_id}
                  selectedAnswerIndex={selectedAnswerByConceptId[quiz.concept_id]}
                  submissionState={quizSubmissionByConceptId[quiz.concept_id]}
                  errorMessage={quizErrorByConceptId[quiz.concept_id]}
                  isSubmitting={isSubmitting}
                  onToggle={() =>
                    setExpandedQuizConceptId((current) =>
                      current === quiz.concept_id ? null : quiz.concept_id,
                    )
                  }
                  onSelectAnswer={(answerIndex) => {
                    setQuizErrorByConceptId((current) => ({ ...current, [quiz.concept_id]: '' }));
                    setSelectedAnswerByConceptId((current) => ({ ...current, [quiz.concept_id]: answerIndex }));
                  }}
                  onSubmit={() => handleQuizSubmit(quiz.concept_id)}
                />
              );
            })
          : null}

        {/* 투기장 탭 */}
        {selectedSegment === 'arenas' ? (
          <ArenaTab onNavigateToArena={() => navigation.navigate('MainTabs', { screen: 'DebateArena' })} />
        ) : null}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.background },
  header: {
    backgroundColor: colors.surface,
    borderBottomColor: colors.border,
    borderBottomWidth: 1,
    minHeight: 56,
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  headerRow: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 8,
    justifyContent: 'space-between',
  },
  backButton: {
    alignItems: 'center', height: 36, justifyContent: 'center', width: 32,
  },
  backArrow: { color: colors.text, fontSize: 22, fontWeight: '400' },
  headerTextGroup: { flex: 1, gap: 4 },
  headerTitle: { color: colors.text, fontSize: 18, fontWeight: '800' },
  headerActionButton: {
    alignItems: 'center',
    alignSelf: 'flex-start',
    backgroundColor: colors.primary,
    borderRadius: 999,
    justifyContent: 'center',
    minHeight: 34,
    paddingHorizontal: 12,
  },
  headerActionButtonPressed: { opacity: 0.88 },
  headerActionButtonText: { color: colors.surface, fontSize: 13, fontWeight: '700' },
  scrollContent: { gap: 12, paddingBottom: 48, paddingHorizontal: 16, paddingTop: 16 },
  segmentControl: {
    backgroundColor: '#F4F5F4',
    borderRadius: 10,
    flexDirection: 'row',
    padding: 3,
  },
  segmentButton: {
    alignItems: 'center',
    borderRadius: 8,
    flex: 1,
    justifyContent: 'center',
    minHeight: 32,
  },
  segmentButtonSelected: {
    backgroundColor: colors.surface,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 6,
  },
  segmentButtonText: { color: '#AFB4B0', fontSize: 13, fontWeight: '500' },
  segmentButtonTextSelected: { color: colors.primary, fontWeight: '700' },
  hintBanner: {
    alignItems: 'center',
    backgroundColor: colors.accentSoft,
    borderColor: colors.accent,
    borderRadius: 10,
    borderWidth: 1,
    flexDirection: 'row',
    gap: 8,
    minHeight: 40,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  hintIcon: { fontSize: 14 },
  hintText: { color: colors.text, flex: 1, fontSize: 12, fontWeight: '500', lineHeight: 16 },
  loadingBox: { alignItems: 'center', justifyContent: 'center', minHeight: 80 },
  card: {
    backgroundColor: colors.surface,
    borderRadius: 14,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 8,
  },
  infoCard: { gap: 8 },
  infoTitle: { color: colors.text, fontSize: 16, fontWeight: '700' },
  infoDescription: { color: colors.muted, fontSize: 13, lineHeight: 19 },
  reportCard: { gap: 8 },
  reportHeader: { alignItems: 'center', flexDirection: 'row', justifyContent: 'space-between' },
  reportMentor: { color: colors.primary, fontSize: 11, fontWeight: '600' },
  reportDate: { color: '#AFB4B0', fontSize: 11 },
  reportTitle: { color: colors.text, fontSize: 15, fontWeight: '700', lineHeight: 20 },
  reportSummary: { color: colors.muted, fontSize: 13, lineHeight: 18 },
  arenaCard: { gap: 10 },
  arenaHeader: { alignItems: 'center', flexDirection: 'row', justifyContent: 'space-between' },
  arenaVsRow: { alignItems: 'center', flexDirection: 'row', gap: 8 },
  arenaMentor: { color: colors.primary, fontSize: 13, fontWeight: '700' },
  arenaVs: { fontSize: 16 },
  arenaTopic: { color: colors.text, fontSize: 14, fontWeight: '600', lineHeight: 20 },
  arenaLink: { color: colors.muted, fontSize: 12, fontWeight: '600' },
  quizCard: { gap: 14, padding: 0 },
  quizCardExpanded: { paddingBottom: 16 },
  quizCardToggle: { alignItems: 'flex-start', flexDirection: 'row', gap: 12, padding: 16 },
  quizIndicator: {
    alignItems: 'center', backgroundColor: colors.primarySoft, borderRadius: 18,
    height: 36, justifyContent: 'center', width: 36,
  },
  quizIndicatorText: { color: colors.primary, fontSize: 16, fontWeight: '800' },
  quizBody: { flex: 1, gap: 6 },
  quizMeta: { color: colors.primary, fontSize: 11, fontWeight: '500' },
  quizConcept: { color: colors.text, fontSize: 15, fontWeight: '800' },
  quizQuestion: { color: colors.text, fontSize: 13, lineHeight: 19 },
  quizResultChip: {
    alignSelf: 'flex-start', borderRadius: 11, marginTop: 4,
    minHeight: 22, paddingHorizontal: 10, paddingVertical: 4,
  },
  chipCorrect: { backgroundColor: colors.primarySoft },
  chipIncorrect: { backgroundColor: '#FCE7E3' },
  chipReview: { backgroundColor: colors.accentSoft },
  quizResultChipText: { fontSize: 11, fontWeight: '700' },
  chipTextCorrect: { color: colors.primary },
  chipTextIncorrect: { color: colors.rose },
  chipTextReview: { color: '#8A6300' },
  quizArrow: { color: colors.muted, fontSize: 20, lineHeight: 24, marginTop: 18 },
  quizDetail: { borderTopColor: colors.border, borderTopWidth: 1, gap: 12, paddingHorizontal: 16 },
  quizOptionList: { gap: 10, marginTop: 16 },
  quizOptionButton: {
    alignItems: 'flex-start', borderRadius: 16, borderWidth: 1,
    flexDirection: 'row', gap: 12, paddingHorizontal: 14, paddingVertical: 14,
  },
  quizOptionButtonIdle: { backgroundColor: colors.surface, borderColor: colors.border },
  quizOptionButtonSelected: { backgroundColor: colors.primarySoft, borderColor: colors.primary },
  quizOptionButtonPressed: { opacity: 0.88 },
  quizOptionIndex: { color: colors.muted, fontSize: 13, fontWeight: '800', lineHeight: 20, width: 16 },
  quizOptionIndexSelected: { color: colors.primary },
  quizOptionText: { color: colors.text, flex: 1, fontSize: 14, fontWeight: '600', lineHeight: 20 },
  quizOptionTextSelected: { color: colors.primary },
  quizErrorText: { color: colors.rose, fontSize: 13, lineHeight: 18 },
  quizExplanationBox: { backgroundColor: colors.background, borderRadius: 16, gap: 8, padding: 14 },
  quizExplanationTitle: { color: colors.text, fontSize: 13, fontWeight: '700' },
  quizExplanationText: { color: colors.muted, fontSize: 13, lineHeight: 19 },
  quizSyncText: { color: colors.primary, fontSize: 12, fontWeight: '600', lineHeight: 18 },
  quizSubmitButton: {
    alignItems: 'center', backgroundColor: colors.text, borderRadius: 14,
    justifyContent: 'center', minHeight: 44,
  },
  quizSubmitButtonDisabled: { opacity: 0.4 },
  quizSubmitButtonPressed: { opacity: 0.9 },
  quizSubmitButtonText: { color: colors.surface, fontSize: 14, fontWeight: '700' },
});
