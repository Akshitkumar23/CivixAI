'use client';

import { Card, CardContent } from "@/components/ui/card";
import { CheckSquare, FileText } from "lucide-react";

export function DocumentChecklistSection() {
  return (
    <section className="py-16 sm:py-24 bg-muted">
      <div className="container mx-auto px-4">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div className="max-w-md">
            <h2 className="text-3xl sm:text-4xl font-bold text-primary">
              Know What You Need Before You Apply
            </h2>
            <p className="mt-4 text-lg text-muted-foreground">
              Our auto-generated checklists give you scheme-wise clarity on all required paperwork, significantly reducing the risk of application rejection.
            </p>
            <ul className="mt-6 space-y-4">
              <li className="flex items-start gap-3">
                <CheckSquare className="w-6 h-6 text-secondary mt-1 flex-shrink-0" />
                <span><span className="font-semibold">Personalized Checklists:</span> Get a list of documents based on the exact schemes you are eligible for.</span>
              </li>
              <li className="flex items-start gap-3">
                <CheckSquare className="w-6 h-6 text-secondary mt-1 flex-shrink-0" />
                <span><span className="font-semibold">Reduce Rejection Risk:</span> Avoid common mistakes and ensure your application is complete the first time.</span>
              </li>
            </ul>
          </div>
          <div className="flex justify-center">
            <Card className="p-8 bg-background shadow-xl w-full max-w-sm">
              <CardContent className="p-0">
                <div className="flex items-center justify-center mb-6">
                    <FileText className="w-16 h-16 text-primary" />
                </div>
                <h3 className="text-lg font-semibold text-center mb-4">Sample Document Checklist</h3>
                <ul className="space-y-3">
                    <li className="flex items-center gap-3 p-2 rounded-md bg-muted">
                        <CheckSquare className="w-5 h-5 text-green-600" />
                        <span>Aadhar Card</span>
                    </li>
                    <li className="flex items-center gap-3 p-2 rounded-md bg-muted">
                        <CheckSquare className="w-5 h-5 text-green-600" />
                        <span>Ration Card</span>
                    </li>
                    <li className="flex items-center gap-3 p-2 rounded-md bg-muted">
                        <CheckSquare className="w-5 h-5 text-green-600" />
                        <span>Income Certificate</span>
                    </li>
                     <li className="flex items-center gap-3 p-2 rounded-md bg-muted">
                        <CheckSquare className="w-5 h-5 text-green-600" />
                        <span>Bank Passbook</span>
                    </li>
                </ul>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </section>
  );
}
