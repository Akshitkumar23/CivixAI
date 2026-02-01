import type { UserProfile, Scheme, RecommendedScheme } from './types';

function checkEligibility(profile: UserProfile, scheme: Scheme): boolean {
  const { eligibility } = scheme;
  if (eligibility.minAge && profile.age < eligibility.minAge) return false;
  if (eligibility.maxAge && profile.age > eligibility.maxAge) return false;
  if (eligibility.maxIncome && profile.annualIncome > eligibility.maxIncome) return false;
  if (eligibility.states && !eligibility.states.includes(profile.state)) return false;
  if (eligibility.genders && !eligibility.genders.includes(profile.gender)) return false;
  if (eligibility.isStudent !== undefined && profile.isStudent !== eligibility.isStudent) return false;
  if (eligibility.hasDisability !== undefined && profile.hasDisability !== eligibility.hasDisability) return false;
  if (eligibility.castes && !eligibility.castes.includes(profile.caste)) return false;

  return true;
}

function estimateBenefit(profile: UserProfile, scheme: Scheme): string {
    // This is a simplified benefit estimation. A real-world app would have more complex logic.
    if (scheme.id === 'PM-JAY') {
        return 'Up to ₹5 lakh health insurance coverage per family per year.';
    }
    if (scheme.id === 'PMAY-U') {
        return `Subsidy on home loan interest, potentially saving over ₹2.67 lakh.`;
    }
    if (scheme.id === 'Digital India Internship') {
        return 'A stipend of ₹10,000 per month for valuable work experience.';
    }
    return scheme.benefits;
}

function calculatePriority(profile: UserProfile, scheme: Scheme): { priority: number; confidence: number } {
  let score = 0;

  // Benefit Score (simplified)
  if (scheme.benefits.toLowerCase().includes('lakh') || scheme.benefits.toLowerCase().includes('insurance')) {
    score += 40;
  } else if (scheme.benefits.toLowerCase().includes('stipend') || scheme.benefits.toLowerCase().includes('subsidy')) {
    score += 30;
  } else {
    score += 10;
  }

  // Eligibility Ease Score
  const criteriaCount = Object.keys(scheme.eligibility).length;
  score += (1 - criteriaCount / 8) * 30; // Max 8 criteria fields

  // Document Score
  const docCount = scheme.documentsRequired.length;
  score += (1 - docCount / 5) * 30; // Assume max 5 docs for simplicity

  // Confidence calculation
  let confidence = 100;
  const { eligibility } = scheme;
  if (eligibility.minAge && eligibility.maxAge) {
    const ageRange = eligibility.maxAge - eligibility.minAge;
    const proximity = Math.min(profile.age - eligibility.minAge, eligibility.maxAge - profile.age);
    if (ageRange > 0 && (proximity / ageRange) < 0.1) {
        confidence -= 10; // Close to edge
    }
  }
  if (eligibility.maxIncome) {
     if(profile.annualIncome > eligibility.maxIncome * 0.9) {
         confidence -= 15; // Close to income limit
     }
  }
  confidence = Math.max(75, Math.floor(confidence));


  return { priority: Math.min(100, Math.floor(score)), confidence };
}


export function getRecommendations(profile: UserProfile, schemes: Scheme[]): RecommendedScheme[] {
  const eligibleSchemes = schemes.filter(scheme => checkEligibility(profile, scheme));

  const recommendations: RecommendedScheme[] = eligibleSchemes.map(scheme => {
    const { priority, confidence } = calculatePriority(profile, scheme);
    return {
      ...scheme,
      estimatedBenefit: estimateBenefit(profile, scheme),
      priority,
      confidence,
    };
  });
  
  // Sort by priority score, descending
  recommendations.sort((a, b) => b.priority - a.priority);

  return recommendations.slice(0, 5); // Return top 5
}
