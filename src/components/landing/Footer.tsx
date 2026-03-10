'use client';

import Link from 'next/link';
import { Handshake } from 'lucide-react';

export function Footer() {
  return (
    <footer className="bg-transparent border-t border-white/10 relative z-10 backdrop-blur-sm">
      <div className="container mx-auto py-12 px-4 sm:px-8 max-w-screen-2xl">
        <div className="flex flex-col md:flex-row justify-between items-center">
          <div className="flex items-center space-x-3 group cursor-pointer">
            <div className="w-10 h-10 rounded-xl bg-white/5 border border-white/20 flex items-center justify-center transition-colors shadow-inner">
              <Handshake className="h-5 w-5 text-blue-400 group-hover:scale-110 transition-transform" />
            </div>
            <span className="font-extrabold text-2xl text-white tracking-tight drop-shadow-md">
              CivixAI
            </span>
          </div>
          <p className="text-slate-400 font-medium mt-6 md:mt-0 text-sm drop-shadow-sm">Smarter benefits, powered by AI.</p>
        </div>
        <div className="mt-10 pt-8 border-t border-white/10 flex flex-col sm:flex-row justify-between items-center">
          <p className="text-sm text-slate-500">&copy; {new Date().getFullYear()} CivixAI. All rights reserved.</p>
          <div className="flex gap-6 mt-6 sm:mt-0">
            <Link href="#" className="text-sm font-medium text-slate-400 hover:text-white transition-colors tracking-wide">About</Link>
            <Link href="#" className="text-sm font-medium text-slate-400 hover:text-white transition-colors tracking-wide">Privacy</Link>
            <Link href="#" className="text-sm font-medium text-slate-400 hover:text-white transition-colors tracking-wide">Terms</Link>
            <Link href="#" className="text-sm font-medium text-slate-400 hover:text-white transition-colors tracking-wide">Contact</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
