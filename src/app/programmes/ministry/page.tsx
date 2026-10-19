'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, Building2, Layers, Search, RefreshCw, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface MinistryItem {
  ministry: string;
  programme_count: number;
  government_level: string;
  categories?: string[];
}

export default function MinistryBrowsingPage() {
  const [ministries, setMinistries] = useState<MinistryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    fetch('/api/programmes/ministry')
      .then((res) => res.json())
      .then((data) => {
        setMinistries(data.ministries || []);
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const filtered = ministries.filter((m) =>
    m.ministry.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-[#050510] text-slate-100 pt-24 pb-24 selection:bg-blue-600 selection:text-white">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-6xl">
        <div className="flex items-center justify-between mb-8">
          <Button asChild variant="ghost" className="text-slate-400 hover:text-white -ml-3">
            <Link href="/programmes">
              <ArrowLeft className="w-4 h-4 mr-1.5" /> Back to All Programmes
            </Link>
          </Button>
          <span className="text-xs text-slate-500 font-mono">
            {ministries.length} Ministries & Departments
          </span>
        </div>

        <div className="text-center max-w-2xl mx-auto mb-10">
          <h1 className="text-3xl sm:text-4xl font-black text-white tracking-tight mb-2">
            Programmes by Ministry & Department
          </h1>
          <p className="text-slate-400 text-sm">
            Browse national welfare initiatives and departmental interventions by administering ministry.
          </p>

          <div className="relative max-w-md mx-auto mt-6">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search ministry or department..."
              className="w-full pl-10 pr-4 py-2.5 bg-white/5 border border-white/10 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
            />
          </div>
        </div>

        {loading ? (
          <div className="py-24 text-center">
            <RefreshCw className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-3" />
            <p className="text-slate-400 text-sm">Loading Ministry Directory...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {filtered.map((m) => (
              <div
                key={m.ministry}
                className="bg-[#0a0a1a] hover:bg-[#0c0c22] border border-white/10 hover:border-blue-500/40 rounded-2xl p-5 flex flex-col justify-between transition-all group"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider bg-amber-950/40 text-amber-300 border border-amber-800/30">
                      {m.government_level}
                    </span>
                    <span className="text-sm font-black text-blue-400">
                      {m.programme_count} Schemes
                    </span>
                  </div>

                  <h3 className="text-base font-bold text-white group-hover:text-blue-400 transition-colors mb-3 line-clamp-2">
                    {m.ministry}
                  </h3>

                  {m.categories && m.categories.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-4">
                      {m.categories.map((cat, i) => (
                        <span key={i} className="px-2 py-0.5 rounded text-[10px] bg-white/5 text-slate-400">
                          {cat}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                <Button asChild size="sm" variant="outline" className="w-full bg-white/5 border-white/10 hover:bg-blue-600 hover:text-white rounded-xl text-xs font-semibold">
                  <Link href={`/programmes?ministry=${encodeURIComponent(m.ministry)}`}>
                    View Initiatives <ArrowRight className="w-3.5 h-3.5 ml-1" />
                  </Link>
                </Button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
