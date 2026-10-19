'use client';

import { Card } from '@/components/ui/card';
import {
    BrainCircuit,
    Target,
    Calculator,
    GitCompareArrows,
    FileCheck2,
    MapPin,
    Landmark,
    ShieldCheck,
    Languages,
    Smartphone,
    ArrowRight,
    Sparkles
} from 'lucide-react';
import { ScrollWrapper } from '@/components/animations/ScrollWrapper';
import { Badge } from '@/components/ui/badge';

const features = [
    { 
        icon: <BrainCircuit className="w-6 h-6" />, 
        title: 'Deterministic Statutory Rules',
        description: 'Hard legal AST rule engine evaluates age, land, domicile, and income against official Gazette orders without hallucination.',
        color: 'text-blue-400'
    },
    { 
        icon: <ShieldCheck className="w-6 h-6" />, 
        title: 'Grounded Gazette Evidence',
        description: 'Every entitlement is strictly backed by verifiable Ministry guidelines, official notifications, and legal citations.',
        color: 'text-emerald-400'
    },
    { 
        icon: <Calculator className="w-6 h-6" />, 
        title: 'Formula & Benefit Calculator',
        description: 'Computes exact tranche schedules, DBT cashflows, interest subventions, and toolkit vouchers mathematically.',
        color: 'text-amber-400'
    },
    { 
        icon: <FileCheck2 className="w-6 h-6" />, 
        title: 'Application Readiness Tracker',
        description: 'Evaluates required documentation, identifies blocker criteria, and scores your readiness before applying.',
        color: 'text-rose-400'
    },
    { 
        icon: <Sparkles className="w-6 h-6" />, 
        title: 'Multi-Programme Benefit Paths',
        description: 'Synthesizes sequential support pipelines—from foundational ID registration to working capital and risk protection.',
        color: 'text-purple-400'
    },
    { 
        icon: <MapPin className="w-6 h-6" />, 
        title: 'Hyper-Local Statutory Rules',
        description: 'State-specific exclusions, district-level urban/rural vendor zones, and local nodal office verification criteria.',
        color: 'text-sky-400'
    },
    { 
        icon: <Landmark className="w-6 h-6" />, 
        title: 'DPDP Act Privacy-by-Design',
        description: 'Ephemeral anonymous sessions, zero mandatory login, and complete data sovereignty compliant with DPDP Act 2023.',
        color: 'text-indigo-400'
    },
    { 
        icon: <Languages className="w-6 h-6" />, 
        title: 'Multilingual Vernacular Support',
        description: 'Natural Hindi, English, and Hinglish query understanding with localized scheme colloquialisms and number normalization.',
        color: 'text-teal-400'
    },
];

export function FeaturesSection() {
    return (
        <section id="features" className="py-24 sm:py-32 bg-transparent relative overflow-hidden">
            {/* Background decorative glow */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-blue-600/5 rounded-full blur-[120px] pointer-events-none" />
            
            <div className="container mx-auto px-4 relative z-10">
                <ScrollWrapper>
                    <div className="text-center max-w-3xl mx-auto mb-20 space-y-4">
                        <Badge variant="outline" className="px-4 py-1 border-blue-500/30 bg-blue-500/10 text-blue-400 rounded-full font-bold tracking-widest uppercase text-[10px]">
                            Public Service Infrastructure
                        </Badge>
                        <h2 className="text-4xl sm:text-5xl font-black text-white tracking-tight leading-tight">
                            Built on <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-indigo-500">Statutory Precision</span>
                        </h2>
                        <p className="text-lg text-slate-400 font-medium max-w-2xl mx-auto">
                            Combining deterministic legal verification, official gazette citations, and structured multi-programme pathways for India's 1.4 billion citizens.
                        </p>
                    </div>
                </ScrollWrapper>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                    {features.map((feature, index) => (
                        <ScrollWrapper key={index}>
                            <div className="group relative h-full perspective-1000">
                                {/* Invisible glow that appears on hover */}
                                <div className="absolute -inset-[1px] bg-gradient-to-b from-blue-500/20 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
                                
                                <Card className="h-full bg-[#050510]/60 border border-white/10 backdrop-blur-md rounded-2xl p-6 transition-all duration-500 group-hover:bg-[#0a0a1a]/80 group-hover:border-blue-500/30 group-hover:-translate-y-1 group-hover:shadow-[0_20px_40px_-20px_rgba(59,130,246,0.3)]">
                                    <div className="space-y-4">
                                        <div className={`w-12 h-12 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center ${feature.color} group-hover:scale-110 group-hover:bg-blue-500/10 group-hover:border-blue-500/20 transition-all duration-500`}>
                                            {feature.icon}
                                        </div>
                                        <div className="space-y-2">
                                            <h3 className="text-lg font-bold text-white group-hover:text-blue-400 transition-colors uppercase tracking-tight">
                                                {feature.title}
                                            </h3>
                                            <p className="text-sm text-slate-400 leading-relaxed group-hover:text-slate-300 transition-colors">
                                                {feature.description}
                                            </p>
                                        </div>
                                    </div>
                                    
                                    {/* Corner Decoration */}
                                    <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <Sparkles className="w-4 h-4 text-blue-500/40" />
                                    </div>
                                </Card>
                            </div>
                        </ScrollWrapper>
                    ))}
                </div>

                <ScrollWrapper>
                    <div className="mt-20 flex flex-col items-center justify-center space-y-6">
                        <p className="text-slate-500 text-sm font-semibold uppercase tracking-[0.2em]">Ready to find your match?</p>
                        <div className="h-[1px] w-20 bg-gradient-to-r from-transparent via-blue-500/50 to-transparent" />
                    </div>
                </ScrollWrapper>
            </div>
        </section>
    );
}
