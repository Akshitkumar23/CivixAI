'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { Header } from '@/components/Header';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { SearchX, Loader2, Sparkles } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { motion } from 'framer-motion';
import Chatbot from '@/components/Chatbot';
import { Input } from '@/components/ui/input';

interface APIResponse {
  success: boolean;
  eligibleSchemes?: string[];
  schemeDetails?: Array<{
    id?: string;
    name: string;
    eligible: boolean;
    confidence: number;
    threshold: number;
  }>;
  topSchemes?: Array<{
    scheme: string;
    confidence: number;
    threshold: number;
  }>;
  mlPrediction?: boolean;
  mlFallback?: boolean;
  insights?: {
    locationInsights?: any;
    nlpSuggestions?: string[];
    clarifications?: string[];
  };
  error?: string;
}

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
    <Card className="overflow-hidden">
      <div className="h-48 bg-gradient-to-br from-primary/20 to-secondary/20 animate-pulse" />
      <CardContent className="p-6">
        <Skeleton className="h-8 w-3/4 mb-4" />
        <Skeleton className="h-4 w-full mb-2" />
        <Skeleton className="h-4 w-2/3 mb-4" />
        <div className="flex gap-2">
          <Skeleton className="h-8 w-20" />
          <Skeleton className="h-8 w-20" />
        </div>
      </CardContent>
    </Card>
  );
}

function DetailedSchemeCard({ scheme, index, details }: { scheme: any; index: number; details?: any }) {
  const confidence = scheme.confidence || scheme.priority || 50;
  const isEligible = scheme.eligible !== false;
  const priority = scheme.priority || 'medium';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: index * 0.1 }}
    >
      <Card className="bg-card/60 backdrop-blur-md hover:shadow-lg transition-all duration-300 border border-border/60">
        <CardHeader className="pb-4">
          <div className="flex items-start justify-between">
            <div className="space-y-2">
              <div className="flex items-center gap-3">
              <CardTitle className="text-2xl font-bold">{details?.scheme_name || scheme.scheme_name || scheme.id}</CardTitle>
                {isEligible ? (
                  <Badge variant="outline" className="bg-green-500/10 text-green-700 border-green-500/20">
                    Eligible
                  </Badge>
                ) : (
                  <Badge variant="outline" className="bg-red-500/10 text-red-700 border-red-500/20">
                    Not Eligible
                  </Badge>
                )}
              </div>
              <CardDescription className="text-lg">
                {details?.summary || scheme.description || scheme.benefits || 'Detailed scheme information'}
              </CardDescription>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold text-primary">{Math.round(confidence)}%</div>
              <div className="text-sm text-muted-foreground">Confidence</div>
            </div>
          </div>
        </CardHeader>
        
        <CardContent className="space-y-6">
          {/* Confidence Progress Bar */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>AI Confidence Score</span>
              <span>{Math.round(confidence)}%</span>
            </div>
            <Progress value={confidence} className="h-3" />
          </div>

          {/* Priority Indicator */}
          <div className="flex gap-2">
            {priority === 'high' && (
              <Badge className="bg-primary/10 text-primary border border-primary/20">Highly Recommended</Badge>
            )}
            {priority === 'medium' && (
              <Badge className="bg-secondary/30 text-secondary-foreground border border-border/60">Recommended</Badge>
            )}
            {priority === 'low' && (
              <Badge className="bg-muted text-muted-foreground border border-border/60">Consider</Badge>
            )}
          </div>

          <div className="space-y-3 text-sm text-muted-foreground">
            {details?.eligibility_snippets?.length > 0 ? (
              <div>
                <div className="font-semibold text-foreground">Eligibility</div>
                {details.eligibility_snippets.slice(0, 3).map((line: string, i: number) => (
                  <div key={i}>{line}</div>
                ))}
              </div>
            ) : null}

            {details?.benefits_snippets?.length > 0 ? (
              <div>
                <div className="font-semibold text-foreground">Benefits</div>
                {details.benefits_snippets.slice(0, 3).map((line: string, i: number) => (
                  <div key={i}>{line}</div>
                ))}
              </div>
            ) : null}

            {details?.documents_snippets?.length > 0 ? (
              <div>
                <div className="font-semibold text-foreground">Documents</div>
                {details.documents_snippets.slice(0, 3).map((line: string, i: number) => (
                  <div key={i}>{line}</div>
                ))}
              </div>
            ) : null}
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            {details?.source_url ? (
              <Button className="flex-1" asChild>
                <a href={details.source_url} target="_blank" rel="noreferrer">
                  Apply / Learn More
                </a>
              </Button>
            ) : (
              <Button className="flex-1" disabled>
                Apply / Learn More
              </Button>
            )}
            <Button variant="outline" asChild>
              <Link href={`/scheme/${scheme.id}`}>View Details</Link>
            </Button>
            <Button variant="ghost" asChild>
              <Link href={`/check-eligibility`}>Edit Profile</Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

export default function RecommendationsPage() {
  const searchParams = useSearchParams();
  const [apiData, setApiData] = useState<APIResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [latestSources, setLatestSources] = useState<any[]>([]);
  const [structuredSchemes, setStructuredSchemes] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [minConfidence, setMinConfidence] = useState(0);
  const [isExporting, setIsExporting] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);

        const getParam = (key: string) => searchParams?.get(key) || undefined;
        const toBool = (value?: string) => value === 'true';

        // Prepare the request data for ML eligibility API
        const requestData = {
          age: Number(getParam('age')) || undefined,
          income: Number(getParam('income')) || undefined,
          state: getParam('state'),
          category: getParam('category'),
          occupation: getParam('occupation'),
          gender: getParam('gender'),
          hasDisability: toBool(getParam('hasDisability')),
          hasLand: toBool(getParam('hasLand')),
          familyIncome: Number(getParam('familyIncome')) || 0,
          landSize: Number(getParam('landSize')) || 0,
          familySize: Number(getParam('familySize')) || 1,
          isSingleGirlChild: toBool(getParam('isSingleGirlChild')),
          isWidowOrSenior: toBool(getParam('isWidowOrSenior')),
          isTaxPayer: toBool(getParam('isTaxPayer')),
          isBankLinked: toBool(getParam('isBankLinked')),
          educationLevel: getParam('educationLevel') || '',
          digitalLiteracy: getParam('digitalLiteracy') || '',
          urbanRural: getParam('urbanRural') || '',
          monthlyExpenses: Number(getParam('monthlyExpenses')) || 0,
          hasSmartphone: toBool(getParam('hasSmartphone')),
          hasInternet: toBool(getParam('hasInternet')),
          employmentType: getParam('employmentType') || '',
          skillCertification: getParam('skillCertification') || '',
          loanRequirement: getParam('loanRequirement') || 'none',
          monthlySavings: Number(getParam('monthlySavings')) || 0,
          hasInsurance: toBool(getParam('hasInsurance')),
          hasPension: toBool(getParam('hasPension'))
        };

        // Call the ML eligibility API
        const response = await fetch('/api/test-mock', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestData),
        });

        if (!response.ok) {
          throw new Error(`API Error: ${response.status}`);
        }

        const data = await response.json();
        setApiData(data);
      } catch (err) {
        console.error('Error fetching recommendations:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch recommendations');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [searchParams]);

  useEffect(() => {
    const fetchSources = async () => {
      try {
        // Load scraped schemes data
        const response = await fetch('/api/schemes?file=schemes_update_20260204_222630.json');
        if (response.ok) {
          const rawData = await response.json();
          // Process the scraped data to get source information
          const sources = rawData
            .filter(item => item.extraction_status === 'ok' && item.source_url)
            .slice(0, 6)
            .map(item => ({
              domain: item.domain,
              source_url: item.source_url,
              content_type: item.content_type,
              priority: item.priority,
              scheme_name: item.scheme_name,
              summary: item.summary
            }));
          setLatestSources(sources);
        }
      } catch (error) {
        console.warn('Failed to load scraped sources:', error);
        setLatestSources([]);
      }
    };
    fetchSources();
  }, []);

  useEffect(() => {
    const fetchStructured = async () => {
      try {
        // Load scraped schemes data for structured information
        const response = await fetch('/api/schemes?file=schemes_update_20260204_222630.json');
        if (response.ok) {
          const rawData = await response.json();
          // Process the scraped data to get structured scheme information
          const structured = rawData
            .filter(item => item.extraction_status === 'ok' && item.scheme_name)
            .map(item => ({
              scheme_name: item.scheme_name,
              source_url: item.source_url,
              summary: item.summary,
              eligibility_snippets: item.eligibility_snippets || [],
              benefits_snippets: item.benefits_snippets || [],
              documents_snippets: item.documents_snippets || []
            }));
          setStructuredSchemes(structured);
        }
      } catch (error) {
        console.warn('Failed to load structured schemes:', error);
        setStructuredSchemes([]);
      }
    };
    fetchStructured();
  }, []);

  const handleExport = () => {
    setIsExporting(true);
    try {
      const payload = filteredSchemes.map(s => ({
        id: s.id,
        confidence: s.confidence,
        priority: s.priority,
        eligible: s.eligible,
        details: structuredById.get(s.id) || null
      }));
      const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'eligible_schemes.json';
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setIsExporting(false);
    }
  };

  const normalizeConfidence = (value?: number) => {
    if (typeof value !== 'number') return 50;
    return value <= 1 ? value * 100 : value;
  };

  const toPriority = (confidence: number) => {
    if (confidence >= 80) return 'high';
    if (confidence >= 60) return 'medium';
    return 'low';
  };

  const toSlug = (text: string) =>
    (text || '')
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '_')
      .replace(/^_+|_+$/g, '')
      .slice(0, 60) || 'scheme';

  const structuredById = useMemo(() => {
    return new Map(
      structuredSchemes.map(s => [
        toSlug(s.scheme_name || s.source_url || ''),
        s
      ])
    );
  }, [structuredSchemes]);

  type ModelItem = {
    key: string;
    eligible: boolean;
    confidence?: number;
    threshold?: number;
  };

  const modelItems: ModelItem[] =
    apiData?.schemeDetails && apiData.schemeDetails.length > 0
      ? apiData.schemeDetails.map(item => ({
          key: item.id || item.name,
          eligible: item.eligible,
          confidence: item.confidence,
          threshold: item.threshold
        }))
      : apiData?.topSchemes && apiData.topSchemes.length > 0
      ? apiData.topSchemes.map(item => ({
          key: item.scheme,
          eligible: true,
          confidence: item.confidence,
          threshold: item.threshold
        }))
      : (apiData?.eligibleSchemes || []).map(name => ({
          key: name,
          eligible: true
        }));

  const schemes = modelItems.map(item => {
    const schemeName = item.key;
    const confidence = normalizeConfidence(item.confidence);
    const eligible = item.eligible !== false;
    return {
      id: item.key,
      scheme_name: schemeName,
      confidence,
      priority: eligible ? toPriority(confidence) : 'low',
      eligible
    };
  });

  const dedupedSchemes = Array.from(
    new Map(schemes.map(s => [s.id, s])).values()
  );

  const rankedSchemes = dedupedSchemes
    .sort((a, b) => (b.confidence || 0) - (a.confidence || 0));

  const eligibleOnlySchemes = rankedSchemes.filter(s => s.eligible);

  const filteredSchemes = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    return eligibleOnlySchemes.filter(s => {
      if (s.confidence < minConfidence) return false;
      if (!q) return true;
      const details = structuredById.get(s.id);
      const name = (details?.scheme_name || s.scheme_name || '').toLowerCase();
      const summary = (details?.summary || '').toLowerCase();
      return name.includes(q) || summary.includes(q);
    });
  }, [eligibleOnlySchemes, minConfidence, searchQuery, structuredById]);

  if (loading) {
    return (
      <div className="flex flex-col min-h-screen bg-background">
        <Header />
        <main className="flex-grow bg-muted">
          <section className="container mx-auto px-4 py-10 sm:py-14">
            <div className="text-center mb-8">
              <div className="flex justify-center mb-4">
                <Loader2 className="h-12 w-12 animate-spin text-primary" />
              </div>
              <h1 className="font-headline text-4xl sm:text-5xl font-bold text-primary">Analyzing Your Profile</h1>
              <p className="mt-4 max-w-2xl mx-auto text-lg text-muted-foreground">
                Our AI is processing your information to find the best government schemes for you...
              </p>
            </div>
            <RecommendationsSkeleton />
          </section>
        </main>
        <Chatbot />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col min-h-screen bg-background">
        <Header />
        <main className="flex-grow bg-muted">
          <section className="container mx-auto px-4 py-10 sm:py-14">
            <div className="flex flex-col items-center justify-center text-center py-20">
              <Alert className="max-w-lg bg-card/60 backdrop-blur-md">
                <SearchX className="h-4 w-4" />
                <AlertTitle className="font-headline">Error Loading Recommendations</AlertTitle>
                <AlertDescription>
                  {error}
                </AlertDescription>
              </Alert>
              <Button asChild variant="link" className="mt-4">
                <Link href="/check-eligibility">Try again</Link>
              </Button>
            </div>
          </section>
        </main>
        <Chatbot />
      </div>
    );
  }

  if (!apiData?.success || eligibleOnlySchemes.length === 0) {
    return (
      <div className="flex flex-col min-h-screen bg-background">
        <Header />
        <main className="flex-grow bg-muted">
          <section className="container mx-auto px-4 py-10 sm:py-14">
            <div className="flex flex-col items-center justify-center text-center py-20">
              <Alert className="max-w-lg bg-card/60 backdrop-blur-md">
                <SearchX className="h-4 w-4" />
                <AlertTitle className="font-headline">No Schemes Found</AlertTitle>
                <AlertDescription>
                  Based on your profile, we couldn't find any matching government schemes at the moment.
                  Please try with different information or check back later.
                </AlertDescription>
              </Alert>
              <Button asChild variant="link" className="mt-4">
                <Link href="/check-eligibility">Try with different details</Link>
              </Button>
            </div>
          </section>
        </main>
        <Chatbot />
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen bg-background">
      <Header />
      <main className="flex-grow bg-muted">
        <section className="container mx-auto px-4 py-10 sm:py-14">
          <div className="mb-8 text-center">
          <h1 className="font-headline text-4xl sm:text-5xl font-bold text-primary">Your Scheme Recommendations</h1>
          <p className="mt-4 max-w-2xl mx-auto text-lg text-muted-foreground">
            Based on your profile, we analyzed {schemes.length} schemes and found the best eligible matches for you.
          </p>
          <div className="mt-4 flex justify-center">
            {apiData?.mlFallback ? (
              <Badge variant="outline" className="bg-yellow-500/10 text-yellow-700 border-yellow-500/20">
                Fallback Used
              </Badge>
            ) : apiData?.mlPrediction ? (
              <Badge variant="outline" className="bg-green-500/10 text-green-700 border-green-500/20">
                ML Prediction
              </Badge>
            ) : null}
          </div>
          
          {/* Quick Stats */}
          <div className="mt-6 flex justify-center gap-6 text-center">
            <div>
              <div className="text-2xl font-bold text-primary">{filteredSchemes.length}</div>
              <div className="text-sm text-muted-foreground">Eligible</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600">{schemes.length}</div>
              <div className="text-sm text-muted-foreground">Analyzed</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-yellow-600">
                {filteredSchemes.filter(s => s.priority === 'high').length}
              </div>
              <div className="text-sm text-muted-foreground">High Priority</div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="grid gap-8 lg:grid-cols-3">
          {/* Recommendations Grid */}
          <div className="lg:col-span-2 space-y-6">
            <Card className="bg-card/60 backdrop-blur-md">
              <CardHeader>
                <CardTitle>Filter Eligible Schemes</CardTitle>
                <CardDescription>Search by name/summary and set minimum confidence</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Input
                  placeholder="Search schemes..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Minimum Confidence</span>
                    <span>{minConfidence}%</span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={100}
                    step={5}
                    value={minConfidence}
                    onChange={(e) => setMinConfidence(Number(e.target.value))}
                    className="w-full"
                  />
                </div>
                <Button
                  onClick={handleExport}
                  disabled={filteredSchemes.length === 0 || isExporting}
                  className="w-full"
                >
                  {isExporting ? 'Exporting...' : 'Export Eligible Schemes'}
                </Button>
              </CardContent>
            </Card>
            {filteredSchemes.length === 0 ? (
              <Card className="bg-card/60 backdrop-blur-md">
                <CardContent className="py-8 text-center text-sm text-muted-foreground">
                  No schemes match your current filters. Try lowering the confidence or clearing the search.
                </CardContent>
              </Card>
            ) : null}
            <div className="grid gap-6 md:grid-cols-1 lg:grid-cols-2">
              {filteredSchemes.map((scheme, index) => (
                <DetailedSchemeCard
                  key={scheme.id}
                  scheme={scheme}
                  index={index}
                  details={structuredById.get(scheme.id)}
                />
              ))}
            </div>
          </div>

          {/* Sidebar with Additional Info */}
          <div className="lg:col-span-1 space-y-6">
            {/* AI Insights */}
            <Card className="bg-card/60 backdrop-blur-md">
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  <Sparkles className="h-6 w-6 text-primary" />
                  AI Insights
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {apiData?.insights?.clarifications && apiData.insights.clarifications.length > 0 && (
                  <div className="space-y-2">
                    <h4 className="font-semibold">Clarifications Needed</h4>
                    {apiData.insights.clarifications.map((clarification, idx) => (
                      <p key={idx} className="text-sm text-muted-foreground bg-yellow-500/10 p-3 rounded">
                        {clarification}
                      </p>
                    ))}
                  </div>
                )}
                
                {apiData?.insights?.nlpSuggestions && apiData.insights.nlpSuggestions.length > 0 && (
                  <div className="space-y-2">
                    <h4 className="font-semibold">AI Suggestions</h4>
                    {apiData.insights.nlpSuggestions.map((suggestion, idx) => (
                      <p key={idx} className="text-sm text-muted-foreground bg-green-500/10 p-3 rounded">
                        {suggestion}
                      </p>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Location Insights */}
            {apiData?.insights?.locationInsights && (
              <Card className="bg-card/60 backdrop-blur-md">
                <CardHeader>
                  <CardTitle className="flex items-center gap-3">
                    <Sparkles className="h-6 w-6 text-primary" />
                    Location Analysis
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-sm">
                    <p><strong>Location Type:</strong> {apiData.insights.locationInsights.location_type}</p>
                    <p><strong>Infrastructure:</strong> {apiData.insights.locationInsights.infrastructure_quality}</p>
                    <p><strong>Scheme Availability:</strong> {apiData.insights.locationInsights.scheme_availability}</p>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Quick Actions */}
            <Card className="bg-card/60 backdrop-blur-md">
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button className="w-full" asChild>
                  <Link href="/check-eligibility">Check More Schemes</Link>
                </Button>
                <Button variant="outline" className="w-full" asChild>
                  <Link href="/features">Learn About Our AI</Link>
                </Button>
                <Button variant="ghost" className="w-full" asChild>
                  <Link href="/chatbot">Chat with AI Assistant</Link>
                </Button>
              </CardContent>
            </Card>

            {/* Latest Official Sources */}
            <Card className="bg-card/60 backdrop-blur-md">
              <CardHeader>
                <CardTitle>Latest Official Sources</CardTitle>
                <CardDescription>Freshly discovered government sources</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {latestSources.length === 0 ? (
                  <div className="text-sm text-muted-foreground">No sources available yet.</div>
                ) : (
                  latestSources.map((source, idx) => (
                    <div key={idx} className="text-sm">
                      <div className="font-medium">{source.domain}</div>
                      <a
                        className="text-muted-foreground truncate block"
                        href={source.source_url}
                        target="_blank"
                        rel="noreferrer"
                      >
                        {source.source_url}
                      </a>
                      <div className="text-xs text-muted-foreground">
                        {source.content_type.toUpperCase()} · {source.priority}
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>
        </div>
        </section>
      </main>
      <Chatbot />
    </div>
  );
}

