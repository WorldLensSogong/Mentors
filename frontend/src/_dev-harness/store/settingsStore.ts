import AsyncStorage from '@react-native-async-storage/async-storage';
import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';

export const DEFAULT_REMINDER_TIME = '20:00';

export interface ReminderPreferences {
  learningReminderEnabled: boolean;
  dailyReportReminderEnabled: boolean;
  reminderTime: string;
}

interface SettingsState extends ReminderPreferences {
  setLearningReminderEnabled: (enabled: boolean) => void;
  setDailyReportReminderEnabled: (enabled: boolean) => void;
  setReminderTime: (time: string) => void;
  reset: () => void;
}

const defaultState: ReminderPreferences = {
  learningReminderEnabled: false,
  dailyReportReminderEnabled: false,
  reminderTime: DEFAULT_REMINDER_TIME,
};

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      ...defaultState,
      setLearningReminderEnabled: (enabled) => set({ learningReminderEnabled: enabled }),
      setDailyReportReminderEnabled: (enabled) => set({ dailyReportReminderEnabled: enabled }),
      setReminderTime: (reminderTime) => {
        set({ reminderTime });
      },
      reset: () => set(defaultState),
    }),
    {
      name: 'mentors-settings',
      storage: createJSONStorage(() => AsyncStorage),
    },
  ),
);
