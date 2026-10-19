'use server';

/**
 * @fileOverview Provides chatbot assistance to users, answering questions about schemes in Hinglish.
 *
 * - provideChatbotAssistance - A function that handles the chatbot assistance process.
 * - ProvideChatbotAssistanceInput - The input type for the provideChatbotAssistance function.
 * - ProvideChatbotAssistanceOutput - The return type for the provideChatbotAssistance function.
 */

import { ai } from '@/ai/genkit';
import { z } from 'genkit';

const ProvideChatbotAssistanceInputSchema = z.object({
  query: z.string().describe('The user query in Hinglish.'),
  schemeDetails: z.string().optional().describe('Details about specific schemes to provide context.'),
});
export type ProvideChatbotAssistanceInput = z.infer<
  typeof ProvideChatbotAssistanceInputSchema
>;

const ProvideChatbotAssistanceOutputSchema = z.object({
  answer: z.string().describe('The chatbot answer in Hinglish.'),
  redirectUrl: z.string().optional().describe('An optional URL to redirect the user to, e.g. if they provide age and income, generate /recommendations?age=X&annualIncome=Y'),
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
  input: { schema: ProvideChatbotAssistanceInputSchema },
  output: { schema: ProvideChatbotAssistanceOutputSchema },
  prompt: `You are a helpful chatbot assistant that answers questions about government schemes in Hinglish.

  If the user provides their basic demographic details (like age, income, state, category, etc.) and asks for schemes, generate a \`redirectUrl\` field in the output with the path \`/recommendations\` and query parameters. For example: \`/recommendations?age=25&annualIncome=300000\`.
  Otherwise, just provide clear, concise and easy to understand answers. Use simple language.

  Here are some scheme details for context (if any): {{{schemeDetails}}}

  User Query: {{{query}}} `,
});

const provideChatbotAssistanceFlow = ai.defineFlow(
  {
    name: 'provideChatbotAssistanceFlow',
    inputSchema: ProvideChatbotAssistanceInputSchema,
    outputSchema: ProvideChatbotAssistanceOutputSchema,
  },
  async input => {
    try {
      // Truncate context if it's too large to prevent token limit errors
      const truncatedInput = {
        ...input,
        schemeDetails: input.schemeDetails ? input.schemeDetails.slice(0, 10000) : ''
      };

      const { output } = await prompt(truncatedInput);
      return output!;
    } catch (error) {
      console.error('Chatbot AI Error:', error);
      return {
        answer: "Maaf kijiye, abhi hamare AI servers par bahut load hai. Main aapki query thodi der mein process kar paunga. Tab tak aap hamari recommendation list check kar sakte hain!"
      };
    }
  }
);
