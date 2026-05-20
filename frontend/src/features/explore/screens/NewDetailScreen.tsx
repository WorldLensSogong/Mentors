import React from 'react';
import { 
  StyleSheet, 
  Text, 
  View, 
  TouchableOpacity, 
  SafeAreaView, 
  ScrollView 
} from 'react-native';

interface NewsDetailScreenProps {
  onBack: () => void;
}

export default function NewsDetailScreen({ onBack }: NewsDetailScreenProps) {
  return (
    <SafeAreaView style={styles.container}>
      {/* 상단 네비바 헤더 */}
      <View style={styles.detailHeader}>
        <TouchableOpacity onPress={onBack} style={styles.backButton}>
          <Text style={styles.backIcon}>←</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>뉴스 상세</Text>
        <View style={styles.headerIcons}>
          <Text style={styles.iconText}>🔔</Text>
          <Text style={styles.iconText}>🔖</Text>
          <Text style={styles.iconText}>👤</Text>
        </View>
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {/* 상단 썸네일 대용 그레이 영역 */}
        <View style={styles.imagePlaceholder} />

        {/* 기사 헤더 정보 */}
        <View style={styles.badgeSection}>
          <View style={styles.badgeEconomy}><Text style={styles.badgeEconomyText}>경제</Text></View>
        </View>
        <Text style={styles.mainTitle}>
          글로벌 IT 대기업, 서울에 아시아 최대 AI 연구소 설립 발표
        </Text>
        <Text style={styles.dateText}>2026-03-19 · 5분 읽기</Text>

        {/* 기사 본문 */}
        <Text style={styles.bodyText}>
          글로벌 IT 대기업이 서울에 아시아 최대 규모의 인공지능 연구개발 센터를 설립한다고 발표했다. 총 투자 규모는 5조 원이며, 향후 5년간 1,000명 이상의 AI 전문 인력을 채용할 계획이다.
        </Text>

        {/* AI 요약 박스 */}
        <View style={styles.aiSummaryBox}>
          <View style={styles.badgeAiSummary}><Text style={styles.badgeAiSummaryText}>AI 요약</Text></View>
          <Text style={styles.aiSummaryContent}>
            국내 AI 투자 확대 소식. 반도체·AI 관련주에 긍정적 영향이 예상됩니다.
          </Text>
        </View>

        {/* 원본 기사 보기 버튼 */}
        <TouchableOpacity style={styles.linkButton}>
          <Text style={styles.linkButtonText}>원본 기사 보기</Text>
        </TouchableOpacity>

        {/* 관련 기사 섹션 */}
        <Text style={styles.sectionTitle}>관련 기사</Text>
        <View style={styles.relatedGrid}>
          {[1, 2].map((item) => (
            <View key={item} style={styles.relatedCard}>
              <View style={styles.relatedImagePlaceholder} />
              <Text style={styles.relatedTitle} numberOfLines={2}>관련 뉴스 제목</Text>
            </View>
          ))}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FFFFFF' },
  detailHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 16, height: 48, borderBottomWidth: 1, borderBottomColor: '#F3F4F6' },
  backButton: { padding: 4 },
  backIcon: { fontSize: 22, color: '#111111', fontWeight: 'bold' },
  headerTitle: { fontSize: 16, fontWeight: 'bold', color: '#111111', marginLeft: 16, flex: 1 },
  headerIcons: { flexDirection: 'row', gap: 10 },
  iconText: { fontSize: 20 },
  scrollContent: { paddingBottom: 100 },
  imagePlaceholder: { height: 200, backgroundColor: '#BCBCBC' },
  badgeSection: { paddingHorizontal: 20, paddingTop: 20 },
  badgeEconomy: { backgroundColor: '#3A6351', paddingHorizontal: 8, paddingVertical: 3, borderRadius: 4, alignSelf: 'flex-start' },
  badgeEconomyText: { color: '#FFFFFF', fontSize: 11, fontWeight: 'bold' },
  mainTitle: { fontSize: 22, fontWeight: 'bold', color: '#111111', paddingHorizontal: 20, marginTop: 12, lineHeight: 30 },
  dateText: { fontSize: 13, color: '#9CA3AF', paddingHorizontal: 20, marginTop: 8 },
  bodyText: { fontSize: 15, color: '#333333', paddingHorizontal: 20, marginTop: 20, lineHeight: 26 },
  aiSummaryBox: { marginHorizontal: 20, marginTop: 24, backgroundColor: 'rgba(58, 99, 81, 0.05)', borderRadius: 12, padding: 16 },
  badgeAiSummary: { backgroundColor: '#3A6351', paddingHorizontal: 8, paddingVertical: 3, borderRadius: 4, alignSelf: 'flex-start', marginBottom: 8 },
  badgeAiSummaryText: { color: '#FFFFFF', fontSize: 11, fontWeight: 'bold' },
  aiSummaryContent: { fontSize: 14, color: '#3A6351', fontWeight: '600', lineHeight: 22 },
  linkButton: { marginHorizontal: 20, marginTop: 16, height: 48, backgroundColor: '#F3F4F6', borderRadius: 12, justifyContent: 'center', alignItems: 'center' },
  linkButtonText: { fontSize: 14, color: '#4B5563', fontWeight: '600' },
  sectionTitle: { fontSize: 16, fontWeight: 'bold', color: '#111111', marginHorizontal: 20, marginTop: 28, marginBottom: 12 },
  relatedGrid: { flexDirection: 'row', paddingHorizontal: 20, gap: 12 },
  relatedCard: { flex: 1, backgroundColor: '#FFFFFF', borderWidth: 1, borderColor: '#F3F4F6', borderRadius: 12, overflow: 'hidden' },
  relatedImagePlaceholder: { height: 90, backgroundColor: '#F3F4F6' },
  relatedTitle: { fontSize: 13, color: '#111111', padding: 8, fontWeight: '500' },
});