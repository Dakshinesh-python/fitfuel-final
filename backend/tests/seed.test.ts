/**
 * Unit tests for the healthScoreFor function and validateImageUrls guard used in seed.ts.
 * These are pure functions so we can test them in isolation from the database.
 */

// Inline the functions to avoid importing seed.ts (which runs main() as a side-effect)

function healthScoreFor(m: {
  proteinG: number;
  fatG: number;
  carbsG: number;
  calories: number;
}): number {
  const proteinRatio = (m.proteinG * 4) / m.calories;
  const fatRatio = (m.fatG * 9) / m.calories;
  const score = 100 * proteinRatio - 40 * fatRatio + 40;
  return Math.max(0, Math.min(100, Math.round(score)));
}

function validateImageUrls(meals: Array<{ name: string; imageUrl: string }>): void {
  const missing = meals
    .filter((m) => !m.imageUrl || m.imageUrl.trim() === "")
    .map((m) => m.name);
  if (missing.length > 0) {
    throw new Error(
      `[seed] ABORTED — the following meals are missing imageUrl:\n` +
        missing.map((n) => `  • ${n}`).join("\n")
    );
  }
}

describe("healthScoreFor (seed heuristic)", () => {
  it("gives a higher score to a high-protein / low-fat meal than a high-fat / low-protein one", () => {
    const highProtein = { proteinG: 40, fatG: 5, carbsG: 20, calories: 300 };
    const highFat = { proteinG: 5, fatG: 30, carbsG: 20, calories: 350 };

    expect(healthScoreFor(highProtein)).toBeGreaterThan(healthScoreFor(highFat));
  });

  it("clamps the score between 0 and 100", () => {
    const extremeHighFat = { proteinG: 0, fatG: 100, carbsG: 0, calories: 900 };
    const extremeHighProtein = { proteinG: 100, fatG: 0, carbsG: 0, calories: 400 };

    expect(healthScoreFor(extremeHighFat)).toBeGreaterThanOrEqual(0);
    expect(healthScoreFor(extremeHighProtein)).toBeLessThanOrEqual(100);
  });

  it("produces a mid-range score for a balanced meal", () => {
    const balanced = { proteinG: 25, fatG: 15, carbsG: 40, calories: 400 };
    const score = healthScoreFor(balanced);
    expect(score).toBeGreaterThan(20);
    expect(score).toBeLessThan(90);
  });
});

describe("validateImageUrls (seed guard)", () => {
  it("does not throw when all meals have imageUrl", () => {
    const meals = [
      { name: "Meal A", imageUrl: "https://images.unsplash.com/photo-abc?w=600" },
      { name: "Meal B", imageUrl: "https://images.unsplash.com/photo-xyz?w=600" },
    ];
    expect(() => validateImageUrls(meals)).not.toThrow();
  });

  it("throws when any meal has an empty imageUrl", () => {
    const meals = [
      { name: "Meal A", imageUrl: "https://images.unsplash.com/photo-abc?w=600" },
      { name: "Meal B", imageUrl: "" },
    ];
    expect(() => validateImageUrls(meals)).toThrow(/ABORTED/);
    expect(() => validateImageUrls(meals)).toThrow(/Meal B/);
  });

  it("throws when any meal has a whitespace-only imageUrl", () => {
    const meals = [{ name: "Meal C", imageUrl: "   " }];
    expect(() => validateImageUrls(meals)).toThrow(/Meal C/);
  });

  it("lists all missing meals in the error message", () => {
    const meals = [
      { name: "Meal A", imageUrl: "" },
      { name: "Meal B", imageUrl: "https://example.com/img.jpg" },
      { name: "Meal C", imageUrl: "" },
    ];
    let msg = "";
    try {
      validateImageUrls(meals);
    } catch (e) {
      msg = (e as Error).message;
    }
    expect(msg).toContain("Meal A");
    expect(msg).toContain("Meal C");
    expect(msg).not.toContain("Meal B");
  });
});
