import type { UserProfile, Scheme, RecommendedScheme } from './types';

function checkEligibility(profile: UserProfile, scheme: any): boolean {
  const eligibility = scheme.eligibility;
  if (!eligibility) return true; // If no criteria, assume eligible for rule-based check

  if (eligibility.minAge && profile.age < eligibility.minAge) return false;
  if (eligibility.maxAge && profile.age > eligibility.maxAge) return false;
  if (eligibility.maxIncome && profile.annualIncome > eligibility.maxIncome) return false;
  
  if (eligibility.states && Array.isArray(eligibility.states) && !eligibility.states.includes(profile.state)) {
      if (!eligibility.states.includes('ALL')) return false;
  }

  if (eligibility.occupationEligibility && profile.occupation !== eligibility.occupationEligibility) {
      if (eligibility.occupationEligibility !== 'ALL') return false;
  }

  if (eligibility.disabilityRequired !== undefined && profile.hasDisability !== eligibility.disabilityRequired) return false;

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
    return scheme.benefitAmount || scheme.description || "";
}

function calculatePriority(profile: UserProfile, scheme: any): { priority: number; confidence: number } {
  let score = 0;
  const description = scheme.description || "";

  // Benefit Score (simplified)
  if (description.toLowerCase().includes('lakh') || description.toLowerCase().includes('insurance')) {
    score += 40;
  } else if (description.toLowerCase().includes('stipend') || description.toLowerCase().includes('subsidy')) {
    score += 30;
  } else {
    score += 10;
  }

  // Eligibility Ease Score
  const criteriaCount = scheme.eligibility ? Object.keys(scheme.eligibility).length : 0;
  score += (1 - criteriaCount / 8) * 30;

  // Document Score
  const docCount = (scheme.documentsRequired || []).length;
  score += (1 - docCount / 5) * 30;

  // Confidence calculation
  let confidence = 100;
  const eligibility = scheme.eligibility;
  if (eligibility) {
    if (eligibility.minAge && eligibility.maxAge) {
      const ageRange = eligibility.maxAge - eligibility.minAge;
      const proximity = Math.min(profile.age - eligibility.minAge, eligibility.maxAge - profile.age);
      if (ageRange > 0 && (proximity / ageRange) < 0.1) {
          confidence -= 10;
      }
    }
    if (eligibility.maxIncome) {
       if(profile.annualIncome > eligibility.maxIncome * 0.9) {
           confidence -= 15;
       }
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
      eligible: true,
      estimatedBenefit: estimateBenefit(profile, scheme),
      priority,
      confidence,
    };
  });
  
  // Sort by priority score, descending
  recommendations.sort((a, b) => b.priority - a.priority);

  return recommendations.slice(0, 5); // Return top 5
}
