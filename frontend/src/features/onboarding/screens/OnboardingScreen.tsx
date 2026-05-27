import { StyleSheet, Text, View, Pressable } from 'react-native';
import { useUserStore } from '@/store/userStore';
import { colors } from '@/constants/colors';

export function OnboardingScreen() {
  const finishOnboarding = useUserStore((state) => state.finishOnboarding);
  const clearToken = useUserStore((state) => state.clearToken);

  function handleCompleteOnboarding() {
    finishOnboarding({
      profile: {
        experienceLevel: 'beginner',
        interests: ['value', 'tech'],
        riskProfile: 'steady',
        learningGoal: 'build-habit',
        preferredStyle: 'gentle',
        selectedMentorId: 1,
        completedAt: new Date().toISOString(),
        syncState: 'local',
      },
      source: 'local',
    });
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>투자 성향 분석 (온보딩)</Text>
      <Text style={styles.description}>
        실제 프론트엔드 온보딩 화면이 이곳에 개발될 예정입니다. 아래 버튼을 눌러 임시 프로필을 설정하고 홈 화면으로 이동할 수 있습니다.
      </Text>

      <Pressable onPress={handleCompleteOnboarding} style={styles.primaryButton}>
        <Text style={styles.primaryButtonText}>온보딩 완료 처리하기</Text>
      </Pressable>

      <Pressable onPress={clearToken} style={styles.secondaryButton}>
        <Text style={styles.secondaryButtonText}>로그아웃</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  title: {
    color: colors.text,
    fontSize: 24,
    fontWeight: '800',
    marginBottom: 16,
    textAlign: 'center',
  },
  description: {
    color: colors.muted,
    fontSize: 14,
    lineHeight: 22,
    textAlign: 'center',
    marginBottom: 32,
  },
  primaryButton: {
    backgroundColor: colors.primary,
    paddingVertical: 14,
    paddingHorizontal: 28,
    borderRadius: 12,
    width: '100%',
    alignItems: 'center',
    marginBottom: 12,
  },
  primaryButtonText: {
    color: colors.surface,
    fontSize: 16,
    fontWeight: '700',
  },
  secondaryButton: {
    borderColor: colors.border,
    borderWidth: 1,
    paddingVertical: 14,
    paddingHorizontal: 28,
    borderRadius: 12,
    width: '100%',
    alignItems: 'center',
  },
  secondaryButtonText: {
    color: colors.muted,
    fontSize: 16,
    fontWeight: '700',
  },
});
