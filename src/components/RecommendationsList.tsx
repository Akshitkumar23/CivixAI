
'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { SearchX } from 'lucide-react';

export function RecommendationsList() {
  return (
    <div className="flex flex-col items-center justify-center text-center py-20">
      <Alert className="max-w-lg bg-card/60 backdrop-blur-md">
        <SearchX className="h-4 w-4" />
        <AlertTitle className="font-headline">No Schemes Available</AlertTitle>
        <AlertDescription>
          This app no longer uses predefined schemes. Please use the eligibility flow to fetch live results.
        </AlertDescription>
      </Alert>
      <Button asChild variant="link" className="mt-4">
        <Link href="/check-eligibility">Check Eligibility</Link>
      </Button>
    </div>
  );
}
