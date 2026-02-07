export type UserProfile = {
  age: number;
  gender: 'male' | 'female' | 'other';
  annualIncome: number;
  state: string;
  isStudent: boolean;
  hasDisability: boolean;
  caste: 'general' | 'obc' | 'sc' | 'st';
};

export type Scheme = {
  id: string;
  name: string;
  description: string;
  eligibility: {
    minAge?: number;
    maxAge?: number;
    maxIncome?: number;
    states?: string[];
    genders?: ('male' | 'female' | 'other')[];
    isStudent?: boolean;
    hasDisability?: boolean;
    castes?: ('general' | 'obc' | 'sc' | 'st')[];
  };
  benefits: string;
  documentsRequired: string[];
  applicationProcess: string;
};

export type RecommendedScheme = Scheme & {
  estimatedBenefit: string;
  priority: number;
  confidence: number;
};

export type SchemeCatalogEntry = {
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
};

// API Response types for ML model
export interface MLModelPrediction {
  eligible: boolean;
  confidence: number;
  threshold: number;
  error?: string;
}

export interface MLModelResponse {
  [schemeKey: string]: MLModelPrediction;
  error?: MLModelPrediction;
}

export interface SchemeDetails {
  name: string;
  eligible: boolean;
  confidence: number;
  threshold: number;
}

export interface TopScheme {
  scheme: string;
  confidence: number;
  threshold: number;
}
