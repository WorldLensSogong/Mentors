import type { InterestTag } from './types';

export function toggleInterest(interests: InterestTag[], interest: InterestTag): InterestTag[] {
  if (interests.includes(interest)) {
    return interests.filter((item) => item !== interest);
  }

  return [...interests, interest];
}
