import axios from 'axios';
import { useUserStore } from '../store/userStore';

const baseURL = process.env.EXPO_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

// eslint-disable-next-line import/no-named-as-default-member
export const apiClient = axios.create({
  baseURL,
  timeout: 10000,
});

apiClient.interceptors.request.use((config) => {
  const token = useUserStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      useUserStore.getState().clearToken();
    }
    return Promise.reject(err);
  },
);
