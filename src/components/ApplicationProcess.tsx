'use client';

import { useState } from 'react';
import { getApplicationSummary } from '@/lib/actions';
import type { Scheme } from '@/lib/types';
import { Button } from '@/components/ui/button';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { Loader2, ChevronsUpDown } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from './ui/alert';

type ApplicationProcessProps = {
  scheme: Scheme;
};

export function ApplicationProcess({ scheme }: ApplicationProcessProps) {
  const [summary, setSummary] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);

  const handleGeneration = async () => {
    if (summary) {
        setIsOpen(!isOpen);
        return;
    };
    
    setIsLoading(true);
    setError(null);
    setIsOpen(true);
    try {
      const result = await getApplicationSummary(scheme);
      setSummary(result);
    } catch (e) {
      setError('Failed to generate application details. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen} className="w-full space-y-2">
      <CollapsibleTrigger asChild>
        <Button
          onClick={handleGeneration}
          variant="outline"
          className="w-full"
          disabled={isLoading}
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Generating Details...
            </>
          ) : (
            <>
              Application Process
              <ChevronsUpDown className="ml-auto h-4 w-4" />
            </>
          )}
        </Button>
      </CollapsibleTrigger>
      <CollapsibleContent>
        {summary && (
          <div className="prose prose-sm dark:prose-invert max-w-none mt-4 rounded-md border p-4 text-sm">
            <h4 className='font-headline'>Summary of Application Process</h4>
            <p>{summary}</p>
          </div>
        )}
        {error && (
            <Alert variant="destructive" className="mt-4">
                <AlertTitle>Error</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
            </Alert>
        )}
      </CollapsibleContent>
    </Collapsible>
  );
}
