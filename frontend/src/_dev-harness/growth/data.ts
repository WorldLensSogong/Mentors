export type ReportUnderstanding = 'known' | 'heard' | 'unknown';

export interface ReportRecord {
  id: string;
  mentor: string;
  date: string;
  title: string;
  summary: string;
  understanding: ReportUnderstanding;
}

export interface ArenaRecord {
  id: string;
  date: string;
  topicLabel: string;
  topic: string;
  mentorALetter: string;
  mentorBLetter: string;
  mentorALabel: string;
  mentorBLabel: string;
}

export const reportRecords: ReportRecord[] = [
  {
    id: 'report-1',
    mentor: '워런 버핏',
    date: '오늘',
    title: '반도체 투자 심리 회복에 삼성전자 3% 상승',
    summary: '실적 기대와 밸류에이션 관점에서 이번 반등을 어떻게 읽어야 하는지 정리합니다.',
    understanding: 'known',
  },
  {
    id: 'report-2',
    mentor: '워런 버핏',
    date: '어제',
    title: '경제적 해자가 무엇인가요?',
    summary: '오래 버티는 경쟁 우위가 왜 장기 투자에서 중요한지 초보자 눈높이로 설명합니다.',
    understanding: 'heard',
  },
  {
    id: 'report-3',
    mentor: '벤저민 그레이엄',
    date: '3일 전',
    title: '청산가치와 안전마진의 관계',
    summary: '보수적인 밸류에이션과 하방 방어를 함께 보는 사고법을 다룹니다.',
    understanding: 'unknown',
  },
];

export const arenaRecords: ArenaRecord[] = [
  {
    id: 'arena-1',
    date: '오늘',
    topicLabel: '토론 주제',
    topic: '실적 시즌에는 어떤 신호를 가장 먼저 봐야 할까요?',
    mentorALetter: '워',
    mentorBLetter: '피',
    mentorALabel: '버핏',
    mentorBLabel: '린치',
  },
  {
    id: 'arena-2',
    date: '어제',
    topicLabel: '토론 주제',
    topic: 'ETF 분산투자가 항상 개별 종목보다 더 나은 선택일까요?',
    mentorALetter: '레',
    mentorBLetter: '워',
    mentorALabel: '달리오',
    mentorBLabel: '버핏',
  },
  {
    id: 'arena-3',
    date: '3일 전',
    topicLabel: '토론 주제',
    topic: '성장주 조정장에서 현금을 늘리는 전략은 언제 유효할까요?',
    mentorALetter: '피',
    mentorBLetter: '레',
    mentorALabel: '린치',
    mentorBLabel: '달리오',
  },
  {
    id: 'arena-4',
    date: '1주 전',
    topicLabel: '토론 주제',
    topic: '금리 하락기에는 왜 배당주 매력이 다시 커질까요?',
    mentorALetter: '워',
    mentorBLetter: '레',
    mentorALabel: '버핏',
    mentorBLabel: '달리오',
  },
];
