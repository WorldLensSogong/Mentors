const assert = require('node:assert/strict');

const { resolveEntryScreenState } = require('../.tmp-navigation/logic.js');

assert.equal(
  resolveEntryScreenState({
    accessToken: null,
    hasCompletedOnboarding: false,
    isCheckingRemoteStatus: false,
  }),
  'login',
  'users without a token should land on the login screen first',
);

assert.equal(
  resolveEntryScreenState({
    accessToken: 'token',
    hasCompletedOnboarding: false,
    isCheckingRemoteStatus: true,
  }),
  'checking',
  'tokened users should briefly show the remote onboarding status check when needed',
);

assert.equal(
  resolveEntryScreenState({
    accessToken: 'token',
    hasCompletedOnboarding: false,
    isCheckingRemoteStatus: false,
  }),
  'onboarding',
  'authenticated users without onboarding completion should enter onboarding',
);

assert.equal(
  resolveEntryScreenState({
    accessToken: 'token',
    hasCompletedOnboarding: true,
    isCheckingRemoteStatus: false,
  }),
  'home',
  'completed users should land on home',
);

console.log('navigation logic tests passed');
