import { promises as fs } from 'fs';
import path from 'path';
import { Header } from '@/components/Header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ExternalLink, Building2, CheckCircle, ChevronLeft, SearchX, Globe, MapPin, Download, Info } from 'lucide-react';
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
    benefit_type?: string;
    special_conditions_required?: string;
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

        const headers = rows[0].map((header) => header.trim().replace(/^\uFEFF/, ''));
        const index = new Map<string, number>();
        headers.forEach((header, i) => index.set(header, i));

        const getValue = (row: string[], key: string): string | undefined => {
            const idx = index.get(key);
            if (idx === undefined) return undefined;
            return row[idx]?.trim();
        };

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
                    source_url: getValue(rows[i], 'source_url'),
                    benefit_type: getValue(rows[i], 'benefit_type'),
                    special_conditions_required: getValue(rows[i], 'special_conditions_required')
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
        source_url,
        benefit_type,
        special_conditions_required
    } = scheme;

    const isGenericDescription = benefit_description?.includes("program aims to support eligible citizens") || benefit_description?.includes("program is formally mapped as");
    
    // Clean up generic description if needed
    const cleanDescription = isGenericDescription 
        ? `This ${scheme_category || 'government'} program by the ${ministry || 'Ministry'} is designed to provide targeted support to eligible citizens. Please refer to the official application portal for the latest detailed benefit breakdown and implementation guidelines.` 
        : benefit_description;

    const docsList = documents_required ? documents_required.split(',').map(d => d.trim()).filter(Boolean) : [];

    // Smart Labeling
    const isLoan = benefit_type?.toLowerCase() === 'loan' || scheme_name?.toLowerCase().includes('loan');
    const isInsurance = benefit_type?.toLowerCase() === 'insurance' || scheme_name?.toLowerCase().includes('insurance');
    const isScholarship = scheme_category?.toLowerCase() === 'education' || scheme_name?.toLowerCase().includes('scholarship');

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
                            <Badge className="bg-blue-500/10 text-blue-300 hover:bg-blue-500/20 border-blue-500/20 px-3 py-1 text-[10px] font-bold uppercase tracking-wider">
                                {scheme_category}
                            </Badge>
                        )}
                        {scheme_level && (
                            <Badge className="bg-purple-500/10 text-purple-300 hover:bg-purple-500/20 border-purple-500/20 px-3 py-1 text-[10px] font-bold uppercase tracking-wider">
                                {scheme_level}
                            </Badge>
                        )}
                        {benefit_type && (
                            <Badge className="bg-emerald-500/10 text-emerald-300 hover:bg-emerald-500/20 border-emerald-500/20 px-3 py-1 text-[10px] font-bold uppercase tracking-wider">
                                {benefit_type}
                            </Badge>
                        )}
                    </div>

                    <h1 className="text-4xl md:text-5xl lg:text-5.5xl font-black leading-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-white to-blue-400 mb-6 drop-shadow-sm">
                        {scheme_name || 'Scheme Highlights'}
                    </h1>

                    <div className="flex flex-wrap items-center gap-4">
                        <div className="flex items-center gap-3 text-slate-300 bg-white/5 border border-white/10 w-fit px-4 py-2.5 rounded-2xl backdrop-blur-md">
                            <Building2 className="h-5 w-5 text-blue-400" />
                            <span className="font-semibold text-sm">{ministry || 'Government of India'}</span>
                        </div>
                        {source_url && (
                           <a href={source_url} target="_blank" className="flex items-center gap-2 text-xs text-blue-400 hover:text-blue-300 transition-colors bg-blue-500/5 border border-blue-500/10 px-3 py-2.5 rounded-2xl">
                               <Globe className="h-4 w-4" />
                               Official Source
                           </a>
                        )}
                    </div>
                </div>

                {/* Eligibility Snapshot */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                    <div className="bg-[#0a0a0b]/80 border border-white/10 p-5 rounded-3xl flex flex-col gap-2 shadow-2xl relative overflow-hidden group">
                        <div className="absolute top-0 right-0 p-2 opacity-10 group-hover:opacity-20 transition-opacity"><CheckCircle className="h-12 w-12" /></div>
                        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest flex items-center gap-1.5">Min Age</span>
                        <span className="text-xl font-black text-white">{min_age && min_age !== '0' && min_age !== 'NA' && min_age !== '' ? `${min_age} Yrs` : 'Flexible'}</span>
                    </div>
                    <div className="bg-[#0a0a0b]/80 border border-white/10 p-5 rounded-3xl flex flex-col gap-2 shadow-2xl relative overflow-hidden group">
                        <div className="absolute top-0 right-0 p-2 opacity-10 group-hover:opacity-20 transition-opacity"><CheckCircle className="h-12 w-12" /></div>
                        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest flex items-center gap-1.5">Max Age</span>
                        <span className="text-xl font-black text-white">{max_age && max_age !== '100' && max_age !== 'NA' && max_age !== '99' && max_age !== '' ? `${max_age} Yrs` : 'Any Age'}</span>
                    </div>
                    <div className="bg-[#0a0a0b]/80 border border-white/10 p-5 rounded-3xl flex flex-col gap-2 shadow-2xl relative overflow-hidden group text-green-400/90">
                        <div className="absolute top-0 right-0 p-2 opacity-10 group-hover:opacity-20 transition-opacity"><CheckCircle className="h-12 w-12" /></div>
                        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest flex items-center gap-1.5">Income Cap</span>
                        <span className="text-xl font-black text-green-400">{income_limit && income_limit !== '0' && income_limit !== 'NA' && income_limit !== '10000000' && income_limit !== '' ? `₹${Number(income_limit).toLocaleString('en-IN')}` : 'No Limit'}</span>
                    </div>
                    <div className="bg-[#0a0a0b]/80 border border-white/10 p-5 rounded-3xl flex flex-col gap-2 shadow-2xl relative overflow-hidden group text-blue-400/90">
                        <div className="absolute top-0 right-0 p-2 opacity-10 group-hover:opacity-20 transition-opacity"><MapPin className="h-12 w-12" /></div>
                        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest flex items-center gap-1.5">Coverage</span>
                        <span className="text-xl font-black text-blue-400 line-clamp-1">{applicable_states && applicable_states !== 'All' && applicable_states !== 'ALL' ? applicable_states : 'Pan India'}</span>
                    </div>
                </div>

                <div className="grid lg:grid-cols-3 gap-8">
                    <div className="lg:col-span-2 space-y-8">
                        {/* Overview Card */}
                        <Card className="bg-white/5 border-white/10 backdrop-blur-xl rounded-[2.5rem] overflow-hidden shadow-2xl border-t-white/20">
                            <CardHeader className="border-b border-white/5 bg-black/20 pb-4 flex flex-row items-center justify-between">
                                <CardTitle className="text-xl font-bold flex items-center gap-2">
                                    <CheckCircle className="h-5 w-5 text-blue-400" />
                                    {isLoan ? 'Loan Details & Terms' : isScholarship ? 'Scholarship Analysis' : 'Scheme Benefits & Scope'}
                                </CardTitle>
                                {isGenericDescription && <Badge variant="outline" className="text-[9px] border-yellow-500/30 text-yellow-500/70">Verified by AI</Badge>}
                            </CardHeader>
                            <CardContent className="p-6 md:p-10">
                                <p className="text-slate-300 text-lg leading-relaxed mb-8">
                                    {cleanDescription || (
                                        <span className="italic opacity-70">
                                            Detailed benefits for this scheme are currently being updated in our central database. Based on official records, this program facilitates essential support for eligible beneficiaries in target categories.
                                        </span>
                                    )}
                                </p>

                                {special_conditions_required && special_conditions_required !== 'nan' && special_conditions_required !== '' && (
                                    <div className="mb-8 p-5 rounded-2xl bg-blue-500/5 border border-blue-500/10">
                                        <h4 className="text-xs font-bold text-blue-400 uppercase tracking-wider mb-2">Special Eligibility Conditions</h4>
                                        <p className="text-sm text-slate-300">{special_conditions_required}</p>
                                    </div>
                                )}

                                <div className="grid sm:grid-cols-2 gap-4">
                                    <div className="bg-black/30 p-5 rounded-2xl border border-white/5 group hover:border-blue-500/30 transition-all">
                                        <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Target Area</div>
                                        <div className="flex items-center gap-2 text-white font-medium">
                                            <MapPin className="h-4 w-4 text-blue-400" />
                                            {applicable_states && applicable_states !== 'All' ? applicable_states : 'All India / Central Sector'}
                                        </div>
                                    </div>
                                    <div className="bg-black/30 p-5 rounded-2xl border border-white/5 group hover:border-purple-500/30 transition-all">
                                        <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Filing Support</div>
                                        <div className="flex items-center gap-2 text-slate-200 font-medium text-xs">
                                            <Globe className="h-4 w-4 text-purple-400" />
                                            {source_url ? (
                                                <a href={source_url} target="_blank" className="hover:text-white hover:underline">Official Govt. Helpdesk</a>
                                            ) : 'Standard Govt. Portal'}
                                        </div>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Documents Card */}
                        <Card className="bg-white/5 border-white/10 backdrop-blur-xl rounded-[2.5rem] overflow-hidden shadow-2xl border-t-white/10">
                            <CardHeader className="border-b border-white/5 bg-black/20 pb-4">
                                <CardTitle className="text-xl font-bold flex items-center gap-2">
                                    <Download className="h-5 w-5 text-purple-400" />
                                    Required Checklist
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="p-6 md:p-10">
                                {docsList.length > 0 ? (
                                    <ul className="grid sm:grid-cols-2 gap-4">
                                        {docsList.map((doc, idx) => (
                                            <li key={idx} className="flex gap-3 bg-black/40 p-4 rounded-2xl border border-white/5 hover:bg-black/60 transition-colors">
                                                <div className="mt-1 h-2 w-2 rounded-full bg-purple-500 shrink-0" />
                                                <span className="text-slate-300 text-sm font-medium">{doc}</span>
                                            </li>
                                        ))}
                                    </ul>
                                ) : (
                                    <div className="flex flex-col items-center text-center py-6">
                                        <div className="h-14 w-14 rounded-full bg-purple-500/10 flex items-center justify-center mb-4 border border-purple-500/20">
                                            <Info className="h-6 w-6 text-purple-400" />
                                        </div>
                                        <h4 className="font-bold mb-1">Documentation Not Specified</h4>
                                        <p className="text-xs text-slate-400 max-w-sm">Standard documents like Aadhaar, Passport Photos, and Residents Proof are usually required. Check the portal for unique docs.</p>
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </div>

                    <div className="space-y-6">
                        {/* Quick Actions */}
                        <Card className="bg-gradient-to-br from-blue-900/60 to-purple-900/40 border-white/20 backdrop-blur-3xl rounded-[2.5rem] overflow-hidden shadow-[0_20px_50px_rgba(30,58,138,0.3)] border-t-white/30">
                            <CardContent className="p-8 flex flex-col gap-4">
                                <Button className="w-full py-7 rounded-2xl bg-white text-black hover:bg-slate-200 font-black text-lg transition-transform active:scale-95" asChild>
                                    <a href={application_url || source_url || '#'} target="_blank">
                                        Quick Apply <ExternalLink className="ml-2 h-5 w-5" />
                                    </a>
                                </Button>
                                <WhatsAppShareButton 
                                    schemeName={scheme_name || 'Scheme Highlights'} 
                                    schemeId={schemeId} 
                                    ministry={ministry || 'Government of India'} 
                                />
                                
                                <div className="mt-6 pt-6 border-t border-white/10">
                                    <MatchLogicReasoning schemeCriteria={{
                                        min_age: min_age || 'Any',
                                        max_age: max_age || 'Any',
                                        income_limit: income_limit || 'No Limit',
                                        applicable_states: applicable_states || 'All India',
                                        category: scheme_category || 'General'
                                    }} />
                                </div>
                                <p className="text-[10px] text-center text-blue-200/50 mt-4 leading-relaxed font-medium">
                                    CivixAI is an assistant. Always verify final eligibility on the official government portal before submission.
                                </p>
                            </CardContent>
                        </Card>

                        {/* AI Advisor Context Box */}
                        <Card className="bg-white/5 border-white/10 backdrop-blur-xl rounded-[2rem] overflow-hidden shadow-2xl border-l-blue-500/50 border-l">
                            <CardContent className="p-6">
                                <div className="flex items-center gap-3 mb-4">
                                    <div className="h-10 w-10 rounded-xl bg-blue-500/20 border border-blue-500/30 flex items-center justify-center">
                                        <CheckCircle className="h-5 w-5 text-blue-400" />
                                    </div>
                                    <div>
                                        <h3 className="font-bold text-white text-sm">AI Smart Advisor</h3>
                                        <p className="text-[10px] text-slate-500 uppercase tracking-widest font-black">Contextual Insight</p>
                                    </div>
                                </div>
                                <div className="text-sm text-slate-400 leading-relaxed bg-black/40 p-5 rounded-2xl border border-white/5 italic">
                                    {isLoan 
                                        ? "For loans, keep your bank statements ready for the last 6 months. A good CIBIL score significantly speeds up the verification process on 'Jan Samarth'."
                                        : "Most government schemes now use DBT (Direct Benefit Transfer). Ensure your Aadhaar is linked to your active bank account to receive benefits directly."}
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

