import { rankMeals, scoreMeal, MealCandidate, RecommendationContext } from "../src/services/recommendationEngine";

const baseCtx: RecommendationContext = {
  targetCaloriesPerMeal: 500,
  targetProteinPerMeal: 35,
  dailyBudgetPerMeal: 200,
  dietaryPreference: "NON_VEGETARIAN",
  allergies: [],
};

function meal(overrides: Partial<MealCandidate>): MealCandidate {
  return {
    id: "meal-1",
    calories: 500,
    proteinG: 35,
    carbsG: 50,
    fatG: 15,
    price: 150,
    isVegetarian: false,
    isVegan: false,
    allergens: [],
    healthScore: 80,
    ...overrides,
  };
}

describe("scoreMeal", () => {
  it("gives a near-perfect score for a meal that exactly matches targets", () => {
    const scored = scoreMeal(meal({}), baseCtx);
    expect(scored).not.toBeNull();
    expect(scored!.score).toBeGreaterThan(90);
  });

  it("excludes meals with allergens the user is allergic to", () => {
    const scored = scoreMeal(meal({ allergens: ["peanuts"] }), { ...baseCtx, allergies: ["peanuts"] });
    expect(scored).toBeNull();
  });

  it("excludes non-vegetarian meals when user wants vegetarian", () => {
    const scored = scoreMeal(meal({ isVegetarian: false }), {
      ...baseCtx,
      dietaryPreference: "VEGETARIAN",
    });
    expect(scored).toBeNull();
  });

  it("allows vegan meals for vegetarian preference", () => {
    const scored = scoreMeal(meal({ isVegetarian: false, isVegan: true }), {
      ...baseCtx,
      dietaryPreference: "VEGETARIAN",
    });
    expect(scored).not.toBeNull();
  });

  it("penalizes meals over budget", () => {
    const withinBudget = scoreMeal(meal({ price: 150 }), baseCtx)!;
    const overBudget = scoreMeal(meal({ price: 400 }), baseCtx)!;
    expect(overBudget.score).toBeLessThan(withinBudget.score);
  });
});

describe("rankMeals", () => {
  it("returns meals sorted by descending score, capped at topN", () => {
    const meals = [
      meal({ id: "a", calories: 500, proteinG: 35 }), // perfect match
      meal({ id: "b", calories: 900, proteinG: 10 }), // poor match
      meal({ id: "c", calories: 520, proteinG: 32 }), // close match
    ];
    const ranked = rankMeals(meals, baseCtx, 2);
    expect(ranked).toHaveLength(2);
    expect(ranked[0].score).toBeGreaterThanOrEqual(ranked[1].score);
    expect(ranked.map((r) => r.mealId)).toContain("a");
  });
});
