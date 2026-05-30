import { useEffect, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { colors } from '@/constants/colors';
import { getOnboardingStatus } from '@/features/onboarding/api';
import type {
  CompletedOnboardingProfile,
  OnboardingStatusResponse,
} from '@/features/onboarding/types';
import { useUserStore } from '@/store/userStore';
import { LoginScreen } from '../features/auth/screens/LoginScreen';
import { SignupScreen } from '../features/auth/screens/SignupScreen';
import { OnboardingScreen } from '../features/onboarding/screens/OnboardingScreen';
import { SearchScreen } from '../features/explore/screens/SearchScreen';
import { NewsDetailScreen } from '../features/explore/screens/NewsDetailScreen';
import { DebateArenaScreen } from '../features/debate-arena/screens/DebateArenaScreen';
import type { AppStackParamList } from './types';

const Stack = createNativeStackNavigator<AppStackParamList>();

export function RootNavigator() {
  const accessToken = useUserStore((state) => state.accessToken);
  const hasCompletedOnboarding = useUserStore((state) => state.hasCompletedOnboarding);
  const finishOnboarding = useUserStore((state) => state.finishOnboarding);
  const resetOnboarding = useUserStore((state) => state.resetOnboarding);
  const [isCheckingOnboarding, setIsCheckingOnboarding] = useState(false);

  useEffect(() => {
    let ignore = false;

    if (!accessToken) {
      setIsCheckingOnboarding(false);
      return;
    }

    setIsCheckingOnboarding(true);
    getOnboardingStatus()
      .then((status) => {
        if (ignore) {
          return;
        }

        if (status.onboarded) {
          finishOnboarding({
            profile: toCompletedOnboardingProfile(status),
            source: 'remote',
          });
          return;
        }

        resetOnboarding();
      })
      .catch(() => {
        if (!ignore) {
          resetOnboarding();
        }
      })
      .finally(() => {
        if (!ignore) {
          setIsCheckingOnboarding(false);
        }
      });

    return () => {
      ignore = true;
    };
  }, [accessToken, finishOnboarding, resetOnboarding]);

  if (accessToken && isCheckingOnboarding) {
    return <SplashScreen message="사용자 정보를 확인하고 있어요." />;
  }

  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      {!accessToken ? (
        <>
          <Stack.Screen name="Login" component={LoginScreen} />
          <Stack.Screen name="Signup" component={SignupScreen} />
        </>
      ) : !hasCompletedOnboarding ? (
        <Stack.Screen name="Onboarding" component={OnboardingScreen} />
      ) : (
        <>
          <Stack.Screen name="Search" component={SearchScreen} />
          <Stack.Screen name="DebateArena" component={DebateArenaScreen} />
          <Stack.Screen name="NewsDetail" component={NewsDetailScreen} />
        </>
      )}
    </Stack.Navigator>
  );
}

function toCompletedOnboardingProfile(
  status: OnboardingStatusResponse,
): CompletedOnboardingProfile | null {
  if (!status.profile || !status.completed_at) {
    return null;
  }

  return {
    completedAt: status.completed_at,
    experienceLevel: status.profile.experience_level,
    interests: status.profile.interests,
    learningGoal: status.profile.learning_goal,
    preferredStyle: status.profile.preferred_style,
    riskProfile: status.profile.risk_profile,
    selectedMentorId: status.selected_mentor?.id ?? 0,
    syncState: 'remote',
  };
}

function SplashScreen({ message }: { message: string }) {
  return (
    <View style={styles.splash}>
      <ActivityIndicator color={colors.primary} />
      <Text style={styles.splashText}>{message}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  splash: {
    alignItems: 'center',
    backgroundColor: colors.background,
    flex: 1,
    gap: 12,
    justifyContent: 'center',
    padding: 20,
  },
  splashText: {
    color: colors.muted,
    fontSize: 14,
    fontWeight: '700',
  },
});
