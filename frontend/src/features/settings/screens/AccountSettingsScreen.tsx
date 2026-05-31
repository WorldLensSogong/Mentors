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
import { getCurrentUser } from '@/features/auth/api';
import { getOnboardingStatus } from '@/features/onboarding/api';
import { useUserStore } from '@/store/userStore';
import type { AppStackParamList } from '@/navigation/types';

type Nav = NativeStackNavigationProp<AppStackParamList, 'AccountSettings'>;

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.infoRow}>
      <Text style={styles.infoLabel}>{label}</Text>
      <Text style={styles.infoValue}>{value}</Text>
    </View>
  );
}

export function AccountSettingsScreen() {
  const navigation = useNavigation<Nav>();
  const accessToken = useUserStore((s) => s.accessToken);

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

  const profile = onboardingQuery.data?.profile;
  const mentor = onboardingQuery.data?.selected_mentor?.name ?? '-';
  const isLoading = userQuery.isLoading || onboardingQuery.isLoading;

  const expLabel: Record<string, string> = {
    beginner: '처음이에요',
    exploring: '조금 해봤어요',
    confident: '꽤 경험이 있어요',
  };
  const riskLabel: Record<string, string> = {
    steady: '안정 우선',
    balanced: '균형 추구',
    bold: '기회 선호',
  };
  const styleLabel: Record<string, string> = {
    gentle: '친근하고 쉽게',
    structured: '체계적으로',
    challenging: '도전적으로',
  };
  const goalLabel: Record<string, string> = {
    'build-habit': '습관 만들기',
    'understand-news': '경제 뉴스 이해',
    'find-style': '나만의 투자 스타일 찾기',
  };

  return (
    <SafeAreaView style={styles.screen}>
      <View style={styles.header}>
        <Pressable onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Text style={styles.backArrow}>←</Text>
        </Pressable>
        <Text style={styles.headerTitle}>설정</Text>
      </View>

      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        {/* 내 정보 */}
        <Text style={styles.sectionLabel}>내 정보</Text>
        <View style={styles.card}>
          {isLoading ? (
            <View style={styles.center}><ActivityIndicator color={colors.primary} /></View>
          ) : (
            <>
              <InfoRow label="닉네임" value={userQuery.data?.nickname ?? '-'} />
              <View style={styles.divider} />
              <InfoRow label="이메일" value={userQuery.data?.email ?? '-'} />
              <View style={styles.divider} />
              <InfoRow label="멘토" value={mentor} />
              {profile && (
                <>
                  <View style={styles.divider} />
                  <InfoRow label="투자 경험" value={expLabel[profile.experience_level] ?? profile.experience_level} />
                  <View style={styles.divider} />
                  <InfoRow label="위험 성향" value={riskLabel[profile.risk_profile] ?? profile.risk_profile} />
                  <View style={styles.divider} />
                  <InfoRow label="학습 목표" value={goalLabel[profile.learning_goal] ?? profile.learning_goal} />
                  <View style={styles.divider} />
                  <InfoRow label="설명 스타일" value={styleLabel[profile.preferred_style] ?? profile.preferred_style} />
                </>
              )}
            </>
          )}
        </View>

      </ScrollView>
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
  scroll: { paddingHorizontal: 16, paddingTop: 20, paddingBottom: 48, gap: 6 },
  sectionLabel: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 0.4,
    marginBottom: 4,
    marginTop: 8,
    textTransform: 'uppercase',
  },
  card: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 16,
    borderWidth: 1,
    overflow: 'hidden',
    paddingHorizontal: 16,
  },
  center: { alignItems: 'center', justifyContent: 'center', paddingVertical: 24 },
  divider: { backgroundColor: colors.border, height: StyleSheet.hairlineWidth },
  infoRow: { flexDirection: 'row', gap: 12, paddingVertical: 13, alignItems: 'flex-start' },
  infoLabel: { color: colors.muted, fontSize: 13, fontWeight: '600', width: 80 },
  infoValue: { color: colors.text, flex: 1, fontSize: 13, lineHeight: 19 },
});
