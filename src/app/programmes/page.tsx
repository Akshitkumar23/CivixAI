'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { 
  Search, Filter, ChevronLeft, ChevronRight, ExternalLink, 
  ShieldCheck, AlertCircle, Building2, MapPin, Layers,
  CheckCircle2, FileText, ArrowRight, X, RefreshCw,
  Sparkles, Globe2, Briefcase, HelpCircle, ChevronDown
} from 'lucide-react';
import { Button } from '@/components/ui/button';

interface ProgrammeItem {
  programme_id: string;
  canonical_name: string;
  programme_type: string;
  government_level: string;
  jurisdiction: string;
  authority?: string;
  ministry?: string;
  department?: string;
  category: string;
  state_or_ut?: string;
  beneficiary_type: string;
  description?: string;
  benefit_summary?: string;
  eligibility_status: string;
  eligibility_status_label: string;
  applicability: string;
  source_url?: string;
  last_verified_at?: string;
  certified: boolean;
}

interface FilterCounts {
  categories: Record<string, number>;
  states_and_uts: Record<string, number>;
  jurisdictions: Record<string, number>;
  ministries: Record<string, number>;
  programme_types: Record<string, number>;
  applicabilities: Record<string, number>;
  eligibility_statuses: Record<string, number>;
  total_programmes: number;
  certified_recommendation_pool: number;
}

export default function ProgrammesDiscoveryPage() {
  const [items, setItems] = useState<ProgrammeItem[]>([]);
  const [total, setTotal] = useState<number | null>(null);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(24);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);

  // Search & Filter State
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedJurisdiction, setSelectedJurisdiction] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedState, setSelectedState] = useState('');
  const [selectedEligibilityStatus, setSelectedEligibilityStatus] = useState('');
  const [selectedSort, setSelectedSort] = useState('name_asc');
  const [mobileFilterOpen, setMobileFilterOpen] = useState(false);

  // Dynamic filter metadata from DB
  const [filterMeta, setFilterMeta] = useState<FilterCounts | null>(null);

  // Fetch filter metadata once on load
  useEffect(() => {
    fetch('/api/programmes/filters')
      .then((res) => res.json())
      .then((data) => {
        if (data && data.total_programmes) {
          setFilterMeta(data);
        }
      })
      .catch((err) => console.error('Failed to load filter metadata', err));
  }, []);

  // Fetch Programmes from API
  const fetchProgrammes = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (searchQuery.trim()) params.set('q', searchQuery.trim());
      if (selectedJurisdiction) params.set('jurisdiction', selectedJurisdiction);
      if (selectedCategory) params.set('category', selectedCategory);
      if (selectedState) params.set('state', selectedState);
      if (selectedEligibilityStatus) params.set('eligibility_status', selectedEligibilityStatus);
      if (selectedSort) params.set('sort', selectedSort);
      params.set('page', page.toString());
      params.set('page_size', pageSize.toString());

      const res = await fetch(`/api/programmes?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setItems(data.items || []);
        setTotal(data.total);
        setTotalPages(data.total_pages || 1);
      }
    } catch (err) {
      console.error('Failed to load programmes', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchProgrammes();
    }, 250);
    return () => clearTimeout(timer);
  }, [searchQuery, selectedJurisdiction, selectedCategory, selectedState, selectedEligibilityStatus, selectedSort, page, pageSize]);

  const resetFilters = () => {
    setSearchQuery('');
    setSelectedJurisdiction('');
    setSelectedCategory('');
    setSelectedState('');
    setSelectedEligibilityStatus('');
    setSelectedSort('name_asc');
    setPage(1);
  };

  const getStatusBadge = (item: ProgrammeItem) => {
    const status = item.eligibility_status;
    const isCert = item.certified || status === 'ELIGIBILITY_READY';

    if (isCert) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-950/60 text-emerald-300 border border-emerald-500/40 shadow-[0_0_10px_rgba(16,185,129,0.2)]">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" /> ✓ Eligibility verified
        </span>
      );
    }
    if (status === 'ELIGIBILITY_REVIEW') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-indigo-950/60 text-indigo-300 border border-indigo-500/30">
          <Sparkles className="w-3.5 h-3.5 text-indigo-400" /> Eligibility review pending
        </span>
      );
    }
    if (status === 'INSUFFICIENT_OFFICIAL_EVIDENCE') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-900 text-slate-400 border border-slate-800">
          <AlertCircle className="w-3.5 h-3.5 text-slate-500" /> Official evidence unavailable
        </span>
      );
    }
    if (status === 'INSTITUTIONAL_ONLY' || status === 'EMPLOYER_ONLY' || item.programme_type.includes('INSTITUTIONAL') || item.programme_type.includes('EMPLOYER')) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-950/50 text-rose-300 border border-rose-800/40">
          <Building2 className="w-3.5 h-3.5 text-rose-400" /> Institution / Employer programme
        </span>
      );
    }
    if (status === 'INFORMATIONAL') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-sky-950/50 text-sky-300 border border-sky-800/30">
          <HelpCircle className="w-3.5 h-3.5 text-sky-400" /> Informational
        </span>
      );
    }
    if (status === 'SERVICE' || item.programme_type.includes('SERVICE')) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-cyan-950/50 text-cyan-300 border border-cyan-800/30">
          <Globe2 className="w-3.5 h-3.5 text-cyan-400" /> Service
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-900 text-slate-400 border border-slate-800">
        <AlertCircle className="w-3.5 h-3.5 text-slate-500" /> {item.eligibility_status_label}
      </span>
    );
  };

  const getCardCta = (item: ProgrammeItem) => {
    const status = item.eligibility_status;
    const isCert = item.certified || status === 'ELIGIBILITY_READY';

    if (isCert) {
      return (
        <Button asChild size="sm" className="bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold shadow-lg shadow-emerald-500/20">
          <Link href={`/check-eligibility?scheme=${item.programme_id}`}>
            Check Eligibility <ArrowRight className="w-3.5 h-3.5 ml-1" />
          </Link>
        </Button>
      );
    }
    if (status === 'ELIGIBILITY_REVIEW') {
      return (
        <Button asChild size="sm" variant="outline" className="border-indigo-500/40 bg-indigo-950/30 hover:bg-indigo-900/50 text-indigo-300 rounded-xl text-xs font-semibold">
          <Link href={`/programmes/${item.programme_id}`}>
            View Eligibility Criteria <ArrowRight className="w-3.5 h-3.5 ml-1" />
          </Link>
        </Button>
      );
    }
    if (status === 'INSUFFICIENT_OFFICIAL_EVIDENCE') {
      return (
        <Button asChild size="sm" variant="ghost" className="text-slate-400 hover:text-white hover:bg-white/5 rounded-xl text-xs">
          <Link href={`/programmes/${item.programme_id}`}>
            View Official Information <ArrowRight className="w-3.5 h-3.5 ml-1" />
          </Link>
        </Button>
      );
    }
    if (status === 'INSTITUTIONAL_ONLY' || status === 'EMPLOYER_ONLY') {
      return (
        <Button asChild size="sm" variant="ghost" className="text-slate-400 hover:text-white hover:bg-white/5 rounded-xl text-xs">
          <Link href={`/programmes/${item.programme_id}`}>
            View Programme <ArrowRight className="w-3.5 h-3.5 ml-1" />
          </Link>
        </Button>
      );
    }
    return (
      <Button asChild size="sm" variant="ghost" className="text-slate-400 hover:text-white hover:bg-white/5 rounded-xl text-xs">
        <Link href={`/programmes/${item.programme_id}`}>
          View Details <ArrowRight className="w-3.5 h-3.5 ml-1" />
        </Link>
      </Button>
    );
  };

  const topCategories = filterMeta?.categories ? Object.keys(filterMeta.categories).slice(0, 10) : [
    'Agriculture', 'Education & Learning', 'Social Welfare', 'Health & Wellness',
    'Financial Services', 'Women and Child', 'Skills & Employment', 'Housing & Shelter'
  ];

  return (
    <div className="min-h-screen bg-[#050510] text-slate-100 pt-24 pb-24 selection:bg-blue-600 selection:text-white">
      {/* Background Glow */}
      <div className="fixed inset-0 pointer-events-none -z-10">
        <div className="absolute top-10 left-1/2 -translate-x-1/2 w-[1100px] h-[350px] bg-blue-600/10 blur-[130px] rounded-full"></div>
      </div>

      <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-7xl">
        {/* Header Section */}
        <div className="text-center max-w-3xl mx-auto mb-8">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs font-semibold text-blue-400 mb-4 backdrop-blur-md">
            <Globe2 className="w-3.5 h-3.5" /> India-Wide Government Scheme Universe
          </div>
          <h1 className="text-3xl sm:text-5xl font-black text-white tracking-tight mb-3">
            Government Programmes
          </h1>
          <p className="text-slate-400 text-sm sm:text-base leading-relaxed">
            Explore government schemes and programmes from across India.
          </p>

          {/* Live Count & Separation Banner (Section 10) */}
          <div className="mt-5 p-3.5 rounded-2xl bg-[#0a0a1e] border border-blue-500/20 flex flex-wrap items-center justify-center gap-4 text-xs sm:text-sm text-slate-300 shadow-xl">
            <span className="flex items-center gap-2 font-bold text-white">
              <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
              {total !== null ? `${total.toLocaleString()} programmes discovered` : '5,742 programmes discovered'}
            </span>
            <span className="text-slate-600 hidden sm:inline">|</span>
            <span className="flex items-center gap-2 text-emerald-400 font-semibold">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              27 currently eligibility-verified for automated checking
            </span>
          </div>
        </div>

        {/* Directory Navigation Links */}
        <div className="flex items-center justify-center gap-3 mb-8">
          <Button asChild variant="outline" size="sm" className="bg-white/5 border-white/10 hover:bg-white/10 text-slate-300 rounded-xl text-xs">
            <Link href="/programmes/state">
              <MapPin className="w-3.5 h-3.5 mr-1.5 text-indigo-400" /> Browse by State / UT
            </Link>
          </Button>
          <Button asChild variant="outline" size="sm" className="bg-white/5 border-white/10 hover:bg-white/10 text-slate-300 rounded-xl text-xs">
            <Link href="/programmes/ministry">
              <Building2 className="w-3.5 h-3.5 mr-1.5 text-amber-400" /> Browse by Ministry
            </Link>
          </Button>
        </div>

        {/* Search & Main Controls Bar */}
        <div className="bg-[#0a0a1a] border border-white/10 rounded-2xl p-4 sm:p-5 mb-8 shadow-2xl backdrop-blur-xl">
          <div className="flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between mb-4">
            {/* Search Input */}
            <div className="relative flex-1">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => { setSearchQuery(e.target.value); setPage(1); }}
                placeholder="Search by scheme name, keyword, authority, or ministry..."
                className="w-full pl-10 pr-10 py-2.5 bg-white/5 border border-white/10 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>

            {/* Quick Sort & Page Size Controls */}
            <div className="flex items-center gap-2.5">
              <select
                value={selectedSort}
                onChange={(e) => { setSelectedSort(e.target.value); setPage(1); }}
                className="bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
              >
                <option value="name_asc" className="bg-slate-900">Name (A to Z)</option>
                <option value="name_desc" className="bg-slate-900">Name (Z to A)</option>
                <option value="recently_verified" className="bg-slate-900">Recently Verified</option>
                <option value="jurisdiction" className="bg-slate-900">Government Level</option>
                <option value="category" className="bg-slate-900">Category</option>
              </select>

              <select
                value={pageSize}
                onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1); }}
                className="bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
              >
                <option value="12" className="bg-slate-900">12 / page</option>
                <option value="24" className="bg-slate-900">24 / page</option>
                <option value="48" className="bg-slate-900">48 / page</option>
                <option value="100" className="bg-slate-900">100 / page</option>
              </select>

              <Button
                variant="outline"
                size="sm"
                onClick={() => setMobileFilterOpen(!mobileFilterOpen)}
                className="md:hidden bg-white/5 border-white/10 text-white rounded-xl text-xs"
              >
                <Filter className="w-3.5 h-3.5 mr-1" /> Filters
              </Button>
            </div>
          </div>

          {/* Filter Pills Bar */}
          <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-white/5 text-xs">
            <span className="text-slate-500 font-semibold mr-1">Level:</span>
            {['', 'CENTRAL', 'STATE', 'UT'].map((jur) => (
              <button
                key={jur}
                onClick={() => { setSelectedJurisdiction(jur); setPage(1); }}
                className={`px-3 py-1 rounded-full transition-all ${
                  selectedJurisdiction === jur
                    ? 'bg-blue-600 text-white font-bold shadow-md shadow-blue-500/20'
                    : 'bg-white/5 text-slate-400 hover:text-white hover:bg-white/10'
                }`}
              >
                {jur === '' ? 'All Levels' : (jur === 'CENTRAL' ? 'Central' : (jur === 'STATE' ? 'State' : 'UT'))}
              </button>
            ))}

            <span className="text-slate-500 font-semibold ml-3 mr-1">Status:</span>
            {[
              { val: '', label: 'All' },
              { val: 'ELIGIBILITY_READY', label: 'Verified (27)' },
              { val: 'ELIGIBILITY_REVIEW', label: 'Under Review' },
              { val: 'INSUFFICIENT_OFFICIAL_EVIDENCE', label: 'Evidence Unavailable' },
            ].map((st) => (
              <button
                key={st.val}
                onClick={() => { setSelectedEligibilityStatus(st.val); setPage(1); }}
                className={`px-3 py-1 rounded-full transition-all ${
                  selectedEligibilityStatus === st.val
                    ? 'bg-indigo-600 text-white font-bold shadow-md shadow-indigo-500/20'
                    : 'bg-white/5 text-slate-400 hover:text-white hover:bg-white/10'
                }`}
              >
                {st.label}
              </button>
            ))}

            {(selectedJurisdiction || selectedCategory || selectedState || selectedEligibilityStatus || searchQuery) && (
              <button
                onClick={resetFilters}
                className="ml-auto text-rose-400 hover:text-rose-300 font-medium flex items-center gap-1"
              >
                <X className="w-3.5 h-3.5" /> Clear Filters
              </button>
            )}
          </div>

          {/* Category Horizontal Scroll / Pills */}
          <div className="flex items-center gap-2 overflow-x-auto py-2.5 mt-2 scrollbar-none text-xs">
            <span className="text-slate-500 font-semibold shrink-0">Category:</span>
            <button
              onClick={() => { setSelectedCategory(''); setPage(1); }}
              className={`px-2.5 py-1 rounded-lg shrink-0 transition-all ${
                selectedCategory === ''
                  ? 'bg-white/20 text-white font-bold'
                  : 'bg-white/5 text-slate-400 hover:text-white'
              }`}
            >
              All Categories
            </button>
            {topCategories.map((cat) => (
              <button
                key={cat}
                onClick={() => { setSelectedCategory(cat === selectedCategory ? '' : cat); setPage(1); }}
                className={`px-2.5 py-1 rounded-lg shrink-0 transition-all ${
                  selectedCategory === cat
                    ? 'bg-blue-600 text-white font-bold shadow-sm'
                    : 'bg-white/5 text-slate-400 hover:text-white hover:bg-white/10'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Active Filter Summary Bar */}
        <div className="flex items-center justify-between mb-6 text-xs text-slate-400 px-1">
          <div>
            Showing <span className="font-bold text-white">{items.length}</span> of{' '}
            <span className="font-bold text-white">{total !== null ? total.toLocaleString() : '...'}</span> programmes
            {searchQuery && <span> matching &quot;{searchQuery}&quot;</span>}
          </div>
          <div className="text-slate-500">
            Page {page} of {totalPages}
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="py-24 text-center">
            <RefreshCw className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-3" />
            <p className="text-slate-400 text-sm">Searching 5,742 National Programmes...</p>
          </div>
        )}

        {/* Empty State (Section 20) */}
        {!loading && items.length === 0 && (
          <div className="bg-[#0a0a1a] border border-white/10 rounded-3xl p-12 text-center max-w-xl mx-auto my-12">
            <AlertCircle className="w-12 h-12 text-slate-500 mx-auto mb-3" />
            <h3 className="text-lg font-bold text-white mb-1">No programmes found for these filters.</h3>
            <p className="text-slate-400 text-xs mb-5">
              Try adjusting your keyword, resetting sector categories, or widening government level filters.
            </p>
            <Button onClick={resetFilters} className="bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold">
              Reset All Filters
            </Button>
          </div>
        )}

        {/* Grid of Programme Cards (Section 7 & 8) */}
        {!loading && items.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 mb-12">
            {items.map((item) => (
              <div
                key={item.programme_id}
                className="bg-[#0a0a1a] hover:bg-[#0c0c22] border border-white/10 hover:border-blue-500/40 rounded-2xl p-5 flex flex-col justify-between transition-all duration-200 group relative shadow-lg"
              >
                <div>
                  {/* Card Meta Badges */}
                  <div className="flex flex-wrap items-center gap-1.5 mb-3">
                    <span className="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider bg-white/5 text-slate-300 border border-white/5">
                      {item.government_level}
                    </span>
                    {item.state_or_ut && (
                      <span className="px-2 py-0.5 rounded-md text-[10px] font-medium bg-indigo-950/40 text-indigo-300 border border-indigo-800/30">
                        {item.state_or_ut}
                      </span>
                    )}
                    <span className="px-2 py-0.5 rounded-md text-[10px] font-medium bg-white/5 text-slate-400">
                      {item.category}
                    </span>
                  </div>

                  {/* Programme Title */}
                  <h3 className="text-base font-bold text-white group-hover:text-blue-400 transition-colors leading-snug mb-2 line-clamp-2">
                    <Link href={`/programmes/${item.programme_id}`}>
                      {item.canonical_name}
                    </Link>
                  </h3>

                  {/* Authority / Ministry */}
                  <div className="text-xs text-slate-500 mb-3 line-clamp-1">
                    {item.ministry || item.authority || 'Government of India'}
                  </div>

                  {/* Short Description */}
                  <p className="text-xs text-slate-400 leading-relaxed mb-4 line-clamp-3">
                    {item.description || 'Official government welfare programme. Comprehensive guidelines and entitlement parameters are maintained through authorized portals.'}
                  </p>
                </div>

                {/* Card Footer: Badge & Action CTA */}
                <div className="pt-3 border-t border-white/5 flex flex-col gap-2.5">
                  <div className="flex items-center justify-between">
                    {getStatusBadge(item)}
                  </div>
                  <div className="flex items-center justify-between mt-1">
                    <Link
                      href={`/programmes/${item.programme_id}`}
                      className="text-xs text-slate-400 hover:text-white font-medium inline-flex items-center gap-1 transition-colors"
                    >
                      View Details
                    </Link>
                    {getCardCta(item)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Server-Side Pagination Controls (Section 3) */}
        {!loading && totalPages > 1 && (
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 py-4 px-2 border-t border-white/10 text-xs text-slate-400">
            <div>
              Showing page <span className="font-bold text-white">{page}</span> of{' '}
              <span className="font-bold text-white">{totalPages}</span> ({total?.toLocaleString()} programmes)
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="bg-white/5 border-white/10 hover:bg-white/10 text-slate-300 rounded-xl"
              >
                <ChevronLeft className="w-4 h-4 mr-1" /> Previous
              </Button>

              <span className="px-3 py-1 font-mono text-white bg-white/5 rounded-lg border border-white/10">
                {page} / {totalPages}
              </span>

              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="bg-white/5 border-white/10 hover:bg-white/10 text-slate-300 rounded-xl"
              >
                Next <ChevronRight className="w-4 h-4 ml-1" />
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
