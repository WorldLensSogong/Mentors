import { create } from 'zustand';

interface UserState {
  accessToken: string | null;
  setAccessToken: (token: string) => void;
  clearToken: () => void;
}

export const useUserStore = create<UserState>((set) => ({
  accessToken: null,
  setAccessToken: (token) => set({ accessToken: token }),
  clearToken: () => set({ accessToken: null }),
}));
