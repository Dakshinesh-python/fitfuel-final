/**
 * Free LLM layer using Groq's API (generous free tier, OpenAI-compatible format,
 * very low latency). Used ONLY for natural-language explanations / chat -
 * the actual nutrition numbers always come from nutritionCalculator.ts,
 * never from the LLM, so figures stay accurate and reproducible.
 *
 * Get a free key at https://console.groq.com
 */

const GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions";
const GROQ_MODEL = "llama-3.1-8b-instant"; // fast + free-tier friendly

interface NutritionTargetsForPrompt {
  calorieTarget: number;
  proteinTargetG: number;
  carbTargetG: number;
  fatTargetG: number;
  fitnessGoal: string;
}

interface GroqChatCompletionResponse {
  choices?: Array<{ message?: { content?: string } }>;
}

export async function explainNutritionPlan(targets: NutritionTargetsForPrompt): Promise<string> {
  const apiKey = process.env.GROQ_API_KEY;
  if (!apiKey) {
    // Graceful fallback if no key configured - app still works without the LLM
    return `Your daily target is ${targets.calorieTarget} kcal with ${targets.proteinTargetG}g protein, ` +
      `${targets.carbTargetG}g carbs and ${targets.fatTargetG}g fat, tailored for your ${targets.fitnessGoal.toLowerCase().replace("_", " ")} goal.`;
  }

  const prompt =
    `A user has a fitness goal of ${targets.fitnessGoal}. Their calculated daily targets are: ` +
    `${targets.calorieTarget} kcal, ${targets.proteinTargetG}g protein, ${targets.carbTargetG}g carbs, ${targets.fatTargetG}g fat. ` +
    `In 2-3 short, encouraging sentences, explain what this means for them in plain language. ` +
    `Do not invent different numbers - use exactly the ones given.`;

  const response = await fetch(GROQ_API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model: GROQ_MODEL,
      messages: [{ role: "user", content: prompt }],
      max_tokens: 200,
      temperature: 0.6,
    }),
  });

  if (!response.ok) {
    throw new Error(`Groq API error: ${response.status}`);
  }

  const data = (await response.json()) as GroqChatCompletionResponse;
  return data.choices?.[0]?.message?.content?.trim() ?? "";
}

export async function chatWithNutritionAssistant(
  userMessage: string,
  contextSummary: string
): Promise<string> {
  const apiKey = process.env.GROQ_API_KEY;
  if (!apiKey) {
    return "AI chat isn't configured yet. Add a free GROQ_API_KEY to enable this feature.";
  }

  const systemPrompt =
    `You are FitFuel's nutrition assistant. Be concise, encouraging, and practical. ` +
    `Never invent medical claims. Your reply should be concise and accurate (around 2-4 sentences), not too big, not too small. ` +
    `CRITICAL: Do NOT use any markdown formatting (no asterisks, no bold, no italics, no lists). Reply in plain text ONLY. ` +
    `Here is the user's current profile summary: ${contextSummary}`;

  const response = await fetch(GROQ_API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model: GROQ_MODEL,
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: userMessage },
      ],
      max_tokens: 600,
      temperature: 0.7,
    }),
  });

  if (!response.ok) {
    throw new Error(`Groq API error: ${response.status}`);
  }

  const data = (await response.json()) as GroqChatCompletionResponse;
  return data.choices?.[0]?.message?.content?.trim() ?? "";
}
