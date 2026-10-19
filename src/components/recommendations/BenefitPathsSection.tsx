'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Briefcase,
  Sprout,
  ShieldCheck,
  GraduationCap,
  Home,
  CheckCircle2,
  Clock,
  ArrowRight,
  Download,
  Copy,
  Check,
  Layers,
  Loader2,
  Milestone
} from 'lucide-react';
import { motion } from 'framer-motion';

export interface PathwayStep {
  step_number: number;
  stage_title: string;
  stage_type: string;
  description: string;
  action_item: string;
  estimated_duration: string;
  schemes: Array<{
    scheme_id: string;
    scheme_name: string;
    eligibility_status: string;
    benefit_amount: string;
    match_score: number;
    category?: string;
  }>;
  prerequisites_unlocked: string[];
}

export interface BenefitPathway {
  pathway_id: string;
  goal_id: string;
  goal_title: string;
  description: string;
  target_citizen_profile: string;
  total_milestones: number;
  total_schemes_count: number;
  steps: PathwayStep[];
  cumulative_benefits_summary: string;
  printable_action_plan_markdown: string;
}

const AVAILABLE_GOALS = [
  {
    id: 'START_OR_EXPAND_BUSINESS',
    title: 'Enterprise & Business Funding',
    subtitle: 'From Udyam to MUDRA loans, CGTMSE credit guarantee & worker cover',
    icon: Briefcase,
    color: 'from-blue-500/20 via-indigo-500/10 to-transparent',
    activeBorder: 'border-blue-500/50',
    activeText: 'text-blue-400',
    accent: 'bg-blue-500/10 text-blue-300 border-blue-500/30',
  },
  {
    id: 'FARMING_AND_AGRICULTURE',
    title: 'Farmer Empowerment & Agri Credit',
    subtitle: 'Land validation to PM-KISAN, KCC revolving credit & PMFBY insurance',
    icon: Sprout,
    color: 'from-emerald-500/20 via-green-500/10 to-transparent',
    activeBorder: 'border-emerald-500/50',
    activeText: 'text-emerald-400',
    accent: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30',
  },
  {
    id: 'UNORGANIZED_WORKER_SAFETY_NET',
    title: 'Gig & Unorganized Worker Safety',
    subtitle: 'e-Shram identity, PM SVANidhi working capital & PM-JAY cover',
    icon: ShieldCheck,
    color: 'from-amber-500/20 via-orange-500/10 to-transparent',
    activeBorder: 'border-amber-500/50',
    activeText: 'text-amber-400',
    accent: 'bg-amber-500/10 text-amber-300 border-amber-500/30',
  },
  {
    id: 'STUDENT_HIGHER_EDUCATION',
    title: 'Student Higher Education & Skills',
    subtitle: 'NSP scholarship grants, zero-interest student loans & stipends',
    icon: GraduationCap,
    color: 'from-purple-500/20 via-pink-500/10 to-transparent',
    activeBorder: 'border-purple-500/50',
    activeText: 'text-purple-400',
    accent: 'bg-purple-500/10 text-purple-300 border-purple-500/30',
  },
  {
    id: 'FAMILY_HEALTH_AND_HOUSING',
    title: 'Family Health & Housing Security',
    subtitle: 'NFSA ration seeding to PM-JAY ₹5L health cover & PMAY housing',
    icon: Home,
    color: 'from-rose-500/20 via-red-500/10 to-transparent',
    activeBorder: 'border-rose-500/50',
    activeText: 'text-rose-400',
    accent: 'bg-rose-500/10 text-rose-300 border-rose-500/30',
  },
];

interface BenefitPathsSectionProps {
  sessionId?: string | null;
}

export function BenefitPathsSection({ sessionId }: BenefitPathsSectionProps) {
  const [selectedGoal, setSelectedGoal] = useState<string>('START_OR_EXPAND_BUSINESS');
  const [pathway, setPathway] = useState<BenefitPathway | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  useEffect(() => {
    let isMounted = true;

    async function fetchPathway() {
      setLoading(true);
      setError(null);
      try {
        const payload: Record<string, any> = { goal_id: selectedGoal };
        if (sessionId) {
          payload.session_id = sessionId;
        }

        const res = await fetch('/v1/benefit-paths/synthesize', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });

        if (!res.ok) {
          throw new Error(`Failed to synthesize pathway: ${res.statusText}`);
        }

        const data = await res.json();
        if (isMounted) {
          setPathway(data);
        }
      } catch (err: any) {
        console.error('Pathway synthesis error:', err);
        if (isMounted) {
          setError('Unable to synthesize benefit path right now. Please try again later.');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    fetchPathway();

    return () => {
      isMounted = false;
    };
  }, [selectedGoal, sessionId]);

  const handleCopyMarkdown = () => {
    if (!pathway?.printable_action_plan_markdown) return;
    navigator.clipboard.writeText(pathway.printable_action_plan_markdown);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadMarkdown = () => {
    if (!pathway?.printable_action_plan_markdown) return;
    const blob = new Blob([pathway.printable_action_plan_markdown], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `CivixAI-Action-Plan-${pathway.goal_id.toLowerCase()}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <section className="my-16 space-y-8">
      {/* Section Header */}
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="border-blue-500/30 bg-blue-500/10 text-blue-400 px-3 py-1 text-xs font-semibold uppercase tracking-wider rounded-full">
            <Layers className="w-3.5 h-3.5 mr-1.5" />
            Multi-Programme Action Plans
          </Badge>
          <span className="text-xs text-slate-400 hidden sm:inline-block">• Coordinated Roadmap</span>
        </div>
        <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
          Sequenced <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-indigo-300 to-purple-400">Benefit Pathways</span>
        </h2>
        <p className="text-slate-400 text-sm sm:text-base max-w-3xl">
          Schemes work best when combined sequentially. Select your primary goal to see the exact step-by-step roadmap—from identity validation to working capital and risk protection.
        </p>
      </div>

      {/* Goal Selector Tabs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {AVAILABLE_GOALS.map((goal) => {
          const Icon = goal.icon;
          const isSelected = selectedGoal === goal.id;
          return (
            <button
              key={goal.id}
              onClick={() => setSelectedGoal(goal.id)}
              className={`text-left p-4 rounded-xl transition-all duration-300 relative border flex flex-col justify-between group ${
                isSelected
                  ? `bg-slate-900/90 ${goal.activeBorder} shadow-[0_0_20px_-5px_rgba(59,130,246,0.3)] ring-1 ring-blue-500/30`
                  : 'bg-black/40 border-white/10 hover:border-white/20 hover:bg-slate-900/40 text-slate-300'
              }`}
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className={`p-2 rounded-lg ${isSelected ? goal.accent : 'bg-white/5 text-slate-400 group-hover:text-white'}`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  {isSelected && (
                    <span className="flex h-2 w-2 relative">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
                    </span>
                  )}
                </div>
                <div>
                  <h4 className={`text-sm font-bold leading-tight ${isSelected ? 'text-white' : 'text-slate-300'}`}>
                    {goal.title}
                  </h4>
                  <p className="text-[11px] text-slate-400 mt-1 line-clamp-2 leading-relaxed">
                    {goal.subtitle}
                  </p>
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Pathway Display */}
      {loading ? (
        <Card className="bg-slate-950/60 border-white/10 p-12 text-center flex flex-col items-center justify-center min-h-[320px]">
          <Loader2 className="w-8 h-8 animate-spin text-blue-400 mb-3" />
          <p className="text-slate-300 font-medium text-sm">Synthesizing coordinated statutory roadmap...</p>
          <p className="text-slate-500 text-xs mt-1">Cross-referencing legal prerequisites and sequential unlock rules</p>
        </Card>
      ) : error ? (
        <Card className="bg-rose-950/20 border-rose-500/20 p-6 text-center text-rose-300 text-sm">
          {error}
        </Card>
      ) : pathway ? (
        <div className="space-y-6">
          {/* Pathway Overview Banner */}
          <Card className="bg-gradient-to-r from-blue-950/40 via-slate-900/60 to-slate-950/80 border border-blue-500/20 rounded-2xl overflow-hidden backdrop-blur-md">
            <CardHeader className="p-6 pb-4">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="bg-blue-500/20 text-blue-300 border-blue-500/30 text-xs">
                      {pathway.total_milestones} Milestones
                    </Badge>
                    <Badge variant="outline" className="bg-emerald-500/10 text-emerald-300 border-emerald-500/30 text-xs">
                      {pathway.total_schemes_count} Relevant Programmes
                    </Badge>
                  </div>
                  <CardTitle className="text-xl sm:text-2xl font-black text-white">
                    {pathway.goal_title}
                  </CardTitle>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 shrink-0">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleCopyMarkdown}
                    className="border-white/10 bg-white/5 hover:bg-white/10 text-slate-200 text-xs gap-1.5"
                  >
                    {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    {copied ? 'Copied Plan' : 'Copy Plan'}
                  </Button>
                  <Button
                    variant="default"
                    size="sm"
                    onClick={handleDownloadMarkdown}
                    className="bg-blue-600 hover:bg-blue-500 text-white text-xs gap-1.5"
                  >
                    <Download className="w-3.5 h-3.5" />
                    Download Action Plan
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-6 pt-0">
              <div className="p-3.5 rounded-xl bg-blue-500/10 border border-blue-500/20 text-xs sm:text-sm text-blue-200 leading-relaxed">
                <span className="font-semibold text-white">Cumulative Benefit Impact: </span>
                {pathway.cumulative_benefits_summary}
              </div>
            </CardContent>
          </Card>

          {/* Sequential Step Timeline */}
          <div className="relative pl-6 sm:pl-8 space-y-6 before:absolute before:left-3 sm:before:left-4 before:top-4 before:bottom-4 before:w-0.5 before:bg-gradient-to-b before:from-blue-500 before:via-indigo-500 before:to-emerald-500">
            {pathway.steps.map((step, idx) => (
              <motion.div
                key={step.step_number}
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: idx * 0.08 }}
                className="relative"
              >
                {/* Node Icon on Timeline */}
                <div className="absolute -left-6 sm:-left-8 top-5 w-6 h-6 sm:w-8 sm:h-8 rounded-full bg-slate-950 border-2 border-blue-500 flex items-center justify-center text-blue-400 font-bold text-xs shadow-[0_0_12px_rgba(59,130,246,0.6)]">
                  {step.step_number}
                </div>

                <Card className="bg-[#0b0f19]/90 border-white/10 hover:border-blue-500/30 transition-all rounded-2xl overflow-hidden backdrop-blur-xl">
                  <CardHeader className="p-5 pb-3">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div>
                        <span className="text-[10px] uppercase font-bold tracking-wider text-blue-400/90">
                          {step.stage_type.replace(/_/g, ' ')}
                        </span>
                        <CardTitle className="text-lg font-bold text-white mt-0.5">
                          {step.stage_title}
                        </CardTitle>
                      </div>
                      <div className="flex items-center gap-1.5 text-xs text-slate-400 bg-white/5 border border-white/10 px-2.5 py-1 rounded-full w-fit shrink-0">
                        <Clock className="w-3.5 h-3.5 text-blue-400" />
                        <span>{step.estimated_duration}</span>
                      </div>
                    </div>
                  </CardHeader>

                  <CardContent className="p-5 pt-0 space-y-4">
                    {/* Description */}
                    <p className="text-slate-300 text-sm leading-relaxed">
                      {step.description}
                    </p>

                    {/* Citizen Action Item */}
                    <div className="p-3 rounded-xl bg-slate-900/80 border border-white/5 text-xs text-slate-300 flex items-start gap-2.5">
                      <ArrowRight className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
                      <div>
                        <span className="font-semibold text-white">Action Required: </span>
                        {step.action_item}
                      </div>
                    </div>

                    {/* Matched Official Schemes */}
                    {step.schemes && step.schemes.length > 0 && (
                      <div className="space-y-2 pt-1">
                        <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                          <Milestone className="w-3.5 h-3.5 text-indigo-400" />
                          Applicable Government Programmes:
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                          {step.schemes.map((sc) => (
                            <div
                              key={sc.scheme_id}
                              className="p-3 rounded-xl bg-black/40 border border-white/5 hover:border-blue-500/20 transition-all flex flex-col justify-between space-y-2"
                            >
                              <div className="flex items-start justify-between gap-2">
                                <h5 className="text-sm font-semibold text-white leading-tight">
                                  {sc.scheme_name}
                                </h5>
                                <Badge
                                  variant="outline"
                                  className={`text-[10px] shrink-0 font-medium ${
                                    sc.eligibility_status === 'ELIGIBLE'
                                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                                      : 'bg-blue-500/10 text-blue-400 border-blue-500/30'
                                  }`}
                                >
                                  {sc.eligibility_status === 'ELIGIBLE' ? '✓ Eligible' : '⚡ Applicable'}
                                </Badge>
                              </div>
                              {sc.benefit_amount && (
                                <div className="text-xs font-medium text-emerald-400">
                                  ₹ {sc.benefit_amount}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Prerequisites / Deliverables Unlocked */}
                    {step.prerequisites_unlocked && step.prerequisites_unlocked.length > 0 && (
                      <div className="flex items-center flex-wrap gap-2 pt-1">
                        <span className="text-xs text-slate-400 font-medium">Unlocks:</span>
                        {step.prerequisites_unlocked.map((deliverable, dIdx) => (
                          <span
                            key={dIdx}
                            className="inline-flex items-center gap-1 text-[11px] font-medium text-blue-300 bg-blue-500/10 border border-blue-500/20 px-2 py-0.5 rounded-full"
                          >
                            <CheckCircle2 className="w-3 h-3 text-blue-400" />
                            {deliverable}
                          </span>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  );
}
export default BenefitPathsSection;
