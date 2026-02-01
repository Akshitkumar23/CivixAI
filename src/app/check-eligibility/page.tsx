'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { zodResolver } from '@hookform/resolvers/zod';
import { useForm, type SubmitHandler } from 'react-hook-form';
import { z } from 'zod';
import { ArrowRight, User, Hand, IndianRupee, Briefcase, GraduationCap, Accessibility, Users } from 'lucide-react';
import { findSchemes } from '@/lib/actions';
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

const profileSchema = z.object({
  age: z.coerce.number().min(1, 'Age is required').max(120, 'Enter a valid age'),
  gender: z.enum(['male', 'female', 'other'], { required_error: 'Gender is required' }),
  state: z.string().min(1, 'State is required'),
  annualIncome: z.coerce.number().min(0, 'Income must be a positive number'),
  isStudent: z.boolean().default(false),
  hasDisability: z.boolean().default(false),
  caste: z.enum(['general', 'obc', 'sc', 'st'], { required_error: 'Caste is required' }),
});

type ProfileFormValues = z.infer<typeof profileSchema>;

const stepFields: (keyof ProfileFormValues)[][] = [
  ['age', 'gender', 'state'],
  ['annualIncome', 'caste', 'isStudent', 'hasDisability'],
];

export default function CheckEligibilityPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [step, setStep] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const form = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      isStudent: false,
      hasDisability: false,
      annualIncome: 0,
      age: undefined,
    },
  });

  const onSubmit: SubmitHandler<ProfileFormValues> = async (data) => {
    setIsSubmitting(true);
    try {
      await findSchemes(data);
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'An error occurred',
        description: 'Could not process your request. Please try again.',
      });
      setIsSubmitting(false);
    }
  };

  const handleNext = async () => {
    const fieldsToValidate = stepFields[step];
    const isValid = await form.trigger(fieldsToValidate);
    if (isValid) {
      setStep((prev) => prev + 1);
    }
  };

  const handleBack = () => {
    setStep((prev) => prev - 1);
  };

  const steps = [
    { icon: User, title: "Personal Details", description: "Let's start with the basics." },
    { icon: Hand, title: "Social & Financial Status", description: "Help us understand your background." },
  ];
  
  const StepIcon = steps[step]?.icon;

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
              <CardTitle className="font-headline text-2xl flex items-center gap-3">
                 {StepIcon && <StepIcon className="text-primary h-6 w-6" />}
                {steps[step]?.title}
              </CardTitle>
              <CardDescription>{steps[step]?.description}</CardDescription>
            </CardHeader>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)}>
                <CardContent className="space-y-6">
                  {step === 0 && (
                    <>
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
                        name="gender"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Gender</FormLabel>
                            <Select onValueChange={field.onChange} defaultValue={field.value}>
                              <FormControl>
                                <SelectTrigger>
                                  <SelectValue placeholder="Select your gender" />
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
                    </>
                  )}
                  {step === 1 && (
                    <>
                      <FormField
                        control={form.control}
                        name="annualIncome"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Annual Family Income (₹)</FormLabel>
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
                       <FormField
                        control={form.control}
                        name="caste"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Caste Category</FormLabel>
                            <Select onValueChange={field.onChange} defaultValue={field.value}>
                              <FormControl>
                                <SelectTrigger>
                                  <SelectValue placeholder="Select your caste category" />
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
                      <div className="space-y-4">
                       <FormField
                          control={form.control}
                          name="isStudent"
                          render={({ field }) => (
                            <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                              <div className="space-y-0.5">
                                <FormLabel className="text-base flex items-center gap-2"><GraduationCap/>Are you a student?</FormLabel>
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
                                <FormLabel className="text-base flex items-center gap-2"><Accessibility />Do you have a disability?</FormLabel>
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
                    </>
                  )}
                </CardContent>
                <CardFooter className="flex justify-between">
                  {step > 0 && (
                    <Button type="button" variant="outline" onClick={handleBack}>
                      Back
                    </Button>
                  )}
                  {step < 1 ? (
                    <Button type="button" onClick={handleNext} className="ml-auto">
                      Next
                    </Button>
                  ) : (
                    <Button type="submit" className="ml-auto bg-accent text-accent-foreground hover:bg-accent/90" disabled={isSubmitting}>
                      {isSubmitting ? 'Finding Schemes...' : 'Find My Schemes'}
                    </Button>
                  )}
                </CardFooter>
              </form>
            </Form>
          </Card>
      </main>
      <Chatbot />
    </div>
  );
}
