import { Award, CheckCircle, FileText, Landmark, HelpingHand } from 'lucide-react';
import type { RecommendedScheme } from '@/lib/types';
import { Badge } from '@/components/ui/badge';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { ApplicationProcess } from './ApplicationProcess';
import { AadharCardIcon } from './icons/AadharCardIcon';
import { RationCardIcon } from './icons/RationCardIcon';
import { BankPassbookIcon } from './icons/BankPassbookIcon';
import { IncomeCertificateIcon } from './icons/IncomeCertificateIcon';
import { Separator } from './ui/separator';

const priorityDetails = [
  { label: 'Highest Priority', color: 'bg-destructive', badgeVariant: 'destructive' as const },
  { label: 'High Priority', color: 'bg-accent', badgeVariant: 'secondary' as const },
  { label: 'Medium Priority', color: 'bg-chart-4', badgeVariant: 'secondary' as const },
];

const documentIcons: { [key: string]: React.FC<React.SVGProps<SVGSVGElement>> } = {
  'Aadhar Card': AadharCardIcon,
  'Ration Card': RationCardIcon,
  'Bank Passbook': BankPassbookIcon,
  'Income Certificate': IncomeCertificateIcon,
  'Proof of Identity': FileText,
};

const schemeIcons = {
  'PM-JAY': HelpingHand,
  'PMAY-U': Landmark,
  'Digital India Internship': CheckCircle,
  default: Award,
};

type RecommendationCardProps = {
  scheme: RecommendedScheme;
  priorityIndex: number;
};

export function RecommendationCard({ scheme, priorityIndex }: RecommendationCardProps) {
  const priority = priorityDetails[priorityIndex] || { label: 'Recommended', color: 'bg-primary', badgeVariant: 'default' as const };
  const SchemeIcon = schemeIcons[scheme.id as keyof typeof schemeIcons] || schemeIcons.default;

  return (
    <div className="group relative h-full">
      <div className="absolute -inset-px bg-gradient-to-r from-primary via-accent to-primary rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300 group-hover:animate-gradient-pan bg-[length:200%_auto]" />
      <Card className="relative flex flex-col bg-card shadow-lg h-full border-transparent transition-all duration-300 group-hover:bg-[radial-gradient(circle_at_center,_hsl(var(--primary)/0.15),_hsl(var(--card))_40%)]">
        <CardHeader>
          <div className="flex justify-between items-start">
              <div>
                  <CardTitle className="font-headline text-xl flex items-center gap-3">
                      <SchemeIcon className="w-6 h-6 text-primary" />
                      {scheme.name}
                  </CardTitle>
                  <CardDescription className="mt-1">{scheme.description}</CardDescription>
              </div>
              <Badge variant={priority.badgeVariant}>{priority.label}</Badge>
          </div>
        </CardHeader>
        <CardContent className="flex-grow space-y-6">
          <div>
            <h3 className="text-sm font-semibold text-muted-foreground mb-2">Estimated Benefit</h3>
            <p className="text-lg font-bold text-primary">{scheme.estimatedBenefit}</p>
          </div>
          
          <Separator />

          <div>
              <h3 className="text-sm font-semibold text-muted-foreground mb-2">Eligibility Confidence</h3>
              <div className="flex items-center gap-4">
                  <Progress value={scheme.confidence} className="w-full" indicatorClassName={priority.color} />
                  <span className="text-sm font-bold text-muted-foreground">{scheme.confidence}%</span>
              </div>
          </div>

          <Separator />
          
          <div>
            <h3 className="text-sm font-semibold text-muted-foreground mb-2">Documents Required</h3>
            <div className="flex flex-wrap gap-4">
              {scheme.documentsRequired.map((doc) => {
                const Icon = documentIcons[doc] || FileText;
                return (
                  <div key={doc} className="flex flex-col items-center text-center gap-1 w-20">
                    <div className="w-10 h-10 flex items-center justify-center rounded-lg bg-accent/20">
                      <Icon className="w-6 h-6 text-accent" />
                    </div>
                    <span className="text-xs text-foreground/80">{doc}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </CardContent>
        <CardFooter>
          <ApplicationProcess scheme={scheme} />
        </CardFooter>
      </Card>
    </div>
  );
}
