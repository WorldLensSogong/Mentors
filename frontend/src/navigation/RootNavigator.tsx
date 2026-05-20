import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { RootStackParamList } from './types';

// 방금 만든 온보딩 설문 화면 가져오기
import OnboardingFlow from '../features/onboarding/components/OnboardingFlow';
import { Text, View } from 'react-native';

const Stack = createNativeStackNavigator<RootStackParamList>();

function InternalHomeScreen() {
  return (
    <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
      <Text>Mentors — Home (placeholder)</Text>
    </View>
  );
}

export function RootNavigator() {
  return (
    // 💡 타입을 맞추기 위해 initialRouteName을 무조건 존재하는 "Login"으로 둡니다.
    <Stack.Navigator 
      initialRouteName="Login"
      screenOptions={{ headerShown: false }}
    >
      {/* 💡 name을 "Login"으로 속이고 실제 컴포넌트는 OnboardingFlow를 보여줍니다! */}
      <Stack.Screen name="Login" component={OnboardingFlow} />
      <Stack.Screen name="Home" component={InternalHomeScreen} />
    </Stack.Navigator>
  );
}