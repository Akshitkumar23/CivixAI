/**
 * Centralized form configuration for the eligibility checker.
 * This file consolidates all form-related constants, options, and schemas.
 */

import { z } from "zod";

// ── State/UT Options ────────────────────────────────────────────────────────
export const INDIAN_STATES = [
    'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh', 'Goa',
    'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka', 'Kerala',
    'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram', 'Nagaland',
    'Odisha', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 'Tripura',
    'Uttar Pradesh', 'Uttarakhand', 'West Bengal', 'Andaman and Nicobar Islands',
    'Chandigarh', 'Dadra and Nagar Haveli and Daman and Diu', 'Delhi', 'Jammu and Kashmir',
    'Ladakh', 'Lakshadweep', 'Puducherry'
] as const;

// ── Enum Options ─────────────────────────────────────────────────────────────
export const CASTE_OPTIONS = [
    { value: 'general', label: 'General' },
    { value: 'obc', label: 'OBC' },
    { value: 'sc', label: 'SC' },
    { value: 'st', label: 'ST' },
] as const;

export const OCCUPATION_OPTIONS = [
    { value: 'student', label: 'Student' },
    { value: 'employed', label: 'Employed' },
    { value: 'farmer', label: 'Farmer' },
    { value: 'unemployed', label: 'Unemployed' },
    { value: 'retired', label: 'Retired' },
] as const;

export const GENDER_OPTIONS = [
    { value: 'male', label: 'Male' },
    { value: 'female', label: 'Female' },
    { value: 'other', label: 'Other' },
] as const;

export const EDUCATION_OPTIONS = [
    { value: 'illiterate', label: 'Illiterate' },
    { value: 'primary', label: 'Primary (1-5)' },
    { value: 'secondary', label: 'Secondary (6-10)' },
    { value: 'higher_secondary', label: 'Higher Secondary (11-12)' },
    { value: 'graduate', label: 'Graduate' },
    { value: 'postgraduate', label: 'Post Graduate' },
    { value: 'phd', label: 'PhD' },
] as const;

export const DIGITAL_LITERACY_OPTIONS = [
    { value: 'none', label: 'None' },
    { value: 'basic', label: 'Basic (Can use phone)' },
    { value: 'intermediate', label: 'Intermediate (Can use apps)' },
    { value: 'advanced', label: 'Advanced (Can use computers)' },
] as const;

export const URBAN_RURAL_OPTIONS = [
    { value: 'urban', label: 'Urban (City)' },
    { value: 'rural', label: 'Rural (Village)' },
] as const;

export const MARITAL_STATUS_OPTIONS = [
    { value: 'single', label: 'Single' },
    { value: 'married', label: 'Married' },
    { value: 'widowed', label: 'Widowed' },
    { value: 'divorced', label: 'Divorced' },
] as const;

export const EMPLOYMENT_TYPE_OPTIONS = [
    { value: 'government', label: 'Government' },
    { value: 'private', label: 'Private' },
    { value: 'self_employed', label: 'Self Employed' },
    { value: 'daily_wage', label: 'Daily Wage' },
    { value: 'not_applicable', label: 'Not Applicable' },
] as const;

export const SKILL_CERTIFICATION_OPTIONS = [
    { value: 'none', label: 'None' },
    { value: 'it', label: 'IT Skills' },
    { value: 'technical', label: 'Technical Skills' },
    { value: 'agriculture', label: 'Agriculture Skills' },
    { value: 'handicraft', label: 'Handicraft Skills' },
    { value: 'other', label: 'Other Skills' },
] as const;

export const LOAN_REQUIREMENT_OPTIONS = [
    { value: 'none', label: 'None' },
    { value: 'education', label: 'Education Loan' },
    { value: 'business', label: 'Business Loan' },
    { value: 'housing', label: 'Housing Loan' },
    { value: 'agriculture', label: 'Agriculture Loan' },
    { value: 'emergency', label: 'Emergency Loan' },
] as const;

// ── Zod Schemas ──────────────────────────────────────────────────────────────
// Core inputs (always required)
export const coreSchema = z.object({
    age: z.coerce.number().min(1, 'Age is required').max(120, 'Enter a valid age'),
    annualIncome: z.coerce.number().min(0, 'Income must be a positive number'),
    state: z.string().min(1, 'State is required'),
    caste: z.enum(['general', 'obc', 'sc', 'st'], { required_error: 'Caste is required' }),
    occupation: z.enum(['student', 'employed', 'farmer', 'unemployed', 'retired'], { required_error: 'Occupation is required' }),
});

// Optional Level 1 inputs
export const optionalLevel1Schema = z.object({
    gender: z.enum(['male', 'female', 'other'], { required_error: 'Gender is required' }).optional(),
    hasLand: z.boolean().default(false),
    hasDisability: z.boolean().default(false),
    familyIncome: z.coerce.number().min(0, 'Family income must be a positive number').optional(),
    hasAvailedSimilarScheme: z.boolean().default(false),
});

// Modern intelligent inputs (Level 2)
export const modernLevel2Schema = z.object({
    landSize: z.coerce.number().min(0, 'Land size must be a positive number').optional(),
    familySize: z.coerce.number().min(1, 'Family size must be at least 1').optional(),
    isSingleGirlChild: z.boolean().default(false),
    isWidowOrSenior: z.boolean().default(false),
    isTaxPayer: z.boolean().default(false),
    isBankLinked: z.boolean().default(false),
    educationLevel: z.enum(['illiterate', 'primary', 'secondary', 'higher_secondary', 'graduate', 'postgraduate', 'phd']).optional(),
    digitalLiteracy: z.enum(['none', 'basic', 'intermediate', 'advanced']).optional(),
    urbanRural: z.enum(['urban', 'rural']).optional(),
    maritalStatus: z.enum(['single', 'married', 'widowed', 'divorced']).optional(),
    isBPL: z.boolean().default(false),
    isMinority: z.boolean().default(false),
    monthlyExpenses: z.coerce.number().min(0).optional(),
    hasSmartphone: z.boolean().default(false),
    hasInternet: z.boolean().default(false),
    employmentType: z.enum(['government', 'private', 'self_employed', 'daily_wage', 'not_applicable']).optional(),
    skillCertification: z.enum(['none', 'it', 'technical', 'agriculture', 'handicraft', 'other']).optional(),
    loanRequirement: z.enum(['none', 'education', 'business', 'housing', 'agriculture', 'emergency']).optional(),
    monthlySavings: z.coerce.number().min(0, 'Monthly savings must be a positive number').optional(),
    hasInsurance: z.boolean().default(false),
    hasPension: z.boolean().default(false),
    prioritySchemes: z.array(z.string()).optional(),
});

// Combined profile schema
export const profileSchema = coreSchema.merge(optionalLevel1Schema).merge(modernLevel2Schema);
export type ProfileFormValues = z.infer<typeof profileSchema>;

// ── Default Form Values ──────────────────────────────────────────────────────
export const DEFAULT_FORM_VALUES: Partial<ProfileFormValues> = {
    hasLand: false,
    hasDisability: false,
    hasAvailedSimilarScheme: false,
    isSingleGirlChild: false,
    isWidowOrSenior: false,
    isTaxPayer: false,
    isBankLinked: false,
    annualIncome: 0,
    age: undefined,
    familyIncome: 0,
    landSize: 0,
    familySize: 1,
    educationLevel: undefined,
    digitalLiteracy: undefined,
    urbanRural: undefined,
    maritalStatus: undefined,
    isBPL: false,
    isMinority: false,
    monthlyExpenses: 0,
    hasSmartphone: false,
    hasInternet: false,
    employmentType: undefined,
    skillCertification: undefined,
    loanRequirement: undefined,
    monthlySavings: 0,
    hasInsurance: false,
    hasPension: false,
    prioritySchemes: [],
};

// ── Demo Profiles ────────────────────────────────────────────────────────────
export interface DemoProfile {
    label: string;
    emoji: string;
    color: string;
    values: Partial<ProfileFormValues>;
}

export const DEMO_PROFILES: DemoProfile[] = [
    {
        label: '👩‍🎓 OBC Student',
        emoji: '🎓',
        color: 'from-blue-600/20 to-purple-600/20 border-blue-500/30',
        values: {
            age: 20,
            annualIncome: 80000,
            state: 'Uttar Pradesh',
            caste: 'obc',
            occupation: 'student',
            gender: 'female',
            educationLevel: 'graduate',
            isBankLinked: true,
            isBPL: true,
            hasLand: false,
            hasDisability: false,
            familyIncome: 120000,
            hasAvailedSimilarScheme: false,
            landSize: 0,
            familySize: 4,
            isSingleGirlChild: false,
            isWidowOrSenior: false,
            isTaxPayer: false,
            digitalLiteracy: 'advanced',
            urbanRural: 'urban',
            maritalStatus: 'single',
            isMinority: false,
            monthlyExpenses: 5000,
            hasSmartphone: true,
            hasInternet: true,
            employmentType: 'not_applicable',
            skillCertification: 'it',
            loanRequirement: 'education',
            monthlySavings: 1000,
            hasInsurance: false,
            hasPension: false,
        },
    },
    {
        label: '🚜 Marginal Farmer',
        emoji: '🌾',
        color: 'from-green-600/20 to-emerald-600/20 border-green-500/30',
        values: {
            age: 42,
            annualIncome: 60000,
            state: 'Bihar',
            caste: 'obc',
            occupation: 'farmer',
            gender: 'male',
            hasLand: true,
            landSize: 1.5,
            urbanRural: 'rural',
            educationLevel: 'primary',
            isBankLinked: true,
            isBPL: true,
            hasDisability: false,
            familyIncome: 60000,
            hasAvailedSimilarScheme: false,
            familySize: 6,
            isSingleGirlChild: false,
            isWidowOrSenior: false,
            isTaxPayer: false,
            digitalLiteracy: 'basic',
            maritalStatus: 'married',
            isMinority: false,
            monthlyExpenses: 4500,
            hasSmartphone: true,
            hasInternet: true,
            employmentType: 'self_employed',
            skillCertification: 'agriculture',
            loanRequirement: 'agriculture',
            monthlySavings: 500,
            hasInsurance: true,
            hasPension: false,
        },
    },
    {
        label: '👩‍💼 Woman Entrepreneur',
        emoji: '💼',
        color: 'from-pink-600/20 to-rose-600/20 border-pink-500/30',
        values: {
            age: 32,
            annualIncome: 250000,
            state: 'Maharashtra',
            caste: 'general',
            occupation: 'employed',
            gender: 'female',
            employmentType: 'self_employed',
            loanRequirement: 'business',
            educationLevel: 'postgraduate',
            isBankLinked: true,
            isBPL: false,
            hasLand: false,
            landSize: 0,
            hasDisability: false,
            familyIncome: 450000,
            hasAvailedSimilarScheme: false,
            familySize: 3,
            isSingleGirlChild: false,
            isWidowOrSenior: false,
            isTaxPayer: true,
            digitalLiteracy: 'advanced',
            urbanRural: 'urban',
            maritalStatus: 'married',
            isMinority: false,
            monthlyExpenses: 15000,
            hasSmartphone: true,
            hasInternet: true,
            skillCertification: 'technical',
            monthlySavings: 8000,
            hasInsurance: true,
            hasPension: true,
        },
    },
];

// ── Form Step Configuration ──────────────────────────────────────────────────
export const FORM_STEPS = {
    STEP_1: {
        title: 'Basic Core Profile',
        description: 'Step 1 of 2: Required for basic eligibility matching.',
        progressWidth: '50%',
    },
    STEP_2: {
        title: 'Personalized Details',
        description: (occupation: string) => `Step 2 of 2: Optional details for ${occupation}s to improve match accuracy.`,
        progressWidth: '100%',
    },
};

// ── Local Storage Keys ───────────────────────────────────────────────────────
export const STORAGE_KEYS = {
    USER_PROFILE: 'civix_user_profile',
};