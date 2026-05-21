import { useMemo, useState } from 'react';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { colors } from '@/constants/colors';
import { getAuthApiErrorMessage, issueDevAccessToken } from '@/features/auth/api';
import { useUserStore } from '@/store/userStore';
import { getAccessTokenPreview, normalizeAccessTokenInput } from '@/utils/devAccessToken';

export function DevLoginScreen() {
  const accessToken = useUserStore((state) => state.accessToken);
  const setAccessToken = useUserStore((state) => state.setAccessToken);
  const clearToken = useUserStore((state) => state.clearToken);
  const resetOnboarding = useUserStore((state) => state.resetOnboarding);
  const [draftToken, setDraftToken] = useState(accessToken ?? '');
  const [issueError, setIssueError] = useState<string | null>(null);
  const [issuedUserLabel, setIssuedUserLabel] = useState<string | null>(null);
  const [isIssuingToken, setIsIssuingToken] = useState(false);

  const normalizedToken = useMemo(() => normalizeAccessTokenInput(draftToken), [draftToken]);

  function beginOnboardingWithToken(token: string) {
    resetOnboarding();
    setAccessToken(token);
    setDraftToken(token);
    setIssueError(null);
  }

  function handleApplyToken() {
    if (!normalizedToken) {
      return;
    }

    setIssuedUserLabel(null);
    beginOnboardingWithToken(normalizedToken);
  }

  function handleClearToken() {
    clearToken();
    resetOnboarding();
    setDraftToken('');
    setIssueError(null);
    setIssuedUserLabel(null);
  }

  async function handleIssueToken() {
    setIsIssuingToken(true);
    setIssueError(null);

    try {
      const timestamp = Date.now();
      const response = await issueDevAccessToken({
        email: `frontend-dev+${timestamp}@local.test`,
        nickname: `frontend-${String(timestamp).slice(-6)}`,
      });

      setIssuedUserLabel(`${response.user.nickname} · ${response.user.email}`);
      beginOnboardingWithToken(response.access_token);
    } catch (error) {
      setIssueError(
        getAuthApiErrorMessage(
          error,
          '테스트 토큰을 발급하지 못했어요. 백엔드가 실행 중인지 확인해 주세요.',
        ),
      );
    } finally {
      setIsIssuingToken(false);
    }
  }

  const tokenPreview = getAccessTokenPreview(accessToken);

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView
        bounces={false}
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.hero}>
          <View style={styles.heroBadge} />
          <Text style={styles.heroTitle}>Mentors</Text>
          <Text style={styles.heroSubtitle}>막막한 당신을 위한 첫 번째 투자 전략</Text>
        </View>

        <View style={styles.card}>
          <Text style={styles.cardEyebrow}>임시 로그인</Text>
          <Text style={styles.cardTitle}>로그인</Text>
          <Text style={styles.cardDescription}>
            실제 로그인 대신 개발용 액세스 토큰으로 온보딩을 시작합니다.
          </Text>

          <View style={styles.fieldGroup}>
            <Text style={styles.fieldLabel}>액세스 토큰</Text>
            <TextInput
              autoCapitalize="none"
              autoCorrect={false}
              placeholder="Bearer eyJ..."
              placeholderTextColor="#AFB4B0"
              style={styles.input}
              value={draftToken}
              onChangeText={setDraftToken}
            />
            <Text style={styles.caption}>
              `Bearer` 접두어가 포함돼 있어도 자동으로 정리한 뒤 적용합니다.
            </Text>
          </View>

          <View style={styles.fieldGroup}>
            <Text style={styles.fieldLabel}>현재 토큰 상태</Text>
            <View style={styles.statusBox}>
              <Text style={styles.statusValue}>{tokenPreview}</Text>
              {issuedUserLabel ? <Text style={styles.issuedUserText}>{issuedUserLabel}</Text> : null}
              {!issuedUserLabel && normalizedToken && normalizedToken !== accessToken ? (
                <Text style={styles.statusHint}>입력한 토큰을 적용하면 바로 온보딩으로 이동합니다.</Text>
              ) : (
                <Text style={styles.statusHint}>토큰이 적용되면 원격 온보딩 상태를 확인한 뒤 바로 이어집니다.</Text>
              )}
            </View>
          </View>

          {issueError ? <Text style={styles.errorText}>{issueError}</Text> : null}

          <Pressable
            disabled={isIssuingToken}
            onPress={() => {
              void handleIssueToken();
            }}
            style={({ pressed }) => [
              styles.primaryButton,
              isIssuingToken && styles.buttonDisabled,
              pressed && !isIssuingToken && styles.buttonPressed,
            ]}
          >
            <Text style={styles.primaryButtonText}>
              {isIssuingToken ? '테스트 토큰 발급 중...' : '새 테스트 토큰 발급'}
            </Text>
          </Pressable>

          <Pressable
            disabled={!normalizedToken}
            onPress={handleApplyToken}
            style={({ pressed }) => [
              styles.secondaryButton,
              !normalizedToken && styles.buttonDisabled,
              pressed && normalizedToken && styles.buttonPressed,
            ]}
          >
            <Text style={styles.secondaryButtonText}>입력한 토큰으로 시작</Text>
          </Pressable>

          <Pressable
            disabled={!accessToken && !draftToken}
            onPress={handleClearToken}
            style={({ pressed }) => [
              styles.ghostButton,
              !accessToken && !draftToken && styles.buttonDisabled,
              pressed && (accessToken || draftToken) && styles.buttonPressed,
            ]}
          >
            <Text style={styles.ghostButtonText}>토큰 지우기</Text>
          </Pressable>

          <View style={styles.noticeBox}>
            <Text style={styles.noticeTitle}>임시 개발 로그인</Text>
            <Text style={styles.noticeDescription}>
              온보딩 전에 토큰만 준비해 두면 학습과 성장 API까지 바로 이어서 테스트할 수 있어요.
            </Text>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.background,
  },
  scrollContent: {
    flexGrow: 1,
    paddingBottom: 40,
  },
  hero: {
    alignItems: 'center',
    backgroundColor: colors.primary,
    minHeight: 312,
    paddingHorizontal: 24,
    paddingTop: 72,
    paddingBottom: 104,
  },
  heroBadge: {
    backgroundColor: '#19795F',
    borderRadius: 999,
    height: 80,
    marginBottom: 16,
    width: 80,
  },
  heroTitle: {
    color: colors.surface,
    fontSize: 32,
    fontWeight: '800',
    lineHeight: 38,
  },
  heroSubtitle: {
    color: '#CCF2DE',
    fontSize: 13,
    fontWeight: '500',
    lineHeight: 20,
    marginTop: 10,
    textAlign: 'center',
  },
  card: {
    backgroundColor: colors.surface,
    borderRadius: 24,
    marginHorizontal: 15,
    marginTop: -52,
    paddingHorizontal: 24,
    paddingTop: 28,
    paddingBottom: 28,
    shadowColor: colors.primary,
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.08,
    shadowRadius: 24,
  },
  cardEyebrow: {
    color: colors.primary,
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.6,
    marginBottom: 6,
    textTransform: 'uppercase',
  },
  cardTitle: {
    color: colors.text,
    fontSize: 28,
    fontWeight: '800',
    lineHeight: 34,
  },
  cardDescription: {
    color: colors.muted,
    fontSize: 14,
    lineHeight: 21,
    marginTop: 8,
    marginBottom: 24,
  },
  fieldGroup: {
    marginBottom: 16,
  },
  fieldLabel: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 8,
  },
  input: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 12,
    borderWidth: 1,
    color: colors.text,
    fontSize: 14,
    minHeight: 48,
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  caption: {
    color: colors.muted,
    fontSize: 12,
    lineHeight: 18,
    marginTop: 8,
  },
  statusBox: {
    backgroundColor: colors.background,
    borderColor: colors.border,
    borderRadius: 12,
    borderWidth: 1,
    paddingHorizontal: 16,
    paddingVertical: 14,
  },
  statusValue: {
    color: colors.text,
    fontSize: 15,
    fontWeight: '700',
    lineHeight: 20,
  },
  statusHint: {
    color: colors.muted,
    fontSize: 12,
    lineHeight: 18,
    marginTop: 6,
  },
  issuedUserText: {
    color: colors.primary,
    fontSize: 12,
    fontWeight: '600',
    lineHeight: 18,
    marginTop: 6,
  },
  errorText: {
    color: colors.rose,
    fontSize: 12,
    lineHeight: 18,
    marginBottom: 12,
  },
  primaryButton: {
    alignItems: 'center',
    backgroundColor: colors.primary,
    borderRadius: 14,
    justifyContent: 'center',
    minHeight: 52,
    paddingHorizontal: 20,
    shadowColor: colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 12,
  },
  primaryButtonText: {
    color: colors.surface,
    fontSize: 16,
    fontWeight: '700',
  },
  secondaryButton: {
    alignItems: 'center',
    backgroundColor: colors.accentSoft,
    borderRadius: 14,
    justifyContent: 'center',
    minHeight: 52,
    marginTop: 10,
    paddingHorizontal: 20,
  },
  secondaryButtonText: {
    color: colors.text,
    fontSize: 16,
    fontWeight: '700',
  },
  ghostButton: {
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 14,
    borderWidth: 1,
    justifyContent: 'center',
    minHeight: 48,
    marginTop: 10,
    paddingHorizontal: 20,
  },
  ghostButtonText: {
    color: colors.text,
    fontSize: 15,
    fontWeight: '600',
  },
  noticeBox: {
    backgroundColor: colors.primarySoft,
    borderRadius: 16,
    marginTop: 18,
    paddingHorizontal: 16,
    paddingVertical: 14,
  },
  noticeTitle: {
    color: colors.primary,
    fontSize: 13,
    fontWeight: '700',
    marginBottom: 4,
  },
  noticeDescription: {
    color: colors.text,
    fontSize: 13,
    lineHeight: 19,
  },
  buttonDisabled: {
    opacity: 0.45,
  },
  buttonPressed: {
    opacity: 0.9,
  },
});
