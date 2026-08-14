import { Router, Response } from "express";
import { MealType } from "@prisma/client";
import { prisma } from "../config/prisma";
import { requireAuth, AuthRequest } from "../middleware/auth";
import { rankMeals, MealCandidate } from "../services/recommendationEngine";

const router = Router();

const MEAL_TYPES: MealType[] = ["BREAKFAST", "LUNCH", "DINNER", "SNACK"];

// POST /api/meal-plans/generate
// Generates a 7-day meal plan (28 items) using the recommendation engine.
// For each day × meal-type slot, picks the highest-ranked eligible meal,
// avoiding the same meal appearing twice in the same day where possible.
router.post("/generate", requireAuth, async (req: AuthRequest, res: Response) => {
  const profile = await prisma.healthProfile.findUnique({ where: { userId: req.userId } });
  if (!profile || !profile.tdee || !profile.proteinTargetG) {
    return res.status(400).json({ error: "Complete your health assessment first" });
  }

  const targetCaloriesPerMeal = Math.round((profile.tdee ?? 2000) / 4);
  const targetProteinPerMeal = Math.round((profile.proteinTargetG ?? 100) / 4);
  const dailyBudgetPerMeal = profile.dailyBudget / 4;

  const ctx = {
    targetCaloriesPerMeal,
    targetProteinPerMeal,
    dailyBudgetPerMeal,
    dietaryPreference: profile.dietaryPreference,
    allergies: profile.allergies,
  };

  // Pre-fetch all meals grouped by type for efficiency
  const allMeals = await prisma.meal.findMany({ take: 500 });
  const mealsByType = new Map<MealType, MealCandidate[]>();
  for (const mt of MEAL_TYPES) {
    mealsByType.set(
      mt,
      allMeals
        .filter((m) => m.mealType === mt)
        .map((m) => ({
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
        }))
    );
  }

  // Week starts at the nearest Monday (Mon=0 .. Sun=6)
  const weekStart = new Date();
  const dayOfWeek = weekStart.getDay(); // 0=Sun in JS
  const daysToMonday = dayOfWeek === 0 ? -6 : 1 - dayOfWeek;
  weekStart.setDate(weekStart.getDate() + daysToMonday);
  weekStart.setHours(0, 0, 0, 0);

  const mealPlan = await prisma.mealPlan.create({
    data: { userId: req.userId!, weekStart },
  });

  const items: Array<{ dayOfWeek: number; mealType: MealType; mealId: string; matchScore: number }> = [];
  const usedIdsThisWeek = new Set<string>();

  for (let day = 0; day < 7; day++) {
    const usedIdsToday = new Set<string>();

    for (const mealType of MEAL_TYPES) {
      const candidates = mealsByType.get(mealType) ?? [];
      const ranked = rankMeals(candidates, ctx, 50);
      
      const unusedThisWeek = ranked.filter(r => !usedIdsThisWeek.has(r.mealId));
      let pick: typeof ranked[0] | undefined;

      if (unusedThisWeek.length > 0) {
        // Pick randomly from the top 3 unused to add variety across different generations
        const poolSize = Math.min(3, unusedThisWeek.length);
        pick = unusedThisWeek[Math.floor(Math.random() * poolSize)];
      } else {
        // Fallback: allow reuse but try to avoid reusing on the same day
        const unusedToday = ranked.filter(r => !usedIdsToday.has(r.mealId));
        if (unusedToday.length > 0) {
          const poolSize = Math.min(3, unusedToday.length);
          pick = unusedToday[Math.floor(Math.random() * poolSize)];
        } else {
          pick = ranked[0];
        }
      }

      if (pick) {
        usedIdsThisWeek.add(pick.mealId);
        usedIdsToday.add(pick.mealId);
        items.push({ dayOfWeek: day, mealType, mealId: pick.mealId, matchScore: pick.score });
      }
    }
  }

  await prisma.mealPlanItem.createMany({
    data: items.map((item) => ({ mealPlanId: mealPlan.id, ...item })),
  });

  const populated = await prisma.mealPlan.findUnique({
    where: { id: mealPlan.id },
    include: { items: { include: { meal: true } } },
  });

  return res.status(201).json({ mealPlan: populated });
});

// GET /api/meal-plans/current
// Returns the user's most recent meal plan with all items and meal details.
router.get("/current", requireAuth, async (req: AuthRequest, res: Response) => {
  const mealPlan = await prisma.mealPlan.findFirst({
    where: { userId: req.userId },
    orderBy: { createdAt: "desc" },
    include: { items: { include: { meal: true } } },
  });

  if (!mealPlan) return res.status(404).json({ error: "No meal plan found" });
  return res.json({ mealPlan });
});

export default router;
