'use client';

import Link from 'next/link';
import { Handshake } from 'lucide-react';

export function Footer() {
  return (
    <footer className="bg-muted border-t">
      <div className="container mx-auto py-8 px-4">
        <div className="flex flex-col md:flex-row justify-between items-center">
          <div className="flex items-center space-x-2">
            <Handshake className="h-7 w-7 text-primary" />
            <span className="font-bold text-2xl text-primary">
              CivixAI
            </span>
          </div>
          <p className="text-muted-foreground mt-4 md:mt-0">Smarter benefits, powered by AI.</p>
        </div>
        <div className="mt-8 pt-8 border-t flex flex-col sm:flex-row justify-between items-center">
          <p className="text-sm text-muted-foreground">&copy; {new Date().getFullYear()} CivixAI. All rights reserved.</p>
          <div className="flex gap-4 mt-4 sm:mt-0">
            <Link href="#" className="text-sm text-muted-foreground hover:text-primary">About</Link>
            <Link href="#" className="text-sm text-muted-foreground hover:text-primary">Privacy</Link>
            <Link href="#" className="text-sm text-muted-foreground hover:text-primary">Terms</Link>
            <Link href="#" className="text-sm text-muted-foreground hover:text-primary">Contact</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
