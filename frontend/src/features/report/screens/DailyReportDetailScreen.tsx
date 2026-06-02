import { StyleSheet, Text, View, Pressable, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute } from '@react-navigation/native';
import type { RouteProp } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { colors } from '@/constants/colors';
import type { AppStackParamList } from '@/navigation/types';

type DailyReportDetailRouteProp = RouteProp<AppStackParamList, 'DailyReportDetail'>;

const STRATEGY_LABELS: Record<string, string> = {
  value: '가치투자',
  growth: '성장투자',
  dividend: '배당투자',
  momentum: '모멘텀투자',
};

function formatReportDate(reportDate: string): string {
  const parsed = new Date(reportDate);
  if (Number.isNaN(parsed.getTime())) {
    return reportDate;
  }
  return `${parsed.getFullYear()}년 ${parsed.getMonth() + 1}월 ${parsed.getDate()}일`;
}

export function DailyReportDetailScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<AppStackParamList>>();
  const route = useRoute<DailyReportDetailRouteProp>();
  const { report, opener } = route.params;

  const strategyLabel = STRATEGY_LABELS[report.mentor_strategy] ?? report.mentor_strategy;
  const isReady = report.status === 'ready';

  return (
    <SafeAreaView style={styles.screen}>
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Pressable onPress={() => navigation.goBack()} style={styles.backBtn}>
            <Text style={styles.backBtnText}>←</Text>
          </Pressable>
          <Text style={styles.headerTitle}>일일 리포트</Text>
        </View>
      </View>

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.metaRow}>
          <View style={styles.badge}>
            <Text style={styles.badgeText}>{strategyLabel}</Text>
          </View>
          <View style={[styles.badge, styles.tierBadge]}>
            <Text style={styles.badgeText}>{report.tier}</Text>
          </View>
        </View>

        <Text style={styles.reportDate}>{formatReportDate(report.report_date)}</Text>

        {opener ? <Text style={styles.opener}>{opener}</Text> : null}

        <View style={styles.divider} />

        {isReady && report.body ? (
          <Text style={styles.body}>{report.body}</Text>
        ) : (
          <View style={styles.pendingBox}>
            <Text style={styles.pendingText}>리포트를 정리하고 있어요. 잠시 후 다시 확인해 주세요.</Text>
          </View>
        )}

        {report.highlights.length > 0 ? (
          <>
            <Text style={styles.sectionTitle}>오늘의 하이라이트</Text>
            <View style={styles.highlightColumn}>
              {report.highlights.map((highlight, index) => (
                <View key={`${highlight.news_id ?? 'highlight'}-${index}`} style={styles.highlightCard}>
                  <Text style={styles.highlightIndex}>{index + 1}</Text>
                  <Text style={styles.highlightTitle}>{highlight.title ?? '관련 뉴스'}</Text>
                </View>
              ))}
            </View>
          </>
        ) : null}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 8,
    borderBottomWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  backBtn: {
    padding: 4,
  },
  backBtnText: {
    fontSize: 22,
    fontWeight: '700',
    color: colors.text,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: colors.text,
  },
  content: {
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 32,
  },
  metaRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 12,
  },
  badge: {
    alignSelf: 'flex-start',
    backgroundColor: colors.primary,
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 5,
  },
  tierBadge: {
    backgroundColor: colors.text,
  },
  badgeText: {
    color: colors.surface,
    fontSize: 12,
    fontWeight: '800',
  },
  reportDate: {
    color: colors.muted,
    fontSize: 13,
    fontWeight: '600',
    marginBottom: 12,
  },
  opener: {
    color: colors.text,
    fontSize: 15,
    fontWeight: '700',
    lineHeight: 22,
  },
  divider: {
    height: 1,
    backgroundColor: colors.border,
    marginVertical: 16,
  },
  body: {
    color: colors.text,
    fontSize: 15,
    lineHeight: 24,
  },
  pendingBox: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 16,
    paddingHorizontal: 18,
    paddingVertical: 20,
  },
  pendingText: {
    color: colors.muted,
    fontSize: 14,
    lineHeight: 20,
    textAlign: 'center',
  },
  sectionTitle: {
    color: colors.text,
    fontSize: 16,
    fontWeight: '800',
    marginTop: 28,
    marginBottom: 12,
  },
  highlightColumn: {
    gap: 10,
  },
  highlightCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 16,
    paddingHorizontal: 16,
    paddingVertical: 14,
  },
  highlightIndex: {
    color: colors.primary,
    fontSize: 14,
    fontWeight: '800',
    width: 16,
  },
  highlightTitle: {
    color: colors.text,
    flex: 1,
    fontSize: 14,
    fontWeight: '600',
    lineHeight: 20,
  },
});
