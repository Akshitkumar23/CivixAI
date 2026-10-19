import { Header } from '@/components/Header';
import { Skeleton } from '@/components/ui/skeleton';
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card';

export default function RecommendationsLoading() {
  return (
    <div className="flex flex-col min-h-screen bg-[#07070a] text-white font-sans">
      <Header />
      <main className="flex-grow container mx-auto px-4 py-8 max-w-6xl">
        {/* Header Skeleton */}
        <div className="mb-6 space-y-3">
          <Skeleton className="h-5 w-24 bg-white/10 rounded-lg" />
          <Skeleton className="h-9 w-64 bg-white/10 rounded-xl" />
          <Skeleton className="h-4 w-80 bg-white/10 rounded-lg" />
        </div>

        {/* Summary Strip Skeleton */}
        <div className="flex gap-3 mb-6">
          <Skeleton className="h-10 w-28 bg-white/10 rounded-xl" />
          <Skeleton className="h-10 w-28 bg-white/10 rounded-xl" />
          <Skeleton className="h-10 w-32 bg-white/10 rounded-xl" />
          <Skeleton className="h-10 w-32 bg-white/10 rounded-xl" />
        </div>

        {/* Search & Tabs Skeleton */}
        <div className="flex flex-col sm:flex-row justify-between gap-4 mb-6">
          <Skeleton className="h-10 w-72 bg-white/10 rounded-xl" />
          <Skeleton className="h-10 w-64 bg-white/10 rounded-xl" />
        </div>

        {/* Cards Grid Skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {Array.from({ length: 6 }).map((_, i) => (
            <Card key={i} className="bg-[#0f1015] border border-white/10 rounded-2xl overflow-hidden">
              <CardHeader className="p-5 pb-3">
                <div className="flex justify-between items-start gap-4">
                  <div className="space-y-2 flex-1">
                    <Skeleton className="h-6 w-3/4 bg-white/10 rounded-lg" />
                    <Skeleton className="h-3 w-1/2 bg-white/10 rounded-md" />
                  </div>
                  <Skeleton className="h-6 w-20 bg-white/10 rounded-full shrink-0" />
                </div>
              </CardHeader>
              <CardContent className="p-5 pt-2 space-y-3">
                <Skeleton className="h-4 w-full bg-white/10 rounded-md" />
                <Skeleton className="h-4 w-5/6 bg-white/10 rounded-md" />
                <div className="p-3 rounded-xl bg-white/[0.03] border border-white/5 space-y-2">
                  <Skeleton className="h-3 w-1/3 bg-white/10 rounded-md" />
                  <Skeleton className="h-3 w-2/3 bg-white/10 rounded-md" />
                </div>
                <Skeleton className="h-7 w-36 bg-emerald-500/10 rounded-lg" />
              </CardContent>
              <CardFooter className="p-5 pt-0 border-t border-white/5 pt-4 flex gap-2">
                <Skeleton className="h-9 flex-1 bg-white/10 rounded-xl" />
                <Skeleton className="h-9 w-24 bg-white/10 rounded-xl" />
              </CardFooter>
            </Card>
          ))}
        </div>
      </main>
    </div>
  );
}
