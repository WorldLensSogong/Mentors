import { Component, type ReactNode } from 'react';
import { StatusBar } from 'expo-status-bar';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { NavigationContainer } from '@react-navigation/native';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from '@/api/queryClient';
import { colors } from '@/constants/colors';
import { HarnessNavigator } from '@/_dev-harness/HarnessNavigator';

interface AppErrorBoundaryState {
  error: Error | null;
}

class AppErrorBoundary extends Component<{ children: ReactNode }, AppErrorBoundaryState> {
  state: AppErrorBoundaryState = {
    error: null,
  };

  static getDerivedStateFromError(error: Error): AppErrorBoundaryState {
    return { error };
  }

  render() {
    if (!this.state.error) {
      return this.props.children;
    }

    return (
      <SafeAreaProvider>
        <ScrollView contentContainerStyle={styles.errorScrollContent}>
          <View style={styles.errorCard}>
            <Text style={styles.errorTitle}>화면을 불러오지 못했어요</Text>
            <Text style={styles.errorDescription}>
              테스트용 프론트엔드가 렌더링 중 예외로 멈췄습니다. 아래 메시지를 확인해 주세요.
            </Text>
            <Text selectable style={styles.errorMessage}>
              {this.state.error.message}
            </Text>
          </View>
        </ScrollView>
      </SafeAreaProvider>
    );
  }
}

export default function App() {
  return (
    <AppErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <SafeAreaProvider>
          <NavigationContainer>
            <HarnessNavigator />
            <StatusBar style="auto" />
          </NavigationContainer>
        </SafeAreaProvider>
      </QueryClientProvider>
    </AppErrorBoundary>
  );
}

const styles = StyleSheet.create({
  errorScrollContent: {
    backgroundColor: colors.background,
    flexGrow: 1,
    justifyContent: 'center',
    padding: 20,
  },
  errorCard: {
    backgroundColor: colors.surface,
    borderRadius: 20,
    gap: 12,
    padding: 20,
  },
  errorTitle: {
    color: colors.rose,
    fontSize: 22,
    fontWeight: '800',
  },
  errorDescription: {
    color: colors.text,
    fontSize: 14,
    lineHeight: 21,
  },
  errorMessage: {
    color: colors.muted,
    fontSize: 13,
    lineHeight: 20,
  },
});
