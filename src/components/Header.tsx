'use client';

import Link from 'next/link';
import { Handshake, ArrowLeft } from 'lucide-react';
import { usePathname, useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import Magnetic from './Magnetic';

export function Header() {
  const pathname = usePathname();
  const router = useRouter();
  const showBackButton = pathname !== '/';

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 max-w-screen-2xl items-center">
        {showBackButton && (
          <Magnetic>
            <Button variant="ghost" size="icon" className="mr-2" onClick={() => router.back()}>
              <ArrowLeft className="h-6 w-6 text-primary" />
              <span className="sr-only">Back</span>
            </Button>
          </Magnetic>
        )}
        <Link href="/" className="mr-6 flex items-center space-x-2">
            <Handshake className="h-6 w-6 text-primary" />
            <span className="font-bold font-headline text-xl text-primary sm:inline-block">
              CivixAI
            </span>
        </Link>
        
        {!showBackButton && (
          <nav className="hidden md:flex items-center gap-6 text-sm ml-auto">
            <Link href="/#how-it-works" className="transition-colors hover:text-primary text-foreground/80">
                How It Works
            </Link>
            <Link href="/features" className="transition-colors hover:text-primary text-foreground/80">
                Features
            </Link>
            <Magnetic>
                <Button asChild>
                    <Link href="/check-eligibility">Get Started</Link>
                </Button>
            </Magnetic>
          </nav>
        )}
      </div>
    </header>
  );
}
