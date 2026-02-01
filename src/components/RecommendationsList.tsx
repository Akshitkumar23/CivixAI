'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import { getRecommendations } from '@/lib/logic';
import type { UserProfile } from '@/lib/types';
import schemesData from '@/lib/schemes.json';
import { RecommendationCard } from '@/components/RecommendationCard';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { SearchX } from 'lucide-react';

export function RecommendationsList({ searchParams }: { searchParams: { [key: string]: string | string[] | undefined } }) {
  const profile: UserProfile = {
    age: Number(searchParams.age) || 0,
    gender: (searchParams.gender as UserProfile['gender']) || 'other',
    state: (searchParams.state as string) || '',
    annualIncome: Number(searchParams.annualIncome) || 0,
    isStudent: searchParams.isStudent === 'true',
    hasDisability: searchParams.hasDisability === 'true',
    caste: (searchParams.caste as UserProfile['caste']) || 'general',
  };

  const recommendedSchemes = getRecommendations(profile, schemesData.schemes);

  if (recommendedSchemes.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-20">
        <Alert className="max-w-lg bg-card/60 backdrop-blur-md">
          <SearchX className="h-4 w-4" />
          <AlertTitle className="font-headline">No Schemes Found</AlertTitle>
          <AlertDescription>
            Based on the information provided, we couldn't find any matching schemes for you at the moment.
          </AlertDescription>
        </Alert>
        <Button asChild variant="link" className="mt-4">
          <Link href="/check-eligibility">Try with different details</Link>
        </Button>
      </div>
    );
  }

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.15,
      },
    },
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        duration: 0.5,
      },
    },
  };

  return (
    <motion.div
      className="grid gap-8 md:grid-cols-1 lg:grid-cols-2 xl:grid-cols-3"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {recommendedSchemes.map((scheme, index) => (
        <motion.div key={scheme.id} variants={itemVariants}>
          <RecommendationCard scheme={scheme} priorityIndex={index} />
        </motion.div>
      ))}
    </motion.div>
  );
}
