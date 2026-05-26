import AsyncStorage from '@react-native-async-storage/async-storage';
import { create } from 'zustand';

export const DEFAULT_REMINDER_TIME = '20:00';
const SETTINGS_STORAGE_KEY = 'mentors-settings';

export interface ReminderPreferences {
  learningReminderEnabled: boolean;
  dailyReportReminderEnabled: boolean;
  reminderTime: string;
}

interface SettingsState extends ReminderPreferences {
  hydrated: boolean;
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

async function persistSettings(nextState: ReminderPreferences): Promise<void> {
  try {
    await AsyncStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(nextState));
  } catch {
    // Ignore persistence failures and keep the in-memory state.
  }
}

export const useSettingsStore = create<SettingsState>((set, get) => ({
  ...defaultState,
  hydrated: false,
  setLearningReminderEnabled: (learningReminderEnabled) => {
    const nextState = { ...get(), learningReminderEnabled };
    set({ learningReminderEnabled });
    void persistSettings({
      learningReminderEnabled: nextState.learningReminderEnabled,
      dailyReportReminderEnabled: nextState.dailyReportReminderEnabled,
      reminderTime: nextState.reminderTime,
    });
  },
  setDailyReportReminderEnabled: (dailyReportReminderEnabled) => {
    const nextState = { ...get(), dailyReportReminderEnabled };
    set({ dailyReportReminderEnabled });
    void persistSettings({
      learningReminderEnabled: nextState.learningReminderEnabled,
      dailyReportReminderEnabled: nextState.dailyReportReminderEnabled,
      reminderTime: nextState.reminderTime,
    });
  },
  setReminderTime: (reminderTime) => {
    const nextState = { ...get(), reminderTime };
    set({ reminderTime });
    void persistSettings({
      learningReminderEnabled: nextState.learningReminderEnabled,
      dailyReportReminderEnabled: nextState.dailyReportReminderEnabled,
      reminderTime: nextState.reminderTime,
    });
  },
  reset: () => {
    set({ ...defaultState, hydrated: true });
    void persistSettings(defaultState);
  },
}));

void AsyncStorage.getItem(SETTINGS_STORAGE_KEY)
  .then((storedValue) => {
    if (!storedValue) {
      useSettingsStore.setState({ hydrated: true });
      return;
    }

    const parsed = JSON.parse(storedValue) as Partial<ReminderPreferences>;
    useSettingsStore.setState({
      learningReminderEnabled:
        typeof parsed.learningReminderEnabled === 'boolean'
          ? parsed.learningReminderEnabled
          : defaultState.learningReminderEnabled,
      dailyReportReminderEnabled:
        typeof parsed.dailyReportReminderEnabled === 'boolean'
          ? parsed.dailyReportReminderEnabled
          : defaultState.dailyReportReminderEnabled,
      reminderTime:
        typeof parsed.reminderTime === 'string' ? parsed.reminderTime : defaultState.reminderTime,
      hydrated: true,
    });
  })
  .catch(() => {
    useSettingsStore.setState({ hydrated: true });
  });
