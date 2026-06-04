export interface LearningQuizOption {
  index: number;
  text: string;
}

export interface LearningQuiz {
  concept_id: number;
  concept_name: string;
  question: string;
  options: LearningQuizOption[];
  attempted: boolean;
  solved: boolean;
  last_result_correct: boolean | null;
}

export interface TierQuizCatalogResponse {
  tier: string;
  quizzes: LearningQuiz[];
}

export interface SubmitLearningQuizRequest {
  concept_id: number;
  answer_index: number;
  quiz_index?: number;
}

export interface SubmitLearningQuizResponse {
  correct: boolean;
  explanation: string;
}

export interface DailyReportHighlight {
  news_id?: number;
  title?: string;
  [key: string]: unknown;
}

export interface DailyReportCard {
  id: number;
  report_date: string;
  mentor_strategy: string;
  tier: string;
  status: string;
  body: string | null;
  highlights: DailyReportHighlight[];
}

export interface TodayOpenerResponse {
  first_today: boolean;
  opener: string;
  report: DailyReportCard;
}
