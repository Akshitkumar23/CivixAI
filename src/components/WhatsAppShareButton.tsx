'use client';
import { Button } from '@/components/ui/button';
import { MessageCircle } from 'lucide-react';

interface WhatsAppShareButtonProps {
    schemeName: string;
    schemeId: string;
    ministry: string;
}

export function WhatsAppShareButton({ schemeName, schemeId, ministry }: WhatsAppShareButtonProps) {
    const handleShare = () => {
        const url = `https://civix-ai.vercel.app/scheme/${schemeId}`;
        const text = encodeURIComponent(`👋 Check out this government scheme on CivixAI!\n\n📌 *${schemeName}*\n🏦 Ministry: ${ministry}\n\nRead more & Apply here: ${url}`);
        window.open(`https://wa.me/?text=${text}`, '_blank');
    };

    return (
        <Button 
            onClick={handleShare}
            className="w-full py-6 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 hover:bg-emerald-500/20 font-bold transition-all flex items-center justify-center gap-2"
        >
            <MessageCircle className="h-5 w-5" /> Share on WhatsApp
        </Button>
    );
}
