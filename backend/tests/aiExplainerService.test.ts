/**
 * Pure unit tests for aiExplainerService.ts.
 *
 * Uses jest.resetModules() + dynamic import() for each test so that:
 * - The fallback tests can run without GROQ_API_KEY
 * - The success tests can run with a mocked global.fetch
 *
 * No module-level jest.mock() calls — the real service is imported fresh each time.
 */

describe("explainNutritionPlan — fallback (no GROQ_API_KEY)", () => {
  beforeEach(() => {
    delete process.env.GROQ_API_KEY;
    jest.resetModules();
  });

  it("returns a string containing the calorie target and does not throw", async () => {
    const { explainNutritionPlan } = await import("../src/services/aiExplainerService");

    const result = await explainNutritionPlan({
      calorieTarget: 2200,
      proteinTargetG: 165,
      carbTargetG: 248,
      fatTargetG: 73,
      fitnessGoal: "MUSCLE_GAIN",
    });

    expect(typeof result).toBe("string");
    expect(result.length).toBeGreaterThan(0);
    expect(result).toContain("2200");
    expect(result).toContain("165");
  });

  it("does not call fetch when no API key is set", async () => {
    const fetchSpy = jest.spyOn(global, "fetch");
    const { explainNutritionPlan } = await import("../src/services/aiExplainerService");

    await explainNutritionPlan({
      calorieTarget: 1800,
      proteinTargetG: 120,
      carbTargetG: 200,
      fatTargetG: 60,
      fitnessGoal: "WEIGHT_LOSS",
    });

    expect(fetchSpy).not.toHaveBeenCalled();
    fetchSpy.mockRestore();
  });
});

describe("explainNutritionPlan — success path (mocked fetch)", () => {
  beforeEach(() => {
    process.env.GROQ_API_KEY = "test-key-abc";
    jest.resetModules();
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        choices: [{ message: { content: "Great plan! Eat well." } }],
      }),
    }) as jest.Mock;
  });

  afterEach(() => {
    delete process.env.GROQ_API_KEY;
    jest.restoreAllMocks();
  });

  it("returns the content from the Groq response", async () => {
    const { explainNutritionPlan } = await import("../src/services/aiExplainerService");

    const result = await explainNutritionPlan({
      calorieTarget: 2000,
      proteinTargetG: 150,
      carbTargetG: 200,
      fatTargetG: 67,
      fitnessGoal: "MAINTENANCE",
    });

    expect(result).toBe("Great plan! Eat well.");
    expect(global.fetch).toHaveBeenCalledTimes(1);
  });

  it("passes the exact calorie number to the Groq prompt", async () => {
    const { explainNutritionPlan } = await import("../src/services/aiExplainerService");

    await explainNutritionPlan({
      calorieTarget: 1850,
      proteinTargetG: 140,
      carbTargetG: 185,
      fatTargetG: 62,
      fitnessGoal: "WEIGHT_LOSS",
    });

    const fetchCall = (global.fetch as jest.Mock).mock.calls[0] as [string, RequestInit];
    const body = JSON.parse(fetchCall[1].body as string) as {
      messages: Array<{ content: string }>;
    };
    const prompt = body.messages[0].content;

    expect(prompt).toContain("1850");
    expect(prompt).toContain("140");
  });
});
