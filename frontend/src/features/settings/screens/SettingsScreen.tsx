import { useNavigation, type NavigationProp } from '@react-navigation/native';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  ActivityIndicator,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { colors } from '@/constants/colors';
import { deleteCurrentUser, getAuthApiErrorMessage, getCurrentUser } from '@/features/auth/api';
import { getOnboardingStatus, resetOnboardingProfile } from '@/features/onboarding/api';
import { useUserStore } from '@/store/userStore';
import { useSettingsStore } from '@/store/settingsStore';
import { getGrowthProgress } from '@/features/growth/api';
import { buildGrowthProgressQueryKey } from '@/features/growth/logic';
import type { AppStackParamList } from '@/navigation/types';

type SettingsNavigation = NavigationProp<AppStackParamList>;

function showConfirm(title: string, message: string, confirmLabel: string, onConfirm: () => void) {
  if (Platform.OS === 'web' && typeof window !== 'undefined' && typeof window.confirm === 'function') {
    if (window.confirm(`${title}\n\n${message}`)) onConfirm();
    return;
  }
  const { Alert } = require('react-native') as typeof import('react-native');
  Alert.alert(title, message, [
    { text: '취소', style: 'cancel' },
    { text: confirmLabel, style: 'destructive', onPress: onConfirm },
  ]);
}

function MenuItem({
  label,
  subtitle,
  onPress,
  tone = 'default',
}: {
  label: string;
  subtitle?: string;
  onPress: () => void;
  tone?: 'default' | 'danger';
}) {
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [styles.menuItem, pressed && styles.menuItemPressed]}
    >
      <View style={styles.menuItemContent}>
        <Text style={[styles.menuLabel, tone === 'danger' && styles.menuLabelDanger]}>{label}</Text>
        {subtitle ? <Text style={styles.menuSubtitle}>{subtitle}</Text> : null}
      </View>
      {tone !== 'danger' && <Text style={styles.menuArrow}>›</Text>}
    </Pressable>
  );
}

function SectionHeader({ title }: { title: string }) {
  return (
    <View style={styles.sectionHeader}>
      <Text style={styles.sectionTitle}>{title}</Text>
    </View>
  );
}

export function SettingsScreen() {
  const accessToken = useUserStore((state) => state.accessToken);
  const clearToken = useUserStore((state) => state.clearToken);
  const resetOnboarding = useUserStore((state) => state.resetOnboarding);
  const resetSettings = useSettingsStore((state) => state.reset);
  const navigation = useNavigation<SettingsNavigation>();
  const queryClient = useQueryClient();

  const resetOnboardingMutation = useMutation({
    mutationFn: resetOnboardingProfile,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['onboarding-status', accessToken] });
      resetOnboarding();
    },
  });

  const growthQueryKey = buildGrowthProgressQueryKey(accessToken);

  const userQuery = useQuery({
    queryKey: ['auth-me', accessToken],
    queryFn: getCurrentUser,
    enabled: Boolean(accessToken),
    retry: 0,
  });

  const onboardingQuery = useQuery({
    queryKey: ['onboarding-status', accessToken],
    queryFn: getOnboardingStatus,
    enabled: Boolean(accessToken),
    retry: 0,
  });

  const growthQuery = useQuery({
    queryKey: growthQueryKey,
    queryFn: getGrowthProgress,
    enabled: Boolean(accessToken),
    retry: 0,
  });

  const deleteAccountMutation = useMutation({
    mutationFn: deleteCurrentUser,
    onSuccess: () => {
      resetSettings();
      clearToken();
      queryClient.clear();
    },
  });

  function handleLogout() {
    clearToken();
    queryClient.clear();
  }

  function handleDeleteAccount() {
    showConfirm(
      '계정을 삭제할까요?',
      '삭제 후에는 현재 계정으로 다시 학습 기록을 이어갈 수 없어요.',
      '삭제',
      () => deleteAccountMutation.mutate(),
    );
  }

  function handleResetOnboarding() {
    showConfirm(
      '온보딩을 다시 시작할까요?',
      '선택한 멘토·관심사·설명 스타일이 초기화되고 온보딩 화면으로 돌아가요.',
      '다시 시작',
      () => resetOnboardingMutation.mutate(),
    );
  }

  const isLoading = userQuery.isLoading || onboardingQuery.isLoading;
  const user = userQuery.data;
  const mentor = onboardingQuery.data?.selected_mentor?.name;
  const tier = growthQuery.data?.current_tier ?? 'T1';
  const progress = growthQuery.data?.progress_percent ?? 0;
  const progressWidth = `${Math.min(progress, 100)}%` as `${number}%`;

  return (
    <SafeAreaView style={styles.screen}>
      <View style={styles.headerBar}>
        <Pressable onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Text style={styles.backArrow}>←</Text>
        </Pressable>
        <Text style={styles.headerTitle}>설정</Text>
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {/* 프로필 카드 */}
        <View style={styles.profileCard}>
          {isLoading ? (
            <View style={styles.profileLoadingRow}>
              <ActivityIndicator color={colors.primary} />
            </View>
          ) : (
            <>
              <View style={styles.profileRow}>
                <View style={styles.avatarCircle}>
                  <Text style={styles.avatarLetter}>
                    {(user?.nickname ?? 'U').charAt(0).toUpperCase()}
                  </Text>
                </View>
                <View style={styles.profileInfo}>
                  <Text style={styles.profileName}>{user?.nickname ?? '-'}</Text>
                  <Text style={styles.profileEmail}>{user?.email ?? '-'}</Text>
                  {mentor ? (
                    <Text style={styles.profileMentor}>멘토: {mentor}</Text>
                  ) : null}
                </View>
                <View style={styles.tierBadge}>
                  <Text style={styles.tierBadgeText}>{tier}</Text>
                </View>
              </View>

              {/* 성장 게이지 */}
              <View style={styles.growthSection}>
                <View style={styles.growthLabelRow}>
                  <Text style={styles.growthLabel}>{tier} 이해도</Text>
                  <Text style={styles.growthPct}>{progress}%</Text>
                </View>
                <View style={styles.growthTrack}>
                  <View style={[styles.growthFill, { width: progressWidth }]} />
                </View>
                <Text style={styles.growthCaption}>
                  {growthQuery.data
                    ? `개념 ${growthQuery.data.mastered_concepts}/${growthQuery.data.total_concepts}개 완료`
                    : ''}
                </Text>
              </View>
            </>
          )}
        </View>

        {/* 학습 섹션 */}
        <SectionHeader title="학습" />
        <View style={styles.menuCard}>
          <MenuItem
            label="나의 학습 기록"
            subtitle="퀴즈, 리포트 기록 보기"
            onPress={() => navigation.navigate('LearningRecord')}
          />
          <View style={styles.menuDivider} />
          <MenuItem
            label="승급시험 결과"
            subtitle="맞춘 문제와 틀린 문제 다시 보기"
            onPress={() => navigation.navigate('PromotionResult')}
          />
          <View style={styles.menuDivider} />
          <MenuItem
            label="채팅 기록"
            subtitle="이전 멘토 대화 보기"
            onPress={() => navigation.navigate('ChatHistory')}
          />
          <View style={styles.menuDivider} />
          <MenuItem
            label="투기장 기록"
            subtitle="완료된 토론 다시 보기"
            onPress={() => navigation.navigate('DebateHistory')}
          />
        </View>

        {/* 알림 섹션 */}
        <SectionHeader title="알림" />
        <View style={styles.menuCard}>
          <MenuItem
            label="알림 설정"
            subtitle="학습 리마인드, 데일리 리포트"
            onPress={() => navigation.navigate('NotificationSettings')}
          />
        </View>

        {/* 설정 섹션 */}
        <SectionHeader title="설정" />
        <View style={styles.menuCard}>
          <MenuItem
            label="내 정보"
            subtitle="계정 정보 및 온보딩 프로필 확인"
            onPress={() => navigation.navigate('AccountSettings')}
          />
          <View style={styles.menuDivider} />
          <MenuItem
            label="관심사 설정"
            subtitle="관심 분야를 세부적으로 선택"
            onPress={() => navigation.navigate('InterestSettings')}
          />
          <View style={styles.menuDivider} />
          <MenuItem
            label={resetOnboardingMutation.isPending ? '초기화 중...' : '온보딩 재설정'}
            subtitle="멘토·관심사·스타일을 처음부터 다시 설정"
            onPress={handleResetOnboarding}
          />
        </View>

        {/* 계정 섹션 */}
        <SectionHeader title="계정" />
        <View style={styles.menuCard}>
          <MenuItem label="로그아웃" onPress={handleLogout} />
          <View style={styles.menuDivider} />
          <MenuItem
            label={deleteAccountMutation.isPending ? '계정 삭제 중...' : '계정 삭제'}
            onPress={handleDeleteAccount}
            tone="danger"
          />
        </View>

        <Text style={styles.versionText}>Mentors v1.0.0</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.background,
  },
  headerBar: {
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderBottomColor: colors.border,
    borderBottomWidth: 1,
    flexDirection: 'row',
    gap: 8,
    height: 56,
    paddingHorizontal: 16,
  },
  backBtn: {
    alignItems: 'center',
    height: 32,
    justifyContent: 'center',
    width: 32,
  },
  backArrow: {
    color: colors.text,
    fontSize: 22,
    fontWeight: '400',
  },
  headerTitle: {
    color: colors.text,
    fontSize: 17,
    fontWeight: '700',
  },
  scrollContent: {
    gap: 0,
    paddingBottom: 48,
  },
  profileCard: {
    backgroundColor: colors.surface,
    borderBottomColor: colors.border,
    borderBottomWidth: 1,
    padding: 20,
    gap: 16,
    marginBottom: 24,
  },
  profileLoadingRow: {
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 80,
  },
  profileRow: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 14,
  },
  avatarCircle: {
    alignItems: 'center',
    backgroundColor: colors.primarySoft,
    borderRadius: 40,
    height: 60,
    justifyContent: 'center',
    width: 60,
  },
  avatarLetter: {
    color: colors.primary,
    fontSize: 24,
    fontWeight: '800',
  },
  profileInfo: {
    flex: 1,
    gap: 4,
  },
  profileName: {
    color: colors.text,
    fontSize: 18,
    fontWeight: '800',
  },
  profileEmail: {
    color: colors.muted,
    fontSize: 13,
  },
  profileMentor: {
    color: colors.primary,
    fontSize: 12,
    fontWeight: '600',
  },
  tierBadge: {
    alignSelf: 'flex-start',
    backgroundColor: colors.primary,
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 5,
  },
  tierBadgeText: {
    color: colors.surface,
    fontSize: 14,
    fontWeight: '800',
  },
  growthSection: {
    gap: 8,
  },
  growthLabelRow: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  growthLabel: {
    color: colors.text,
    fontSize: 13,
    fontWeight: '700',
  },
  growthPct: {
    color: colors.primary,
    fontSize: 13,
    fontWeight: '800',
  },
  growthTrack: {
    height: 8,
    backgroundColor: colors.primarySoft,
    borderRadius: 999,
    overflow: 'hidden',
  },
  growthFill: {
    height: '100%',
    backgroundColor: colors.primary,
    borderRadius: 999,
  },
  growthCaption: {
    color: colors.muted,
    fontSize: 12,
  },
  sectionHeader: {
    paddingHorizontal: 20,
    paddingBottom: 6,
    paddingTop: 4,
  },
  sectionTitle: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 0.4,
    textTransform: 'uppercase',
  },
  menuCard: {
    backgroundColor: colors.surface,
    borderBottomColor: colors.border,
    borderBottomWidth: 1,
    borderTopColor: colors.border,
    borderTopWidth: 1,
    marginBottom: 24,
  },
  menuItem: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  menuItemPressed: {
    backgroundColor: colors.background,
  },
  menuItemContent: {
    flex: 1,
    gap: 3,
  },
  menuLabel: {
    color: colors.text,
    fontSize: 16,
    fontWeight: '600',
  },
  menuLabelDanger: {
    color: colors.rose,
  },
  menuSubtitle: {
    color: colors.muted,
    fontSize: 12,
  },
  menuArrow: {
    color: colors.muted,
    fontSize: 22,
    fontWeight: '400',
  },
  menuDivider: {
    backgroundColor: colors.border,
    height: StyleSheet.hairlineWidth,
    marginLeft: 20,
  },
  versionText: {
    color: colors.muted,
    fontSize: 12,
    marginTop: 8,
    textAlign: 'center',
  },
});
