'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { zodResolver } from '@hookform/resolvers/zod';
import { useForm, type SubmitHandler } from 'react-hook-form';
import { z } from 'zod';
import { ArrowRight, User, Hand, IndianRupee, Briefcase, GraduationCap, Accessibility, Users, CheckCircle, XCircle, Plus, ChevronDown, ChevronUp, Sparkles, Zap, Shield, Landmark } from 'lucide-react';
import { type UserProfile } from '@/lib/types';
import { Header } from '@/components/Header';
import { useScrollRestoration } from '@/hooks/use-scroll-restoration';
import { ThreeDBackground } from '@/components/canvas/ThreeDBackground';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { useToast } from '@/hooks/use-toast';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import Chatbot from '@/components/Chatbot';

// Define the API Response Type
interface EligibleSchemeDetails {
  id?: string;
  name: string;
  eligible: boolean;
  confidence: number;
  threshold: number;
  description?: string;
  ministry?: string;
  category?: string;
  benefit_type?: string;
}

interface EligibilityResponse {
  success: boolean;
  schemeDetails?: EligibleSchemeDetails[];
  eligibleSchemes?: string[];
  error?: string;
  mlPrediction?: boolean;
}

const states = [
  'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh', 'Goa',
  'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka', 'Kerala',
  'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram', 'Nagaland',
  'Odisha', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 'Tripura',
  'Uttar Pradesh', 'Uttarakhand', 'West Bengal', 'Andaman and Nicobar Islands',
  'Chandigarh', 'Dadra and Nagar Haveli and Daman and Diu', 'Delhi', 'Jammu and Kashmir',
  'Ladakh', 'Lakshadweep', 'Puducherry'
];

// Core inputs (always required)
const coreSchema = z.object({
  age: z.coerce.number().min(1, 'Age is required').max(120, 'Enter a valid age'),
  annualIncome: z.coerce.number().min(0, 'Income must be a positive number'),
  state: z.string().min(1, 'State is required'),
  caste: z.enum(['general', 'obc', 'sc', 'st'], { required_error: 'Caste is required' }),
  occupation: z.enum(['student', 'employed', 'farmer', 'unemployed', 'retired'], { required_error: 'Occupation is required' }),
});

// Optional Level 1 inputs
const optionalLevel1Schema = z.object({
  gender: z.enum(['male', 'female', 'other'], { required_error: 'Gender is required' }).optional(),
  hasLand: z.boolean().default(false),
  hasDisability: z.boolean().default(false),
  familyIncome: z.coerce.number().min(0, 'Family income must be a positive number').optional(),
  hasAvailedSimilarScheme: z.boolean().default(false),
});

// Modern intelligent inputs (Level 2)
const modernLevel2Schema = z.object({
  landSize: z.coerce.number().min(0, 'Land size must be a positive number').optional(),
  familySize: z.coerce.number().min(1, 'Family size must be at least 1').optional(),
  isSingleGirlChild: z.boolean().default(false),
  isWidowOrSenior: z.boolean().default(false),
  isTaxPayer: z.boolean().default(false),
  isBankLinked: z.boolean().default(false),
  educationLevel: z.enum(['illiterate', 'primary', 'secondary', 'higher_secondary', 'graduate', 'postgraduate', 'phd'], { required_error: 'Education level is required' }).optional(),
  digitalLiteracy: z.enum(['none', 'basic', 'intermediate', 'advanced'], { required_error: 'Digital literacy is required' }).optional(),
  urbanRural: z.enum(['urban', 'rural'], { required_error: 'Location type is required' }).optional(),
  maritalStatus: z.enum(['single', 'married', 'widowed', 'divorced'], { required_error: 'Marital status is required' }).optional(),
  isBPL: z.boolean().default(false),
  isMinority: z.boolean().default(false),
  monthlyExpenses: z.coerce.number().min(0, 'Monthly expenses must be a positive number').optional(),
  hasSmartphone: z.boolean().default(false),
  hasInternet: z.boolean().default(false),
  employmentType: z.enum(['government', 'private', 'self_employed', 'daily_wage', 'not_applicable'], { required_error: 'Employment type is required' }).optional(),
  skillCertification: z.enum(['none', 'it', 'technical', 'agriculture', 'handicraft', 'other'], { required_error: 'Skill certification is required' }).optional(),
  loanRequirement: z.enum(['none', 'education', 'business', 'housing', 'agriculture', 'emergency'], { required_error: 'Loan requirement is required' }).optional(),
  monthlySavings: z.coerce.number().min(0, 'Monthly savings must be a positive number').optional(),
  hasInsurance: z.boolean().default(false),
  hasPension: z.boolean().default(false),
  prioritySchemes: z.array(z.string()).optional(),
});

const profileSchema = coreSchema.merge(optionalLevel1Schema).merge(modernLevel2Schema);

type ProfileFormValues = z.infer<typeof profileSchema>;

function CheckEligibilityContent() {
  const router = useRouter();
  const { toast } = useToast();
  // Save and restore scroll position when navigating back
  useScrollRestoration();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [eligibleSchemes, setEligibleSchemes] = useState<string[]>([]);
  const [rawSchemeData, setRawSchemeData] = useState<EligibleSchemeDetails[]>([]);
  const [hasSubmitted, setHasSubmitted] = useState(false);
  const [step, setStep] = useState(1); // Multi-step form
  const [initialResults, setInitialResults] = useState<string[]>([]);

  const form = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
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
      // Modern intelligent fields defaults
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
    },
  });

  // ── Feature 1: LocalStorage Persistence ────────────────────────────────
  // Load saved data on mount
  useEffect(() => {
    const savedData = localStorage.getItem('civix_user_profile');
    if (savedData) {
      try {
        const parsed = JSON.parse(savedData);
        // We only restore values that are non-empty to avoid breaking the form
        Object.entries(parsed).forEach(([key, value]) => {
          if (value !== undefined && value !== null && value !== '') {
            form.setValue(key as any, value as any);
          }
        });
        // No toast notification for profile restoration to keep UI clean
      } catch (e) {
        console.error("Failed to parse saved profile", e);
      }
    }
  }, [form, toast]);

  // Save data on change
  const formValues = form.watch();
  useEffect(() => {
    const timeout = setTimeout(() => {
      localStorage.setItem('civix_user_profile', JSON.stringify(formValues));
    }, 1000); // Debounce save
    return () => clearTimeout(timeout);
  }, [formValues]);

  const clearProfile = () => {
    localStorage.removeItem('civix_user_profile');
    form.reset({
      age: undefined,
      annualIncome: 0,
      state: '',
      caste: undefined,
      occupation: undefined,
    });
    // Profile cleared silently
  };

  // Get current occupation value for conditional logic
  const currentOccupation = form.watch('occupation');
  const hasLand = form.watch('hasLand');
  const currentAge = form.watch('age');

  const onSubmit: SubmitHandler<ProfileFormValues> = async (data) => {
    setIsSubmitting(true);
    try {
      // Convert form data to API format (match InputAgent field names exactly)
      const apiData = {
        age:           data.age!,
        annualIncome:  data.annualIncome || 0,   // was 'income' — FIXED
        state:         data.state,
        caste:         data.caste,               // was 'category' — FIXED
        occupation:    data.occupation,
        gender:        data.gender || 'other',
        hasDisability: data.hasDisability,
        hasLand:       data.hasLand,
        familyIncome:  data.familyIncome || 0,
        hasAvailedSimilarScheme: data.hasAvailedSimilarScheme,
        landSize:      data.landSize,
        familySize:    data.familySize,
        isSingleGirlChild: data.isSingleGirlChild,
        isWidowOrSenior:   data.isWidowOrSenior,
        isTaxPayer:        data.isTaxPayer,
        isBankLinked:      data.isBankLinked,
        // Modern intelligent fields
        educationLevel:    data.educationLevel,
        digitalLiteracy:   data.digitalLiteracy,
        urbanRural:        data.urbanRural,
        maritalStatus:     data.maritalStatus,   // NEW — was missing
        isBPL:             data.isBPL,
        isMinority:        data.isMinority,
        monthlyExpenses:   data.monthlyExpenses || 0,
        hasSmartphone:     data.hasSmartphone,
        hasInternet:       data.hasInternet,
        employmentType:    data.employmentType,
        skillCertification:data.skillCertification,
        loanRequirement:   data.loanRequirement,
        monthlySavings:    data.monthlySavings || 0,
        hasInsurance:      data.hasInsurance,
        hasPension:        data.hasPension,
        prioritySchemes:   data.prioritySchemes,
      };


      // Call the ML-ready API (Full 5-stage pipeline)
      const response = await fetch('/api/recommend', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(apiData),
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || `API Error: ${response.status}`);
      }

      const result = await response.json();

      // Handle both ML and rule-based responses
      let schemes: string[] = [];

      if (result.eligibleSchemes && Array.isArray(result.eligibleSchemes)) {
        schemes = result.eligibleSchemes;
      } else if (result.schemeDetails && Array.isArray(result.schemeDetails)) {
        schemes = result.schemeDetails.map((s: { name?: string; id?: string }) => s.name || s.id || 'Unknown Scheme');
      } else if (result.topSchemes && Array.isArray(result.topSchemes)) {
        schemes = result.topSchemes.map((s: { scheme: string }) => s.scheme);
      } else if (result.eligible_schemes && Array.isArray(result.eligible_schemes)) {
        schemes = result.eligible_schemes.map((s: { scheme_name?: string; scheme_id?: string }) => s.scheme_name || s.scheme_id || 'Unknown Scheme');
      }

      if (result.success === false && schemes.length === 0) {
        throw new Error(result.error || 'Failed to get predictions');
      }

      setEligibleSchemes(schemes);
      if (result.schemeDetails) {
        setRawSchemeData(result.schemeDetails);
      }
      setHasSubmitted(true);

      // Store the exact result schemas to pass forward to the next screen if needed
      setInitialResults(schemes);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Could not process your request. Please try again.';
      toast({
        variant: 'destructive',
        title: 'An error occurred',
        description: message,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // ── Feature 13: Demo Mode profiles ────────────────────────────────────────
  const demoProfiles = [
    {
      label: '👩‍🎓 SC Student',
      emoji: '🎓',
      color: 'from-blue-600/20 to-purple-600/20 border-blue-500/30',
      values: { age: 20, annualIncome: 80000, state: 'Uttar Pradesh', caste: 'sc' as const, occupation: 'student' as const, gender: 'female' as const, educationLevel: 'graduate' as const, isBankLinked: true, isBPL: true },
    },
    {
      label: '🚜 Marginal Farmer',
      emoji: '🌾',
      color: 'from-green-600/20 to-emerald-600/20 border-green-500/30',
      values: { age: 42, annualIncome: 60000, state: 'Bihar', caste: 'obc' as const, occupation: 'farmer' as const, gender: 'male' as const, hasLand: true, landSize: 1.5, urbanRural: 'rural' as const },
    },
    {
      label: '👩‍💼 Woman Entrepreneur',
      emoji: '💼',
      color: 'from-pink-600/20 to-rose-600/20 border-pink-500/30',
      values: { age: 32, annualIncome: 250000, state: 'Maharashtra', caste: 'general' as const, occupation: 'employed' as const, gender: 'female' as const, employmentType: 'self_employed' as const, loanRequirement: 'business' as const },
    },
  ];

  const applyDemoProfile = (profile: typeof demoProfiles[0]) => {
    // Use setValue for each field individually so controlled Select dropdowns update
    const opts = { shouldValidate: true, shouldDirty: true, shouldTouch: true };
    Object.entries(profile.values).forEach(([key, value]) => {
      form.setValue(key as keyof ProfileFormValues, value as any, opts);
    });
    setStep(1);
    // Scroll form into view
    window.scrollTo({ top: 200, behavior: 'smooth' });
  };

  return (
    <div className="flex flex-col min-h-screen bg-transparent relative selection:bg-purple-500/30 text-slate-200 font-sans">
      <ThreeDBackground />
      <Header />
      <main className="flex-grow container mx-auto px-4 py-8 max-w-4xl relative z-10">
        <Card className="w-full bg-black/40 backdrop-blur-2xl border-white/10 shadow-[0_8px_32px_0_rgba(0,0,0,0.36)] rounded-[2.5rem] overflow-hidden">
          {!hasSubmitted ? (
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
                <CardHeader className="text-center pt-10 pb-4 border-b border-white/5 bg-white/[0.02] relative">
                  <div className="absolute top-0 left-0 w-full h-1 bg-white/5">
                    <div className="h-full bg-gradient-to-r from-blue-400 to-purple-500 transition-all duration-500" style={{ width: step === 1 ? '50%' : '100%' }} />
                  </div>
                  <CardTitle className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-blue-300 via-purple-300 to-indigo-300">
                    {step === 1 ? 'Basic Core Profile' : 'Personalized Details'}
                  </CardTitle>
                  <CardDescription className="text-slate-400">
                    {step === 1 
                      ? 'Step 1 of 2: Required for basic eligibility matching.' 
                      : `Step 2 of 2: Optional details for ${currentOccupation}s to improve match accuracy.`}
                  </CardDescription>
                  {form.formState.isDirty && (
                    <button 
                      type="button" 
                      onClick={clearProfile}
                      className="absolute bottom-4 right-8 text-[10px] uppercase tracking-widest text-slate-500 hover:text-red-400 transition-colors"
                    >
                      Reset Form ↺
                    </button>
                  )}
                </CardHeader>
                {/* Feature 13: Demo Mode Bar */}
                {step === 1 && (
                  <div className="px-8 pt-4 pb-2">
                    <div className="flex items-center gap-3 mb-3">
                      <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">⚡ Try a Demo Profile</span>
                      <div className="flex-1 h-px bg-white/5" />
                    </div>
                    <div className="grid grid-cols-3 gap-3">
                      {demoProfiles.map((profile) => (
                        <button
                          key={profile.label}
                          type="button"
                          onClick={() => applyDemoProfile(profile)}
                          className={`flex flex-col items-center gap-2 p-3 rounded-2xl border bg-gradient-to-br ${profile.color} hover:scale-[1.03] active:scale-100 transition-all duration-200 group`}
                        >
                          <span className="text-2xl group-hover:scale-110 transition-transform">{profile.emoji}</span>
                          <span className="text-[11px] font-bold text-slate-300 text-center leading-tight">{profile.label}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                <CardContent className="space-y-8 p-8 max-h-[60vh] overflow-y-auto custom-scrollbar">
                  <div className={step === 1 ? "block animate-in fade-in slide-in-from-left-4 duration-500" : "hidden"}>
                  {/* CORE INPUTS - Always visible and required */}
                  <div className="space-y-4">
                    <div className="flex items-center gap-3 border-b border-white/10 pb-3 mb-6">
                      <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center border border-blue-500/30">
                        <User className="h-4 w-4 text-blue-400" />
                      </div>
                      <h3 className="font-bold tracking-tight text-white text-xl">Core Identity Parameters</h3>
                    </div>
                    <p className="text-sm text-muted-foreground">Required fields to check your basic eligibility</p>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <FormField
                        control={form.control}
                        name="age"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Age</FormLabel>
                            <FormControl>
                              <Input type="number" placeholder="Enter your age" {...field} value={field.value ?? ''} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      <FormField
                        control={form.control}
                        name="annualIncome"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Annual Income (₹)</FormLabel>
                            <FormControl>
                              <div className="relative">
                                <IndianRupee className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                <Input type="number" placeholder="e.g., 250000" {...field} className="pl-8" />
                              </div>
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <FormField
                        control={form.control}
                        name="state"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>State/Union Territory</FormLabel>
                            <Select onValueChange={field.onChange} value={field.value}>
                              <FormControl>
                                <SelectTrigger>
                                  <SelectValue placeholder="Select your state" />
                                </SelectTrigger>
                              </FormControl>
                              <SelectContent>
                                {states.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}
                              </SelectContent>
                            </Select>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      <FormField
                        control={form.control}
                        name="caste"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Caste Category</FormLabel>
                            <Select onValueChange={field.onChange} value={field.value}>
                              <FormControl>
                                <SelectTrigger>
                                  <SelectValue placeholder="Select category" />
                                </SelectTrigger>
                              </FormControl>
                              <SelectContent>
                                <SelectItem value="general">General</SelectItem>
                                <SelectItem value="obc">OBC</SelectItem>
                                <SelectItem value="sc">SC</SelectItem>
                                <SelectItem value="st">ST</SelectItem>
                              </SelectContent>
                            </Select>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                    </div>

                    <FormField
                      control={form.control}
                      name="occupation"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Occupation</FormLabel>
                          <Select onValueChange={field.onChange} value={field.value}>
                            <FormControl>
                              <SelectTrigger>
                                <SelectValue placeholder="Select your occupation" />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              <SelectItem value="student">Student</SelectItem>
                              <SelectItem value="employed">Employed</SelectItem>
                              <SelectItem value="farmer">Farmer</SelectItem>
                              <SelectItem value="unemployed">Unemployed</SelectItem>
                              <SelectItem value="retired">Retired</SelectItem>
                            </SelectContent>
                          </Select>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                  </div>

                  <div className={step === 2 ? "block animate-in fade-in slide-in-from-right-4 duration-500" : "hidden"}>
                  {/* INTELLIGENT FOLLOW-UP QUESTIONS */}
                  <div className="space-y-4">
                      <div className="space-y-4 pt-4">
                        <div className="flex items-center gap-2">
                          <Users className="h-5 w-5 text-primary" />
                          <h3 className="font-semibold text-lg">Additional Questions</h3>
                        </div>
                        <p className="text-sm text-muted-foreground">Based on your profile, we need some additional information to find the best schemes for you</p>

                        {/* Smart follow-up based on occupation */}
                        {currentOccupation === 'student' && (
                          <div className="space-y-4">
                            <FormField
                              control={form.control}
                              name="educationLevel"
                              render={({ field }) => (
                                <FormItem>
                                  <FormLabel>Current Education Level</FormLabel>
                                  <Select onValueChange={field.onChange} value={field.value}>
                                    <FormControl>
                                      <SelectTrigger>
                                        <SelectValue placeholder="Select education level" />
                                      </SelectTrigger>
                                    </FormControl>
                                    <SelectContent>
                                      <SelectItem value="illiterate">Illiterate</SelectItem>
                                      <SelectItem value="primary">Primary (1-5)</SelectItem>
                                      <SelectItem value="secondary">Secondary (6-10)</SelectItem>
                                      <SelectItem value="higher_secondary">Higher Secondary (11-12)</SelectItem>
                                      <SelectItem value="graduate">Graduate</SelectItem>
                                      <SelectItem value="postgraduate">Post Graduate</SelectItem>
                                      <SelectItem value="phd">PhD</SelectItem>
                                    </SelectContent>
                                  </Select>
                                  <FormDescription>Required for education schemes</FormDescription>
                                  <FormMessage />
                                </FormItem>
                              )}
                            />
                            <FormField
                              control={form.control}
                              name="loanRequirement"
                              render={({ field }) => (
                                <FormItem>
                                  <FormLabel>Education Loan Required</FormLabel>
                                  <Select onValueChange={field.onChange} value={field.value}>
                                    <FormControl>
                                      <SelectTrigger>
                                        <SelectValue placeholder="Select loan requirement" />
                                      </SelectTrigger>
                                    </FormControl>
                                    <SelectContent>
                                      <SelectItem value="none">No Loan Required</SelectItem>
                                      <SelectItem value="education">Education Loan</SelectItem>
                                      <SelectItem value="business">Business Loan</SelectItem>
                                      <SelectItem value="housing">Housing Loan</SelectItem>
                                      <SelectItem value="agriculture">Agriculture Loan</SelectItem>
                                      <SelectItem value="emergency">Emergency Loan</SelectItem>
                                    </SelectContent>
                                  </Select>
                                  <FormDescription>Required for education assistance</FormDescription>
                                  <FormMessage />
                                </FormItem>
                              )}
                            />
                          </div>
                        )}

                        {/* Smart follow-up based on land ownership */}
                        {hasLand && (
                          <FormField
                            control={form.control}
                            name="landSize"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel>Land size (in acres)</FormLabel>
                                <FormControl>
                                  <Input type="number" placeholder="e.g., 2.5" {...field} />
                                </FormControl>
                                <FormDescription>Required for agriculture schemes</FormDescription>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                        )}

                        {/* Smart follow-up based on income level */}
                        {form.watch('annualIncome') > 500000 && (
                          <FormField
                            control={form.control}
                            name="isTaxPayer"
                            render={({ field }) => (
                              <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                                <div className="space-y-0.5">
                                  <FormLabel className="text-base">Income tax payer</FormLabel>
                                  <FormDescription>Do you pay income tax?</FormDescription>
                                </div>
                                <FormControl>
                                  <Switch
                                    checked={field.value}
                                    onCheckedChange={field.onChange}
                                  />
                                </FormControl>
                              </FormItem>
                            )}
                          />
                        )}

                        {/* Smart follow-up based on age and occupation */}
                        {(currentAge >= 60 || currentOccupation === 'retired') && (
                          <FormField
                            control={form.control}
                            name="isWidowOrSenior"
                            render={({ field }) => (
                              <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                                <div className="space-y-0.5">
                                  <FormLabel className="text-base">Senior citizen</FormLabel>
                                  <FormDescription>Are you a senior citizen (60+)?</FormDescription>
                                </div>
                                <FormControl>
                                  <Switch
                                    checked={field.value}
                                    onCheckedChange={field.onChange}
                                  />
                                </FormControl>
                              </FormItem>
                            )}
                          />
                        )}

                        {/* Smart follow-up based on tech/location */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <FormField
                            control={form.control}
                            name="urbanRural"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel>Location Habitat</FormLabel>
                                <Select onValueChange={field.onChange} value={field.value}>
                                  <FormControl>
                                    <SelectTrigger><SelectValue placeholder="Select habitat" /></SelectTrigger>
                                  </FormControl>
                                  <SelectContent>
                                    <SelectItem value="urban">Urban (City)</SelectItem>
                                    <SelectItem value="rural">Rural (Village)</SelectItem>
                                  </SelectContent>
                                </Select>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                          <FormField
                            control={form.control}
                            name="maritalStatus"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel>Marital Status</FormLabel>
                                <Select onValueChange={field.onChange} value={field.value}>
                                  <FormControl>
                                    <SelectTrigger><SelectValue placeholder="Select status" /></SelectTrigger>
                                  </FormControl>
                                  <SelectContent>
                                    <SelectItem value="single">Single</SelectItem>
                                    <SelectItem value="married">Married</SelectItem>
                                    <SelectItem value="widowed">Widowed</SelectItem>
                                    <SelectItem value="divorced">Divorced</SelectItem>
                                  </SelectContent>
                                </Select>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <FormField
                            control={form.control}
                            name="isBPL"
                            render={({ field }) => (
                              <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4 bg-white/5">
                                <div className="space-y-0.5">
                                  <FormLabel className="text-base">BPL Card Holder</FormLabel>
                                  <FormDescription>Do you have a BPL card?</FormDescription>
                                </div>
                                <FormControl>
                                  <Switch checked={field.value} onCheckedChange={field.onChange} />
                                </FormControl>
                              </FormItem>
                            )}
                          />
                          <FormField
                            control={form.control}
                            name="isMinority"
                            render={({ field }) => (
                              <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4 bg-white/5">
                                <div className="space-y-0.5">
                                  <FormLabel className="text-base">Minority Community</FormLabel>
                                  <FormDescription>Part of a minority community?</FormDescription>
                                </div>
                                <FormControl>
                                  <Switch checked={field.value} onCheckedChange={field.onChange} />
                                </FormControl>
                              </FormItem>
                            )}
                          />
                        </div>

                        {/* Smart follow-up based on technology access */}
                        {(form.watch('hasSmartphone') || form.watch('hasInternet')) && (
                          <FormField
                            control={form.control}
                            name="digitalLiteracy"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel>Digital Literacy Level</FormLabel>
                                <Select onValueChange={field.onChange} value={field.value}>
                                  <FormControl>
                                    <SelectTrigger>
                                      <SelectValue placeholder="Select digital literacy" />
                                    </SelectTrigger>
                                  </FormControl>
                                  <SelectContent>
                                    <SelectItem value="none">None</SelectItem>
                                    <SelectItem value="basic">Basic (Can use phone)</SelectItem>
                                    <SelectItem value="intermediate">Intermediate (Can use apps)</SelectItem>
                                    <SelectItem value="advanced">Advanced (Can use computers)</SelectItem>
                                  </SelectContent>
                                </Select>
                                <FormDescription>Required for digital India schemes</FormDescription>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                        )}

                        {/* Smart follow-up based on loan requirement */}
                        {form.watch('loanRequirement') !== 'none' && form.watch('loanRequirement') !== undefined && (
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <FormField
                              control={form.control}
                              name="monthlyExpenses"
                              render={({ field }) => (
                                <FormItem>
                                  <FormLabel>Monthly Expenses (₹)</FormLabel>
                                  <FormControl>
                                    <div className="relative">
                                      <IndianRupee className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                      <Input type="number" placeholder="e.g., 15000" {...field} className="pl-8" />
                                    </div>
                                  </FormControl>
                                  <FormDescription>Required for loan eligibility</FormDescription>
                                  <FormMessage />
                                </FormItem>
                              )}
                            />
                            <FormField
                              control={form.control}
                              name="monthlySavings"
                              render={({ field }) => (
                                <FormItem>
                                  <FormLabel>Monthly Savings (₹)</FormLabel>
                                  <FormControl>
                                    <div className="relative">
                                      <IndianRupee className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                      <Input type="number" placeholder="e.g., 5000" {...field} className="pl-8" />
                                    </div>
                                  </FormControl>
                                  <FormDescription>Required for loan eligibility</FormDescription>
                                  <FormMessage />
                                </FormItem>
                              )}
                            />
                          </div>
                        )}
                      </div>
                  </div>

                  {/* OPTIONAL LEVEL 1 */}
                  <div className="space-y-4">
                      <div className="space-y-4 border-t pt-4">
                        <div className="flex items-center gap-2">
                          <Hand className="h-5 w-5 text-primary" />
                          <h3 className="font-semibold text-lg">Additional Information</h3>
                        </div>
                        <p className="text-sm text-muted-foreground">Optional fields that help improve eligibility accuracy</p>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <FormField
                            control={form.control}
                            name="gender"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel>Gender</FormLabel>
                                <Select onValueChange={field.onChange} value={field.value}>
                                  <FormControl>
                                    <SelectTrigger>
                                      <SelectValue placeholder="Select gender" />
                                    </SelectTrigger>
                                  </FormControl>
                                  <SelectContent>
                                    <SelectItem value="male">Male</SelectItem>
                                    <SelectItem value="female">Female</SelectItem>
                                    <SelectItem value="other">Other</SelectItem>
                                  </SelectContent>
                                </Select>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                          <FormField
                            control={form.control}
                            name="familyIncome"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel>Family Income (₹)</FormLabel>
                                <FormControl>
                                  <div className="relative">
                                    <IndianRupee className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                    <Input type="number" placeholder="e.g., 400000" {...field} className="pl-8" />
                                  </div>
                                </FormControl>
                                <FormDescription>Optional: Total family income</FormDescription>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <FormField
                            control={form.control}
                            name="hasLand"
                            render={({ field }) => (
                              <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                                <div className="space-y-0.5">
                                  <FormLabel className="text-base">Land ownership</FormLabel>
                                  <FormDescription>Do you own agricultural land?</FormDescription>
                                </div>
                                <FormControl>
                                  <Switch
                                    checked={field.value}
                                    onCheckedChange={field.onChange}
                                  />
                                </FormControl>
                              </FormItem>
                            )}
                          />
                          <FormField
                            control={form.control}
                            name="hasDisability"
                            render={({ field }) => (
                              <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                                <div className="space-y-0.5">
                                  <FormLabel className="text-base">Disability status</FormLabel>
                                  <FormDescription>Do you have any disability?</FormDescription>
                                </div>
                                <FormControl>
                                  <Switch
                                    checked={field.value}
                                    onCheckedChange={field.onChange}
                                  />
                                </FormControl>
                              </FormItem>
                            )}
                          />
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <FormField
                            control={form.control}
                            name="hasAvailedSimilarScheme"
                            render={({ field }) => (
                              <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                                <div className="space-y-0.5">
                                  <FormLabel className="text-base">Previous scheme</FormLabel>
                                  <FormDescription>Have you availed similar scheme before?</FormDescription>
                                </div>
                                <FormControl>
                                  <Switch
                                    checked={field.value}
                                    onCheckedChange={field.onChange}
                                  />
                                </FormControl>
                              </FormItem>
                            )}
                          />
                        </div>
                      </div>
                  </div>

                  {/* OPTIONAL LEVEL 2 */}
                  <div className="space-y-4 border-t pt-4 mt-8">
                      <div className="space-y-4">
                        <div className="flex items-center gap-2">
                          <Users className="h-5 w-5 text-primary" />
                          <h3 className="font-semibold text-lg">Advanced Details</h3>
                        </div>
                        <p className="text-sm text-muted-foreground">Additional information for more precise eligibility matching</p>

                        {form.watch('hasLand') && (
                          <FormField
                            control={form.control}
                            name="landSize"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel>Land size (in acres)</FormLabel>
                                <FormControl>
                                  <Input type="number" placeholder="e.g., 2.5" {...field} />
                                </FormControl>
                                <FormDescription>Required if you own land</FormDescription>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                        )}

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <FormField
                            control={form.control}
                            name="familySize"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel>Family size</FormLabel>
                                <FormControl>
                                  <Input type="number" placeholder="e.g., 4" {...field} />
                                </FormControl>
                                <FormDescription>Number of family members</FormDescription>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                          {/* Smart logic: Single girl child only relevant for certain occupations */}
                          {currentOccupation !== 'student' && (
                            <FormField
                              control={form.control}
                              name="isSingleGirlChild"
                              render={({ field }) => (
                                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                                  <div className="space-y-0.5">
                                    <FormLabel className="text-base">Single girl child</FormLabel>
                                    <FormDescription>Are you a single girl child in family?</FormDescription>
                                  </div>
                                  <FormControl>
                                    <Switch
                                      checked={field.value}
                                      onCheckedChange={field.onChange}
                                    />
                                  </FormControl>
                                </FormItem>
                              )}
                            />
                          )}
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {/* Smart logic: Widow/Senior citizen only relevant for certain occupations */}
                          {currentOccupation !== 'student' && (
                            <FormField
                              control={form.control}
                              name="isWidowOrSenior"
                              render={({ field }) => (
                                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                                  <div className="space-y-0.5">
                                    <FormLabel className="text-base">Widow/Senior citizen</FormLabel>
                                    <FormDescription>Are you a widow or senior citizen (60+)?</FormDescription>
                                  </div>
                                  <FormControl>
                                    <Switch
                                      checked={field.value}
                                      onCheckedChange={field.onChange}
                                    />
                                  </FormControl>
                                </FormItem>
                              )}
                            />
                          )}
                          {/* Smart logic: Income tax payer only relevant for employed/retired */}
                          {(currentOccupation === 'employed' || currentOccupation === 'retired') && (
                            <FormField
                              control={form.control}
                              name="isTaxPayer"
                              render={({ field }) => (
                                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                                  <div className="space-y-0.5">
                                    <FormLabel className="text-base">Income tax payer</FormLabel>
                                    <FormDescription>Do you pay income tax?</FormDescription>
                                  </div>
                                  <FormControl>
                                    <Switch
                                      checked={field.value}
                                      onCheckedChange={field.onChange}
                                    />
                                  </FormControl>
                                </FormItem>
                              )}
                            />
                          )}
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <FormField
                            control={form.control}
                            name="isBankLinked"
                            render={({ field }) => (
                              <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                                <div className="space-y-0.5">
                                  <FormLabel className="text-base">Bank/DBT linked</FormLabel>
                                  <FormDescription>
                                    {currentOccupation === 'student'
                                      ? 'Is your bank account linked for scholarships/stipends?'
                                      : 'Is your bank account linked for DBT?'
                                    }
                                  </FormDescription>
                                </div>
                                <FormControl>
                                  <Switch
                                    checked={field.value}
                                    onCheckedChange={field.onChange}
                                  />
                                </FormControl>
                              </FormItem>
                            )}
                          />
                        </div>

                        {/* MODERN INTELLIGENT FIELDS - Smart Logic Section */}
                        <div className="space-y-4">
                          <div className="flex items-center gap-2">
                            <GraduationCap className="h-5 w-5 text-primary" />
                            <h3 className="font-semibold text-lg">Modern Intelligence</h3>
                          </div>
                          <p className="text-sm text-muted-foreground">Smart fields that adapt based on your profile</p>

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <FormField
                              control={form.control}
                              name="educationLevel"
                              render={({ field }) => (
                                <FormItem>
                                  <FormLabel>Education Level</FormLabel>
                                  <Select onValueChange={field.onChange} value={field.value}>
                                    <FormControl>
                                      <SelectTrigger>
                                        <SelectValue placeholder="Select education level" />
                                      </SelectTrigger>
                                    </FormControl>
                                    <SelectContent>
                                      <SelectItem value="illiterate">Illiterate</SelectItem>
                                      <SelectItem value="primary">Primary (1-5)</SelectItem>
                                      <SelectItem value="secondary">Secondary (6-10)</SelectItem>
                                      <SelectItem value="higher_secondary">Higher Secondary (11-12)</SelectItem>
                                      <SelectItem value="graduate">Graduate</SelectItem>
                                      <SelectItem value="postgraduate">Post Graduate</SelectItem>
                                      <SelectItem value="phd">PhD</SelectItem>
                                    </SelectContent>
                                  </Select>
                                  <FormDescription>Required for education-based schemes</FormDescription>
                                  <FormMessage />
                                </FormItem>
                              )}
                            />
                            <FormField
                              control={form.control}
                              name="urbanRural"
                              render={({ field }) => (
                                <FormItem>
                                  <FormLabel>Location Type</FormLabel>
                                  <Select onValueChange={field.onChange} value={field.value}>
                                    <FormControl>
                                      <SelectTrigger>
                                        <SelectValue placeholder="Select location" />
                                      </SelectTrigger>
                                    </FormControl>
                                    <SelectContent>
                                      <SelectItem value="urban">Urban</SelectItem>
                                      <SelectItem value="rural">Rural</SelectItem>
                                    </SelectContent>
                                  </Select>
                                  <FormDescription>Required for location-specific schemes</FormDescription>
                                  <FormMessage />
                                </FormItem>
                              )}
                            />
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <FormField
                              control={form.control}
                              name="digitalLiteracy"
                              render={({ field }) => (
                                <FormItem>
                                  <FormLabel>Digital Literacy</FormLabel>
                                  <Select onValueChange={field.onChange} value={field.value}>
                                    <FormControl>
                                      <SelectTrigger>
                                        <SelectValue placeholder="Select digital literacy" />
                                      </SelectTrigger>
                                    </FormControl>
                                    <SelectContent>
                                      <SelectItem value="none">None</SelectItem>
                                      <SelectItem value="basic">Basic (Can use phone)</SelectItem>
                                      <SelectItem value="intermediate">Intermediate (Can use apps)</SelectItem>
                                      <SelectItem value="advanced">Advanced (Can use computers)</SelectItem>
                                    </SelectContent>
                                  </Select>
                                  <FormDescription>Required for digital India schemes</FormDescription>
                                  <FormMessage />
                                </FormItem>
                              )}
                            />
                            {/* Show employment type only for adults (18+) */}
                            {currentAge >= 18 && (
                              <FormField
                                control={form.control}
                                name="employmentType"
                                render={({ field }) => (
                                  <FormItem>
                                    <FormLabel>Employment Type</FormLabel>
                                    <Select onValueChange={field.onChange} value={field.value}>
                                      <FormControl>
                                        <SelectTrigger>
                                          <SelectValue placeholder="Select employment type" />
                                        </SelectTrigger>
                                      </FormControl>
                                      <SelectContent>
                                        <SelectItem value="government">Government</SelectItem>
                                        <SelectItem value="private">Private</SelectItem>
                                        <SelectItem value="self_employed">Self Employed</SelectItem>
                                        <SelectItem value="daily_wage">Daily Wage</SelectItem>
                                        <SelectItem value="not_applicable">Not Applicable</SelectItem>
                                      </SelectContent>
                                    </Select>
                                    <FormDescription>Required for employment schemes</FormDescription>
                                    <FormMessage />
                                  </FormItem>
                                )}
                              />
                            )}
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {/* Show skill certification only for adults (18+) */}
                            {currentAge >= 18 && (
                              <FormField
                                control={form.control}
                                name="skillCertification"
                                render={({ field }) => (
                                  <FormItem>
                                    <FormLabel>Skill Certification</FormLabel>
                                    <Select onValueChange={field.onChange} value={field.value}>
                                      <FormControl>
                                        <SelectTrigger>
                                          <SelectValue placeholder="Select skill type" />
                                        </SelectTrigger>
                                      </FormControl>
                                      <SelectContent>
                                        <SelectItem value="none">None</SelectItem>
                                        <SelectItem value="it">IT Skills</SelectItem>
                                        <SelectItem value="technical">Technical Skills</SelectItem>
                                        <SelectItem value="agriculture">Agriculture Skills</SelectItem>
                                        <SelectItem value="handicraft">Handicraft Skills</SelectItem>
                                        <SelectItem value="other">Other Skills</SelectItem>
                                      </SelectContent>
                                    </Select>
                                    <FormDescription>Required for skill development schemes</FormDescription>
                                    <FormMessage />
                                  </FormItem>
                                )}
                              />
                            )}
                            <FormField
                              control={form.control}
                              name="loanRequirement"
                              render={({ field }) => (
                                <FormItem>
                                  <FormLabel>Loan Requirement</FormLabel>
                                  <Select onValueChange={field.onChange} value={field.value}>
                                    <FormControl>
                                      <SelectTrigger>
                                        <SelectValue placeholder="Select loan type" />
                                      </SelectTrigger>
                                    </FormControl>
                                    <SelectContent>
                                      <SelectItem value="none">None</SelectItem>
                                      <SelectItem value="education">Education Loan</SelectItem>
                                      <SelectItem value="business">Business Loan</SelectItem>
                                      <SelectItem value="housing">Housing Loan</SelectItem>
                                      <SelectItem value="agriculture">Agriculture Loan</SelectItem>
                                      <SelectItem value="emergency">Emergency Loan</SelectItem>
                                    </SelectContent>
                                  </Select>
                                  <FormDescription>Required for loan assistance schemes</FormDescription>
                                  <FormMessage />
                                </FormItem>
                              )}
                            />
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <FormField
                              control={form.control}
                              name="monthlyExpenses"
                              render={({ field }) => (
                                <FormItem>
                                  <FormLabel>Monthly Expenses (₹)</FormLabel>
                                  <FormControl>
                                    <div className="relative">
                                      <IndianRupee className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                      <Input type="number" placeholder="e.g., 15000" {...field} className="pl-8" />
                                    </div>
                                  </FormControl>
                                  <FormDescription>Required for financial assistance schemes</FormDescription>
                                  <FormMessage />
                                </FormItem>
                              )}
                            />
                            <FormField
                              control={form.control}
                              name="monthlySavings"
                              render={({ field }) => (
                                <FormItem>
                                  <FormLabel>Monthly Savings (₹)</FormLabel>
                                  <FormControl>
                                    <div className="relative">
                                      <IndianRupee className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                      <Input type="number" placeholder="e.g., 5000" {...field} className="pl-8" />
                                    </div>
                                  </FormControl>
                                  <FormDescription>Required for savings-based schemes</FormDescription>
                                  <FormMessage />
                                </FormItem>
                              )}
                            />
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <FormField
                              control={form.control}
                              name="hasSmartphone"
                              render={({ field }) => (
                                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                                  <div className="space-y-0.5">
                                    <FormLabel className="text-base">Smartphone ownership</FormLabel>
                                    <FormDescription>Do you own a smartphone?</FormDescription>
                                  </div>
                                  <FormControl>
                                    <Switch
                                      checked={field.value}
                                      onCheckedChange={field.onChange}
                                    />
                                  </FormControl>
                                </FormItem>
                              )}
                            />
                            <FormField
                              control={form.control}
                              name="hasInternet"
                              render={({ field }) => (
                                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                                  <div className="space-y-0.5">
                                    <FormLabel className="text-base">Internet access</FormLabel>
                                    <FormDescription>Do you have regular internet access?</FormDescription>
                                  </div>
                                  <FormControl>
                                    <Switch
                                      checked={field.value}
                                      onCheckedChange={field.onChange}
                                    />
                                  </FormControl>
                                </FormItem>
                              )}
                            />
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <FormField
                              control={form.control}
                              name="hasInsurance"
                              render={({ field }) => (
                                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                                  <div className="space-y-0.5">
                                    <FormLabel className="text-base">Health insurance</FormLabel>
                                    <FormDescription>Do you have health insurance?</FormDescription>
                                  </div>
                                  <FormControl>
                                    <Switch
                                      checked={field.value}
                                      onCheckedChange={field.onChange}
                                    />
                                  </FormControl>
                                </FormItem>
                              )}
                            />
                            <FormField
                              control={form.control}
                              name="hasPension"
                              render={({ field }) => (
                                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                                  <div className="space-y-0.5">
                                    <FormLabel className="text-base">Pension scheme</FormLabel>
                                    <FormDescription>Are you enrolled in any pension scheme?</FormDescription>
                                  </div>
                                  <FormControl>
                                    <Switch
                                      checked={field.value}
                                      onCheckedChange={field.onChange}
                                    />
                                  </FormControl>
                                </FormItem>
                              )}
                            />
                          </div>

                          {/* Smart Logic: Show additional fields based on combinations */}
                          {(form.watch('hasSmartphone') && form.watch('hasInternet')) && (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              <FormField
                                control={form.control}
                                name="digitalLiteracy"
                                render={({ field }) => (
                                  <FormItem>
                                    <FormLabel>Digital Literacy Level</FormLabel>
                                    <Select onValueChange={field.onChange} value={field.value}>
                                      <FormControl>
                                        <SelectTrigger>
                                          <SelectValue placeholder="Select digital literacy" />
                                        </SelectTrigger>
                                      </FormControl>
                                      <SelectContent>
                                        <SelectItem value="none">None</SelectItem>
                                        <SelectItem value="basic">Basic (Can use phone)</SelectItem>
                                        <SelectItem value="intermediate">Intermediate (Can use apps)</SelectItem>
                                        <SelectItem value="advanced">Advanced (Can use computers)</SelectItem>
                                      </SelectContent>
                                    </Select>
                                    <FormDescription>Required for digital India schemes</FormDescription>
                                    <FormMessage />
                                  </FormItem>
                                )}
                              />
                            </div>
                          )}

                          {/* Smart Logic: Show employment details for employed/farmer (only for adults 18+) */}
                          {(currentOccupation === 'employed' || currentOccupation === 'farmer') && (currentAge >= 18) && (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              <FormField
                                control={form.control}
                                name="employmentType"
                                render={({ field }) => (
                                  <FormItem>
                                    <FormLabel>Employment Type</FormLabel>
                                    <Select onValueChange={field.onChange} value={field.value}>
                                      <FormControl>
                                        <SelectTrigger>
                                          <SelectValue placeholder="Select employment type" />
                                        </SelectTrigger>
                                      </FormControl>
                                      <SelectContent>
                                        <SelectItem value="government">Government</SelectItem>
                                        <SelectItem value="private">Private</SelectItem>
                                        <SelectItem value="self_employed">Self Employed</SelectItem>
                                        <SelectItem value="daily_wage">Daily Wage</SelectItem>
                                        <SelectItem value="not_applicable">Not Applicable</SelectItem>
                                      </SelectContent>
                                    </Select>
                                    <FormDescription>Required for employment schemes</FormDescription>
                                    <FormMessage />
                                  </FormItem>
                                )}
                              />
                              <FormField
                                control={form.control}
                                name="skillCertification"
                                render={({ field }) => (
                                  <FormItem>
                                    <FormLabel>Skill Certification</FormLabel>
                                    <Select onValueChange={field.onChange} value={field.value}>
                                      <FormControl>
                                        <SelectTrigger>
                                          <SelectValue placeholder="Select skill type" />
                                        </SelectTrigger>
                                      </FormControl>
                                      <SelectContent>
                                        <SelectItem value="none">None</SelectItem>
                                        <SelectItem value="it">IT Skills</SelectItem>
                                        <SelectItem value="technical">Technical Skills</SelectItem>
                                        <SelectItem value="agriculture">Agriculture Skills</SelectItem>
                                        <SelectItem value="handicraft">Handicraft Skills</SelectItem>
                                        <SelectItem value="other">Other Skills</SelectItem>
                                      </SelectContent>
                                    </Select>
                                    <FormDescription>Required for skill development schemes</FormDescription>
                                    <FormMessage />
                                  </FormItem>
                                )}
                              />
                            </div>
                          )}

                          {/* Smart Logic: Show financial fields for loan requirements (only when loan is needed) */}
                          {form.watch('loanRequirement') !== 'none' && form.watch('loanRequirement') !== undefined && (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              <FormField
                                control={form.control}
                                name="monthlyExpenses"
                                render={({ field }) => (
                                  <FormItem>
                                    <FormLabel>Monthly Expenses (₹)</FormLabel>
                                    <FormControl>
                                      <div className="relative">
                                        <IndianRupee className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                        <Input type="number" placeholder="e.g., 15000" {...field} className="pl-8" />
                                      </div>
                                    </FormControl>
                                    <FormDescription>Required for loan eligibility</FormDescription>
                                    <FormMessage />
                                  </FormItem>
                                )}
                              />
                              <FormField
                                control={form.control}
                                name="monthlySavings"
                                render={({ field }) => (
                                  <FormItem>
                                    <FormLabel>Monthly Savings (₹)</FormLabel>
                                    <FormControl>
                                      <div className="relative">
                                        <IndianRupee className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                        <Input type="number" placeholder="e.g., 5000" {...field} className="pl-8" />
                                      </div>
                                    </FormControl>
                                    <FormDescription>Required for loan eligibility</FormDescription>
                                    <FormMessage />
                                  </FormItem>
                                )}
                              />
                            </div>
                          )}

                          {/* Smart Logic: Show education fields for students */}
                          {currentOccupation === 'student' && (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              <FormField
                                control={form.control}
                                name="educationLevel"
                                render={({ field }) => (
                                  <FormItem>
                                    <FormLabel>Current Education Level</FormLabel>
                                    <Select onValueChange={field.onChange} value={field.value}>
                                      <FormControl>
                                        <SelectTrigger>
                                          <SelectValue placeholder="Select education level" />
                                        </SelectTrigger>
                                      </FormControl>
                                      <SelectContent>
                                        <SelectItem value="illiterate">Illiterate</SelectItem>
                                        <SelectItem value="primary">Primary (1-5)</SelectItem>
                                        <SelectItem value="secondary">Secondary (6-10)</SelectItem>
                                        <SelectItem value="higher_secondary">Higher Secondary (11-12)</SelectItem>
                                        <SelectItem value="graduate">Graduate</SelectItem>
                                        <SelectItem value="postgraduate">Post Graduate</SelectItem>
                                        <SelectItem value="phd">PhD</SelectItem>
                                      </SelectContent>
                                    </Select>
                                    <FormDescription>Required for education schemes</FormDescription>
                                    <FormMessage />
                                  </FormItem>
                                )}
                              />
                              <FormField
                                control={form.control}
                                name="loanRequirement"
                                render={({ field }) => (
                                  <FormItem>
                                    <FormLabel>Education Loan Required</FormLabel>
                                    <Select onValueChange={field.onChange} value={field.value}>
                                      <FormControl>
                                        <SelectTrigger>
                                          <SelectValue placeholder="Select loan requirement" />
                                        </SelectTrigger>
                                      </FormControl>
                                      <SelectContent>
                                        <SelectItem value="none">No Loan Required</SelectItem>
                                        <SelectItem value="education">Education Loan</SelectItem>
                                        <SelectItem value="business">Business Loan</SelectItem>
                                        <SelectItem value="housing">Housing Loan</SelectItem>
                                        <SelectItem value="agriculture">Agriculture Loan</SelectItem>
                                        <SelectItem value="emergency">Emergency Loan</SelectItem>
                                      </SelectContent>
                                    </Select>
                                    <FormDescription>Required for education assistance</FormDescription>
                                    <FormMessage />
                                  </FormItem>
                                )}
                              />
                            </div>
                          )}
                        </div>
                      </div>
                  </div>
                  </div>
                </CardContent>
                <CardFooter className="flex justify-between items-center p-6 border-t border-white/10 bg-black/20">
                  {step === 1 ? (
                    <div className="w-full flex justify-end">
                      <Button
                        type="button"
                        onClick={async () => {
                          const valid = await form.trigger(["age", "annualIncome", "state", "caste", "occupation"]);
                          if (valid) setStep(2);
                        }}
                        className="bg-white text-black hover:bg-slate-200 w-full md:w-auto px-8 py-6 rounded-2xl font-black shadow-[0_0_15px_rgba(255,255,255,0.2)] transition-all group"
                      >
                        Next <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
                      </Button>
                    </div>
                  ) : (
                    <div className="w-full flex flex-col md:flex-row justify-between items-center gap-4">
                      <Button
                        type="button"
                        variant="ghost"
                        onClick={() => setStep(1)}
                        className="text-slate-400 hover:text-white"
                      >
                        Back
                      </Button>
                      <div className="flex flex-col md:flex-row gap-4 w-full md:w-auto">
                        <Button
                          type="submit"
                          variant="secondary"
                          className="bg-slate-800 text-slate-300 hover:bg-slate-700 w-full md:w-auto px-6 py-6 rounded-2xl border border-slate-700 font-bold"
                          disabled={isSubmitting}
                        >
                          Skip & Show Results ⏭️
                        </Button>
                        <Button
                          type="submit"
                          className="bg-white text-black hover:bg-slate-200 w-full md:w-auto px-10 py-6 rounded-2xl font-black shadow-[0_0_20px_rgba(255,255,255,0.2)] transition-all"
                          disabled={isSubmitting}
                        >
                          {isSubmitting ? 'Analyzing...' : 'Submit & Analyze'}
                        </Button>
                      </div>
                    </div>
                  )}
                </CardFooter>
              </form>
            </Form>
          ) : (
            <div className="flex flex-col h-full w-full">
              <CardContent className="space-y-6 pt-6">
                <div className="flex flex-col items-center justify-center p-8 text-center space-y-4">
                  <div className="w-20 h-20 bg-green-500/10 rounded-full flex items-center justify-center mb-4 ring-8 ring-green-500/5">
                    <CheckCircle className="h-10 w-10 text-green-500" />
                  </div>
                  <h2 className="text-3xl font-black text-primary">Analysis Complete</h2>
                  <p className="text-muted-foreground text-lg">
                    Our AI has classified your eligible benefits into 3 distinct categories.
                  </p>

                  <div className="grid md:grid-cols-3 gap-6 w-full mt-8">
                    {/* Schemes Category */}
                    <div className="bg-primary/5 rounded-2xl p-6 border border-primary/20 hover:border-primary/50 transition-colors flex flex-col items-center justify-center space-y-4">
                      <div className="w-14 h-14 bg-primary/10 rounded-full flex items-center justify-center text-primary">
                        <Landmark className="h-7 w-7" />
                      </div>
                      <h3 className="font-bold text-xl">Schemes</h3>
                      <p className="text-sm text-center text-muted-foreground h-16">
                        Government welfare programs, subsidies, and scholarships.
                      </p>
                      <div className="text-3xl font-black text-primary mb-2">
                        {rawSchemeData.filter(s => s.benefit_type === 'scheme' || !s.benefit_type).length}
                      </div>
                      <Button onClick={() => {
                        const rawVals = form.getValues() as Record<string, any>;
                        const cleanVals = Object.fromEntries(Object.entries(rawVals).filter(([_, v]) => v !== undefined && v !== '' && (!Array.isArray(v) || v.length > 0)));
                        const params = new URLSearchParams(cleanVals as Record<string, string>);
                        params.append('type', 'scheme');
                        router.push(`/recommendations?${params.toString()}`);
                      }} className="w-full gap-2">
                        View Schemes <ArrowRight className="h-4 w-4" />
                      </Button>
                    </div>

                    {/* Loans Category */}
                    <div className="bg-orange-500/5 rounded-2xl p-6 border border-orange-500/20 hover:border-orange-500/50 transition-colors flex flex-col items-center justify-center space-y-4">
                      <div className="w-14 h-14 bg-orange-500/10 rounded-full flex items-center justify-center text-orange-600">
                        <Briefcase className="h-7 w-7" />
                      </div>
                      <h3 className="font-bold text-xl text-orange-800">Loans & Credit</h3>
                      <p className="text-sm text-center text-muted-foreground h-16">
                        Business financing, educational loans, and credit subsidies.
                      </p>
                      <div className="text-3xl font-black text-orange-600 mb-2">
                        {rawSchemeData.filter(s => s.benefit_type === 'loan').length}
                      </div>
                      <Button onClick={() => {
                        const rawVals = form.getValues() as Record<string, any>;
                        const cleanVals = Object.fromEntries(Object.entries(rawVals).filter(([_, v]) => v !== undefined && v !== '' && (!Array.isArray(v) || v.length > 0)));
                        const params = new URLSearchParams(cleanVals as Record<string, string>);
                        params.append('type', 'loan');
                        router.push(`/recommendations?${params.toString()}`);
                      }} className="w-full bg-orange-600 hover:bg-orange-700 gap-2">
                        View Loans <ArrowRight className="h-4 w-4" />
                      </Button>
                    </div>

                    {/* Insurance Category */}
                    <div className="bg-purple-500/5 rounded-2xl p-6 border border-purple-500/20 hover:border-purple-500/50 transition-colors flex flex-col items-center justify-center space-y-4">
                      <div className="w-14 h-14 bg-purple-500/10 rounded-full flex items-center justify-center text-purple-600">
                        <Shield className="h-7 w-7" />
                      </div>
                      <h3 className="font-bold text-xl text-purple-800">Insurance</h3>
                      <p className="text-sm text-center text-muted-foreground h-16">
                        Health coverage, life insurance, and pension plans.
                      </p>
                      <div className="text-3xl font-black text-purple-600 mb-2">
                        {rawSchemeData.filter(s => s.benefit_type === 'insurance').length}
                      </div>
                      <Button onClick={() => {
                        const rawVals = form.getValues() as Record<string, any>;
                        const cleanVals = Object.fromEntries(Object.entries(rawVals).filter(([_, v]) => v !== undefined && v !== '' && (!Array.isArray(v) || v.length > 0)));
                        const params = new URLSearchParams(cleanVals as Record<string, string>);
                        params.append('type', 'insurance');
                        router.push(`/recommendations?${params.toString()}`);
                      }} className="w-full bg-purple-600 hover:bg-purple-700 gap-2">
                        View Insurance <ArrowRight className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
              <CardFooter className="flex justify-center flex-wrap gap-4 border-t pt-6 bg-muted/20">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setHasSubmitted(false);
                  }}
                  className="px-8 h-12"
                >
                  Refine Profile
                </Button>
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => {
                    const rawVals = form.getValues() as Record<string, any>;
                    const cleanVals = Object.fromEntries(Object.entries(rawVals).filter(([_, v]) => v !== undefined && v !== '' && (!Array.isArray(v) || v.length > 0)));
                    const params = new URLSearchParams(cleanVals as Record<string, string>);
                    router.push(`/recommendations?${params.toString()}`);
                  }}
                  className="px-8 h-12 gap-2 shadow-sm"
                >
                  View All Together <ArrowRight className="h-4 w-4" />
                </Button>
              </CardFooter>
            </div>
          )}
        </Card>
      </main>
      <Chatbot />
    </div>
  );
}

export default function CheckEligibilityPage() {
  return <CheckEligibilityContent />;
}
