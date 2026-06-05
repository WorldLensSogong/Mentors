import { Platform, Text } from 'react-native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { colors } from '@/constants/colors';
import type { MainTabParamList } from './types';
import { SearchScreen } from '@/features/explore/screens/SearchScreen';
import { MentorChatScreen } from '@/features/chat/screens/MentorChatScreen';
import { DebateArenaScreen } from '@/features/debate-arena/screens/DebateArenaScreen';
import { buildMainTabBarMetrics } from './logic';

const Tab = createBottomTabNavigator<MainTabParamList>();

const TAB_CONFIG: Record<
  keyof MainTabParamList,
  { title: string; icon: string }
> = {
  Search: { title: '탐색', icon: '🔍' },
  MentorChat: { title: '채팅', icon: '💬' },
  DebateArena: { title: '투기장', icon: '⚔️' },
};

function TabIcon({ name, focused }: { name: keyof MainTabParamList; focused: boolean }) {
  const { icon } = TAB_CONFIG[name];
  return (
    <Text
      style={{
        fontSize: 18,
        opacity: focused ? 1 : 0.55,
        marginBottom: Platform.OS === 'ios' ? 0 : 2,
      }}
    >
      {icon}
    </Text>
  );
}

export function MainTabNavigator() {
  const insets = useSafeAreaInsets();
  const tabBarMetrics = buildMainTabBarMetrics({
    bottomInset: insets.bottom,
    platform: Platform.OS === 'ios' ? 'ios' : Platform.OS === 'web' ? 'web' : 'android',
  });

  return (
    <Tab.Navigator
      initialRouteName="Search"
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.muted,
        tabBarStyle: {
          backgroundColor: colors.surface,
          // 바닥에 붙는 flush 바 — 마진 없이 전체 폭을 채워 주변 회색 여백 제거.
          // 상단 모서리만 둥글게 + 상단 테두리로 깔끔하게 구분.
          borderTopLeftRadius: 20,
          borderTopRightRadius: 20,
          borderTopWidth: 1,
          borderTopColor: '#C8CDC8',
          borderLeftWidth: 0,
          borderRightWidth: 0,
          borderBottomWidth: 0,
          height: tabBarMetrics.height,
          paddingBottom: tabBarMetrics.paddingBottom,
          paddingTop: tabBarMetrics.paddingTop,
          elevation: 0,                 // Android: 사각 그림자(회색 박스) 제거
          shadowOpacity: 0,             // iOS: 그림자 제거
        },
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: '700',
        },
      }}
    >
      <Tab.Screen
        name="Search"
        component={SearchScreen}
        options={{
          title: TAB_CONFIG.Search.title,
          tabBarIcon: ({ focused }) => <TabIcon name="Search" focused={focused} />,
        }}
      />
      <Tab.Screen
        name="MentorChat"
        component={MentorChatScreen}
        options={{
          title: TAB_CONFIG.MentorChat.title,
          tabBarIcon: ({ focused }) => <TabIcon name="MentorChat" focused={focused} />,
        }}
      />
      <Tab.Screen
        name="DebateArena"
        component={DebateArenaScreen}
        options={{
          title: TAB_CONFIG.DebateArena.title,
          tabBarIcon: ({ focused }) => <TabIcon name="DebateArena" focused={focused} />,
        }}
      />
    </Tab.Navigator>
  );
}
