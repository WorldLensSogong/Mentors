export type EntryScreenState = 'login' | 'checking' | 'onboarding' | 'home';

interface ResolveEntryScreenStateInput {
  accessToken: string | null;
  hasCompletedOnboarding: boolean;
  isCheckingRemoteStatus: boolean;
}

export function resolveEntryScreenState({
  accessToken,
  hasCompletedOnboarding,
  isCheckingRemoteStatus,
}: ResolveEntryScreenStateInput): EntryScreenState {
  if (!accessToken) {
    return 'login';
  }

  if (hasCompletedOnboarding) {
    return 'home';
  }

  if (isCheckingRemoteStatus) {
    return 'checking';
  }

  return 'onboarding';
}
