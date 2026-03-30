import { promises as fs } from 'fs';
import path from 'path';
import { Header } from '@/components/Header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ExternalLink, Building2, CheckCircle, ChevronLeft, SearchX, Globe, MapPin, Download } from 'lucide-react';
import Link from 'next/link';
import Chatbot from '@/components/Chatbot';
import { ClientScrollRestorer } from '@/components/ClientScrollRestorer';
import { WhatsAppShareButton } from '@/components/WhatsAppShareButton';
import { MatchLogicReasoning } from '@/components/MatchLogicReasoning';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

type SchemeRow = {
    scheme_id?: string;
    scheme_name?: string;
    ministry?: string;
    scheme_level?: string;
    scheme_category?: string;
    applicable_states?: string;
    min_age?: string;
    max_age?: string;
    income_limit?: string;
    benefit_description?: string;
    documents_required?: string;
    application_url?: string;
    source_url?: string;
};

// Simple CSV parser
function parseCsv(text: string): string[][] {
    const rows: string[][] = [];
    let row: string[] = [];
    let field = '';
    let inQuotes = false;
    for (let i = 0; i < text.length; i++) {
        const char = text[i];
        const next = text[i + 1];
        if (char === '"') {
            if (inQuotes && next === '"') { field += '"'; i++; }
            else { inQuotes = !inQuotes; }
            continue;
        }
        if (char === ',' && !inQuotes) { row.push(field); field = ''; continue; }
        if ((char === '\n' || char === '\r') && !inQuotes) {
            if (char === '\r' && next === '\n') { i++; }
            row.push(field); field = '';
            if (row.length > 1 || (row[0] && row[0].trim())) { rows.push(row); }
            row = [];
            continue;
        }
        field += char;
    }
    row.push(field);
    if (row.length > 1 || (row[0] && row[0].trim())) { rows.push(row); }
    return rows;
}

// Function to find a scheme by ID
async function getSchemeById(id: string): Promise<SchemeRow | null> {
    if (!id) return null;
    const DATA_PATH = path.join(process.cwd(), 'data', 'master', 'schemes_master.csv');
    try {
        const csvText = await fs.readFile(DATA_PATH, 'utf-8');
        const rows = parseCsv(csvText);
        if (rows.length === 0) return null;

        const headers = rows[0].map((header) => header.trim());
        const index = new Map<string, number>();
        headers.forEach((header, i) => index.set(header, i));

        const getValue = (row: string[], key: string): string | undefined => {
            const idx = index.get(key);
            if (idx === undefined) return undefined;
            return row[idx]?.trim();
        };

        // Use a case-insensitive search
        const lowerId = id.toLowerCase();

        for (let i = 1; i < rows.length; i++) {
            const rowId = getValue(rows[i], 'scheme_id');
            if (rowId && (rowId.toLowerCase() === lowerId || rowId.toLowerCase().includes(lowerId))) {
                return {
                    scheme_id: rowId,
                    scheme_name: getValue(rows[i], 'scheme_name'),
                    ministry: getValue(rows[i], 'ministry'),
                    scheme_level: getValue(rows[i], 'scheme_level'),
                    scheme_category: getValue(rows[i], 'scheme_category'),
                    applicable_states: getValue(rows[i], 'applicable_states'),
                    min_age: getValue(rows[i], 'min_age'),
                    max_age: getValue(rows[i], 'max_age'),
                    income_limit: getValue(rows[i], 'income_limit'),
                    benefit_description: getValue(rows[i], 'benefit_description'),
                    documents_required: getValue(rows[i], 'documents_required'),
                    application_url: getValue(rows[i], 'application_url'),
                    source_url: getValue(rows[i], 'source_url')
                };
            }
        }
        return null;
    } catch (error) {
        console.error('Error fetching scheme:', error);
        return null;
    }
}

export default async function SchemeDetailsPage({ params }: { params: Promise<{ id: string }> }) {
    const resolvedParams = await params;
    const schemeId = resolvedParams.id;
    const scheme = await getSchemeById(schemeId);

    if (!scheme) {
        return (
            <div className="flex flex-col min-h-screen bg-slate-950 text-white font-sans">
                <Header />
                <main className="flex-grow container mx-auto px-4 py-20 flex flex-col items-center justify-center text-center">
                    <div className="bg-white/5 border border-white/10 backdrop-blur-2xl p-12 rounded-3xl max-w-xl">
                        <SearchX className="h-16 w-16 text-slate-400 mx-auto mb-6" />
                        <h1 className="text-3xl font-black mb-4">Scheme Not Found</h1>
                        <p className="text-slate-400 mb-8">
                            We couldn't find the requested scheme. The link might be broken or the scheme might have been updated.
                        </p>
                        <Button asChild className="rounded-xl">
                            <Link href="/recommendations">
                                <ChevronLeft className="mr-2 h-4 w-4" /> Back to Recommendations
                            </Link>
                        </Button>
                    </div>
                </main>
                <Chatbot />
            </div>
        );
    }

    const {
        scheme_name,
        ministry,
        scheme_level,
        scheme_category,
        applicable_states,
        min_age,
        max_age,
        income_limit,
        benefit_description,
        documents_required,
        application_url,
        source_url
    } = scheme;

    const docsList = documents_required ? documents_required.split(',').map(d => d.trim()).filter(Boolean) : [];

    return (
        <div className="flex flex-col min-h-screen bg-[#050510] text-white font-sans selection:bg-blue-500/30">
            <ClientScrollRestorer />
            <Header />

            {/* Dynamic Background */}
            <div className="fixed top-0 inset-x-0 h-96 bg-gradient-to-b from-blue-900/20 to-transparent pointer-events-none -z-10" />
            <div className="fixed top-[-10%] left-[-10%] w-[50%] h-[50%] bg-blue-600/10 rounded-full blur-[120px] -z-10 animate-pulse" />

            <main className="flex-grow container mx-auto px-4 py-8 lg:py-12 max-w-5xl">
                <div className="mb-8">
                    <Button variant="ghost" asChild className="text-slate-400 hover:text-white -ml-4 mb-4">
                        <Link href="/recommendations">
                            <ChevronLeft className="mr-2 h-4 w-4" /> Back to Recommendations
                        </Link>
                    </Button>

                    <div className="flex flex-wrap gap-3 mb-6">
                        {scheme_category && (
                            <Badge className="bg-blue-500/10 text-blue-300 hover:bg-blue-500/20 border-blue-500/20 px-3 py-1 text-xs">
                                {scheme_category}
                            </Badge>
                        )}
                        {scheme_level && (
                            <Badge className="bg-purple-500/10 text-purple-300 hover:bg-purple-500/20 border-purple-500/20 px-3 py-1 text-xs uppercase">
                                {scheme_level}
                            </Badge>
                        )}
                    </div>

                    <h1 className="text-4xl md:text-5xl lg:text-6xl font-black leading-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-blue-200 mb-6">
                        {scheme_name || 'Scheme Highlights'}
                    </h1>

                    <div className="flex items-center gap-3 text-slate-300 bg-white/5 border border-white/10 w-fit px-4 py-2.5 rounded-2xl backdrop-blur-md">
                        <Building2 className="h-5 w-5 text-blue-400" />
                        <span className="font-semibold">{ministry || 'Government of India'}</span>
                    </div>
                </div>

                {/* Eligibility Snapshot */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                    <div className="bg-[#0a0a0b]/80 border border-white/5 p-4 rounded-2xl flex flex-col gap-2 shadow-sm">
                        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest flex items-center gap-1.5"><CheckCircle className="h-3 w-3 text-slate-500" /> Min Age</span>
                        <span className="text-lg font-black text-white">{min_age && min_age !== '0' && min_age !== 'NA' ? `${min_age} Years` : 'No Minimum'}</span>
                    </div>
                    <div className="bg-[#0a0a0b]/80 border border-white/5 p-4 rounded-2xl flex flex-col gap-2 shadow-sm">
                        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest flex items-center gap-1.5"><CheckCircle className="h-3 w-3 text-slate-500" /> Max Age</span>
                        <span className="text-lg font-black text-white">{max_age && max_age !== '100' && max_age !== 'NA' && max_age !== '99' ? `${max_age} Years` : 'No Limit'}</span>
                    </div>
                    <div className="bg-[#0a0a0b]/80 border border-white/5 p-4 rounded-2xl flex flex-col gap-2 shadow-sm">
                        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest flex items-center gap-1.5"><CheckCircle className="h-3 w-3 text-green-500" /> Income Limit</span>
                        <span className="text-lg font-black text-green-400">{income_limit && income_limit !== '0' && income_limit !== 'NA' ? `₹${Number(income_limit).toLocaleString('en-IN')}` : 'No Limit'}</span>
                    </div>
                    <div className="bg-[#0a0a0b]/80 border border-white/5 p-4 rounded-2xl flex flex-col gap-2 shadow-sm">
                        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest flex items-center gap-1.5"><MapPin className="h-3 w-3 text-blue-500" /> Allowed State</span>
                        <span className="text-lg font-black text-blue-400 line-clamp-1">{applicable_states && applicable_states !== 'All' ? applicable_states : 'All-India Active'}</span>
                    </div>
                </div>

                <div className="grid lg:grid-cols-3 gap-8">
                    <div className="lg:col-span-2 space-y-8">
                        {/* Overview Card */}
                        <Card className="bg-white/5 border-white/10 backdrop-blur-xl rounded-3xl overflow-hidden shadow-2xl">
                            <CardHeader className="border-b border-white/5 bg-black/20 pb-4">
                                <CardTitle className="text-xl font-bold flex items-center gap-2">
                                    <CheckCircle className="h-5 w-5 text-green-400" />
                                    Full Analysis & Benefits
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="p-6 md:p-8">
                                <p className="text-slate-300 text-lg leading-relaxed">
                                    {benefit_description || (
                                        <span className="italic opacity-70">
                                            Detailed benefits for this scheme are currently unavailable in our database, but based on broader policy frameworks, it provides substantial support aligned with the ministry's goals. Please refer to the official portal for precise guidelines.
                                        </span>
                                    )}
                                </p>

                                <div className="grid sm:grid-cols-2 gap-4 mt-8">
                                    <div className="bg-black/30 p-4 rounded-2xl border border-white/5">
                                        <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Applicable Area</div>
                                        <div className="flex items-center gap-2 text-white font-medium">
                                            <MapPin className="h-4 w-4 text-blue-400" />
                                            {applicable_states || 'All India'}
                                        </div>
                                    </div>
                                    <div className="bg-black/30 p-4 rounded-2xl border border-white/5">
                                        <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Information Source</div>
                                        <div className="flex items-center gap-2 text-blue-300 font-medium">
                                            <Globe className="h-4 w-4" />
                                            <a href={source_url || '#'} target="_blank" className="hover:underline line-clamp-1">{source_url || 'Official Portal'}</a>
                                        </div>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Documents Card */}
                        <Card className="bg-white/5 border-white/10 backdrop-blur-xl rounded-3xl overflow-hidden shadow-2xl">
                            <CardHeader className="border-b border-white/5 bg-black/20 pb-4">
                                <CardTitle className="text-xl font-bold flex items-center gap-2">
                                    <Download className="h-5 w-5 text-purple-400" />
                                    Required Documents
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="p-6 md:p-8">
                                {docsList.length > 0 ? (
                                    <ul className="grid sm:grid-cols-2 gap-3">
                                        {docsList.map((doc, idx) => (
                                            <li key={idx} className="flex gap-3 bg-black/20 p-3 rounded-xl border border-white/5">
                                                <CheckCircle className="h-5 w-5 shrink-0 text-purple-400/70" />
                                                <span className="text-slate-300 text-sm">{doc}</span>
                                            </li>
                                        ))}
                                    </ul>
                                ) : (
                                    <Alert className="bg-purple-500/10 border-purple-500/20 text-purple-200">
                                        <AlertTitle>Check Officially</AlertTitle>
                                        <AlertDescription>
                                            The specific document list is not recorded. Generally, identity proof (Aadhaar), income certificate, and residence proof are standard requirements.
                                        </AlertDescription>
                                    </Alert>
                                )}
                            </CardContent>
                        </Card>
                    </div>

                    <div className="space-y-6">
                        {/* Quick Actions */}
                        <Card className="bg-gradient-to-br from-blue-900/40 to-purple-900/20 border-white/10 backdrop-blur-xl rounded-3xl overflow-hidden shadow-[0_8px_32px_rgba(30,58,138,0.2)]">
                            <CardContent className="p-6 flex flex-col gap-4">
                                <Button className="w-full py-6 rounded-2xl bg-white text-black hover:bg-slate-200 font-bold text-lg" asChild>
                                    <a href={application_url || source_url || '#'} target="_blank">
                                        Apply Officially <ExternalLink className="ml-2 h-5 w-5" />
                                    </a>
                                </Button>
                                <WhatsAppShareButton 
                                    schemeName={scheme_name || 'Scheme Highlights'} 
                                    schemeId={schemeId} 
                                    ministry={ministry || 'Government of India'} 
                                />
                                <div className="mt-4 pt-4 border-t border-white/10">
                                    <MatchLogicReasoning schemeCriteria={{
                                        min_age: min_age || '0',
                                        max_age: max_age || '100',
                                        income_limit: income_limit || '10000000',
                                        applicable_states: applicable_states || 'All',
                                        category: scheme_category || 'Any'
                                    }} />
                                </div>
                                <p className="text-xs text-center text-slate-400 opacity-80 mt-2 px-2">
                                    You will be redirected to the official government portal to submit your application.
                                </p>
                            </CardContent>
                        </Card>

                        {/* AI Advisor Context Box */}
                        <Card className="bg-white/5 border-white/10 backdrop-blur-xl rounded-3xl overflow-hidden shadow-2xl">
                            <CardContent className="p-6">
                                <div className="flex items-center gap-3 mb-4">
                                    <div className="h-10 w-10 rounded-full bg-blue-500/20 border border-blue-500/30 flex items-center justify-center">
                                        <CheckCircle className="h-5 w-5 text-blue-400" />
                                    </div>
                                    <div>
                                        <h3 className="font-bold text-white">AI Advisor</h3>
                                        <p className="text-xs text-slate-400">Contextual Info</p>
                                    </div>
                                </div>
                                <div className="text-sm text-slate-400 leading-relaxed bg-black/20 p-4 rounded-xl">
                                    Remember that government workflows can take time. Submit all requested documents correctly in a single go to avoid delays. If you face issues, check the helpdesk contact on the official portal.
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                </div>
            </main>

            <Chatbot context={[scheme]} />
        </div>
    );
}
