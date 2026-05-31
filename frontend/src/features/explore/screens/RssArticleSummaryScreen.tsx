import { useState, useEffect, useRef } from 'react';
import {
  ActivityIndicator,
  Image,
  Linking,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute, type RouteProp } from '@react-navigation/native';
import { colors } from '@/constants/colors';
import { summarizeNewsUrl } from '@/features/explore/content/api';
import type { UrlSummarizeResponse } from '@/features/explore/content/types';
import type { AppStackParamList } from '@/navigation/types';

type RouteProps = RouteProp<AppStackParamList, 'RssArticleSummary'>;

function formatTime(publishedAt: string | null): string {
  if (!publishedAt) return '';
  const diff = Date.now() - new Date(publishedAt).getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return '방금 전';
  if (minutes < 60) return `${minutes}분 전`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}시간 전`;
  const days = Math.floor(hours / 24);
  return `${days}일 전`;
}

const SENTIMENT_MAP: Record<string, { label: string; bg: string; text: string }> = {
  positive: { label: '긍정적', bg: '#D6F5E3', text: '#1A7A45' },
  neutral:  { label: '중립',   bg: '#EFEFEF', text: '#555' },
  negative: { label: '부정적', bg: '#FFE5E5', text: '#C0392B' },
};

const RELEVANCE_MAP: Record<string, { label: string; bg: string; text: string }> = {
  high:   { label: '관련도 높음', bg: '#FFF0DA', text: '#B05A00' },
  medium: { label: '관련도 보통', bg: '#EFEFEF', text: '#555' },
  low:    { label: '관련도 낮음', bg: '#F0F0F0', text: '#888' },
};

const STRATEGY_MAP: Record<string, string> = {
  value:    '가치주',
  growth:   '성장주',
  dividend: '배당주',
  momentum: '모멘텀',
};

export function RssArticleSummaryScreen() {
  const navigation = useNavigation();
  const route = useRoute<RouteProps>();
  const { title, url, source_name, published_at } = route.params;

  const [result, setResult] = useState<UrlSummarizeResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(false);
  const [imageError, setImageError] = useState(false);

  const mountedRef = useRef(true);
  useEffect(() => {
    mountedRef.current = true;
    return () => { mountedRef.current = false; };
  }, []);

  useEffect(() => {
    setIsLoading(true);
    setError(false);
    summarizeNewsUrl({ url, title })
      .then((data) => {
        if (mountedRef.current) setResult(data);
      })
      .catch(() => {
        if (mountedRef.current) setError(true);
      })
      .finally(() => {
        if (mountedRef.current) setIsLoading(false);
      });
  }, [url, title]);

  async function openOriginal() {
    try {
      if (await Linking.canOpenURL(url)) {
        await Linking.openURL(url);
      }
    } catch { /* ignore */ }
  }

  const displayTitle = result?.title || title;
  const imageUrl = imageError ? null : (result?.image_url ?? null);
  const timeLabel = formatTime(published_at);

  const sentimentInfo = result?.sentiment ? SENTIMENT_MAP[result.sentiment] : null;
  const relevanceInfo = result?.investment_relevance ? RELEVANCE_MAP[result.investment_relevance] : null;

  return (
    <SafeAreaView style={styles.screen} edges={['bottom']}>
      {/* 헤더 */}
      <View style={styles.header}>
        <Pressable onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Text style={styles.backArrow}>←</Text>
        </Pressable>
        <Text style={styles.headerTitle}>AI 요약</Text>
        <View style={styles.headerSpacer} />
      </View>

      <ScrollView
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        {/* 대표 이미지 */}
        {imageUrl ? (
          <View style={styles.imageWrapper}>
            <Image
              source={{ uri: imageUrl }}
              style={styles.image}
              resizeMode="cover"
              onError={() => setImageError(true)}
            />
            {source_name ? (
              <View style={styles.imageSourceBadge}>
                <Text style={styles.imageSourceText}>{source_name}</Text>
              </View>
            ) : null}
          </View>
        ) : isLoading ? (
          <View style={[styles.imageWrapper, styles.imagePlaceholder]}>
            <ActivityIndicator color={colors.primary} />
          </View>
        ) : (
          source_name ? (
            <View style={styles.noImageSourceRow}>
              <View style={styles.sourceBadge}>
                <Text style={styles.sourceBadgeText}>{source_name}</Text>
              </View>
              {timeLabel ? <Text style={styles.metaTime}>{timeLabel}</Text> : null}
            </View>
          ) : null
        )}

        {/* 이미지 아래 메타 */}
        {imageUrl ? (
          <View style={styles.metaRowAfterImage}>
            {source_name ? (
              <View style={styles.sourceBadge}>
                <Text style={styles.sourceBadgeText}>{source_name}</Text>
              </View>
            ) : null}
            {timeLabel ? <Text style={styles.metaTime}>{timeLabel}</Text> : null}
          </View>
        ) : null}

        {/* 기사 제목 */}
        <Text style={styles.articleTitle}>{displayTitle}</Text>

        {/* ── AI 분석 배지 행 ── */}
        {!isLoading && result ? (
          <View style={styles.badgeRow}>
            {/* 신뢰도 점수 */}
            {result.reliability_score != null ? (
              <View style={styles.reliabilityBadge}>
                <Text style={styles.reliabilityLabel}>신뢰도</Text>
                <Text style={styles.reliabilityValue}>{result.reliability_score}</Text>
                <View style={styles.reliabilityBarBg}>
                  <View
                    style={[
                      styles.reliabilityBarFill,
                      {
                        width: `${result.reliability_score}%` as `${number}%`,
                        backgroundColor:
                          result.reliability_score >= 70
                            ? colors.primary
                            : result.reliability_score >= 40
                            ? '#E6A817'
                            : '#C0392B',
                      },
                    ]}
                  />
                </View>
              </View>
            ) : null}

            {/* 감성 분석 */}
            {sentimentInfo ? (
              <View style={[styles.chip, { backgroundColor: sentimentInfo.bg }]}>
                <Text style={[styles.chipText, { color: sentimentInfo.text }]}>
                  {sentimentInfo.label}
                </Text>
              </View>
            ) : null}

            {/* 투자 관련도 */}
            {relevanceInfo ? (
              <View style={[styles.chip, { backgroundColor: relevanceInfo.bg }]}>
                <Text style={[styles.chipText, { color: relevanceInfo.text }]}>
                  {relevanceInfo.label}
                </Text>
              </View>
            ) : null}
          </View>
        ) : null}

        {/* 투자 전략 */}
        {!isLoading && result?.strategies && result.strategies.length > 0 ? (
          <View style={styles.strategyRow}>
            <Text style={styles.sectionLabel}>투자 전략</Text>
            <View style={styles.chipRow}>
              {result.strategies.map((s) => (
                <View key={s} style={styles.strategyChip}>
                  <Text style={styles.strategyChipText}>
                    {STRATEGY_MAP[s] ?? s}
                  </Text>
                </View>
              ))}
            </View>
          </View>
        ) : null}

        {/* 키워드 */}
        {!isLoading && result?.keywords && result.keywords.length > 0 ? (
          <View style={styles.keywordRow}>
            <Text style={styles.sectionLabel}>키워드</Text>
            <View style={styles.chipRow}>
              {result.keywords.map((kw, i) => (
                <View key={`${kw}-${i}`} style={styles.keywordChip}>
                  <Text style={styles.keywordChipText}>{kw}</Text>
                </View>
              ))}
            </View>
          </View>
        ) : null}

        <View style={styles.divider} />

        {/* AI 요약 섹션 */}
        <View style={styles.summaryCard}>
          <View style={styles.summaryHeader}>
            <View style={styles.aiBadge}>
              <Text style={styles.aiBadgeText}>AI 요약</Text>
            </View>
            {isLoading ? (
              <View style={styles.loadingRow}>
                <ActivityIndicator color={colors.primary} size="small" />
                <Text style={styles.loadingText}>AI가 기사를 읽고 있어요...</Text>
              </View>
            ) : null}
          </View>

          {isLoading ? (
            <View style={styles.skeletonWrap}>
              <View style={[styles.skeletonLine, { width: '100%' }]} />
              <View style={[styles.skeletonLine, { width: '92%' }]} />
              <View style={[styles.skeletonLine, { width: '96%' }]} />
              <View style={[styles.skeletonLine, { width: '80%' }]} />
            </View>
          ) : error ? (
            <Text style={styles.errorText}>
              요약을 불러오지 못했어요. 원문을 직접 확인해 주세요.
            </Text>
          ) : result ? (
            <Text style={styles.summaryText}>{result.ai_summary}</Text>
          ) : null}
        </View>

        {/* 원문 보기 버튼 */}
        <Pressable
          onPress={openOriginal}
          style={({ pressed }) => [styles.originalBtn, pressed && styles.pressed]}
        >
          <Text style={styles.originalBtnText}>원문 기사 보기 ↗</Text>
        </Pressable>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: {
    backgroundColor: colors.background,
    flex: 1,
  },
  header: {
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderBottomColor: colors.border,
    borderBottomWidth: 1,
    flexDirection: 'row',
    height: 56,
    paddingHorizontal: 16,
  },
  backBtn: {
    alignItems: 'center',
    height: 36,
    justifyContent: 'center',
    width: 36,
  },
  backArrow: {
    color: colors.text,
    fontSize: 22,
  },
  headerTitle: {
    color: colors.text,
    flex: 1,
    fontSize: 17,
    fontWeight: '800',
    textAlign: 'center',
  },
  headerSpacer: {
    width: 36,
  },
  content: {
    paddingBottom: 40,
    paddingHorizontal: 16,
    paddingTop: 16,
  },
  imageWrapper: {
    borderRadius: 20,
    height: 200,
    marginBottom: 12,
    overflow: 'hidden',
    width: '100%',
  },
  image: {
    height: '100%',
    width: '100%',
  },
  imagePlaceholder: {
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    justifyContent: 'center',
  },
  imageSourceBadge: {
    backgroundColor: 'rgba(0,0,0,0.55)',
    borderRadius: 6,
    bottom: 12,
    left: 12,
    paddingHorizontal: 8,
    paddingVertical: 4,
    position: 'absolute',
  },
  imageSourceText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: '700',
  },
  noImageSourceRow: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 8,
    marginBottom: 10,
  },
  metaRowAfterImage: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 8,
    marginBottom: 10,
  },
  sourceBadge: {
    backgroundColor: '#3E654F',
    borderRadius: 4,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  sourceBadgeText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: '700',
  },
  metaTime: {
    color: colors.muted,
    fontSize: 12,
  },
  articleTitle: {
    color: colors.text,
    fontSize: 20,
    fontWeight: '800',
    lineHeight: 28,
    marginBottom: 14,
  },
  // ── AI 분석 배지 ──
  badgeRow: {
    alignItems: 'center',
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 12,
  },
  reliabilityBadge: {
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    flexDirection: 'row',
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  reliabilityLabel: {
    color: colors.muted,
    fontSize: 11,
    fontWeight: '600',
  },
  reliabilityValue: {
    color: colors.text,
    fontSize: 13,
    fontWeight: '800',
  },
  reliabilityBarBg: {
    backgroundColor: colors.border,
    borderRadius: 3,
    height: 6,
    overflow: 'hidden',
    width: 48,
  },
  reliabilityBarFill: {
    borderRadius: 3,
    height: '100%',
  },
  chip: {
    borderRadius: 20,
    paddingHorizontal: 10,
    paddingVertical: 5,
  },
  chipText: {
    fontSize: 12,
    fontWeight: '700',
  },
  sectionLabel: {
    color: colors.muted,
    fontSize: 11,
    fontWeight: '700',
    marginBottom: 6,
  },
  strategyRow: {
    marginBottom: 10,
  },
  chipRow: {
    alignItems: 'center',
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  strategyChip: {
    backgroundColor: '#E8F4FD',
    borderColor: '#7BB8E8',
    borderRadius: 20,
    borderWidth: 1,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  strategyChipText: {
    color: '#1A5F8A',
    fontSize: 12,
    fontWeight: '700',
  },
  keywordRow: {
    marginBottom: 12,
  },
  keywordChip: {
    backgroundColor: colors.primarySoft,
    borderColor: colors.primary,
    borderRadius: 20,
    borderWidth: 1,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  keywordChipText: {
    color: colors.primary,
    fontSize: 12,
    fontWeight: '600',
  },
  divider: {
    backgroundColor: colors.border,
    height: 1,
    marginBottom: 16,
  },
  summaryCard: {
    backgroundColor: '#F0F7F4',
    borderColor: '#D8ECE2',
    borderRadius: 16,
    borderWidth: 1,
    gap: 12,
    marginBottom: 20,
    padding: 18,
  },
  summaryHeader: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 10,
  },
  aiBadge: {
    backgroundColor: colors.primary,
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  aiBadgeText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: '800',
  },
  loadingRow: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 6,
  },
  loadingText: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: '600',
  },
  skeletonWrap: {
    gap: 10,
    paddingTop: 4,
  },
  skeletonLine: {
    backgroundColor: '#D8ECE2',
    borderRadius: 6,
    height: 14,
  },
  summaryText: {
    color: colors.text,
    fontSize: 15,
    fontWeight: '500',
    lineHeight: 24,
  },
  errorText: {
    color: colors.rose,
    fontSize: 14,
    fontWeight: '500',
    lineHeight: 20,
  },
  originalBtn: {
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderColor: colors.primary,
    borderRadius: 99,
    borderWidth: 1.5,
    height: 50,
    justifyContent: 'center',
  },
  originalBtnText: {
    color: colors.primary,
    fontSize: 15,
    fontWeight: '700',
  },
  pressed: {
    opacity: 0.85,
  },
});
