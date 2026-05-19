import { useEffect } from 'react';
import {
  createNativeStackNavigator,
  type NativeStackScreenProps,
} from '@react-navigation/native-stack';
import { useQuery } from '@tanstack/react-query';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { DevAccessTokenCard } from '@/components/DevAccessTokenCard';
import { colors } from '@/constants/colors';
import { getGrowthApiErrorMessage, getGrowthProgress } from '@/features/growth/api';
import { GrowthProgressCard } from '@/features/growth/components/GrowthProgressCard';
import { getOnboardingStatus } from '@/features/onboarding/api';
import {
  getExperienceLevelLabel,
  getInterestLabel,
  getLearningGoalLabel,
  getPreferredStyleLabel,
  getRiskProfileLabel,
} from '@/features/onboarding/data';
import { getMentorById } from '@/features/onboarding/logic';
import { OnboardingScreen } from '@/features/onboarding/screens/OnboardingScreen';
import { PromotionTestScreen } from '@/features/promotion-test/screens/PromotionTestScreen';
import { useUserStore } from '@/store/userStore';
import type { RootStackParamList } from './types';

const Stack = createNativeStackNavigator<RootStackParamList>();

function HomeScreen({ navigation }: NativeStackScreenProps<RootStackParamList, 'Home'>) {
  const accessToken = useUserStore((state) => state.accessToken);
  const onboardingProfile = useUserStore((state) => state.onboardingProfile);
  const onboardingSource = useUserStore((state) => state.onboardingSource);
  const resetOnboarding = useUserStore((state) => state.resetOnboarding);
  const selectedMentor = onboardingProfile
    ? getMentorById(onboardingProfile.selectedMentorId)
    : null;
  const growthProgressQuery = useQuery({
    queryKey: ['growth-progress', accessToken],
    queryFn: getGrowthProgress,
    enabled: Boolean(accessToken),
    retry: 0,
  });

  return (
    <ScrollView contentContainerStyle={styles.homeContainer}>
      <View style={styles.heroCard}>
        <Text style={styles.eyebrow}>Mentors Home</Text>
        <Text style={styles.heroTitle}>온보딩 뒤에 이어질 성장 흐름까지 붙였어요.</Text>
        <Text style={styles.heroDescription}>
          이제 홈 화면에서 현재 티어, 이해도 게이지, 잠금해제 기능, 승급시험 진입 상태를 바로 확인할
          수 있어요.
        </Text>
        <View
          style={[
            styles.syncBadge,
            onboardingSource === 'remote' ? styles.syncBadgeRemote : styles.syncBadgeLocal,
          ]}
        >
          <Text style={styles.syncBadgeText}>
            {onboardingSource === 'remote'
              ? '서버 온보딩 상태와 동기화됨'
              : '로컬 데모 모드로 진행 중'}
          </Text>
        </View>
      </View>

      <DevAccessTokenCard />

      {selectedMentor ? (
        <View style={styles.summaryCard}>
          <Text style={styles.sectionTitle}>선택한 멘토</Text>
          <Text style={styles.mentorName}>{selectedMentor.name}</Text>
          <Text style={styles.mentorTitle}>{selectedMentor.title}</Text>
          <Text style={styles.summaryText}>{selectedMentor.philosophy}</Text>
        </View>
      ) : null}

      {onboardingProfile ? (
        <View style={styles.summaryCard}>
          <Text style={styles.sectionTitle}>저장된 성향 요약</Text>
          <View style={styles.detailList}>
            <Text style={styles.detailItem}>
              투자 경험: {getExperienceLevelLabel(onboardingProfile.experienceLevel)}
            </Text>
            <Text style={styles.detailItem}>
              리스크 성향: {getRiskProfileLabel(onboardingProfile.riskProfile)}
            </Text>
            <Text style={styles.detailItem}>
              학습 목표: {getLearningGoalLabel(onboardingProfile.learningGoal)}
            </Text>
            <Text style={styles.detailItem}>
              선호 코칭: {getPreferredStyleLabel(onboardingProfile.preferredStyle)}
            </Text>
            <Text style={styles.detailItem}>
              관심사: {onboardingProfile.interests.map(getInterestLabel).join(', ')}
            </Text>
          </View>
        </View>
      ) : (
        <View style={styles.summaryCard}>
          <Text style={styles.sectionTitle}>서버 상태로 완료된 사용자</Text>
          <Text style={styles.summaryText}>
            현재는 서버에서 온보딩 완료 여부만 읽고 있어요. 이후 프로필 조회 API가 생기면 같은
            카드에 내용이 바로 채워질 수 있게 유지했습니다.
          </Text>
        </View>
      )}

      <GrowthProgressCard
        progress={growthProgressQuery.data ?? null}
        isLoading={growthProgressQuery.isLoading}
        errorMessage={
          growthProgressQuery.error
            ? getGrowthApiErrorMessage(
                growthProgressQuery.error,
                '성장 현황을 불러오지 못했어요. 잠시 후 다시 시도해 주세요.',
              )
            : null
        }
        requiresAuth={!accessToken}
        onPressPromotionTest={() => navigation.navigate('PromotionTest')}
      />

      <Pressable onPress={resetOnboarding} style={styles.resetButton}>
        <Text style={styles.resetButtonText}>온보딩 다시 보기</Text>
      </Pressable>
    </ScrollView>
  );
}

export function RootNavigator() {
  const accessToken = useUserStore((state) => state.accessToken);
  const hasCompletedOnboarding = useUserStore((state) => state.hasCompletedOnboarding);
  const finishOnboarding = useUserStore((state) => state.finishOnboarding);
  const onboardingStatusQuery = useQuery({
    queryKey: ['onboarding-status', accessToken],
    queryFn: getOnboardingStatus,
    enabled: Boolean(accessToken) && !hasCompletedOnboarding,
    retry: 0,
  });

  useEffect(() => {
    if (onboardingStatusQuery.data?.onboarded && !hasCompletedOnboarding) {
      finishOnboarding({
        profile: null,
        source: 'remote',
      });
    }
  }, [finishOnboarding, hasCompletedOnboarding, onboardingStatusQuery.data]);

  const isCheckingRemoteStatus =
    Boolean(accessToken) && !hasCompletedOnboarding && onboardingStatusQuery.isLoading;

  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      {isCheckingRemoteStatus ? (
        <Stack.Screen name="Onboarding">
          {() => (
            <View style={styles.loadingContainer}>
              <Text style={styles.loadingTitle}>기존 온보딩 상태를 확인하고 있어요</Text>
              <Text style={styles.loadingDescription}>
                서버 정보가 있으면 곧바로 홈으로 보내고, 없으면 이어서 온보딩을 진행할 수 있게
                준비합니다.
              </Text>
            </View>
          )}
        </Stack.Screen>
      ) : hasCompletedOnboarding ? (
        <>
          <Stack.Screen name="Home" component={HomeScreen} />
          <Stack.Screen
            name="PromotionTest"
            component={PromotionTestScreen}
            options={{
              headerShown: true,
              title: '승급시험',
              headerShadowVisible: false,
              headerStyle: { backgroundColor: colors.background },
              headerTintColor: colors.text,
            }}
          />
        </>
      ) : (
        <Stack.Screen name="Onboarding" component={OnboardingScreen} />
      )}
    </Stack.Navigator>
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: 28,
    backgroundColor: colors.background,
  },
  loadingTitle: {
    color: colors.text,
    fontSize: 24,
    fontWeight: '700',
    marginBottom: 12,
  },
  loadingDescription: {
    color: colors.muted,
    fontSize: 15,
    lineHeight: 22,
  },
  homeContainer: {
    padding: 20,
    backgroundColor: colors.background,
    gap: 16,
  },
  heroCard: {
    backgroundColor: colors.surface,
    borderRadius: 24,
    borderWidth: 1,
    borderColor: colors.border,
    padding: 20,
    gap: 10,
  },
  eyebrow: {
    color: colors.primary,
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 1,
    textTransform: 'uppercase',
  },
  heroTitle: {
    color: colors.text,
    fontSize: 28,
    fontWeight: '800',
    lineHeight: 34,
  },
  heroDescription: {
    color: colors.muted,
    fontSize: 15,
    lineHeight: 22,
  },
  syncBadge: {
    alignSelf: 'flex-start',
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  syncBadgeRemote: {
    backgroundColor: colors.primarySoft,
  },
  syncBadgeLocal: {
    backgroundColor: colors.accentSoft,
  },
  syncBadgeText: {
    color: colors.text,
    fontSize: 12,
    fontWeight: '700',
  },
  summaryCard: {
    backgroundColor: colors.surface,
    borderRadius: 24,
    borderWidth: 1,
    borderColor: colors.border,
    padding: 20,
    gap: 10,
  },
  sectionTitle: {
    color: colors.text,
    fontSize: 18,
    fontWeight: '700',
  },
  mentorName: {
    color: colors.text,
    fontSize: 22,
    fontWeight: '800',
  },
  mentorTitle: {
    color: colors.primary,
    fontSize: 15,
    fontWeight: '600',
  },
  summaryText: {
    color: colors.muted,
    fontSize: 15,
    lineHeight: 22,
  },
  detailList: {
    gap: 8,
  },
  detailItem: {
    color: colors.text,
    fontSize: 15,
    lineHeight: 22,
  },
  resetButton: {
    alignItems: 'center',
    backgroundColor: colors.text,
    borderRadius: 18,
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  resetButtonText: {
    color: colors.surface,
    fontSize: 15,
    fontWeight: '700',
  },
});
