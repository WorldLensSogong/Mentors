const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const repoRoot = path.resolve(__dirname, '..', '..');

function readSource(relativePath) {
  return fs.readFileSync(path.join(repoRoot, relativePath), 'utf8');
}

const mainTabNavigatorSource = readSource('src/_dev-harness/MainTabNavigator.tsx');
const chatHistoryScreenSource = readSource('src/_dev-harness/screens/ChatHistoryScreen.tsx');
const learningRecordScreenSource = readSource('src/_dev-harness/screens/LearningRecordScreen.tsx');
const mentorChatScreenSource = readSource('src/_dev-harness/screens/MentorChatScreen.tsx');

assert.ok(
  !mainTabNavigatorSource.includes('name="Settings"'),
  'settings should move out of the bottom tab navigator and into a top-right shortcut like the Figma flow',
);

assert.ok(
  !chatHistoryScreenSource.includes('navigation.goBack()'),
  'opening a chat history card should not immediately pop the screen after navigating',
);

assert.ok(
  learningRecordScreenSource.includes("navigate('Settings')"),
  'learning record should expose a top-right shortcut into settings',
);

assert.ok(
  mentorChatScreenSource.includes("navigate('Settings')"),
  'mentor chat should expose a top-right shortcut into settings',
);

assert.ok(
  mentorChatScreenSource.includes('buildGrowthProgressQueryKey') &&
    mentorChatScreenSource.includes('growthProgressQueryKey'),
  'chat quiz submissions should refresh the same growth-progress query used by the understanding gauge',
);

console.log('harness ui regression tests passed');
