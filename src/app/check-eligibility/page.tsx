'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { zodResolver } from '@hookform/resolvers/zod';
import { useForm, type SubmitHandler } from 'react-hook-form';
import { z } from 'zod';
import { ArrowRight, User, Hand, IndianRupee, Briefcase, GraduationCap, Accessibility, Users, CheckCircle, XCircle, Plus, ChevronDown, ChevronUp } from 'lucide-react';
import { type UserProfile } from '@/lib/types';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Header } from '@/components/Header';
import Chatbot from '@/components/Chatbot';
import { useToast } from '@/hooks/use-toast';

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

export default function CheckEligibilityPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [eligibleSchemes, setEligibleSchemes] = useState<string[]>([]);
  const [hasSubmitted, setHasSubmitted] = useState(false);
  const [showOptionalLevel1, setShowOptionalLevel1] = useState(false);
  const [showOptionalLevel2, setShowOptionalLevel2] = useState(false);
  const [step, setStep] = useState(1); // Multi-step form
  const [initialResults, setInitialResults] = useState<string[]>([]);
  const [showFollowUp, setShowFollowUp] = useState(false);

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

  // Get current occupation value for conditional logic
  const currentOccupation = form.watch('occupation');
  const hasLand = form.watch('hasLand');
  const currentAge = form.watch('age');

  const onSubmit: SubmitHandler<ProfileFormValues> = async (data) => {
    setIsSubmitting(true);
    try {
      // Convert form data to API format
      const apiData = {
        age: data.age!,
        income: data.annualIncome || 0,
        state: data.state,
        category: data.caste,
        occupation: data.occupation,
        gender: data.gender || 'other',
        hasDisability: data.hasDisability,
        hasLand: data.hasLand,
        familyIncome: data.familyIncome || 0,
        hasAvailedSimilarScheme: data.hasAvailedSimilarScheme,
        landSize: data.landSize,
        familySize: data.familySize,
        isSingleGirlChild: data.isSingleGirlChild,
        isWidowOrSenior: data.isWidowOrSenior,
        isTaxPayer: data.isTaxPayer,
        isBankLinked: data.isBankLinked,
        // Modern intelligent fields
        educationLevel: data.educationLevel,
        digitalLiteracy: data.digitalLiteracy,
        urbanRural: data.urbanRural,
        monthlyExpenses: data.monthlyExpenses || 0,
        hasSmartphone: data.hasSmartphone,
        hasInternet: data.hasInternet,
        employmentType: data.employmentType,
        skillCertification: data.skillCertification,
        loanRequirement: data.loanRequirement,
        monthlySavings: data.monthlySavings || 0,
        hasInsurance: data.hasInsurance,
        hasPension: data.hasPension,
        prioritySchemes: data.prioritySchemes
      };

      // Call the ML-ready API
      const response = await fetch('/api/check-eligibility', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(apiData),
      });

      const result = await response.json();

      if (result.success) {
        // Handle both ML and rule-based responses
        let schemes = [];
        
        if (result.eligibleSchemes && Array.isArray(result.eligibleSchemes)) {
          schemes = result.eligibleSchemes;
        } else if (result.schemeDetails && Array.isArray(result.schemeDetails)) {
          schemes = result.schemeDetails.map(s => s.name);
        } else if (result.topSchemes && Array.isArray(result.topSchemes)) {
          schemes = result.topSchemes.map(s => s.scheme);
        }

        setEligibleSchemes(schemes);
        setHasSubmitted(true);
        toast({
          title: "Success!",
          description: `Found ${schemes.length} eligible schemes.`,
        });
      } else {
        throw new Error(result.error || 'Failed to get predictions');
      }
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'An error occurred',
        description: 'Could not process your request. Please try again.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-background">
      <Header />
      <main className="flex-grow flex items-center justify-center">
        <Card className="w-full max-w-2xl mx-auto bg-card/60 backdrop-blur-md shadow-xl my-12">
            <CardHeader>
                <div className="text-center">
                    <h1 className="font-headline text-3xl font-bold text-primary">Check Your Eligibility</h1>
                    <p className="text-muted-foreground mt-2">Fill out the form below to discover schemes, loans, and benefits you qualify for.</p>
                </div>
            </CardHeader>
            <CardHeader>
              <CardTitle className="font-headline text-2xl">Check Eligibility</CardTitle>
              <CardDescription>Fill in the required fields to get started</CardDescription>
            </CardHeader>
            {!hasSubmitted ? (
              <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)}>
                  <CardContent className="space-y-6">
                    {/* CORE INPUTS - Always visible and required */}
                    <div className="space-y-4">
                      <div className="flex items-center gap-2">
                        <User className="h-5 w-5 text-primary" />
                        <h3 className="font-semibold text-lg">Core Information</h3>
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
                                  <Input type="number" placeholder="e.g., 250000" {...field} className="pl-8"/>
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
                              <Select onValueChange={field.onChange} defaultValue={field.value}>
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
                              <Select onValueChange={field.onChange} defaultValue={field.value}>
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
                            <Select onValueChange={field.onChange} defaultValue={field.value}>
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

                    {/* INTELLIGENT FOLLOW-UP QUESTIONS */}
                    <div className="space-y-4">
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => setShowFollowUp(!showFollowUp)}
                        className="w-full justify-between"
                      >
                        <span className="flex items-center gap-2">
                          <Users className="h-4 w-4" />
                          Get personalized questions (recommended)
                        </span>
                        {showFollowUp ? (
                          <ChevronUp className="h-4 w-4" />
                        ) : (
                          <ChevronDown className="h-4 w-4" />
                        )}
                      </Button>

                      {showFollowUp && (
                        <div className="space-y-4 border-t pt-4">
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
                                    <Select onValueChange={field.onChange} defaultValue={field.value}>
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
                                    <Select onValueChange={field.onChange} defaultValue={field.value}>
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

                          {/* Smart follow-up based on technology access */}
                          {(form.watch('hasSmartphone') || form.watch('hasInternet')) && (
                            <FormField
                              control={form.control}
                              name="digitalLiteracy"
                              render={({ field }) => (
                                <FormItem>
                                  <FormLabel>Digital Literacy Level</FormLabel>
                                  <Select onValueChange={field.onChange} defaultValue={field.value}>
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
                                        <Input type="number" placeholder="e.g., 15000" {...field} className="pl-8"/>
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
                                        <Input type="number" placeholder="e.g., 5000" {...field} className="pl-8"/>
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
                      )}
                    </div>

                    {/* OPTIONAL LEVEL 1 - Hidden by default */}
                    <div className="space-y-4">
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => setShowOptionalLevel1(!showOptionalLevel1)}
                        className="w-full justify-between"
                      >
                        <span className="flex items-center gap-2">
                          <Plus className="h-4 w-4" />
                          Add more details (improves accuracy)
                        </span>
                        {showOptionalLevel1 ? (
                          <ChevronUp className="h-4 w-4" />
                        ) : (
                          <ChevronDown className="h-4 w-4" />
                        )}
                      </Button>

                      {showOptionalLevel1 && (
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
                                  <Select onValueChange={field.onChange} defaultValue={field.value}>
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
                                      <Input type="number" placeholder="e.g., 400000" {...field} className="pl-8"/>
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
                      )}
                    </div>

                    {/* OPTIONAL LEVEL 2 - Hidden by default */}
                    <div className="space-y-4">
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => setShowOptionalLevel2(!showOptionalLevel2)}
                        className="w-full justify-between"
                      >
                        <span className="flex items-center gap-2">
                          <Plus className="h-4 w-4" />
                          Advanced inputs (optional)
                        </span>
                        {showOptionalLevel2 ? (
                          <ChevronUp className="h-4 w-4" />
                        ) : (
                          <ChevronDown className="h-4 w-4" />
                        )}
                      </Button>

                      {showOptionalLevel2 && (
                        <div className="space-y-4 border-t pt-4">
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
                                    <Select onValueChange={field.onChange} defaultValue={field.value}>
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
                                    <Select onValueChange={field.onChange} defaultValue={field.value}>
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
                                    <Select onValueChange={field.onChange} defaultValue={field.value}>
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
                                      <Select onValueChange={field.onChange} defaultValue={field.value}>
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
                                      <Select onValueChange={field.onChange} defaultValue={field.value}>
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
                                    <Select onValueChange={field.onChange} defaultValue={field.value}>
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
                                        <Input type="number" placeholder="e.g., 15000" {...field} className="pl-8"/>
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
                                        <Input type="number" placeholder="e.g., 5000" {...field} className="pl-8"/>
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
                                      <Select onValueChange={field.onChange} defaultValue={field.value}>
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
                                      <Select onValueChange={field.onChange} defaultValue={field.value}>
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
                                      <Select onValueChange={field.onChange} defaultValue={field.value}>
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
                                          <Input type="number" placeholder="e.g., 15000" {...field} className="pl-8"/>
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
                                          <Input type="number" placeholder="e.g., 5000" {...field} className="pl-8"/>
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
                                      <Select onValueChange={field.onChange} defaultValue={field.value}>
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
                                      <Select onValueChange={field.onChange} defaultValue={field.value}>
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
                      )}
                    </div>
                  </CardContent>
                  <CardFooter className="flex justify-end">
                    <Button 
                      type="submit" 
                      className="bg-accent text-accent-foreground hover:bg-accent/90 w-full md:w-auto"
                      disabled={isSubmitting}
                    >
                      {isSubmitting ? 'Finding Schemes...' : 'Find My Schemes'}
                    </Button>
                  </CardFooter>
                </form>
              </Form>
            ) : (
              <CardContent className="space-y-6">
                <div className="text-center">
                  <h2 className="font-headline text-2xl font-bold text-primary mb-4">Eligible Schemes</h2>
                  {eligibleSchemes.length > 0 ? (
                    <div className="space-y-3">
                      {eligibleSchemes.map((scheme, index) => (
                        <div key={index} className="flex items-center justify-between p-4 border rounded-lg bg-green-50/50">
                          <div className="flex items-center gap-3">
                            <CheckCircle className="h-5 w-5 text-green-600" />
                            <span className="font-medium">{scheme}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="flex items-center justify-center p-8 border-2 border-dashed rounded-lg">
                      <div className="text-center">
                        <XCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                        <p className="text-gray-600">No eligible schemes found based on your profile.</p>
                        <p className="text-sm text-gray-500 mt-2">Please check your information or try adjusting some criteria.</p>
                      </div>
                    </div>
                  )}
                </div>
                  <div className="flex justify-center space-x-4">
                  <Button 
                    variant="outline" 
                    onClick={() => {
                      setHasSubmitted(false);
                      setEligibleSchemes([]);
                      setShowOptionalLevel1(false);
                      setShowOptionalLevel2(false);
                      form.reset();
                    }}
                  >
                    Try Again
                  </Button>
                  <Button 
                    onClick={() => {
                      // Build search parameters from form data
                      const formData = form.getValues();
                      const searchParams = new URLSearchParams();
                      
                      // Core required fields
                      if (formData.age) searchParams.set('age', formData.age.toString());
                      if (formData.annualIncome) searchParams.set('income', formData.annualIncome.toString());
                      if (formData.state) searchParams.set('state', formData.state);
                      if (formData.caste) searchParams.set('category', formData.caste);
                      if (formData.occupation) searchParams.set('occupation', formData.occupation);
                      if (formData.gender) searchParams.set('gender', formData.gender);
                      
                      // Optional fields
                      if (formData.hasDisability) searchParams.set('hasDisability', 'true');
                      if (formData.hasLand) searchParams.set('hasLand', 'true');
                      if (formData.familyIncome) searchParams.set('familyIncome', formData.familyIncome.toString());
                      if (formData.landSize) searchParams.set('landSize', formData.landSize.toString());
                      if (formData.familySize) searchParams.set('familySize', formData.familySize.toString());
                      if (formData.isSingleGirlChild) searchParams.set('isSingleGirlChild', 'true');
                      if (formData.isWidowOrSenior) searchParams.set('isWidowOrSenior', 'true');
                      if (formData.isTaxPayer) searchParams.set('isTaxPayer', 'true');
                      if (formData.isBankLinked) searchParams.set('isBankLinked', 'true');
                      if (formData.educationLevel) searchParams.set('educationLevel', formData.educationLevel);
                      if (formData.digitalLiteracy) searchParams.set('digitalLiteracy', formData.digitalLiteracy);
                      if (formData.urbanRural) searchParams.set('urbanRural', formData.urbanRural);
                      if (formData.monthlyExpenses) searchParams.set('monthlyExpenses', formData.monthlyExpenses.toString());
                      if (formData.hasSmartphone) searchParams.set('hasSmartphone', 'true');
                      if (formData.hasInternet) searchParams.set('hasInternet', 'true');
                      if (formData.employmentType) searchParams.set('employmentType', formData.employmentType);
                      if (formData.skillCertification) searchParams.set('skillCertification', formData.skillCertification);
                      if (formData.loanRequirement) searchParams.set('loanRequirement', formData.loanRequirement);
                      if (formData.monthlySavings) searchParams.set('monthlySavings', formData.monthlySavings.toString());
                      if (formData.hasInsurance) searchParams.set('hasInsurance', 'true');
                      if (formData.hasPension) searchParams.set('hasPension', 'true');
                      
                      router.push(`/recommendations?${searchParams.toString()}`);
                    }}
                    className="bg-primary text-primary-foreground"
                  >
                    View Detailed Results
                  </Button>
                </div>
              </CardContent>
            )}
          </Card>
      </main>
      <Chatbot />
    </div>
  );
}
