'use server';

/**
 * @fileOverview This file defines a Genkit flow to generate a summary of the application process for a given scheme.
 *
 * - generateSchemeDetails - A function that generates a summary of the application process for a given scheme.
 * - GenerateSchemeDetailsInput - The input type for the generateSchemeDetails function.
 * - GenerateSchemeDetailsOutput - The return type for the generateSchemeDetails function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

const GenerateSchemeDetailsInputSchema = z.object({
  schemeName: z.string().describe('The name of the scheme.'),
  eligibilityCriteria: z.string().describe('The eligibility criteria for the scheme.'),
  benefits: z.string().describe('The benefits of the scheme.'),
  documentsRequired: z.string().describe('The documents required for the scheme.'),
  applicationProcess: z.string().describe('The detailed application process for the scheme.'),
});
export type GenerateSchemeDetailsInput = z.infer<typeof GenerateSchemeDetailsInputSchema>;

const GenerateSchemeDetailsOutputSchema = z.object({
  summary: z.string().describe('A concise summary of the application process.'),
});
export type GenerateSchemeDetailsOutput = z.infer<typeof GenerateSchemeDetailsOutputSchema>;

export async function generateSchemeDetails(input: GenerateSchemeDetailsInput): Promise<GenerateSchemeDetailsOutput> {
  return generateSchemeDetailsFlow(input);
}

const prompt = ai.definePrompt({
  name: 'generateSchemeDetailsPrompt',
  input: {schema: GenerateSchemeDetailsInputSchema},
  output: {schema: GenerateSchemeDetailsOutputSchema},
  prompt: `You are an AI assistant designed to summarize application processes for government schemes.

  Given the following information about a scheme, provide a concise summary of the application process.

  Scheme Name: {{{schemeName}}}
  Eligibility Criteria: {{{eligibilityCriteria}}}
  Benefits: {{{benefits}}}
  Documents Required: {{{documentsRequired}}}
  Application Process: {{{applicationProcess}}}

  Summary:`,
});

const generateSchemeDetailsFlow = ai.defineFlow(
  {
    name: 'generateSchemeDetailsFlow',
    inputSchema: GenerateSchemeDetailsInputSchema,
    outputSchema: GenerateSchemeDetailsOutputSchema,
  },
  async input => {
    const {output} = await prompt(input);
    return output!;
  }
);
