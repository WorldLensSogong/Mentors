/**
 * 일일 리포트 본문 전용 경량 마크다운 렌더러 (의존성 없음).
 *
 * 리포트 프롬프트(backend/features/daily_report/prompts.py)가 만드는 제한된 문법만
 * 처리한다: `#`~`###` 헤더, `-`/`*` 불릿, `**bold**`, 빈 줄 문단 구분. 외부 마크다운
 * 라이브러리를 들이지 않아 RN/React 버전 호환 리스크를 피한다.
 */
import type { ReactNode } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { colors } from '@/constants/colors';

/** `**bold**` 인라인 강조만 파싱해 Text 조각 배열로 반환. */
function renderInline(text: string, keyBase: string): ReactNode[] {
  const parts = text.split(/(\*\*[^*]+\*\*)/g).filter((part) => part.length > 0);
  return parts.map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <Text key={`${keyBase}-b${index}`} style={styles.bold}>
          {part.slice(2, -2)}
        </Text>
      );
    }
    return <Text key={`${keyBase}-t${index}`}>{part}</Text>;
  });
}

/** 리포트 본문(마크다운)을 헤더/불릿/문단 블록으로 렌더. */
export function ReportMarkdown({ body }: { body: string }) {
  const lines = body.replace(/\r\n/g, '\n').split('\n');
  const blocks: ReactNode[] = [];
  let keySeq = 0;

  for (const raw of lines) {
    const line = raw.trimEnd();
    const key = `md-${keySeq++}`;

    if (!line.trim()) {
      blocks.push(<View key={key} style={styles.blockGap} />);
      continue;
    }
    if (line.startsWith('### ')) {
      blocks.push(
        <Text key={key} style={styles.h3}>
          {renderInline(line.slice(4), key)}
        </Text>,
      );
    } else if (line.startsWith('## ')) {
      blocks.push(
        <Text key={key} style={styles.h2}>
          {renderInline(line.slice(3), key)}
        </Text>,
      );
    } else if (line.startsWith('# ')) {
      blocks.push(
        <Text key={key} style={styles.h1}>
          {renderInline(line.slice(2), key)}
        </Text>,
      );
    } else if (/^[-*]\s+/.test(line)) {
      blocks.push(
        <View key={key} style={styles.bulletRow}>
          <Text style={styles.bulletDot}>•</Text>
          <Text style={styles.bulletText}>{renderInline(line.replace(/^[-*]\s+/, ''), key)}</Text>
        </View>,
      );
    } else {
      blocks.push(
        <Text key={key} style={styles.paragraph}>
          {renderInline(line, key)}
        </Text>,
      );
    }
  }

  return <View>{blocks}</View>;
}

/** 미리보기(numberOfLines)용 — 마크다운 마커를 제거한 평문으로 변환. */
export function stripMarkdown(body: string): string {
  return body
    .replace(/\r\n/g, '\n')
    .replace(/^#{1,6}\s+/gm, '')
    .replace(/^[-*]\s+/gm, '• ')
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/\n{2,}/g, '\n')
    .trim();
}

const styles = StyleSheet.create({
  blockGap: {
    height: 10,
  },
  h1: {
    color: colors.text,
    fontSize: 19,
    fontWeight: '800',
    lineHeight: 26,
    marginBottom: 4,
    marginTop: 8,
  },
  h2: {
    color: colors.text,
    fontSize: 16,
    fontWeight: '800',
    lineHeight: 23,
    marginBottom: 4,
    marginTop: 12,
  },
  h3: {
    color: colors.text,
    fontSize: 15,
    fontWeight: '700',
    lineHeight: 21,
    marginBottom: 2,
    marginTop: 8,
  },
  paragraph: {
    color: colors.text,
    fontSize: 15,
    lineHeight: 24,
  },
  bold: {
    fontWeight: '800',
  },
  bulletRow: {
    flexDirection: 'row',
    gap: 8,
    paddingRight: 4,
  },
  bulletDot: {
    color: colors.primary,
    fontSize: 15,
    lineHeight: 24,
  },
  bulletText: {
    color: colors.text,
    flex: 1,
    fontSize: 15,
    lineHeight: 24,
  },
});
