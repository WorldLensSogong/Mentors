import { useEffect, useState } from 'react';
import { useNavigation } from '@react-navigation/native';
import { type NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
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
import { getAuthApiErrorMessage } from '@/features/auth/api';
import { getOnboardingStatus, saveOnboardingProfile } from '@/features/onboarding/api';
import type { InterestTag } from '@/features/onboarding/types';
import { useUserStore } from '@/store/userStore';
import type { AppStackParamList } from '@/navigation/types';
import { buildLearningPreferencesPayload } from '@/features/settings/logic';

type Nav = NativeStackNavigationProp<AppStackParamList, 'InterestSettings'>;

// ── 계층형 관심사 구조 ─────────────────────────────────
interface SubItem { tag: InterestTag; label: string }
interface InterestGroup { id: string; label: string; emoji: string; tags: InterestTag[]; subs: SubItem[] }

const INTEREST_GROUPS: InterestGroup[] = [
  {
    id: 'stocks', label: '주식', emoji: '📈',
    tags: ['domestic-stock', 'us-stock', 'global'],
    subs: [
      { tag: 'domestic-stock', label: '국내 주식 (코스피·코스닥)' },
      { tag: 'us-stock', label: '미국 주식 (나스닥·S&P500)' },
      { tag: 'global', label: '해외 주식 (미국 외)' },
    ],
  },
  {
    id: 'tech', label: 'IT·테크', emoji: '💻',
    tags: ['it'],
    subs: [
      { tag: 'it', label: '소프트웨어·플랫폼' },
      { tag: 'it', label: '보안·네트워크' },
      { tag: 'it', label: '클라우드·SaaS' },
      { tag: 'it', label: '인터넷·이커머스' },
    ],
  },
  {
    id: 'hardware', label: '반도체·전자', emoji: '💾',
    tags: ['semiconductor', 'battery'],
    subs: [
      { tag: 'semiconductor', label: '반도체 설계·제조' },
      { tag: 'semiconductor', label: '반도체 장비·소재' },
      { tag: 'battery', label: '2차전지·배터리' },
      { tag: 'battery', label: '디스플레이·가전' },
    ],
  },
  {
    id: 'ai', label: 'AI', emoji: '🤖',
    tags: ['ai'],
    subs: [
      { tag: 'ai', label: 'AI 서비스·앱' },
      { tag: 'ai', label: 'AI 인프라·칩' },
      { tag: 'ai', label: 'AI 로봇·자동화' },
    ],
  },
  {
    id: 'energy', label: '에너지', emoji: '⚡',
    tags: ['energy'],
    subs: [
      { tag: 'energy', label: '신재생 에너지 (태양광·풍력)' },
      { tag: 'energy', label: '원유·천연가스' },
      { tag: 'energy', label: '원자력·전력설비' },
    ],
  },
  {
    id: 'finance', label: '금융', emoji: '💵',
    tags: ['finance', 'crypto'],
    subs: [
      { tag: 'finance', label: '은행·보험' },
      { tag: 'finance', label: '증권·자산운용' },
      { tag: 'finance', label: '핀테크·결제' },
      { tag: 'crypto', label: '암호화폐·블록체인' },
    ],
  },
  {
    id: 'bio', label: '바이오·헬스', emoji: '🧬',
    tags: ['bio'],
    subs: [
      { tag: 'bio', label: '제약·신약 개발' },
      { tag: 'bio', label: '의료기기·서비스' },
      { tag: 'bio', label: '바이오시밀러·CRO' },
    ],
  },
  {
    id: 'defense', label: '방산·항공우주', emoji: '🛡️',
    tags: ['defense'],
    subs: [
      { tag: 'defense', label: '방위산업' },
      { tag: 'defense', label: '항공우주·드론' },
    ],
  },
  {
    id: 'entertainment', label: '엔터·미디어', emoji: '🎬',
    tags: ['entertainment-media'],
    subs: [
      { tag: 'entertainment-media', label: 'K-콘텐츠·엔터테인먼트' },
      { tag: 'entertainment-media', label: 'OTT·스트리밍' },
      { tag: 'entertainment-media', label: '게임·메타버스' },
    ],
  },
  {
    id: 'consumer', label: '소비재·유통', emoji: '🛒',
    tags: ['fashion-consumer'],
    subs: [
      { tag: 'fashion-consumer', label: '패션·뷰티·화장품' },
      { tag: 'fashion-consumer', label: '유통·마트·편의점' },
      { tag: 'fashion-consumer', label: '음식료·외식' },
      { tag: 'fashion-consumer', label: '레저·여행' },
    ],
  },
  {
    id: 'etf', label: 'ETF·펀드', emoji: '📊',
    tags: ['etf'],
    subs: [
      { tag: 'etf', label: 'ETF (국내·해외)' },
      { tag: 'etf', label: '리츠 (부동산 펀드)' },
      { tag: 'etf', label: '인덱스 펀드' },
    ],
  },
  {
    id: 'macro', label: '거시경제', emoji: '🌐',
    tags: ['macro', 'value'],
    subs: [
      { tag: 'macro', label: '금리·환율 흐름' },
      { tag: 'macro', label: '경기 지표·사이클' },
      { tag: 'value', label: '원자재·금속' },
    ],
  },
];

// ── 헬퍼 ──────────────────────────────────────────────
function isGroupFullySelected(group: InterestGroup, selected: InterestTag[]): boolean {
  return group.tags.every((t) => selected.includes(t));
}
function isGroupPartiallySelected(group: InterestGroup, selected: InterestTag[]): boolean {
  return group.tags.some((t) => selected.includes(t));
}
function toggleGroup(group: InterestGroup, selected: InterestTag[]): InterestTag[] {
  const full = isGroupFullySelected(group, selected);
  if (full) {
    return selected.filter((t) => !group.tags.includes(t));
  }
  const newSet = new Set(selected);
  group.tags.forEach((t) => newSet.add(t));
  return [...newSet];
}
function toggleSub(tag: InterestTag, selected: InterestTag[]): InterestTag[] {
  if (selected.includes(tag)) return selected.filter((t) => t !== tag);
  return [...new Set([...selected, tag])];
}

// ── Group Card ─────────────────────────────────────────
function GroupCard({
  group,
  selected,
  onChange,
}: {
  group: InterestGroup;
  selected: InterestTag[];
  onChange: (next: InterestTag[]) => void;
}) {
  const [open, setOpen] = useState(false);
  const isFull = isGroupFullySelected(group, selected);
  const isPartial = !isFull && isGroupPartiallySelected(group, selected);

  return (
    <View style={styles.groupCard}>
      {/* 부모 헤더 */}
      <Pressable
        onPress={() => setOpen((v) => !v)}
        style={styles.groupHeader}
      >
        <View style={styles.groupHeaderLeft}>
          <Text style={styles.groupEmoji}>{group.emoji}</Text>
          <Text style={styles.groupLabel}>{group.label}</Text>
          {isPartial && <View style={styles.partialDot} />}
        </View>
        <View style={styles.groupHeaderRight}>
          {/* 부모 자체 선택 체크박스 */}
          <Pressable
            onPress={() => onChange(toggleGroup(group, selected))}
            style={[styles.groupCheck, isFull && styles.groupCheckSelected]}
            hitSlop={8}
          >
            {isFull ? <Text style={styles.checkmark}>✓</Text> : null}
          </Pressable>
          <Text style={styles.expandArrow}>{open ? '⌃' : '⌄'}</Text>
        </View>
      </Pressable>

      {/* 서브 아이템 */}
      {open && (
        <View style={styles.subList}>
          {group.subs.map((sub, i) => {
            const isSelected = selected.includes(sub.tag);
            return (
              <Pressable
                key={`${sub.tag}-${i}`}
                onPress={() => onChange(toggleSub(sub.tag, selected))}
                style={[styles.subItem, isSelected && styles.subItemSelected]}
              >
                <View style={[styles.subCheck, isSelected && styles.subCheckSelected]}>
                  {isSelected ? <Text style={styles.subCheckmark}>✓</Text> : null}
                </View>
                <Text style={[styles.subLabel, isSelected && styles.subLabelSelected]}>
                  {sub.label}
                </Text>
              </Pressable>
            );
          })}
        </View>
      )}
    </View>
  );
}

// ── Main Screen ────────────────────────────────────────
export function InterestSettingsScreen() {
  const accessToken = useUserStore((s) => s.accessToken);
  const navigation = useNavigation<Nav>();
  const queryClient = useQueryClient();

  const [selectedInterests, setSelectedInterests] = useState<InterestTag[]>([]);
  const [hydrated, setHydrated] = useState(false);
  const [feedbackMsg, setFeedbackMsg] = useState<string | null>(null);

  const onboardingQuery = useQuery({
    queryKey: ['onboarding-status', accessToken],
    queryFn: getOnboardingStatus,
    enabled: Boolean(accessToken),
    retry: 0,
  });

  const profile = onboardingQuery.data?.profile ?? null;

  useEffect(() => {
    if (!profile || hydrated) return;
    setSelectedInterests(profile.interests);
    setHydrated(true);
  }, [profile, hydrated]);

  const saveMutation = useMutation({
    mutationFn: saveOnboardingProfile,
    onSuccess: async () => {
      setFeedbackMsg('관심사를 저장했어요.');
      await queryClient.invalidateQueries({ queryKey: ['onboarding-status', accessToken] });
      navigation.goBack();
    },
    onError: (error) => {
      setFeedbackMsg(getAuthApiErrorMessage(error, '저장에 실패했어요.'));
    },
  });

  function handleSave() {
    if (!profile || selectedInterests.length === 0) return;
    setFeedbackMsg(null);
    saveMutation.mutate(
      buildLearningPreferencesPayload(profile, {
        interests: selectedInterests,
        preferredStyle: profile.preferred_style,
      }),
    );
  }

  const selectedCount = [...new Set(selectedInterests)].length;

  return (
    <SafeAreaView style={styles.screen}>
      <View style={styles.header}>
        <Pressable onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Text style={styles.backArrow}>←</Text>
        </Pressable>
        <Text style={styles.headerTitle}>관심사 설정</Text>
      </View>

      {onboardingQuery.isLoading ? (
        <View style={styles.center}><ActivityIndicator color={colors.primary} /></View>
      ) : (
        <>
          <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
            <Text style={styles.description}>
              선택한 주제 기반으로 리포트와 뉴스가 추천돼요.{'\n'}
              분야를 누르면 세부 항목을 고를 수 있어요.
            </Text>
            <Text style={styles.countLabel}>
              현재 {selectedCount}개 태그 선택됨
            </Text>

            {INTEREST_GROUPS.map((group) => (
              <GroupCard
                key={group.id}
                group={group}
                selected={selectedInterests}
                onChange={setSelectedInterests}
              />
            ))}

            {feedbackMsg ? <Text style={styles.feedbackText}>{feedbackMsg}</Text> : null}
          </ScrollView>

          <View style={styles.footer}>
            <Pressable
              disabled={selectedInterests.length === 0 || saveMutation.isPending}
              onPress={handleSave}
              style={({ pressed }) => [
                styles.saveBtn,
                (selectedInterests.length === 0 || saveMutation.isPending) && styles.saveBtnDisabled,
                pressed && styles.saveBtnPressed,
              ]}
            >
              <Text style={styles.saveBtnText}>
                {saveMutation.isPending ? '저장 중...' : '저장'}
              </Text>
            </Pressable>
          </View>
        </>
      )}
    </SafeAreaView>
  );
}

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
  center: { alignItems: 'center', flex: 1, justifyContent: 'center' },
  scroll: { paddingHorizontal: 16, paddingTop: 16, paddingBottom: 120, gap: 10 },
  description: { color: colors.muted, fontSize: 13, lineHeight: 19 },
  countLabel: { color: colors.primary, fontSize: 12, fontWeight: '600' },
  // Group card
  groupCard: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 14,
    borderWidth: 1,
    overflow: 'hidden',
  },
  groupHeader: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 14,
    paddingVertical: 14,
  },
  groupHeaderLeft: { alignItems: 'center', flexDirection: 'row', gap: 8, flex: 1 },
  groupEmoji: { fontSize: 18 },
  groupLabel: { color: colors.text, fontSize: 15, fontWeight: '700' },
  partialDot: {
    backgroundColor: colors.primary,
    borderRadius: 4,
    height: 8,
    width: 8,
  },
  groupHeaderRight: { alignItems: 'center', flexDirection: 'row', gap: 12 },
  groupCheck: {
    alignItems: 'center',
    borderColor: colors.border,
    borderRadius: 6,
    borderWidth: 1.5,
    height: 20,
    justifyContent: 'center',
    width: 20,
  },
  groupCheckSelected: { backgroundColor: colors.primary, borderColor: colors.primary },
  checkmark: { color: colors.surface, fontSize: 11, fontWeight: '800' },
  expandArrow: { color: colors.muted, fontSize: 16 },
  // Sub items
  subList: {
    borderTopColor: colors.border,
    borderTopWidth: 1,
    gap: 0,
  },
  subItem: {
    alignItems: 'center',
    borderBottomColor: colors.border,
    borderBottomWidth: StyleSheet.hairlineWidth,
    flexDirection: 'row',
    gap: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  subItemSelected: { backgroundColor: '#F0FAF5' },
  subCheck: {
    alignItems: 'center',
    borderColor: colors.border,
    borderRadius: 4,
    borderWidth: 1.5,
    height: 18,
    justifyContent: 'center',
    width: 18,
  },
  subCheckSelected: { backgroundColor: colors.primary, borderColor: colors.primary },
  subCheckmark: { color: colors.surface, fontSize: 10, fontWeight: '800' },
  subLabel: { color: colors.text, flex: 1, fontSize: 14 },
  subLabelSelected: { color: colors.primary, fontWeight: '600' },
  // Feedback
  feedbackText: { color: colors.primary, fontSize: 13, fontWeight: '600', textAlign: 'center' },
  // Footer
  footer: {
    backgroundColor: colors.surface,
    borderTopColor: colors.border,
    borderTopWidth: 1,
    bottom: 0,
    left: 0,
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 24,
    position: 'absolute',
    right: 0,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -4 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
  },
  saveBtn: {
    alignItems: 'center',
    backgroundColor: colors.primary,
    borderRadius: 14,
    justifyContent: 'center',
    minHeight: 52,
    shadowColor: colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 12,
  },
  saveBtnDisabled: { opacity: 0.45 },
  saveBtnPressed: { opacity: 0.88 },
  saveBtnText: { color: colors.surface, fontSize: 16, fontWeight: '700' },
});
