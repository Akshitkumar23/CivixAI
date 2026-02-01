// Type declarations to bypass TypeScript issues with @genkit-ai/google-genai
declare module '@genkit-ai/google-genai' {
  export function googleAI(): any;
}