'use client';
import { useEffect, useState } from 'react';
import { CheckCircle2, XCircle, Info, HelpCircle } from 'lucide-react';

interface MatchLogicReasoningProps {
  schemeCriteria: {
    min_age?: string;
    max_age?: string;
    income_limit?: string;
    applicable_states?: string;
    category?: string;
  };
}

export function MatchLogicReasoning({ schemeCriteria }: MatchLogicReasoningProps) {
  const [profile, setProfile] = useState<any>(null);

  useEffect(() => {
    const saved = localStorage.getItem('civix_user_profile');
    if (saved) setProfile(JSON.parse(saved));
  }, []);

  if (!profile) {
    return (
      <div className="bg-slate-900/50 border border-white/5 rounded-2xl p-4 flex items-center gap-2 text-xs text-slate-400">
        <HelpCircle className="h-4 w-4 text-blue-400" />
        Fill your profile to see smart match analysis.
      </div>
    );
  }

  const matches = [
    {
      label: 'Age',
      user: `${profile.age} Years`,
      criteria: `${schemeCriteria.min_age || 0} - ${schemeCriteria.max_age || 100} Years`,
      isValid: (Number(profile.age) >= Number(schemeCriteria.min_age || 0)) && (Number(profile.age) <= Number(schemeCriteria.max_age || 100))
    },
    {
      label: 'Annual Income',
      user: `₹${Number(profile.annualIncome).toLocaleString()}`,
      criteria: `Max ₹${Number(schemeCriteria.income_limit || 10000000).toLocaleString()}`,
      isValid: (Number(profile.annualIncome) <= Number(schemeCriteria.income_limit || 10000000))
    },
    {
       label: 'State',
       user: profile.state,
       criteria: schemeCriteria.applicable_states || 'All',
       isValid: (schemeCriteria.applicable_states === 'All' || schemeCriteria.applicable_states?.toLowerCase().includes(profile.state.toLowerCase()))
    },
    {
       label: 'Caste',
       user: profile.caste?.toUpperCase(),
       criteria: schemeCriteria.category || 'Any',
       isValid: (schemeCriteria.category === 'All' || schemeCriteria.category?.toLowerCase() === 'any' || schemeCriteria.category?.toLowerCase().includes(profile.caste?.toLowerCase()))
    }
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 px-1 text-[10px] font-bold text-slate-500 uppercase tracking-widest">
        <Info className="h-3 w-3" /> AI Match Reasoning
      </div>
      <div className="grid gap-2">
        {matches.map((item) => (
          <div key={item.label} className="bg-white/[0.02] border border-white/5 p-3 rounded-2xl flex items-center justify-between group hover:bg-white/[0.04] transition-all">
            <div className="flex flex-col gap-0.5">
              <span className="text-[10px] text-slate-500 font-bold uppercase">{item.label} Analysis</span>
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold text-white">{item.user}</span>
                <span className="text-[10px] text-slate-500 tracking-tight italic">vs Requirement: {item.criteria.length > 20 ? item.criteria.substring(0,20)+'...' : item.criteria}</span>
              </div>
            </div>
            {item.isValid ? (
              <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] font-black uppercase">
                <CheckCircle2 className="h-3 w-3" /> Match
              </div>
            ) : (
              <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-red-500/10 text-red-400 border border-red-500/20 text-[10px] font-black uppercase">
                <XCircle className="h-3 w-3" /> Failed
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
