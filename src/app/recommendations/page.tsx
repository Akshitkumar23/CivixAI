import Link from 'next/link';
import { Suspense } from 'react';
import { Header } from '@/components/Header';
import { RecommendationsList } from '@/components/RecommendationsList';
import Chatbot from '@/components/Chatbot';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { SearchX } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';

function RecommendationsSkeleton() {
  return (
    <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 3 }).map((_, i) => (
        <CardSkeleton key={i} />
      ))}
    </div>
  );
}

function CardSkeleton() {
  return (
    <div className="flex flex-col space-y-3">
      <Skeleton className="h-[200px] w-full rounded-xl" />
      <div className="space-y-2">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-4 w-1/2" />
      </div>
    </div>
  );
}

export default function RecommendationsPage({ searchParams }: { searchParams: { [key: string]: string | string[] | undefined } }) {
  return (
    <div className="flex flex-col min-h-screen bg-background">
      <Header />
      <main className="flex-grow container mx-auto px-4 py-8 sm:py-12">
        <div className="mb-8 text-center">
            <h1 className="font-headline text-4xl sm:text-5xl font-bold text-primary">Your Recommended Schemes</h1>
            <p className="mt-4 max-w-2xl mx-auto text-lg text-foreground/80">
                Here are the top schemes we've identified for you, ranked by priority.
            </p>
        </div>
        <Suspense fallback={<RecommendationsSkeleton />}>
          <RecommendationsList searchParams={searchParams} />
        </Suspense>
      </main>
      <Chatbot />
    </div>
  );
}
