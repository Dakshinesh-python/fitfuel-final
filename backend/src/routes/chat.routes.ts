import { Router, Response } from "express";
import { z } from "zod";
import { prisma } from "../config/prisma";
import { requireAuth, AuthRequest } from "../middleware/auth";
import { chatWithNutritionAssistant } from "../services/aiExplainerService";

const router = Router();

const chatSchema = z.object({
  message: z.string().min(1).max(500),
});

// POST /api/chat (auth required)
// Accepts { message }, builds a profile context summary, and delegates to the
// Groq-backed nutrition assistant (gracefully degrades if no API key is set).
router.post("/", requireAuth, async (req: AuthRequest, res: Response) => {
  const parsed = chatSchema.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({ error: parsed.error.flatten() });
  }

  const profile = await prisma.healthProfile.findUnique({ where: { userId: req.userId } });

  // Build a context string even if the user has no profile yet
  const contextSummary = profile
    ? `Goal: ${profile.fitnessGoal}, dietary preference: ${profile.dietaryPreference}, ` +
      `daily calorie target: ${profile.tdee ? Math.round(profile.tdee) : "unknown"} kcal, ` +
      `protein target: ${profile.proteinTargetG ?? "unknown"}g.`
    : "The user has not yet completed their health assessment.";

  let reply: string;
  try {
    reply = await chatWithNutritionAssistant(parsed.data.message, contextSummary);
  } catch {
    // Non-fatal — LLM layer is optional; return a safe fallback
    reply =
      "I'm having trouble connecting to the AI service right now. " +
      "Please try again later or check your nutrition targets on the dashboard.";
  }

  return res.json({ reply });
});

export default router;
