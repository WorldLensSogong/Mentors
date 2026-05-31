import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useQuery } from '@tanstack/react-query';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { colors } from '@/constants/colors';
import { getGrowthApiErrorMessage, getPromotionHistory } from '@/features/growth/api';
import type { PromotionAttemptDetail, PromotionQuestionResult } from '@/features/growth/types';
import { useUserStore } from '@/store/userStore';
import type { AppStackParamList } from '@/navigation/types';

type Nav = NativeStackNavigationProp<AppStackParamList, 'PromotionResult'>;

function formatDate(iso: string): string {
  const d = new Date(iso);
  return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, '0')}.${String(d.getDate()).padStart(2, '0')}`;
}

function QuestionRow({ q, index }: { q: PromotionQuestionResult; index: number }) {
  const isApplication = q.question_id.includes('-a');
  return (
    <View style={[styles.questionCard, q.is_correct ? styles.questionCorrect : styles.questionWrong]}>
      <View style={styles.questionHeader}>
        <View style={[styles.qBadge, isApplication ? styles.qBadgeApp : styles.qBadgeReuse]}>
          <Text style={styles.qBadgeText}>{isApplication ? '응용' : '팔로우업'}</Text>
        </View>
        <Text style={[styles.qResult, q.is_correct ? styles.correct : styles.wrong]}>
          {q.is_correct ? '✓ 정답' : '✗ 오답'}
        </Text>
      </View>
      <Text style={styles.questionPrompt}>{index + 1}. {q.prompt}</Text>
      <View style={styles.choicesGrid}>
        {Object.entries(q.choices).map(([choiceId, text]) => {
          const isUserChoice = q.user_choice_id === choiceId;
          const isCorrectChoice = q.correct_choice_id === choiceId;
          return (
            <View
              key={choiceId}
              style={[
                styles.choiceRow,
                isCorrectChoice && styles.choiceCorrect,
                isUserChoice && !isCorrectChoice && styles.choiceWrong,
              ]}
            >
              <Text style={[
                styles.choiceId,
                isCorrectChoice && styles.choiceIdCorrect,
                isUserChoice && !isCorrectChoice && styles.choiceIdWrong,
              ]}>
                {choiceId}
              </Text>
              <Text style={[
                styles.choiceText,
                isCorrectChoice && styles.choiceTextCorrect,
              ]} numberOfLines={3}>
                {text}
              </Text>
              {isUserChoice && (
                <Text style={styles.choiceTag}>{isCorrectChoice ? '✓' : '✗'}</Text>
              )}
            </View>
          );
        })}
      </View>
    </View>
  );
}

function AttemptCard({
  attempt,
  isExpanded,
  onToggle,
}: {
  attempt: PromotionAttemptDetail;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  return (
    <View style={styles.attemptCard}>
      <Pressable onPress={onToggle} style={styles.attemptHeader}>
        <View style={styles.attemptMeta}>
          <View style={[styles.resultBadge, attempt.passed ? styles.badgePassed : styles.badgeFailed]}>
            <Text style={[styles.resultBadgeText, attempt.passed ? styles.passedText : styles.failedText]}>
              {attempt.passed ? '합격' : '불합격'}
            </Text>
          </View>
          <View style={styles.attemptInfo}>
            <Text style={styles.attemptTierText}>
              {attempt.current_tier} → {attempt.target_tier ?? '?'}
            </Text>
            <Text style={styles.attemptDate}>{formatDate(attempt.attempted_at)}</Text>
          </View>
        </View>
        <View style={styles.attemptScore}>
          <Text style={styles.scoreText}>{attempt.score_percent}점</Text>
          <Text style={styles.scoreSub}>
            {attempt.correct_answers}/{attempt.total_questions}
          </Text>
        </View>
        <Text style={styles.expandArrow}>{isExpanded ? '⌃' : '⌄'}</Text>
      </Pressable>

      {isExpanded && (
        <View style={styles.questionList}>
          {attempt.question_results.map((q, i) => (
            <QuestionRow key={q.question_id} q={q} index={i} />
          ))}
        </View>
      )}
    </View>
  );
}

export function PromotionResultScreen() {
  const navigation = useNavigation<Nav>();
  const accessToken = useUserStore((state) => state.accessToken);
  const [expandedId, setExpandedId] = React.useState<number | null>(null);

  const historyQuery = useQuery({
    queryKey: ['promotion-history', accessToken],
    queryFn: getPromotionHistory,
    enabled: Boolean(accessToken),
    retry: 1,
  });

  return (
    <SafeAreaView style={styles.screen}>
      <View style={styles.header}>
        <Pressable onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Text style={styles.backArrow}>←</Text>
        </Pressable>
        <Text style={styles.headerTitle}>승급시험 결과</Text>
      </View>

      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        {historyQuery.isLoading && (
          <View style={styles.center}><ActivityIndicator color={colors.primary} /></View>
        )}
        {historyQuery.error && !historyQuery.isLoading && (
          <View style={styles.emptyCard}>
            <Text style={styles.emptyTitle}>결과를 불러오지 못했어요</Text>
            <Text style={styles.emptyDesc}>
              {getGrowthApiErrorMessage(historyQuery.error, '잠시 후 다시 시도해 주세요.')}
            </Text>
          </View>
        )}
        {!historyQuery.isLoading && !historyQuery.error && historyQuery.data?.length === 0 && (
          <View style={styles.emptyCard}>
            <Text style={styles.emptyTitle}>아직 응시한 승급시험이 없어요</Text>
            <Text style={styles.emptyDesc}>
              이해도 게이지를 80% 이상 채운 뒤 승급시험에 도전해 보세요.
            </Text>
            <Pressable
              onPress={() => navigation.navigate('PromotionTest')}
              style={styles.ctaButton}
            >
              <Text style={styles.ctaButtonText}>승급시험 도전하기</Text>
            </Pressable>
          </View>
        )}
        {historyQuery.data?.map((attempt) => (
          <AttemptCard
            key={attempt.id}
            attempt={attempt}
            isExpanded={expandedId === attempt.id}
            onToggle={() => setExpandedId((prev) => (prev === attempt.id ? null : attempt.id))}
          />
        ))}
      </ScrollView>
    </SafeAreaView>
  );
}

// Need to import React for useState
import React from 'react';

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.background },
  header: {
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderBottomColor: colors.border,
    borderBottomWidth: 1,
    flexDirection: 'row',
    gap: 8,
    height: 56,
    paddingHorizontal: 16,
  },
  backBtn: { alignItems: 'center', height: 32, justifyContent: 'center', width: 32 },
  backArrow: { color: colors.text, fontSize: 22, fontWeight: '400' },
  headerTitle: { color: colors.text, fontSize: 17, fontWeight: '700' },
  scroll: { gap: 12, paddingHorizontal: 16, paddingTop: 16, paddingBottom: 48 },
  center: { alignItems: 'center', justifyContent: 'center', minHeight: 120 },
  emptyCard: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 20,
    borderWidth: 1,
    gap: 10,
    padding: 24,
  },
  emptyTitle: { color: colors.text, fontSize: 17, fontWeight: '800' },
  emptyDesc: { color: colors.muted, fontSize: 14, lineHeight: 20 },
  ctaButton: {
    alignItems: 'center',
    backgroundColor: colors.primary,
    borderRadius: 12,
    marginTop: 8,
    paddingHorizontal: 20,
    paddingVertical: 14,
  },
  ctaButtonText: { color: colors.surface, fontSize: 14, fontWeight: '700' },
  attemptCard: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 16,
    borderWidth: 1,
    overflow: 'hidden',
  },
  attemptHeader: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 12,
    padding: 16,
  },
  attemptMeta: { flex: 1, flexDirection: 'row', alignItems: 'center', gap: 10 },
  resultBadge: {
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  badgePassed: { backgroundColor: colors.primarySoft },
  badgeFailed: { backgroundColor: '#FCE7E3' },
  resultBadgeText: { fontSize: 12, fontWeight: '800' },
  passedText: { color: colors.primary },
  failedText: { color: colors.rose },
  attemptInfo: { gap: 2 },
  attemptTierText: { color: colors.text, fontSize: 15, fontWeight: '700' },
  attemptDate: { color: colors.muted, fontSize: 12 },
  attemptScore: { alignItems: 'flex-end', gap: 2 },
  scoreText: { color: colors.text, fontSize: 18, fontWeight: '800' },
  scoreSub: { color: colors.muted, fontSize: 12 },
  expandArrow: { color: colors.muted, fontSize: 18 },
  questionList: {
    borderTopColor: colors.border,
    borderTopWidth: 1,
    gap: 10,
    padding: 12,
  },
  questionCard: {
    borderRadius: 12,
    borderWidth: 1,
    gap: 10,
    padding: 12,
  },
  questionCorrect: {
    backgroundColor: '#F0FAF5',
    borderColor: '#A8D8C0',
  },
  questionWrong: {
    backgroundColor: '#FFF5F5',
    borderColor: '#F1CACA',
  },
  questionHeader: { alignItems: 'center', flexDirection: 'row', gap: 8 },
  qBadge: { borderRadius: 6, paddingHorizontal: 6, paddingVertical: 3 },
  qBadgeReuse: { backgroundColor: colors.primarySoft },
  qBadgeApp: { backgroundColor: colors.accentSoft },
  qBadgeText: { fontSize: 10, fontWeight: '700', color: colors.muted },
  qResult: { fontSize: 13, fontWeight: '800', marginLeft: 'auto' },
  correct: { color: colors.primary },
  wrong: { color: colors.rose },
  questionPrompt: { color: colors.text, fontSize: 13, fontWeight: '600', lineHeight: 19 },
  choicesGrid: { gap: 6 },
  choiceRow: {
    alignItems: 'flex-start',
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    backgroundColor: colors.surface,
    flexDirection: 'row',
    gap: 8,
    padding: 8,
  },
  choiceCorrect: { backgroundColor: '#E8F5EF', borderColor: colors.primary },
  choiceWrong: { backgroundColor: '#FEE2E2', borderColor: colors.rose },
  choiceId: { color: colors.muted, fontSize: 12, fontWeight: '800', width: 14 },
  choiceIdCorrect: { color: colors.primary },
  choiceIdWrong: { color: colors.rose },
  choiceText: { color: colors.text, flex: 1, fontSize: 12, lineHeight: 17 },
  choiceTextCorrect: { color: colors.primary, fontWeight: '600' },
  choiceTag: { fontSize: 12, fontWeight: '800' },
});
