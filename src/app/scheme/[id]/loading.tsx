import { Header } from '@/components/Header';
import { Skeleton } from '@/components/ui/skeleton';
import { Card, CardContent, CardHeader } from '@/components/ui/card';

export default function SchemeDetailsLoading() {
  return (
    <div className="flex flex-col min-h-screen bg-[#07070a] text-white font-sans">
      <Header />
      <main className="flex-grow container mx-auto px-4 py-8 max-w-4xl space-y-6">
        {/* Navigation & Header */}
        <div className="space-y-3">
          <Skeleton className="h-5 w-32 bg-white/10 rounded-lg" />
          <div className="flex items-center gap-3">
            <Skeleton className="h-6 w-24 bg-white/10 rounded-full" />
            <Skeleton className="h-6 w-32 bg-white/10 rounded-full" />
          </div>
          <Skeleton className="h-10 w-3/4 bg-white/10 rounded-xl" />
          <Skeleton className="h-4 w-full bg-white/10 rounded-lg" />
          <Skeleton className="h-4 w-2/3 bg-white/10 rounded-lg" />
        </div>

        {/* Quick Stats Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="p-4 rounded-2xl bg-white/[0.03] border border-white/5 space-y-2">
              <Skeleton className="h-3 w-16 bg-white/10 rounded-md" />
              <Skeleton className="h-6 w-24 bg-white/10 rounded-lg" />
            </div>
          ))}
        </div>

        {/* Benefit Block */}
        <Card className="bg-[#0f1015] border border-white/10 rounded-2xl p-6 space-y-4">
          <Skeleton className="h-6 w-40 bg-white/10 rounded-lg" />
          <Skeleton className="h-10 w-48 bg-emerald-500/10 rounded-xl" />
          <Skeleton className="h-4 w-full bg-white/10 rounded-md" />
        </Card>

        {/* Eligibility & Documents */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <Card className="bg-[#0f1015] border border-white/10 rounded-2xl p-6 space-y-3">
            <Skeleton className="h-5 w-32 bg-white/10 rounded-lg" />
            <Skeleton className="h-4 w-full bg-white/10 rounded-md" />
            <Skeleton className="h-4 w-3/4 bg-white/10 rounded-md" />
          </Card>
          <Card className="bg-[#0f1015] border border-white/10 rounded-2xl p-6 space-y-3">
            <Skeleton className="h-5 w-32 bg-white/10 rounded-lg" />
            <Skeleton className="h-4 w-full bg-white/10 rounded-md" />
            <Skeleton className="h-4 w-3/4 bg-white/10 rounded-md" />
          </Card>
        </div>
      </main>
    </div>
  );
}
