const assert = require('node:assert/strict');

const {
  buildLearningPreferenceSeed,
  buildLearningPreferencesPayload,
  buildScheduledReminderRequests,
  formatReminderTime,
  hasLearningPreferenceChanges,
} = require('../../.tmp-settings/_dev-harness/settings/logic.js');
const mergedPayload = buildLearningPreferencesPayload(
  {
    experience_level: 'beginner',
    interests: ['macro'],
    risk_profile: 'balanced',
    learning_goal: 'understand-news',
    preferred_style: 'gentle',
  },
  {
    interests: ['macro', 'etf'],
    preferredStyle: 'structured',
  },
);

assert.deepEqual(
  mergedPayload,
  {
    experience_level: 'beginner',
    interests: ['macro', 'etf'],
    risk_profile: 'balanced',
    learning_goal: 'understand-news',
    preferred_style: 'structured',
    answers: [],
  },
  'settings saves should preserve the onboarding profile fields that are not editable on the screen',
);

assert.equal(
  formatReminderTime('08:05'),
  '08:05',
  'time labels should stay in a mobile-friendly HH:MM format',
);

assert.equal(
  hasLearningPreferenceChanges(
    {
      experience_level: 'beginner',
      interests: ['macro', 'tech'],
      risk_profile: 'balanced',
      learning_goal: 'understand-news',
      preferred_style: 'gentle',
    },
    {
      interests: ['tech', 'macro'],
      preferredStyle: 'gentle',
    },
  ),
  false,
  'reordered interests should not mark the learning preferences as changed',
);

assert.equal(
  hasLearningPreferenceChanges(
    {
      experience_level: 'beginner',
      interests: ['macro', 'tech'],
      risk_profile: 'balanced',
      learning_goal: 'understand-news',
      preferred_style: 'gentle',
    },
    {
      interests: ['macro', 'bio'],
      preferredStyle: 'gentle',
    },
  ),
  true,
  'adding a different 관심 분야 should activate the save action',
);

assert.equal(
  buildLearningPreferenceSeed({
    interests: ['bio', 'macro', 'bio'],
    preferredStyle: 'structured',
  }),
  'bio|macro::structured',
  'learning preference seeds should stay stable across duplicate selections and order changes',
);

const reminderRequests = buildScheduledReminderRequests({
  learningReminderEnabled: true,
  dailyReportReminderEnabled: true,
  reminderTime: '20:15',
});

assert.equal(reminderRequests.length, 2, 'two reminder types should produce two schedules');
assert.deepEqual(
  reminderRequests.map((request) => request.key),
  ['learning-reminder', 'daily-report'],
  'schedule identifiers should stay stable so notifications can be replaced cleanly',
);
assert.deepEqual(
  reminderRequests.map((request) => request.trigger),
  [
    { hour: 20, minute: 15 },
    { hour: 20, minute: 15 },
  ],
  'daily reminders should reuse the chosen time for both schedule requests',
);

console.log('settings logic tests passed');
