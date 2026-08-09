import { Router, Response } from "express";
import { z } from "zod";
import { prisma } from "../config/prisma";
import { requireAuth, AuthRequest } from "../middleware/auth";
import { calculateNutritionTargets } from "../services/nutritionCalculator";
import { explainNutritionPlan } from "../services/aiExplainerService";

const router = Router();

const profileSchema = z.object({
  currentWeightKg: z.number().positive(),
  targetWeightKg: z.number().positive(),
  activityLevel: z.enum(["SEDENTARY", "LIGHT", "MODERATE", "ACTIVE", "VERY_ACTIVE"]),
  fitnessGoal: z.enum(["WEIGHT_LOSS", "WEIGHT_GAIN", "MUSCLE_GAIN", "MAINTENANCE"]),
  dietaryPreference: z.enum(["VEGETARIAN", "NON_VEGETARIAN", "VEGAN"]),
  allergies: z.array(z.string()).default([]),
  dailyBudget: z.number().positive(),
});

// Phase 2 + 3: submit health assessment, get back BMI/BMR/TDEE/macros
router.post("/", requireAuth, async (req: AuthRequest, res: Response) => {
  const parsed = profileSchema.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({ error: parsed.error.flatten() });
  }

  const user = await prisma.user.findUnique({ where: { id: req.userId } });
  if (!user || !user.age || !user.gender || !user.heightCm) {
    return res.status(400).json({
      error: "Complete your basic profile (age, gender, height) before submitting the health assessment",
    });
  }

  const data = parsed.data;

  const targets = calculateNutritionTargets({
    weightKg: data.currentWeightKg,
    heightCm: user.heightCm,
    age: user.age,
    gender: user.gender,
    activityLevel: data.activityLevel,
    fitnessGoal: data.fitnessGoal,
  });

  const profile = await prisma.healthProfile.upsert({
    where: { userId: user.id },
    create: {
      userId: user.id,
      currentWeightKg: data.currentWeightKg,
      targetWeightKg: data.targetWeightKg,
      activityLevel: data.activityLevel,
      fitnessGoal: data.fitnessGoal,
      dietaryPreference: data.dietaryPreference,
      allergies: data.allergies,
      dailyBudget: data.dailyBudget,
      bmi: targets.bmi,
      bmr: targets.bmr,
      tdee: targets.tdee,
      proteinTargetG: targets.proteinTargetG,
      carbTargetG: targets.carbTargetG,
      fatTargetG: targets.fatTargetG,
    },
    update: {
      currentWeightKg: data.currentWeightKg,
      targetWeightKg: data.targetWeightKg,
      activityLevel: data.activityLevel,
      fitnessGoal: data.fitnessGoal,
      dietaryPreference: data.dietaryPreference,
      allergies: data.allergies,
      dailyBudget: data.dailyBudget,
      bmi: targets.bmi,
      bmr: targets.bmr,
      tdee: targets.tdee,
      proteinTargetG: targets.proteinTargetG,
      carbTargetG: targets.carbTargetG,
      fatTargetG: targets.fatTargetG,
    },
  });

  let explanation: string | null = null;
  try {
    explanation = await explainNutritionPlan({
      calorieTarget: targets.calorieTarget,
      proteinTargetG: targets.proteinTargetG,
      carbTargetG: targets.carbTargetG,
      fatTargetG: targets.fatTargetG,
      fitnessGoal: data.fitnessGoal,
    });
  } catch {
    explanation = null; // non-fatal - LLM layer is optional
  }

  return res.status(201).json({ profile, targets, explanation });
});

router.get("/", requireAuth, async (req: AuthRequest, res: Response) => {
  const profile = await prisma.healthProfile.findUnique({ where: { userId: req.userId } });
  if (!profile) return res.status(404).json({ error: "No health profile found" });
  return res.json({ profile });
});

export default router;
