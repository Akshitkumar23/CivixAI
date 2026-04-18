/**
 * Centralized type definitions for CivixAI
 * This file consolidates all TypeScript interfaces and types used across the application.
 */

// ── User Profile Types ──────────────────────────────────────────────────────

/** Core demographic information required for basic eligibility */
export interface CoreUserProfile {
  age: number;
  annualIncome: number;
  state: string;
  caste: CasteCategory;
  occupation: Occupation;
}

export type CasteCategory = 'general' | 'obc' | 'sc' | 'st';
export type Occupation = 'student' | 'employed' | 'farmer' | 'unemployed' | 'retired';
export type Gender = 'male' | 'female' | 'other';
export type EducationLevel = 'illiterate' | 'primary' | 'secondary' | 'higher_secondary' | 'graduate' | 'postgraduate' | 'phd';
export type DigitalLiteracyLevel = 'none' | 'basic' | 'intermediate' | 'advanced';
export type LocationType = 'urban' | 'rural';
export type MaritalStatus = 'single' | 'married' | 'widowed' | 'divorced';
export type EmploymentType = 'government' | 'private' | 'self_employed' | 'daily_wage' | 'not_applicable';
export type SkillCertification = 'none' | 'it' | 'technical' | 'agriculture' | 'handicraft' | 'other';
export type LoanType = 'none' | 'education' | 'business' | 'housing' | 'agriculture' | 'emergency';

/** Extended profile with optional Level 1 fields */
export interface ExtendedUserProfileLevel1 {
  gender?: Gender;
  hasLand: boolean;
  hasDisability: boolean;
  familyIncome?: number;
  hasAvailedSimilarScheme: boolean;
}

/** Extended profile with optional Level 2 (modern intelligent) fields */
export interface ExtendedUserProfileLevel2 {
  landSize?: number;
  familySize?: number;
  isSingleGirlChild: boolean;
  isWidowOrSenior: boolean;
  isTaxPayer: boolean;
  isBankLinked: boolean;
  educationLevel?: EducationLevel;
  digitalLiteracy?: DigitalLiteracyLevel;
  urbanRural?: LocationType;
  maritalStatus?: MaritalStatus;
  isBPL: boolean;
  isMinority: boolean;
  monthlyExpenses?: number;
  hasSmartphone: boolean;
  hasInternet: boolean;
  employmentType?: EmploymentType;
  skillCertification?: SkillCertification;
  loanRequirement?: LoanType;
  monthlySavings?: number;
  hasInsurance: boolean;
  hasPension: boolean;
  prioritySchemes?: string[];
}

/** Complete user profile combining all levels */
export type UserProfile = CoreUserProfile & ExtendedUserProfileLevel1 & ExtendedUserProfileLevel2;

// ── Scheme Types ─────────────────────────────────────────────────────────────

/** Basic scheme information */
export interface Scheme {
  id: string;
  name: string;
  description: string;
  ministry?: string;
  category?: string;
  benefitType?: 'scheme' | 'loan' | 'insurance';
  benefitAmount?: string;
  applicationUrl?: string;
  documentsRequired?: string[];
}

/** Scheme with eligibility criteria */
export interface SchemeWithEligibility extends Scheme {
  eligibility: {
    minAge?: number;
    maxAge?: number;
    maxIncome?: number;
    applicableStates?: string[];
    genderEligibility?: string;
    casteEligibility?: string;
    occupationEligibility?: string;
    disabilityRequired?: boolean;
  };
}

/** Scheme recommendation with confidence score */
export interface RecommendedScheme extends Scheme {
  eligible: boolean;
  confidence: number;
  priority: number;
  estimatedBenefit?: string;
  reasons?: string[];
  missingInputs?: string[];
  pathToEligibility?: string[];
}

/** Detailed scheme information for display */
export interface SchemeDetails extends Scheme {
  tldrBullets?: Array<{ icon: string; title: string; text: string }>;
  docChecklist?: Array<{ name: string; checked: boolean }>;
  howToApplySteps?: Array<{ step: number; title: string; description: string }>;
  fullDescription?: string;
  agency?: string;
  level?: string;
}

// ── API Response Types ──────────────────────────────────────────────────────

/** Response from ML eligibility check */
export interface EligibilityResponse {
  success: boolean;
  schemeDetails?: EligibleSchemeDetails[];
  eligibleSchemes?: string[];
  error?: string;
  confidence_score?: number;
}

/** Individual scheme eligibility result */
export interface EligibleSchemeDetails {
  id?: string;
  name: string;
  eligible: boolean;
  confidence: number;
  threshold?: number;
  description?: string;
  ministry?: string;
  category?: string;
  benefitType?: string;
  benefitAmount?: string;
  type?: 'scheme' | 'loan' | 'insurance';
  reasons?: string[];
  missingInputs?: string[];
  pathToEligibility?: string[];
}

/** Response from ML recommendation engine */
export interface RecommendationResponse {
  rankedSchemes: RankedScheme[];
  benefitEstimates: BenefitEstimate[];
  requiredDocuments: DocumentRequirement[];
  whyThisScheme: SchemeReasoning[];
  knowledgeGraph: KnowledgeGraphNode[];
}

/** Ranked scheme from recommendation engine */
export interface RankedScheme {
  schemeId: string;
  name: string;
  type: 'scheme' | 'loan' | 'insurance';
  eligible: boolean;
  confidence: number;
  benefitScore: number;
  rankScore: number;
  category: string;
  description: string;
  ministry: string;
  level: string;
  url: string;
  documents: string[];
  reasons: string[];
  missing: string[];
  benefitAmount: string;
  pathToEligibility: string[];
}

/** Benefit estimate for a scheme */
export interface BenefitEstimate {
  schemeId: string;
  estimate: {
    amount: number;
    isRange: boolean;
    summary: string;
  };
}

/** Document requirements for a scheme */
export interface DocumentRequirement {
  schemeId: string;
  documentsRequired: string[];
}

/** Reasoning for scheme recommendation */
export interface SchemeReasoning {
  schemeId: string;
  reasons: string[];
  pathToEligibility: string[];
}

/** Knowledge graph node for related schemes */
export interface KnowledgeGraphNode {
  schemeId: string;
  related: Array<{ id: string; name: string }>;
}

// ── ML Model Types ──────────────────────────────────────────────────────────

/** Prediction for a single scheme */
export interface MLModelPrediction {
  eligible: boolean;
  confidence: number;
  threshold: number;
  error?: string;
}

/** Full ML model response */
export interface MLModelResponse {
  [schemeKey: string]: MLModelPrediction;
  error?: MLModelPrediction;
}

/** Scheme catalog entry for ML processing */
export interface SchemeCatalogEntry {
  id: string;
  name: string;
  mlKey?: string;
  description?: string;
  benefits?: string;
  documents?: string[];
  maxIncome?: number;
  minAge?: number;
  categories?: string[] | "ALL";
  states?: string[] | "ALL";
}

// ── Form Types ──────────────────────────────────────────────────────────────

/** Form step configuration */
export interface FormStep {
  title: string;
  description: string | ((occupation: string) => string);
  progressWidth: string;
}

/** Demo profile for quick testing */
export interface DemoProfile {
  label: string;
  emoji: string;
  color: string;
  values: Partial<UserProfile>;
}

// ── UI Component Types ──────────────────────────────────────────────────────

/** Toast notification */
export interface Toast {
  id: string;
  title: string;
  description?: string;
  variant?: 'default' | 'destructive' | 'success';
}

/** Pagination state */
export interface PaginationState {
  currentPage: number;
  totalPages: number;
  itemsPerPage: number;
  totalItems: number;
}

/** Filter state for scheme listing */
export interface SchemeFilters {
  type?: 'scheme' | 'loan' | 'insurance';
  category?: string;
  ministry?: string;
  minConfidence?: number;
  searchQuery?: string;
}