'use client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Lightbulb } from 'lucide-react';

const problems = [
    { title: 'Scattered Schemes', description: 'Benefits are spread across hundreds of confusing websites.' },
    { title: 'Complex Eligibility', description: 'Rules are hard to understand, leading to missed opportunities.' },
    { title: 'Lack of Guidance', description: 'No personalized help to navigate the application process.' },
];

export function ProblemSection() {
    return (
        <section className="py-16 sm:py-24 bg-background">
            <div className="container mx-auto px-4">
                <div className="text-center max-w-3xl mx-auto">
                    <h2 className="font-headline text-3xl sm:text-4xl font-bold text-primary">
                        The Challenge: A Maze of Missed Opportunities
                    </h2>
                    <p className="mt-4 text-lg text-muted-foreground">
                        Every year, millions of Indians miss out on government benefits they are entitled to simply because the system is too complex to navigate.
                    </p>
                </div>
                <div className="mt-12 grid md:grid-cols-3 gap-8">
                    {problems.map((problem) => (
                        <div key={problem.title} className="group relative">
                             <div className="absolute -inset-px bg-gradient-to-r from-primary via-accent to-primary rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300 group-hover:animate-gradient-pan bg-[length:200%_auto]" />
                            <Card className="relative bg-card shadow-lg h-full border-transparent transition-all duration-300 group-hover:bg-[radial-gradient(circle_at_center,_hsl(var(--primary)/0.15),_hsl(var(--card))_40%)]">
                                <CardHeader>
                                    <CardTitle className="font-headline text-xl">{problem.title}</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <p className="text-muted-foreground">{problem.description}</p>
                                </CardContent>
                            </Card>
                        </div>
                    ))}
                </div>
                <div className="mt-12 text-center">
                    <div className="group relative max-w-3xl mx-auto">
                         <div className="absolute -inset-px bg-gradient-to-r from-primary via-accent to-primary rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 group-hover:animate-gradient-pan bg-[length:200%_auto]" />
                        <Card className="relative p-8 bg-muted shadow-lg border-transparent">
                            <div className="flex flex-col md:flex-row items-center justify-center gap-4 text-center md:text-left">
                                <div className="bg-primary text-primary-foreground p-3 rounded-full flex-shrink-0">
                                    <Lightbulb className="w-7 h-7" />
                                </div>
                                <div>
                                    <h3 className="font-headline text-xl md:text-2xl font-bold text-primary">
                                        The Solution: AI-Powered Clarity
                                    </h3>
                                    <p className="text-muted-foreground mt-2">
                                    CivixAI uses artificial intelligence to simplify this complexity, providing a clear, personalized path to your benefits.
                                    </p>
                                </div>
                            </div>
                        </Card>
                    </div>
                </div>
            </div>
        </section>
    );
}
