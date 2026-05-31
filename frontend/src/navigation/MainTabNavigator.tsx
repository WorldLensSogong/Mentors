import { Platform, Text } from 'react-native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { colors } from '@/constants/colors';
import type { MainTabParamList } from './types';
import { SearchScreen } from '@/features/explore/screens/SearchScreen';
import { MentorChatScreen } from '@/features/chat/screens/MentorChatScreen';
import { DebateArenaScreen } from '@/features/debate-arena/screens/DebateArenaScreen';

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
  return (
    <Tab.Navigator
      initialRouteName="Search"
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.muted,
        tabBarStyle: {
          backgroundColor: colors.surface,
          borderTopColor: colors.border,
          height: Platform.OS === 'ios' ? 84 : 72,
          paddingBottom: Platform.OS === 'ios' ? 24 : 10,
          paddingTop: 10,
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
