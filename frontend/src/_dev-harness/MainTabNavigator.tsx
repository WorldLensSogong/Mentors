import { Text } from 'react-native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { colors } from '@/constants/colors';
import { LearningRecordScreen } from './screens/LearningRecordScreen';
import { SettingsScreen } from './screens/SettingsScreen';
import type { MainTabParamList } from './navigation/types';

const Tab = createBottomTabNavigator<MainTabParamList>();

function TabIcon({ label, focused }: { label: string; focused: boolean }) {
  return (
    <Text
      style={{
        color: focused ? colors.primary : colors.muted,
        fontSize: 15,
        fontWeight: focused ? '700' : '500',
      }}
    >
      {label}
    </Text>
  );
}

export function MainTabNavigator() {
  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.muted,
        tabBarStyle: {
          backgroundColor: colors.surface,
          borderTopColor: colors.border,
          height: 72,
          paddingBottom: 10,
          paddingTop: 10,
        },
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: '700',
        },
      }}
    >
      <Tab.Screen
        name="LearningRecord"
        component={LearningRecordScreen}
        options={{
          title: '기록',
          tabBarIcon: ({ focused }) => <TabIcon focused={focused} label="기록" />,
        }}
      />
      <Tab.Screen
        name="Settings"
        component={SettingsScreen}
        options={{
          title: '설정',
          tabBarIcon: ({ focused }) => <TabIcon focused={focused} label="설정" />,
        }}
      />
    </Tab.Navigator>
  );
}
