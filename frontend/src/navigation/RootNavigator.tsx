import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { RootStackParamList } from './types';

// 💡 가져오는 경로(Import)를 가장 안전한 상대 경로로 지정합니다.
import LoginScreen from '../features/onboarding/screens/LoginScreen';
import { Text, View } from 'react-native';

const Stack = createNativeStackNavigator<RootStackParamList>();

// 팀의 기존 HomeScreen 구조를 해치지 않기 위해 임시 컴포넌트 이름 변경
function InternalHomeScreen() {
  return (
    <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
      <Text>Mentors — Home (placeholder)</Text>
    </View>
  );
}

export function RootNavigator() {
  return (
    // 💡 안전하게 초기 화면을 Login으로 설정
    <Stack.Navigator 
      initialRouteName="Login"
      screenOptions={{ headerShown: false }}
    >
      <Stack.Screen name="Login" component={LoginScreen} />
      {/* 혹시 팀의 types.ts에 Home이 지정되어 있을 수 있으므로 그대로 유지 */}
      <Stack.Screen name="Home" component={InternalHomeScreen} />
    </Stack.Navigator>
  );
}