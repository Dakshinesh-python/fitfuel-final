import { Router, Response } from "express";
import { z } from "zod";
import { MealType } from "@prisma/client";
import { prisma } from "../config/prisma";
import { requireAuth, AuthRequest } from "../middleware/auth";
import { rankMeals, MealCandidate } from "../services/recommendationEngine";

const router = Router();

const mealTypeSchema = z.nativeEnum(MealType);

// GET /api/recommendations?mealType=LUNCH
router.get("/", requireAuth, async (req: AuthRequest, res: Response) => {
  const mealTypeResult = mealTypeSchema.safeParse(req.query.mealType ?? "LUNCH");
  if (!mealTypeResult.success) {
    return res.status(400).json({ error: "Invalid mealType value" });
  }
  const mealType = mealTypeResult.data;

  const profile = await prisma.healthProfile.findUnique({ where: { userId: req.userId } });
  if (!profile || !profile.tdee || !profile.proteinTargetG) {
    return res.status(400).json({ error: "Complete your health assessment first" });
  }

  try {
    const candidateMeals = await prisma.meal.findMany({
      where: { mealType },
      take: 200,
    });

    const targetCaloriesPerMeal = Math.round((profile.tdee ?? 2000) / 4); // 4 meals/day incl. snack
    const targetProteinPerMeal = Math.round((profile.proteinTargetG ?? 100) / 4);
    const dailyBudgetPerMeal = profile.dailyBudget / 4;

    const candidates: MealCandidate[] = candidateMeals.map((m) => ({
      id: m.id,
      calories: m.calories,
      proteinG: m.proteinG,
      carbsG: m.carbsG,
      fatG: m.fatG,
      price: m.price,
      isVegetarian: m.isVegetarian,
      isVegan: m.isVegan,
      allergens: m.allergens,
      healthScore: m.healthScore,
    }));

    const ranked = rankMeals(
      candidates,
      {
        targetCaloriesPerMeal,
        targetProteinPerMeal,
        dailyBudgetPerMeal,
        dietaryPreference: profile.dietaryPreference,
        allergies: profile.allergies,
      },
      5
    );

    const mealsById = new Map(candidateMeals.map((m) => [m.id, m]));
    const results = ranked.map((r) => ({
      ...r,
      meal: mealsById.get(r.mealId),
    }));

    return res.json({ recommendations: results });
  } catch (err) {
    console.error(err);
    return res.status(400).json({ error: "Invalid query parameters" });
  }
});

export default router;