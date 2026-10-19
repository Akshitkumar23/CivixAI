'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, MapPin, Building2, Layers, Search, RefreshCw, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface StateItem {
  state_name: string;
  total: number;
  central_contributing: number;
  state_ut_dedicated: number;
  jurisdiction: string;
  top_categories?: string[];
}

export default function StateBrowsingPage() {
  const [states, setStates] = useState<StateItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    fetch('/api/programmes/state')
      .then((res) => res.json())
      .then((data) => {
        setStates(data.states || []);
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const filtered = states.filter((s) =>
    s.state_name.toLowerCase().includes(search.toLowerCase())
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
            {states.length} States & UTs Represented
          </span>
        </div>

        <div className="text-center max-w-2xl mx-auto mb-10">
          <h1 className="text-3xl sm:text-4xl font-black text-white tracking-tight mb-2">
            Programmes by State & Union Territory
          </h1>
          <p className="text-slate-400 text-sm">
            Explore dedicated state welfare programmes and central schemes operating within each jurisdiction.
          </p>

          <div className="relative max-w-md mx-auto mt-6">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search state or union territory..."
              className="w-full pl-10 pr-4 py-2.5 bg-white/5 border border-white/10 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
            />
          </div>
        </div>

        {loading ? (
          <div className="py-24 text-center">
            <RefreshCw className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-3" />
            <p className="text-slate-400 text-sm">Loading State Breakdown...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {filtered.map((st) => (
              <div
                key={st.state_name}
                className="bg-[#0a0a1a] hover:bg-[#0c0c22] border border-white/10 hover:border-blue-500/40 rounded-2xl p-5 flex flex-col justify-between transition-all group"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider bg-indigo-950/50 text-indigo-300 border border-indigo-700/40">
                      {st.jurisdiction}
                    </span>
                    <span className="text-sm font-black text-blue-400">
                      {st.total.toLocaleString()} Schemes
                    </span>
                  </div>

                  <h3 className="text-lg font-bold text-white group-hover:text-blue-400 transition-colors mb-2">
                    {st.state_name}
                  </h3>

                  <div className="grid grid-cols-2 gap-2 text-xs text-slate-400 mb-4 pt-2 border-t border-white/5">
                    <div>
                      <span className="text-slate-500 block text-[10px]">State/UT Dedicated</span>
                      <span className="text-slate-200 font-semibold">{st.state_ut_dedicated}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[10px]">Central Contributing</span>
                      <span className="text-slate-200 font-semibold">{st.central_contributing}</span>
                    </div>
                  </div>

                  {st.top_categories && st.top_categories.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-4">
                      {st.top_categories.map((cat, i) => (
                        <span key={i} className="px-2 py-0.5 rounded text-[10px] bg-white/5 text-slate-400">
                          {cat}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                <Button asChild size="sm" variant="outline" className="w-full bg-white/5 border-white/10 hover:bg-blue-600 hover:text-white rounded-xl text-xs font-semibold">
                  <Link href={`/programmes?state=${encodeURIComponent(st.state_name)}`}>
                    Explore Schemes in {st.state_name} <ArrowRight className="w-3.5 h-3.5 ml-1" />
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
