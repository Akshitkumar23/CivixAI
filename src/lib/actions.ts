'use server';

import { redirect } from 'next/navigation';
import { generateSchemeDetails } from '@/ai/flows/generate-scheme-details';
import { provideChatbotAssistance } from '@/ai/flows/provide-chatbot-assistance';
import type { UserProfile, Scheme } from '@/lib/types';

export async function findSchemes(profile: UserProfile) {
  const params = new URLSearchParams();
  // Ensure boolean values are strings for URL params
  const profileForUrl = {
    ...profile,
    // Add specific boolean string conversions if needed by the receiver
    hasDisability: String(profile.hasDisability),
    hasLand: String(profile.hasLand),
    isBPL: String(profile.isBPL),
  };

  Object.entries(profileForUrl).forEach(([key, value]) => {
    if (value !== undefined) {
      params.append(key, String(value));
    }
  });
  redirect(`/recommendations?${params.toString()}`);
}

export async function getApplicationSummary(scheme: any) {
  const result = await generateSchemeDetails({
    schemeName: scheme.name,
    eligibilityCriteria: JSON.stringify(scheme.reasons || scheme.eligibility || 'Check specific criteria'),
    benefits: scheme.benefitAmount || scheme.description,
    documentsRequired: (scheme.documentsRequired || scheme.documents || []).join(', '),
    applicationProcess: scheme.applicationUrl || 'Visit the official portal to apply.',
  });
  return result.summary;
}

export async function getChatbotResponse(query: string, context: string = '[]') {
  const result = await provideChatbotAssistance({
    query,
    schemeDetails: context,
  });

  return {
    answer: result.answer,
    redirectUrl: result.redirectUrl
  };
}
