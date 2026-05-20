import React, { useState } from 'react';
import { 
  StyleSheet, 
  Text, 
  View, 
  TextInput, 
  TouchableOpacity, 
  SafeAreaView, 
  ScrollView 
} from 'react-native';

interface SearchScreenProps {
  onNavigateToDetail: () => void;
}

export default function SearchScreen({ onNavigateToDetail }: SearchScreenProps) {
  const [activeTab, setActiveTab] = useState('환율');
  const tabs = ['환율', '금리', '코스피', '나스닥'];

  return (
    <SafeAreaView style={styles.container}>
      {/* 상단 검색바 영역 */}
      <View style={styles.searchHeader}>
        <TextInput 
          style={styles.searchInput} 
          placeholder="종목, 뉴스, 경제 용어 검색" 
          placeholderTextColor="#BCBCBC"
        />
        <View style={styles.headerIcons}>
          <Text style={styles.iconText}>🔔</Text>
          <Text style={styles.iconText}>🔖</Text>
          <Text style={styles.iconText}>👤</Text>
        </View>
      </View>

      {/* 상단 탭바 */}
      <View style={styles.tabBar}>
        {tabs.map((tab) => {
          const isSelected = activeTab === tab;
          return (
            <TouchableOpacity 
              key={tab} 
              style={[styles.tabItem, isSelected ? styles.tabItemActive : null]}
              onPress={() => setActiveTab(tab)}
            >
              <Text style={[styles.tabText, isSelected ? styles.tabTextActive : null]}>
                {tab}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {/* 메인 지표 카드 */}
        <View style={styles.mainCard}>
          <Text style={styles.priceText}>1,320.50원</Text>
          <Text style={styles.changeText}>+12.30 (+0.94%)</Text>
          
          {/* 피그마 차트 그래픽 구현 (View 조절) */}
          <View style={styles.chartContainer}>
            <View style={styles.chartLine} />
            <View style={styles.chartTimeline}>
              <Text style={styles.timeText}>09:00</Text>
              <Text style={styles.timeText}>11:00</Text>
              <Text style={styles.timeText}>13:00</Text>
              <Text style={styles.timeText}>15:00</Text>
            </View>
          </View>
        </View>

        {/* AI 요약 섹션 */}
        <View style={styles.aiSummarySection}>
          <View style={styles.badgeAi}><Text style={styles.badgeAiText}>AI</Text></View>
          <Text style={styles.aiSummaryText}>
            달러/원 환율이 2주 만에 최저치를 기록했어요. 미 연준의 금리 인하 기대감이 반영된 것으로 분석됩니다.
          </Text>
        </View>

        {/* 관련 뉴스 섹션 */}
        <Text style={styles.sectionTitle}>관련 뉴스</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.newsHorizontalScroll}>
          {[1, 2, 3].map((item) => (
            <TouchableOpacity key={item} style={styles.newsCard} onPress={onNavigateToDetail}>
              <View style={styles.badgeEconomy}><Text style={styles.badgeEconomyText}>경제</Text></View>
              <Text style={styles.newsCardTitle} numberOfLines={2}>
                환율 1,320원대 하락 마감
              </Text>
              <Text style={styles.newsTimeText}>2분 전</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FFFFFF' },
  searchHeader: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingTop: 8, paddingBottom: 12 },
  searchInput: { flex: 1, height: 40, backgroundColor: '#F3F4F6', borderRadius: 20, paddingHorizontal: 16, fontSize: 14, color: '#111111' },
  headerIcons: { flexDirection: 'row', marginLeft: 12, gap: 10 },
  iconText: { fontSize: 20 },
  tabBar: { flexDirection: 'row', borderBottomWidth: 1, borderColor: '#E5E7EB' },
  tabItem: { flex: 1, alignItems: 'center', paddingVertical: 12, borderBottomWidth: 2, borderBottomColor: 'transparent' },
  tabItemActive: { borderBottomColor: '#3A6351' },
  tabText: { fontSize: 15, color: '#9CA3AF', fontWeight: '500' },
  tabTextActive: { color: '#3A6351', fontWeight: 'bold' },
  scrollContent: { padding: 16, paddingBottom: 100 },
  mainCard: { backgroundColor: '#FFFFFF', borderWidth: 1, borderColor: '#F3F4F6', borderRadius: 16, padding: 20, marginBottom: 16, shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.05, shadowRadius: 8, elevation: 2 },
  priceText: { fontSize: 28, fontWeight: 'bold', color: '#111111' },
  changeText: { fontSize: 14, color: '#3A6351', marginTop: 4, fontWeight: '500' },
  chartContainer: { marginTop: 20, backgroundColor: 'rgba(58, 99, 81, 0.05)', borderRadius: 8, padding: 12 },
  chartLine: { height: 60, borderBottomWidth: 2, borderBottomColor: '#3A6351', marginBottom: 8 },
  chartTimeline: { flexDirection: 'row', justifyContent: 'space-between' },
  timeText: { fontSize: 11, color: '#9CA3AF' },
  aiSummarySection: { backgroundColor: 'rgba(58, 99, 81, 0.05)', borderRadius: 12, padding: 16, marginBottom: 24 },
  badgeAi: { backgroundColor: '#3A6351', paddingHorizontal: 8, paddingVertical: 2, borderRadius: 4, alignSelf: 'flex-start', marginBottom: 8 },
  badgeAiText: { color: '#FFFFFF', fontSize: 11, fontWeight: 'bold' },
  aiSummaryText: { fontSize: 14, color: '#333333', lineHeight: 22 },
  sectionTitle: { fontSize: 18, fontWeight: 'bold', color: '#111111', marginBottom: 12 },
  newsHorizontalScroll: { flexDirection: 'row' },
  newsCard: { width: 160, backgroundColor: '#F9FAFB', borderRadius: 12, padding: 14, marginRight: 12, borderWidth: 1, borderColor: '#F3F4F6' },
  badgeEconomy: { backgroundColor: '#6B7280', paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4, alignSelf: 'flex-start', marginBottom: 12 },
  badgeEconomyText: { color: '#FFFFFF', fontSize: 10, fontWeight: 'bold' },
  newsCardTitle: { fontSize: 14, fontWeight: '600', color: '#111111', lineHeight: 20, height: 40 },
  newsTimeText: { fontSize: 11, color: '#9CA3AF', marginTop: 8 },
});