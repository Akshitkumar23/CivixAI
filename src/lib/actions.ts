'use server';

import { redirect } from 'next/navigation';
import { generateSchemeDetails } from '@/ai/flows/generate-scheme-details';
import { provideChatbotAssistance } from '@/ai/flows/provide-chatbot-assistance';
import type { UserProfile, Scheme } from '@/lib/types';
import schemesData from '@/lib/schemes.json';

export async function findSchemes(profile: UserProfile) {
  const params = new URLSearchParams();
  // Ensure boolean values are strings
  const profileWithStringBooleans = {
    ...profile,
    isStudent: String(profile.isStudent),
    hasDisability: String(profile.hasDisability),
  };

  Object.entries(profileWithStringBooleans).forEach(([key, value]) => {
    params.append(key, String(value));
  });
  redirect(`/recommendations?${params.toString()}`);
}

export async function getApplicationSummary(scheme: Scheme) {
  const result = await generateSchemeDetails({
    schemeName: scheme.name,
    eligibilityCriteria: JSON.stringify(scheme.eligibility),
    benefits: scheme.benefits,
    documentsRequired: scheme.documentsRequired.join(', '),
    applicationProcess: scheme.applicationProcess,
  });
  return result.summary;
}

export async function getChatbotResponse(query: string) {
  const schemeDetailsForContext = schemesData.schemes.map(s => ({ 
    name: s.name, 
    description: s.description,
    eligibility: s.eligibility 
  }));

  const result = await provideChatbotAssistance({
    query,
    schemeDetails: JSON.stringify(schemeDetailsForContext),
  });

  return result.answer;
}
