import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, SafeAreaView } from 'react-native';

// 화면 컴포넌트 임포트
import SearchScreen from '../features/explore/screens/SearchScreen';
import NewsDetailScreen from '../features/explore/screens/NewDetailScreen';

export function RootNavigator() {
  const [currentScreen, setCurrentScreen] = useState<'Search' | 'Detail'>('Search');
  const [activeTab, setActiveTab] = useState('탐색');

  return (
    <SafeAreaView style={styles.container}>
      {/* 💡 메인 화면 전환 로직 (상세 페이지 우선 조건 방식) */}
      <View style={styles.screenBody}>
        {currentScreen === 'Search' ? (
          <SearchScreen onNavigateToDetail={() => setCurrentScreen('Detail')} />
        ) : (
          <NewsDetailScreen onBack={() => setCurrentScreen('Search')} />
        )}
      </View>

      {/* 💡 피그마 최하단 고정 하단 탭바 구현 */}
      <View style={styles.bottomTabBar}>
        {[
          { name: '탐색', icon: '🔍' },
          { name: '채팅', icon: '💬' },
          { name: '투기장', icon: '⚔️' }
        ].map((tab) => {
          const isSelected = activeTab === tab.name;
          return (
            <TouchableOpacity 
              key={tab.name} 
              style={[styles.tabButton, isSelected ? styles.tabButtonActive : null]}
              onPress={() => {
                setActiveTab(tab.name);
                if (tab.name === '탐색') setCurrentScreen('Search'); // 탐색 누르면 원래대로 리셋
              }}
            >
              <Text style={styles.tabIcon}>{tab.icon}</Text>
              <Text style={[styles.tabLabel, isSelected ? styles.tabLabelActive : null]}>
                {tab.name}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FFFFFF' },
  screenBody: { flex: 1 },
  bottomTabBar: { flexDirection: 'row', height: 64, borderTopWidth: 1, borderTopColor: '#E5E7EB', backgroundColor: '#FFFFFF', alignItems: 'center' },
  tabButton: { flex: 1, alignItems: 'center', justifyContent: 'center', height: '100%' },
  tabButtonActive: { backgroundColor: 'rgba(58, 99, 81, 0.05)' },
  tabIcon: { fontSize: 18, marginBottom: 2 },
  tabLabel: { fontSize: 11, color: '#9CA3AF', fontWeight: '500' },
  tabLabelActive: { color: '#3A6351', fontWeight: 'bold' },
});