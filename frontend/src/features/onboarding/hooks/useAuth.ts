import { useState } from 'react';

export function useAuthForm(isLoginMode: boolean) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  const [emailError, setEmailError] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [confirmError, setConfirmError] = useState('');

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

  // 폼 초기화 함수
  const reset = () => {
    setEmail('');
    setPassword('');
    setConfirmPassword('');
    setEmailError('');
    setPasswordError('');
    setConfirmError('');
  };

  const onSubmit = () => {
    if (!email.includes('@') || password.length < 8) {
      return;
    }
    if (!isLoginMode && password !== confirmPassword) {
      return;
    }
    console.log(isLoginMode ? '로그인 성공:' : '회원가입 성공:', email);
  };

  return {
    email, password, confirmPassword,
    emailError, passwordError, confirmError,
    handleEmailChange, handlePasswordChange, handleConfirmChange,
    onSubmit, reset
  };
}