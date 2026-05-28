/**
 * 콘텐츠 동 사용자 관심 키워드 CRUD 검증 화면 (dev-harness 전용).
 *
 * - GET /api/content/keywords 목록 표시
 * - POST 으로 키워드 추가 (industry source 자동 매칭 OR 새 manual 키워드 생성)
 * - DELETE 으로 본인 소유 키워드 제거
 *
 * owner: content 동 (5동) backend — _dev-harness 자유 추가
 */

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  ActivityIndicator,
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { colors } from '@/constants/colors';
import { addMyKeyword, listMyKeywords, removeMyKeyword } from '@/features/content/api';
import type { UserKeywordResponse, UserKeywordSource } from '@/features/content/types';
import { useUserStore } from '@/store/userStore';

const SOURCE_LABEL: Record<UserKeywordSource, string> = {
  onboarding: '온보딩',
  manual: '직접',
  auto: '자동',
};

// 자주 사용하는 시드 키워드 (PR-6 industry pool에 매칭됨)
const SUGGESTED_KEYWORDS = [
  '인공지능',
  '반도체 장비',
  '반도체 파운드리',
  '전기차',
  '배터리소재',
  '암호화폐',
  '바이오',
  '신재생 에너지',
];

export function ContentKeywordsScreen() {
  const queryClient = useQueryClient();
  const accessToken = useUserStore((state) => state.accessToken);
  const [newKeyword, setNewKeyword] = useState('');

  const listQuery = useQuery({
    queryKey: ['content-user-keywords', accessToken],
    queryFn: listMyKeywords,
    enabled: Boolean(accessToken),
    retry: 0,
  });

  const addMutation = useMutation({
    mutationFn: (keyword: string) => addMyKeyword({ keyword }),
    onSuccess: async () => {
      setNewKeyword('');
      await queryClient.invalidateQueries({ queryKey: ['content-user-keywords', accessToken] });
    },
    onError: (err: unknown) => {
      const message = (err as { response?: { data?: { code?: string } } })?.response?.data?.code;
      if (message === 'conflict') {
        Alert.alert('알림', '이미 등록된 키워드입니다');
      } else {
        Alert.alert('오류', '키워드 추가 실패');
      }
    },
  });

  const removeMutation = useMutation({
    mutationFn: (id: number) => removeMyKeyword(id),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ['content-user-keywords', accessToken] }),
  });

  const handleAdd = (keyword: string) => {
    const k = keyword.trim();
    if (!k) return;
    addMutation.mutate(k);
  };

  if (!accessToken) {
    return (
      <SafeAreaView style={styles.container}>
        <Text style={styles.title}>관심 키워드</Text>
        <Text style={styles.muted}>로그인이 필요합니다.</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <Text style={styles.title}>관심 키워드</Text>
        <Text style={styles.subtitle}>
          시드 키워드(예: 인공지능)는 기존 마스터키워드와 자동 매칭 — 산업 회사 뉴스가 노출됩니다.
        </Text>

        {/* 추가 입력 */}
        <View style={styles.addRow}>
          <TextInput
            style={styles.input}
            placeholder="키워드 입력 (예: 반도체 장비)"
            value={newKeyword}
            onChangeText={setNewKeyword}
            onSubmitEditing={() => handleAdd(newKeyword)}
            returnKeyType="done"
          />
          <Pressable
            style={[
              styles.addBtn,
              (addMutation.isPending || !newKeyword.trim()) && styles.addBtnDisabled,
            ]}
            onPress={() => handleAdd(newKeyword)}
            disabled={addMutation.isPending || !newKeyword.trim()}
          >
            <Text style={styles.addBtnText}>추가</Text>
          </Pressable>
        </View>

        {/* 추천 키워드 칩 */}
        <Text style={styles.sectionLabel}>추천 (산업 풀 시드)</Text>
        <View style={styles.suggestedRow}>
          {SUGGESTED_KEYWORDS.map((kw) => (
            <Pressable
              key={kw}
              onPress={() => handleAdd(kw)}
              style={styles.suggestedChip}
              disabled={addMutation.isPending}
            >
              <Text style={styles.suggestedChipText}>+ {kw}</Text>
            </Pressable>
          ))}
        </View>

        {/* 현재 키워드 목록 */}
        <Text style={styles.sectionLabel}>내 키워드 ({listQuery.data?.total ?? 0})</Text>
        {listQuery.isLoading ? (
          <ActivityIndicator color={colors.primary} style={styles.loading} />
        ) : listQuery.isError ? (
          <Text style={styles.error}>키워드 목록 불러오기 실패</Text>
        ) : (listQuery.data?.items ?? []).length === 0 ? (
          <Text style={styles.muted}>등록된 키워드가 없습니다.</Text>
        ) : (
          (listQuery.data?.items ?? []).map((kw) => (
            <KeywordRow
              key={kw.id}
              keyword={kw}
              onRemove={() => removeMutation.mutate(kw.id)}
              removing={removeMutation.isPending && removeMutation.variables === kw.id}
            />
          ))
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

function KeywordRow({
  keyword,
  onRemove,
  removing,
}: {
  keyword: UserKeywordResponse;
  onRemove: () => void;
  removing: boolean;
}) {
  return (
    <View style={styles.kwRow}>
      <View style={styles.kwInfo}>
        <Text style={styles.kwText}>{keyword.keyword}</Text>
        <Text style={styles.kwMeta}>
          {SOURCE_LABEL[keyword.source]} · master_id={keyword.master_keyword_id}
        </Text>
      </View>
      <Pressable
        style={styles.removeBtn}
        onPress={onRemove}
        disabled={removing}
      >
        {removing ? (
          <ActivityIndicator size="small" color={colors.rose} />
        ) : (
          <Text style={styles.removeBtnText}>삭제</Text>
        )}
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  scrollContent: {
    padding: 20,
    paddingBottom: 64,
  },
  title: {
    fontSize: 22,
    fontWeight: '800',
    color: colors.text,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 12,
    color: colors.muted,
    lineHeight: 18,
    marginBottom: 16,
  },
  addRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 16,
  },
  input: {
    flex: 1,
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 14,
    color: colors.text,
  },
  addBtn: {
    backgroundColor: colors.primary,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 10,
  },
  addBtnDisabled: {
    backgroundColor: colors.muted,
  },
  addBtnText: {
    color: colors.surface,
    fontWeight: '700',
    fontSize: 14,
  },
  sectionLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: colors.muted,
    marginTop: 8,
    marginBottom: 6,
  },
  suggestedRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 16,
  },
  suggestedChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: colors.primarySoft,
  },
  suggestedChipText: {
    fontSize: 12,
    color: colors.primary,
    fontWeight: '600',
  },
  kwRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 10,
    padding: 12,
    marginBottom: 8,
  },
  kwInfo: {
    flex: 1,
  },
  kwText: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.text,
  },
  kwMeta: {
    fontSize: 11,
    color: colors.muted,
    marginTop: 2,
  },
  removeBtn: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.rose,
  },
  removeBtnText: {
    fontSize: 12,
    fontWeight: '700',
    color: colors.rose,
  },
  loading: {
    marginVertical: 16,
  },
  error: {
    color: colors.rose,
    textAlign: 'center',
    marginVertical: 16,
  },
  muted: {
    color: colors.muted,
    textAlign: 'center',
    marginVertical: 16,
  },
});
