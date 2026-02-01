'use client';

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { GitCompareArrows, IndianRupee, FileText, CheckSquare, Clock } from "lucide-react";

const factors = [
    { icon: <IndianRupee className="w-5 h-5 text-primary"/>, text: "Benefit amount"},
    { icon: <CheckSquare className="w-5 h-5 text-primary"/>, text: "Eligibility complexity"},
    { icon: <FileText className="w-5 h-5 text-primary"/>, text: "Documents required"},
    { icon: <Clock className="w-5 h-5 text-primary"/>, text: "Processing time"},
    { icon: <GitCompareArrows className="w-5 h-5 text-primary"/>, text: "Similar or overlapping schemes"},
]

export function SchemeComparisonSection() {
  return (
    <section className="py-16 sm:py-24 bg-background">
      <div className="container mx-auto px-4">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div>
            <h2 className="text-3xl sm:text-4xl font-bold text-primary">
              Compare. Decide. Benefit More.
            </h2>
            <p className="mt-4 text-lg text-muted-foreground">
              CivixAI doesn't just list schemes. It helps you compare them on factors that matter, so you can make the smartest choice for your needs.
            </p>
            <div className="mt-6 grid grid-cols-2 gap-4">
                {factors.map(factor => (
                    <div key={factor.text} className="flex items-center gap-3">
                        {factor.icon}
                        <span className="font-medium">{factor.text}</span>
                    </div>
                ))}
            </div>
          </div>
          <div className="flex justify-center">
            <Card className="p-6 bg-muted shadow-xl w-full max-w-lg">
                <CardHeader className="p-0 mb-4">
                    <CardTitle className="text-center text-xl">Scheme Comparison</CardTitle>
                </CardHeader>
              <CardContent className="p-0">
                <div className="grid grid-cols-3 gap-2 text-center text-sm font-semibold">
                    <div className="p-2 rounded-t-lg"></div>
                    <div className="bg-primary/10 p-2 rounded-t-lg">Scheme A</div>
                    <div className="bg-primary/10 p-2 rounded-t-lg">Scheme B</div>
                </div>
                <div className="grid grid-cols-3 gap-2 text-center text-sm items-center mt-1">
                    <div className="font-semibold text-left p-2">Benefit</div>
                    <div className="bg-background p-2 rounded-md">₹5 Lakh Insurance</div>
                    <div className="bg-background p-2 rounded-md">₹10,000 Stipend</div>
                </div>
                <div className="grid grid-cols-3 gap-2 text-center text-sm items-center mt-1">
                    <div className="font-semibold text-left p-2">Docs Needed</div>
                    <div className="bg-background p-2 rounded-md">3</div>
                    <div className="bg-background p-2 rounded-md">2</div>
                </div>
                 <div className="grid grid-cols-3 gap-2 text-center text-sm items-center mt-1">
                    <div className="font-semibold text-left p-2">Eligibility</div>
                    <div className="bg-background p-2 rounded-md">Medium</div>
                    <div className="bg-background p-2 rounded-md">Easy</div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </section>
  );
}
