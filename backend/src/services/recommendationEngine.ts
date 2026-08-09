/**
 * Ranks candidate meals against a user's nutrition targets and preferences.
 * This is the "intelligent recommendation" layer referenced in Phase 5.
 * It's a transparent weighted-scoring model (not a black-box ML model) -
 * appropriate for a project of this scope and fully explainable to evaluators.
 */

export interface MealCandidate {
  id: string;
  calories: number;
  proteinG: number;
  carbsG: number;
  fatG: number;
  price: number;
  isVegetarian: boolean;
  isVegan: boolean;
  allergens: string[];
  healthScore: number; // 0-100, precomputed
}

export interface RecommendationContext {
  targetCaloriesPerMeal: number;
  targetProteinPerMeal: number;
  dailyBudgetPerMeal: number;
  dietaryPreference: "VEGETARIAN" | "NON_VEGETARIAN" | "VEGAN";
  allergies: string[];
}

export interface ScoredMeal {
  mealId: string;
  score: number; // 0-100
  breakdown: {
    calorieAccuracy: number;
    proteinQuality: number;
    budgetFit: number;
    healthScore: number;
  };
}

const WEIGHTS = {
  calorieAccuracy: 0.35,
  proteinQuality: 0.3,
  budgetFit: 0.15,
  healthScore: 0.2,
};

function isEligible(meal: MealCandidate, ctx: RecommendationContext): boolean {
  if (ctx.dietaryPreference === "VEGAN" && !meal.isVegan) return false;
  if (ctx.dietaryPreference === "VEGETARIAN" && !meal.isVegetarian && !meal.isVegan) return false;
  const hasAllergen = meal.allergens.some((a) => ctx.allergies.includes(a));
  if (hasAllergen) return false;
  return true;
}

function closenessScore(actual: number, target: number): number {
  // 100 when equal to target, decaying as the gap grows, floor at 0
  const pctDiff = Math.abs(actual - target) / target;
  return Math.max(0, 100 - pctDiff * 150);
}

export function scoreMeal(meal: MealCandidate, ctx: RecommendationContext): ScoredMeal | null {
  if (!isEligible(meal, ctx)) return null;

  const calorieAccuracy = closenessScore(meal.calories, ctx.targetCaloriesPerMeal);
  const proteinQuality = closenessScore(meal.proteinG, ctx.targetProteinPerMeal);
  const budgetFit = meal.price <= ctx.dailyBudgetPerMeal
    ? 100
    : Math.max(0, 100 - ((meal.price - ctx.dailyBudgetPerMeal) / ctx.dailyBudgetPerMeal) * 100);
  const healthScore = meal.healthScore;

  const score =
    calorieAccuracy * WEIGHTS.calorieAccuracy +
    proteinQuality * WEIGHTS.proteinQuality +
    budgetFit * WEIGHTS.budgetFit +
    healthScore * WEIGHTS.healthScore;

  return {
    mealId: meal.id,
    score: Number(score.toFixed(1)),
    breakdown: {
      calorieAccuracy: Number(calorieAccuracy.toFixed(1)),
      proteinQuality: Number(proteinQuality.toFixed(1)),
      budgetFit: Number(budgetFit.toFixed(1)),
      healthScore,
    },
  };
}

export function rankMeals(
  meals: MealCandidate[],
  ctx: RecommendationContext,
  topN = 5
): ScoredMeal[] {
  return meals
    .map((m) => scoreMeal(m, ctx))
    .filter((s): s is ScoredMeal => s !== null)
    .sort((a, b) => b.score - a.score)
    .slice(0, topN);
}
