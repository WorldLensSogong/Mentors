import React, { useState, useEffect } from 'react';
import { 
  StyleSheet, 
  Text, 
  View, 
  TextInput, 
  TouchableOpacity, 
  SafeAreaView, 
  KeyboardAvoidingView, 
  Platform, 
  ScrollView 
} from 'react-native';

export default function LoginScreen() {
  const [isLoginMode, setIsLoginMode] = useState(true);
  
  // 💡 외부 훅을 쓰지 않고 화면 내부 상태(State)로 통합하여 에러 원천 차단
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  const [emailError, setEmailError] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [confirmError, setConfirmError] = useState('');

  // 모드 변경 시 입력값 및 에러 초기화
  useEffect(() => {
    setEmail('');
    setPassword('');
    setConfirmPassword('');
    setEmailError('');
    setPasswordError('');
    setConfirmError('');
  }, [isLoginMode]);

  // 실시간 이메일 검사
  const handleEmailChange = (text: string) => {
    setEmail(text);
    if (!text) {
      setEmailError('이메일을 입력해 주세요.');
    } else if (!text.includes('@')) {
      setEmailError('올바른 이메일 형식이 아닙니다.');
    } else {
      setEmailError('');
    }
  };

  // 실시간 비밀번호 검사
  const handlePasswordChange = (text: string) => {
    setPassword(text);
    if (text.length < 8) {
      setPasswordError('비밀번호는 최소 8자 이상이어야 합니다.');
    } else {
      setPasswordError('');
    }
  };

  // 실시간 비밀번호 확인 검사
  const handleConfirmChange = (text: string) => {
    setConfirmPassword(text);
    if (!isLoginMode && password !== text) {
      setConfirmError('비밀번호가 일치하지 않습니다.');
    } else {
      setConfirmError('');
    }
  };

  const onSubmit = () => {
    if (!email.includes('@') || password.length < 8) return;
    if (!isLoginMode && password !== confirmPassword) return;
    alert(isLoginMode ? '로그인 성공!' : '회원가입 성공!');
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'} 
        style={styles.keyboardView}
      >
        <ScrollView contentContainerStyle={styles.scrollContainer} bounces={false}>
          
          <View style={styles.logoSection}>
            <View style={styles.logoCircle} />
            <Text style={styles.logoTitle}>Mentors</Text>
            <Text style={styles.logoSubtitle}>막막한 당신을 위한 첫 번째 투자 전략</Text>
          </View>

          <View style={styles.card}>
            <Text style={styles.cardTitle}>{isLoginMode ? '로그인' : '회원가입'}</Text>

            {/* 이메일 */}
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>이메일</Text>
              <TextInput 
                style={[styles.input, emailError ? styles.inputError : null]} 
                placeholder="email@example.com" 
                placeholderTextColor="#999999"
                autoCapitalize="none"
                keyboardType="email-address"
                onChangeText={handleEmailChange}
                value={email}
              />
              {emailError ? <Text style={styles.errorText}>{emailError}</Text> : null}
            </View>

            {/* 비밀번호 */}
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>비밀번호</Text>
              <TextInput 
                style={[styles.input, passwordError ? styles.inputError : null]} 
                placeholder="********" 
                placeholderTextColor="#999999"
                secureTextEntry
                onChangeText={handlePasswordChange}
                value={password}
              />
              {passwordError ? <Text style={styles.errorText}>{passwordError}</Text> : null}
            </View>

            {/* 비밀번호 확인 (회원가입 모드일 때만) */}
            {!isLoginMode && (
              <View style={styles.inputGroup}>
                <Text style={styles.inputLabel}>비밀번호 확인</Text>
                <TextInput 
                  style={[styles.input, confirmError ? styles.inputError : null]} 
                  placeholder="********" 
                  placeholderTextColor="#999999"
                  secureTextEntry
                  onChangeText={handleConfirmChange}
                  value={confirmPassword}
                />
                {confirmError ? <Text style={styles.errorText}>{confirmError}</Text> : null}
              </View>
            )}

            {/* 버튼 */}
            <TouchableOpacity 
              style={[styles.button, { backgroundColor: '#1E40AF' }]}
              onPress={onSubmit}
            >
              <Text style={styles.buttonText}>{isLoginMode ? '로그인' : '회원가입'}</Text>
            </TouchableOpacity>

            {/* 전환 링크 */}
            <View style={styles.switchModeContainer}>
              <Text style={styles.switchModeText}>
                {isLoginMode ? '계정이 없으신가요?' : '이미 계정이 있으신가요?'}
              </Text>
              <TouchableOpacity onPress={() => setIsLoginMode(!isLoginMode)}>
                <Text style={[styles.switchModeLink, { color: '#1E40AF' }]}>
                  {isLoginMode ? '회원가입' : '로그인'}
                </Text>
              </TouchableOpacity>
            </View>

          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

// 💡 하드코딩된 안전한 컬러 값으로 경로 꼬임 문제 해결
const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#1E40AF' },
  keyboardView: { flex: 1 },
  scrollContainer: { flexGrow: 1 },
  logoSection: { flex: 0.8, justifyContent: 'center', alignItems: 'center', paddingVertical: 40 },
  logoCircle: { width: 70, height: 70, borderRadius: 35, backgroundColor: 'rgba(255, 255, 255, 0.2)', marginBottom: 16 },
  logoTitle: { fontSize: 32, fontWeight: 'bold', color: '#FFFFFF', letterSpacing: 0.5 },
  logoSubtitle: { fontSize: 13, color: 'rgba(255, 255, 255, 0.8)', marginTop: 6 },
  card: { flex: 2, backgroundColor: '#FFFFFF', borderTopLeftRadius: 32, borderTopRightRadius: 32, paddingHorizontal: 28, paddingTop: 36, paddingBottom: 40 },
  cardTitle: { fontSize: 24, fontWeight: 'bold', color: '#111111', marginBottom: 28 },
  inputGroup: { marginBottom: 20 },
  inputLabel: { fontSize: 13, fontWeight: '600', color: '#111111', marginBottom: 8 },
  input: { height: 48, borderWidth: 1, borderColor: '#E5E7EB', borderRadius: 8, paddingHorizontal: 16, fontSize: 15, color: '#111111', backgroundColor: '#FAFAFA' },
  inputError: { borderColor: '#FF3B30' },
  errorText: { color: '#FF3B30', fontSize: 12, marginTop: 4, fontWeight: '500' },
  button: { height: 52, borderRadius: 8, justifyContent: 'center', alignItems: 'center', marginTop: 12 },
  buttonText: { color: '#FFFFFF', fontSize: 16, fontWeight: 'bold' },
  switchModeContainer: { flexDirection: 'row', justifyContent: 'center', alignItems: 'center', marginTop: 24 },
  switchModeText: { fontSize: 14, color: '#666666' },
  switchModeLink: { fontSize: 14, fontWeight: 'bold', marginLeft: 8, textDecorationLine: 'underline' },
});