import { useState, useEffect, useRef } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute, type RouteProp } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { colors } from '@/constants/colors';
import { rssSearchNews } from '@/features/explore/content/api';
import type { RssNewsItem } from '@/features/explore/content/types';
import type { AppStackParamList } from '@/navigation/types';

type RouteProps = RouteProp<AppStackParamList, 'SearchResult'>;

function formatTime(publishedAt: string | null): string {
  if (!publishedAt) return '';
  const diff = Date.now() - new Date(publishedAt).getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return '방금 전';
  if (minutes < 60) return `${minutes}분 전`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}시간 전`;
  return `${Math.floor(hours / 24)}일 전`;
}

export function SearchResultScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<AppStackParamList>>();
  const route = useRoute<RouteProps>();
  const { query: initialQuery } = route.params;

  const [inputText, setInputText] = useState(initialQuery);
  const [activeQuery, setActiveQuery] = useState(initialQuery);
  const [results, setResults] = useState<RssNewsItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const mountedRef = useRef(true);
  useEffect(() => {
    mountedRef.current = true;
    return () => { mountedRef.current = false; };
  }, []);

  // activeQuery가 바뀔 때마다 검색
  useEffect(() => {
    if (!activeQuery.trim()) return;
    setIsLoading(true);
    setHasSearched(false);
    rssSearchNews(activeQuery.trim(), 15)
      .then((data) => {
        if (mountedRef.current) {
          setResults(data);
          setHasSearched(true);
        }
      })
      .catch(() => {
        if (mountedRef.current) {
          setResults([]);
          setHasSearched(true);
        }
      })
      .finally(() => {
        if (mountedRef.current) setIsLoading(false);
      });
  }, [activeQuery]);

  function handleSearch() {
    const q = inputText.trim();
    if (!q) return;
    if (q === activeQuery) {
      // 같은 쿼리 재검색 강제
      setActiveQuery('');
      setTimeout(() => setActiveQuery(q), 0);
    } else {
      setActiveQuery(q);
    }
  }

  function openSummary(item: RssNewsItem) {
    navigation.navigate('RssArticleSummary', {
      title: item.title,
      url: item.url,
      source_name: item.source_name,
      published_at: item.published_at,
    });
  }

  return (
    <SafeAreaView style={styles.screen} edges={['bottom']}>
      {/* 헤더 — 뒤로가기 + 검색창 */}
      <View style={styles.header}>
        <Pressable onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Text style={styles.backArrow}>←</Text>
        </Pressable>
        <View style={styles.searchBar}>
          <TextInput
            style={styles.searchInput}
            value={inputText}
            onChangeText={setInputText}
            placeholder="검색어를 입력하세요"
            placeholderTextColor="#A4A9A5"
            returnKeyType="search"
            onSubmitEditing={handleSearch}
            autoFocus={false}
          />
          <Pressable
            onPress={handleSearch}
            style={({ pressed }) => [styles.searchBtn, pressed && styles.searchBtnPressed]}
          >
            <Text style={styles.searchBtnText}>검색</Text>
          </Pressable>
        </View>
      </View>

      {/* 결과 */}
      {isLoading ? (
        <View style={styles.centerBox}>
          <ActivityIndicator color={colors.primary} size="large" />
          <Text style={styles.loadingText}>"{activeQuery}" 검색 중...</Text>
        </View>
      ) : !hasSearched ? null : results.length === 0 ? (
        <View style={styles.centerBox}>
          <Text style={styles.emptyTitle}>검색 결과가 없어요</Text>
          <Text style={styles.emptyDesc}>다른 키워드로 다시 검색해 보세요.</Text>
        </View>
      ) : (
        <ScrollView
          contentContainerStyle={styles.listContent}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          {/* 결과 수 */}
          <Text style={styles.resultCount}>
            "{activeQuery}" 검색 결과 {results.length}건
          </Text>

          {results.map((item, index) => (
            <Pressable
              key={`${item.url}-${index}`}
              onPress={() => openSummary(item)}
              style={({ pressed }) => [styles.card, pressed && styles.cardPressed]}
            >
              {/* 상단: 출처 뱃지 + 시간 */}
              <View style={styles.cardTop}>
                <View style={styles.badgeRow}>
                  {item.source_name ? (
                    <View style={styles.sourceBadge}>
                      <Text style={styles.sourceBadgeText}>{item.source_name}</Text>
                    </View>
                  ) : null}
                  <View style={styles.rssBadge}>
                    <Text style={styles.rssBadgeText}>구글 뉴스</Text>
                  </View>
                </View>
                <Text style={styles.timeText}>{formatTime(item.published_at)}</Text>
              </View>

              {/* 제목 */}
              <Text numberOfLines={3} style={styles.title}>
                {item.title}
              </Text>

              {/* 키워드 */}
              {item.keywords && item.keywords.length > 0 ? (
                <View style={styles.keywordRow}>
                  {item.keywords.slice(0, 4).map((kw, i) => (
                    <View key={`${kw}-${i}`} style={styles.keywordChip}>
                      <Text style={styles.keywordChipText}>{kw}</Text>
                    </View>
                  ))}
                </View>
              ) : null}

              {/* 링크 힌트 */}
              <Text style={styles.linkHint}>AI 요약 보기 →</Text>
            </Pressable>
          ))}
        </ScrollView>
      )}
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
    backgroundColor: colors.surface,
    borderBottomColor: colors.border,
    borderBottomWidth: 1,
    flexDirection: 'row',
    gap: 10,
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  backBtn: {
    alignItems: 'center',
    flexShrink: 0,
    height: 36,
    justifyContent: 'center',
    width: 32,
  },
  backArrow: {
    color: colors.text,
    fontSize: 22,
  },
  searchBar: {
    alignItems: 'center',
    backgroundColor: colors.background,
    borderColor: colors.border,
    borderRadius: 99,
    borderWidth: 1,
    flex: 1,
    flexDirection: 'row',
    gap: 8,
    height: 42,
    paddingLeft: 14,
    paddingRight: 6,
  },
  searchInput: {
    color: colors.text,
    flex: 1,
    fontSize: 14,
  },
  searchBtn: {
    backgroundColor: colors.primary,
    borderRadius: 20,
    paddingHorizontal: 14,
    paddingVertical: 7,
  },
  searchBtnPressed: {
    opacity: 0.8,
  },
  searchBtnText: {
    color: colors.surface,
    fontSize: 13,
    fontWeight: '700',
  },
  centerBox: {
    alignItems: 'center',
    flex: 1,
    gap: 12,
    justifyContent: 'center',
    padding: 24,
  },
  loadingText: {
    color: colors.muted,
    fontSize: 14,
    fontWeight: '600',
  },
  emptyTitle: {
    color: colors.text,
    fontSize: 18,
    fontWeight: '800',
  },
  emptyDesc: {
    color: colors.muted,
    fontSize: 14,
    lineHeight: 20,
    textAlign: 'center',
  },
  listContent: {
    gap: 10,
    paddingBottom: 32,
    paddingHorizontal: 16,
    paddingTop: 16,
  },
  resultCount: {
    color: colors.muted,
    fontSize: 13,
    fontWeight: '600',
    marginBottom: 4,
  },
  card: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 16,
    borderWidth: 1,
    gap: 10,
    padding: 16,
  },
  cardPressed: {
    opacity: 0.88,
  },
  cardTop: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 8,
    justifyContent: 'space-between',
  },
  badgeRow: {
    alignItems: 'center',
    flex: 1,
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  sourceBadge: {
    backgroundColor: '#3E654F',
    borderRadius: 4,
    paddingHorizontal: 6,
    paddingVertical: 3,
  },
  sourceBadgeText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: '700',
  },
  rssBadge: {
    backgroundColor: colors.primarySoft,
    borderColor: colors.primary,
    borderRadius: 4,
    borderWidth: 1,
    paddingHorizontal: 6,
    paddingVertical: 3,
  },
  rssBadgeText: {
    color: colors.primary,
    fontSize: 10,
    fontWeight: '700',
  },
  timeText: {
    color: colors.muted,
    flexShrink: 0,
    fontSize: 11,
  },
  title: {
    color: colors.text,
    fontSize: 15,
    fontWeight: '700',
    lineHeight: 22,
  },
  keywordRow: {
    alignItems: 'center',
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 5,
  },
  keywordChip: {
    backgroundColor: colors.primarySoft,
    borderColor: colors.primary,
    borderRadius: 20,
    borderWidth: 1,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  keywordChipText: {
    color: colors.primary,
    fontSize: 11,
    fontWeight: '600',
  },
  linkHint: {
    color: colors.primary,
    fontSize: 12,
    fontWeight: '700',
  },
});
