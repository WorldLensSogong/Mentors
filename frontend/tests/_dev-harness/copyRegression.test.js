const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const repoRoot = path.resolve(__dirname, '..', '..');

function readSource(relativePath) {
  return fs.readFileSync(path.join(repoRoot, relativePath), 'utf8');
}

function assertDoesNotInclude(relativePath, bannedText, message) {
  const source = readSource(relativePath);
  assert.ok(!source.includes(bannedText), message);
}

function assertIncludes(relativePath, expectedText, message) {
  const source = readSource(relativePath);
  assert.ok(source.includes(expectedText), message);
}

const growthCardSource = readSource('src/_dev-harness/components/GrowthProgressCard.tsx');
assert.ok(
  !/>\s*Growth\s*</.test(growthCardSource),
  'growth progress card should not expose the English eyebrow copy',
);

assertDoesNotInclude(
  'src/_dev-harness/screens/MentorChatScreen.tsx',
  'Mentor Chat',
  'mentor chat screen should use Korean headings',
);

assertDoesNotInclude(
  'src/_dev-harness/screens/MentorChatScreen.tsx',
  'Follow-up Quiz',
  'follow-up quiz sections should use Korean copy',
);

assertDoesNotInclude(
  'src/_dev-harness/screens/ChatHistoryScreen.tsx',
  'Chat Archive',
  'chat history hero copy should be Korean',
);

assertDoesNotInclude(
  'src/_dev-harness/growth/data.ts',
  'Warren Buffett',
  'report and arena fixtures should use Korean mentor names',
);

assertDoesNotInclude(
  'src/_dev-harness/growth/data.ts',
  'Today',
  'report and arena fixtures should use Korean date labels',
);

assertDoesNotInclude(
  'src/_dev-harness/growth/data.ts',
  'Debate topic',
  'arena topic labels should use Korean copy',
);

assertDoesNotInclude(
  'src/_dev-harness/onboarding/data.ts',
  'Ray Dalio',
  'onboarding mentor data should use Korean mentor names',
);

assertIncludes(
  'src/_dev-harness/onboarding/data.ts',
  '워런 버핏',
  'onboarding mentor copy should expose localized mentor names',
);

console.log('copy regression tests passed');
