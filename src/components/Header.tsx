'use client';

import Link from 'next/link';
import { Handshake, ArrowLeft } from 'lucide-react';
import { usePathname, useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import Magnetic from './Magnetic';
import { GoogleTranslate } from './GoogleTranslate';

export function Header() {
  const pathname = usePathname();
  const router = useRouter();
  const showBackButton = pathname !== '/';

  return (
    <header className={`fixed top-0 z-50 w-full transition-all duration-300 ${pathname === '/' ? 'bg-[#050510]/50 backdrop-blur-xl border-b border-white/10' : 'sticky bg-[#050510]/90 backdrop-blur-lg border-b border-white/10 shadow-lg'}`}>
      <div className="container mx-auto flex h-20 px-4 sm:px-8 max-w-screen-2xl items-center">
        {showBackButton && (
          <Magnetic>
            <Button variant="ghost" size="icon" className="mr-4 hover:bg-white/10 transition-colors" onClick={() => router.back()}>
              <ArrowLeft className="h-6 w-6 text-white drop-shadow-md" />
              <span className="sr-only">Back</span>
            </Button>
          </Magnetic>
        )}
        <Link href="/" className="mr-8 flex items-center space-x-3 group">
          <div className="p-2 rounded-xl flex items-center justify-center transition-colors bg-white/5 border border-white/10 group-hover:bg-white/10 shadow-[0_0_15px_rgba(59,130,246,0.3)]">
            <Handshake className="h-6 w-6 transition-transform group-hover:scale-110 text-blue-400 drop-shadow-lg" />
          </div>
          <span className="font-black text-2xl tracking-tight text-white drop-shadow-md sm:inline-block">
            CivixAI
          </span>
        </Link>

        {!showBackButton && (
          <nav className="hidden md:flex items-center gap-8 text-sm font-semibold ml-auto mr-4 sm:mr-8">
            <Link href="/#how-it-works" className="transition-colors text-slate-300 hover:text-white uppercase tracking-wider text-xs drop-shadow-sm">
              How It Works
            </Link>
            <Link href="/features" className="transition-colors text-slate-300 hover:text-white uppercase tracking-wider text-xs drop-shadow-sm">
              Features
            </Link>
            <Magnetic>
              <div className="relative group">
                <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full blur opacity-20 group-hover:opacity-60 transition duration-500 animate-pulse pointer-events-none"></div>
                <Button asChild className="relative bg-white/10 border border-white/20 hover:bg-white/20 text-white rounded-full px-6 shadow-2xl backdrop-blur-md transition-all font-bold">
                  <Link href="/check-eligibility">Check Eligibility</Link>
                </Button>
              </div>
            </Magnetic>
          </nav>
        )}

        {/* Language Translator Widget */}
        <div className={pathname === '/' ? 'block ml-4' : 'hidden'}>
          <GoogleTranslate />
        </div>

      </div>
    </header>
  );
}
