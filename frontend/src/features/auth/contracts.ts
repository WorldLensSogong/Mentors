export const DEV_LOCAL_TEST_ACCOUNT_EMAIL = 'local-test@mentors.dev';
export const DEV_LOCAL_TEST_ACCOUNT_PASSWORD = 'Mentors123!';

export interface LocalSignupRequest {
  email: string;
  password: string;
  password_confirm: string;
}

export interface LocalLoginRequest {
  email: string;
  password: string;
}
