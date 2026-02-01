'use server';

/**
 * @fileOverview Provides chatbot assistance to users, answering questions about schemes in Hinglish.
 *
 * - provideChatbotAssistance - A function that handles the chatbot assistance process.
 * - ProvideChatbotAssistanceInput - The input type for the provideChatbotAssistance function.
 * - ProvideChatbotAssistanceOutput - The return type for the provideChatbotAssistance function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

const ProvideChatbotAssistanceInputSchema = z.object({
  query: z.string().describe('The user query in Hinglish.'),
  schemeDetails: z.string().optional().describe('Details about specific schemes to provide context.'),
});
export type ProvideChatbotAssistanceInput = z.infer<
  typeof ProvideChatbotAssistanceInputSchema
>;

const ProvideChatbotAssistanceOutputSchema = z.object({
  answer: z.string().describe('The chatbot answer in Hinglish.'),
});
export type ProvideChatbotAssistanceOutput = z.infer<
  typeof ProvideChatbotAssistanceOutputSchema
>;

export async function provideChatbotAssistance(
  input: ProvideChatbotAssistanceInput
): Promise<ProvideChatbotAssistanceOutput> {
  return provideChatbotAssistanceFlow(input);
}

const prompt = ai.definePrompt({
  name: 'provideChatbotAssistancePrompt',
  input: {schema: ProvideChatbotAssistanceInputSchema},
  output: {schema: ProvideChatbotAssistanceOutputSchema},
  prompt: `You are a helpful chatbot assistant that answers questions about government schemes in Hinglish.

  You should provide clear, concise and easy to understand answers. Use simple language. Your goal is to help the user understand the schemes.

  Here are some scheme details: {{{schemeDetails}}}

  User Query: {{{query}}} `,
});

const provideChatbotAssistanceFlow = ai.defineFlow(
  {
    name: 'provideChatbotAssistanceFlow',
    inputSchema: ProvideChatbotAssistanceInputSchema,
    outputSchema: ProvideChatbotAssistanceOutputSchema,
  },
  async input => {
    const {output} = await prompt(input);
    return output!;
  }
);
