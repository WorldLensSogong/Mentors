import React, { useState } from 'react';
import { 
  StyleSheet, 
  Text, 
  View, 
  TouchableOpacity, 
  SafeAreaView, 
  ScrollView, 
  Platform
} from 'react-native';

// 6개 화면의 질문과 옵션 데이터 정의
const ONBOARDING_STEPS = [
  { id: 'age', title: '연령대가\n어떻게 되시나요?', options: ['10대', '20대 초반 (20~24세)', '20대 후반 (25~29세)', '30대', '40대 이상'], multiple: false },
  { id: 'experience', title: '투자 경험이\n있으신가요?', options: ['없어요, 처음이에요', '조금 해봤어요', '꽤 경험이 있어요'], multiple: false },
  { id: 'goal', title: '투자이 관심을 갖게 된\n이유가 무엇인가요?', subtitle: '복수 선택 가능해요', options: ['재테크·자산 불리기', '노후 준비', '주변 사람들의 영향', '경제 공부가 하고 싶어서', '기타'], multiple: true },
  { id: 'scale', title: '투자 자산 규모가\n어느 정도인가요?', options: ['100만원 미만', '100~500만원', '500만~1000만원', '1000만원 이상', '아직 없어요'], multiple: false },
  { id: 'risk', title: '손실을 어느 정도\n감안할 수 있나요?', options: ['손실 없이 안정적으로만', '5~10% 정도는 괜찮아요', '20~30% 정도도 감수 가능'], multiple: false },
  { id: 'interest', title: '어떤 주제에\n관심이 있으신가요?', subtitle: '복수 선택 가능해요 · 관심사 기반으로 리포트를 추천해드려요', options: ['국내 주식', '미국 주식', '해외 주식', '바이오', 'IT·테크', '반도체', '2차전지', 'AI', '방산', '에너지', '금융', '엔터·미디어', '패션·소비재', 'ETF·펀드', '암호화폐'], multiple: true },
];

export default function OnboardingFlow() {
  const [currentStep, setCurrentStep] = useState(0);
  
  // 유저가 선택한 답변들을 저장하는 상태
  const [answers, setAnswers] = useState<Record<string, string[]>>({
    age: [], experience: [], goal: [], scale: [], risk: [], interest: []
  });

  const stepData = ONBOARDING_STEPS[currentStep];
  const currentKey = stepData.id;
  const selectedAnswers = answers[currentKey] || [];

  // 옵션을 클릭했을 때 작동하는 함수
  const handleSelectOption = (option: string) => {
    if (stepData.multiple) {
      // 다중 선택 가능한 경우 (3단계, 6단계)
      if (selectedAnswers.includes(option)) {
        setAnswers({ ...answers, [currentKey]: selectedAnswers.filter(item => item !== option) });
      } else {
        setAnswers({ ...answers, [currentKey]: [...selectedAnswers, option] });
      }
    } else {
      // 단일 선택만 가능한 경우 (1, 2, 4, 5단계)
      setAnswers({ ...answers, [currentKey]: [option] });
    }
  };

  // 다음 버튼 클릭 시
  const handleNext = () => {
    if (selectedAnswers.length === 0) return; // 선택 안 하면 작동 안 함

    if (currentStep < ONBOARDING_STEPS.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      // 6단계 완료 시 최종 데이터 출력!
      console.log('✨ [온보딩 데이터 수집 완료]:', answers);
      alert('온보딩 완료! 수집된 데이터는 콘솔창에서 확인할 수 있습니다.');
    }
  };

  // 뒤로가기 화살표 클릭 시
  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  // 다음 버튼 활성화 여부
  const isButtonEnabled = selectedAnswers.length > 0;

  return (
    <SafeAreaView style={styles.container}>
      {/* 상단 헤더 영역 (뒤로가기 버튼 + 페이지 인디케이터) */}
      <View style={styles.header}>
        {currentStep > 0 ? (
          <TouchableOpacity onPress={handleBack} style={styles.backButton}>
            <Text style={styles.backButtonText}>←</Text>
          </TouchableOpacity>
        ) : (
          <View style={styles.backButtonPlaceholder} />
        )}
        <Text style={styles.stepText}>{currentStep + 1}/{ONBOARDING_STEPS.length}</Text>
      </View>

      {/* 진행 바 (ProgressBar) */}
      <View style={styles.progressTrack}>
        <View style={[styles.progressBar, { width: `${((currentStep + 1) / ONBOARDING_STEPS.length) * 100}%` }]} />
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent} bounces={false}>
        <Text style={styles.userNameText}>안녕하세요, OOO님!</Text>
        <Text style={styles.title}>{stepData.title}</Text>
        {stepData.subtitle ? <Text style={styles.subtitle}>{stepData.subtitle}</Text> : null}

        {/* 6단계(관심 주제)일 때는 칩 모양 레이아웃, 나머지는 세로 카드 레이아웃 */}
        {currentKey === 'interest' ? (
          <View style={styles.chipContainer}>
            {stepData.options.map((option) => {
              const isSelected = selectedAnswers.includes(option);
              return (
                <TouchableOpacity
                  key={option}
                  style={[styles.chip, isSelected ? styles.chipSelected : null]}
                  onPress={() => handleSelectOption(option)}
                >
                  <Text style={[styles.chipText, isSelected ? styles.chipTextSelected : null]}>
                    {option}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>
        ) : (
          <View style={styles.optionContainer}>
            {stepData.options.map((option) => {
              const isSelected = selectedAnswers.includes(option);
              return (
                <TouchableOpacity
                  key={option}
                  style={[styles.optionCard, isSelected ? styles.optionCardSelected : null]}
                  onPress={() => handleSelectOption(option)}
                >
                  <View style={[styles.radioCircle, isSelected ? styles.radioCircleSelected : null]}>
                    {isSelected && <View style={styles.radioInnerCircle} />}
                  </View>
                  <Text style={[styles.optionText, isSelected ? styles.optionTextSelected : null]}>
                    {option}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>
        )}
      </ScrollView>

      {/* 하단 고정 버튼 */}
      <View style={styles.bottomContainer}>
        <TouchableOpacity 
          style={[styles.nextButton, isButtonEnabled ? styles.nextButtonActive : styles.nextButtonDisabled]}
          onPress={handleNext}
          disabled={!isButtonEnabled}
        >
          <Text style={styles.nextButtonText}>
            {currentStep === ONBOARDING_STEPS.length - 1 ? '시작하기' : '다음'}
          </Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#3A6351' }, // 피그마 딥그린 배경색 반영
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: 20, height: 44, marginTop: 10 },
  backButton: { padding: 8 },
  backButtonText: { color: '#FFFFFF', fontSize: 24, fontWeight: 'bold' },
  backButtonPlaceholder: { width: 40 },
  stepText: { color: 'rgba(255, 255, 255, 0.6)', fontSize: 14, fontWeight: '600' },
  progressTrack: { height: 3, backgroundColor: 'rgba(255, 255, 255, 0.2)', marginHorizontal: 20, marginTop: 4, borderRadius: 2, overflow: 'hidden' },
  progressBar: { height: '100%', backgroundColor: '#FFFFFF' },
  scrollContent: { backgroundColor: '#FFFFFF', borderTopLeftRadius: 24, borderTopRightRadius: 24, marginTop: 24, flexGrow: 1, paddingHorizontal: 24, paddingTop: 32, paddingBottom: 40 },
  userNameText: { fontSize: 13, color: '#999999', marginBottom: 6 },
  title: { fontSize: 24, fontWeight: 'bold', color: '#111111', lineHeight: 32, marginBottom: 8 },
  subtitle: { fontSize: 13, color: '#666666', marginBottom: 24 },
  optionContainer: { marginTop: 12 },
  optionCard: { flexDirection: 'row', alignItems: 'center', height: 56, borderWidth: 1, borderColor: '#E5E7EB', borderRadius: 12, paddingHorizontal: 16, marginBottom: 12, backgroundColor: '#FAFAFA' },
  optionCardSelected: { borderColor: '#3A6351', backgroundColor: 'rgba(58, 99, 81, 0.05)' },
  radioCircle: { width: 20, height: 20, borderRadius: 10, borderWidth: 1, borderColor: '#D1D5DB', alignItems: 'center', justifyContent: 'center', marginRight: 12, backgroundColor: '#FFFFFF' },
  radioCircleSelected: { borderColor: '#3A6351' },
  radioInnerCircle: { width: 10, height: 10, borderRadius: 5, backgroundColor: '#3A6351' },
  optionText: { fontSize: 15, color: '#4B5563' },
  optionTextSelected: { color: '#3A6351', fontWeight: '600' },
  chipContainer: { flexDirection: 'row', flexWrap: 'wrap', gap: 10, marginTop: 16 },
  chip: { paddingHorizontal: 16, height: 38, borderRadius: 19, borderWidth: 1, borderColor: '#E5E7EB', justifyContent: 'center', alignItems: 'center', backgroundColor: '#FAFAFA' },
  chipSelected: { borderColor: '#3A6351', backgroundColor: '#3A6351' },
  chipText: { fontSize: 14, color: '#4B5563' },
  chipTextSelected: { color: '#FFFFFF', fontWeight: '600' },
  bottomContainer: { backgroundColor: '#FFFFFF', paddingHorizontal: 24, paddingBottom: Platform.OS === 'ios' ? 20 : 30 },
  nextButton: { height: 52, borderRadius: 12, justifyContent: 'center', alignItems: 'center' },
  nextButtonActive: { backgroundColor: '#3A6351' },
  nextButtonDisabled: { backgroundColor: '#E5E7EB' },
  nextButtonText: { color: '#FFFFFF', fontSize: 16, fontWeight: 'bold' },
});