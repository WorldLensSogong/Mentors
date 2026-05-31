export interface PromotionTestChoice {
  choice_id: string;
  text: string;
}

export interface PromotionTestQuestion {
  question_id: string;
  prompt: string;
  choices: PromotionTestChoice[];
}

export interface PromotionTestPreview {
  target_tier: string;
  passing_score: number;
  question_count: number;
  questions: PromotionTestQuestion[];
}

export interface GrowthProgressResponse {
  current_tier: string;
  next_tier: string | null;
  progress_percent: number;
  mastered_concepts: number;
  total_concepts: number;
  eligible_for_promotion: boolean;
  promotion_eligible_at: string | null;
  unlocked_features: string[];
  next_unlocks: string[];
  promotion_test: PromotionTestPreview | null;
}

export interface PromotionTestAnswerRequest {
  question_id: string;
  choice_id: string;
}

export interface PromotionTestRequest {
  answers: PromotionTestAnswerRequest[];
}

export interface PromotionTestResponse {
  previous_tier: string;
  current_tier: string;
  target_tier: string | null;
  passed: boolean;
  score_percent: number;
  correct_answers: number;
  total_questions: number;
  unlocked_features: string[];
  message: string;
}

export interface GrowthStageCopy {
  badge: string;
  title: string;
  description: string;
}

export interface PromotionQuestionResult {
  question_id: string;
  prompt: string;
  user_choice_id: string;
  correct_choice_id: string;
  is_correct: boolean;
  choices: Record<string, string>;
}

export interface PromotionAttemptDetail {
  id: number;
  current_tier: string;
  target_tier: string | null;
  total_questions: number;
  correct_answers: number;
  score_percent: number;
  passed: boolean;
  attempted_at: string;
  question_results: PromotionQuestionResult[];
}
