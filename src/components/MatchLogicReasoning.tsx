'use client';
import { CheckCircle2, AlertCircle, HelpCircle, ShieldCheck } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface RuleItem {
  rule_id?: string;
  fact_key: string;
  operator: string;
  expected_value: any;
  is_mandatory?: boolean;
  description?: string;
}

interface UserMatchData {
  eligibility_status: string;
  deterministic_result?: string;
  eligible?: boolean;
  confidence?: number;
  reasons?: string[];
  missing_facts?: string[];
  criteria_met_count?: number;
  criteria_total_count?: number;
  criteria_progress_pct?: number;
}

interface MatchLogicReasoningProps {
  userMatch?: UserMatchData | null;
  rules?: RuleItem[];
  schemeCriteria?: {
    min_age?: string;
    max_age?: string;
    income_limit?: string;
    applicable_states?: string;
    category?: string;
  };
}

export function MatchLogicReasoning({ userMatch, rules = [], schemeCriteria }: MatchLogicReasoningProps) {
  // If we have an authoritative user match from the backend
  if (userMatch) {
    const status = userMatch.eligibility_status;
    const isEligible = status === 'ELIGIBLE';
    const isNeedsInfo = status === 'NEEDS_INFO';
    const isNotEligible = status === 'NOT_ELIGIBLE';

    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between px-1">
          <div className="flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
            <ShieldCheck className="h-3.5 w-3.5 text-blue-400" /> Statutory Criteria Evaluation
          </div>
          <Badge
            variant="outline"
            className={`text-[10px] font-bold uppercase tracking-wider ${
              isEligible
                ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
                : isNeedsInfo
                ? 'bg-amber-500/15 text-amber-300 border-amber-500/30'
                : 'bg-rose-500/15 text-rose-300 border-rose-500/30'
            }`}
          >
            {isEligible ? 'Verified Match' : isNeedsInfo ? 'Pending Information' : 'Outside Eligibility'}
          </Badge>
        </div>

        {/* Criteria Progress */}
        {userMatch.criteria_total_count !== undefined && userMatch.criteria_total_count > 0 && (
          <div className="p-3 rounded-2xl bg-white/[0.02] border border-white/5 space-y-1.5">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400 font-medium">Statutory Criteria Progress</span>
              <span className="font-bold text-white">
                {userMatch.criteria_met_count || 0} / {userMatch.criteria_total_count} Verified ({userMatch.criteria_progress_pct || 0}%)
              </span>
            </div>
            <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-300 ${
                  isEligible ? 'bg-emerald-500' : isNeedsInfo ? 'bg-amber-500' : 'bg-rose-500'
                }`}
                style={{ width: `${Math.min(100, Math.max(userMatch.criteria_progress_pct || 0, 5))}%` }}
              />
            </div>
          </div>
        )}

        {/* Criteria Met List */}
        {userMatch.reasons && userMatch.reasons.length > 0 && (
          <div className="space-y-1.5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400 block px-1">
              Confirmed Statutory Inclusions
            </span>
            <div className="space-y-1">
              {userMatch.reasons.map((r, idx) => (
                <div key={idx} className="bg-emerald-500/5 border border-emerald-500/15 p-2.5 rounded-xl flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
                  <span className="text-xs text-emerald-200/90 leading-snug">{r}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Missing Facts List */}
        {userMatch.missing_facts && userMatch.missing_facts.length > 0 && (
          <div className="space-y-1.5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-amber-400 block px-1">
              Pending Statutory Fields
            </span>
            <div className="space-y-1">
              {userMatch.missing_facts.map((factKey, idx) => {
                const cleanLabel = factKey
                  .replace(/^(applicant\.|household\.|person\.|location\.|student\.|artisan\.|enterprise\.|family\.|social\.|agriculture\.|health\.|finance\.)/, '')
                  .replace(/_/g, ' ');
                return (
                  <div key={idx} className="bg-amber-500/5 border border-amber-500/15 p-2.5 rounded-xl flex items-start gap-2">
                    <AlertCircle className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
                    <span className="text-xs text-amber-200/90 capitalize leading-snug">
                      Required input: {cleanLabel}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    );
  }

  // Fallback: When no user profile session is linked, show the scheme's statutory rule checklist
  if (rules && rules.length > 0) {
    return (
      <div className="space-y-3">
        <div className="flex items-center gap-2 px-1 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
          <ShieldCheck className="h-3.5 w-3.5 text-blue-400" /> Statutory Eligibility Rules
        </div>
        <div className="space-y-1.5">
          {rules.slice(0, 5).map((rule, idx) => {
            const cleanKey = (rule.fact_key || '')
              .replace(/^(applicant\.|household\.|person\.|location\.|student\.|artisan\.|enterprise\.|family\.|social\.|agriculture\.|health\.|finance\.)/, '')
              .replace(/_/g, ' ');
            return (
              <div key={idx} className="bg-white/[0.02] border border-white/5 p-2.5 rounded-xl flex items-center justify-between text-xs">
                <span className="text-slate-300 capitalize">{cleanKey}</span>
                <span className="font-mono text-slate-400 text-[11px]">
                  {rule.operator} {String(rule.expected_value)}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-900/50 border border-white/5 rounded-2xl p-4 flex items-center gap-2 text-xs text-slate-400">
      <HelpCircle className="h-4 w-4 text-blue-400 shrink-0" />
      <span>Complete the questionnaire to view your statutory eligibility breakdown.</span>
    </div>
  );
}
