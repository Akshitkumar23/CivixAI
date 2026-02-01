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
