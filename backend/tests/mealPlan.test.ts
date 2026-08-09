/**
 * Meal Plan route integration tests.
 * Prisma is mocked — no real database needed in CI.
 */

import request from "supertest";
import jwt from "jsonwebtoken";
import { createApp } from "../src/app";

jest.mock("../src/config/prisma", () => ({
  prisma: {
    healthProfile: {
      findUnique: jest.fn(),
    },
    meal: {
      findMany: jest.fn(),
    },
    mealPlan: {
      create: jest.fn(),
      findFirst: jest.fn(),
      findUnique: jest.fn(),
    },
    mealPlanItem: {
      createMany: jest.fn(),
    },
  },
}));

import { prisma } from "../src/config/prisma";

const app = createApp();
const JWT_SECRET = "dev-secret-change-me";

function makeToken(userId: string): string {
  return jwt.sign({ userId }, JWT_SECRET, { expiresIn: "7d" });
}

const mockProfileFindUnique = prisma.healthProfile.findUnique as jest.MockedFunction<typeof prisma.healthProfile.findUnique>;
const mockMealFindMany = prisma.meal.findMany as jest.MockedFunction<typeof prisma.meal.findMany>;
const mockMealPlanCreate = prisma.mealPlan.create as jest.MockedFunction<typeof prisma.mealPlan.create>;
const mockMealPlanItemCreateMany = prisma.mealPlanItem.createMany as jest.MockedFunction<typeof prisma.mealPlanItem.createMany>;
const mockMealPlanFindUnique = prisma.mealPlan.findUnique as jest.MockedFunction<typeof prisma.mealPlan.findUnique>;
const mockMealPlanFindFirst = prisma.mealPlan.findFirst as jest.MockedFunction<typeof prisma.mealPlan.findFirst>;

const profile = {
  id: "profile-1",
  userId: "user-1",
  currentWeightKg: 80,
  targetWeightKg: 75,
  activityLevel: "MODERATE" as const,
  fitnessGoal: "MUSCLE_GAIN" as const,
  dietaryPreference: "NON_VEGETARIAN" as const,
  allergies: [] as string[],
  dailyBudget: 600,
  bmi: 25.2,
  bmr: 1890,
  tdee: 2929,
  proteinTargetG: 200,
  carbTargetG: 250,
  fatTargetG: 90,
  createdAt: new Date(),
  updatedAt: new Date(),
};

// Minimal meal fixtures covering all 4 meal types
const meals = [
  { id: "m1", name: "Chicken Bowl", restaurant: "FreshFit", platform: "SWIGGY" as const, cuisine: "Healthy Bowls", mealType: "LUNCH" as const, calories: 500, proteinG: 40, carbsG: 40, fatG: 15, price: 200, healthScore: 75, isVegetarian: false, isVegan: false, allergens: [] as string[], deepLinkQuery: "Chicken Bowl", createdAt: new Date() },
  { id: "m2", name: "Paneer Bowl", restaurant: "GreenBowl", platform: "ZOMATO" as const, cuisine: "North Indian", mealType: "LUNCH" as const, calories: 450, proteinG: 25, carbsG: 45, fatG: 18, price: 180, healthScore: 60, isVegetarian: true, isVegan: false, allergens: ["dairy"] as string[], deepLinkQuery: "Paneer Bowl", createdAt: new Date() },
  { id: "m3", name: "Egg Omelette", restaurant: "Morning Cafe", platform: "ZOMATO" as const, cuisine: "Continental", mealType: "BREAKFAST" as const, calories: 280, proteinG: 22, carbsG: 10, fatG: 14, price: 150, healthScore: 70, isVegetarian: false, isVegan: false, allergens: ["egg"] as string[], deepLinkQuery: "Egg Omelette", createdAt: new Date() },
  { id: "m4", name: "Masala Oats", restaurant: "Morning Cafe", platform: "SWIGGY" as const, cuisine: "South Indian", mealType: "BREAKFAST" as const, calories: 280, proteinG: 10, carbsG: 45, fatG: 6, price: 100, healthScore: 55, isVegetarian: true, isVegan: true, allergens: [] as string[], deepLinkQuery: "Masala Oats", createdAt: new Date() },
  { id: "m5", name: "Grilled Fish", restaurant: "Coastal Grill", platform: "SWIGGY" as const, cuisine: "Continental", mealType: "DINNER" as const, calories: 480, proteinG: 40, carbsG: 20, fatG: 20, price: 320, healthScore: 72, isVegetarian: false, isVegan: false, allergens: ["fish"] as string[], deepLinkQuery: "Grilled Fish", createdAt: new Date() },
  { id: "m6", name: "Tofu Stir Fry", restaurant: "Wok This Way", platform: "ZOMATO" as const, cuisine: "Chinese", mealType: "DINNER" as const, calories: 400, proteinG: 22, carbsG: 35, fatG: 16, price: 260, healthScore: 58, isVegetarian: true, isVegan: true, allergens: ["soy"] as string[], deepLinkQuery: "Tofu Stir Fry", createdAt: new Date() },
  { id: "m7", name: "Chana Chaat", restaurant: "Snack Shack", platform: "ZOMATO" as const, cuisine: "North Indian", mealType: "SNACK" as const, calories: 180, proteinG: 9, carbsG: 28, fatG: 4, price: 90, healthScore: 62, isVegetarian: true, isVegan: true, allergens: [] as string[], deepLinkQuery: "Chana Chaat", createdAt: new Date() },
  { id: "m8", name: "Protein Smoothie", restaurant: "Blend Bar", platform: "SWIGGY" as const, cuisine: "Healthy Bowls", mealType: "SNACK" as const, calories: 220, proteinG: 20, carbsG: 25, fatG: 5, price: 140, healthScore: 68, isVegetarian: true, isVegan: false, allergens: ["dairy"] as string[], deepLinkQuery: "Protein Smoothie", createdAt: new Date() },
];

const mealPlanResult = {
  id: "plan-1",
  userId: "user-1",
  weekStart: new Date(),
  createdAt: new Date(),
  items: Array.from({ length: 28 }, (_, i) => ({
    id: `item-${i}`,
    mealPlanId: "plan-1",
    mealId: meals[i % meals.length].id,
    dayOfWeek: Math.floor(i / 4),
    mealType: (["BREAKFAST", "LUNCH", "DINNER", "SNACK"] as const)[i % 4],
    matchScore: 75,
    meal: meals[i % meals.length],
  })),
};

beforeEach(() => {
  jest.clearAllMocks();
});

describe("POST /api/meal-plans/generate", () => {
  it("returns 401 without auth token", async () => {
    const res = await request(app).post("/api/meal-plans/generate");
    expect(res.status).toBe(401);
  });

  it("returns 400 when user has no health profile", async () => {
    mockProfileFindUnique.mockResolvedValueOnce(null);

    const token = makeToken("user-1");
    const res = await request(app)
      .post("/api/meal-plans/generate")
      .set("Authorization", `Bearer ${token}`);

    expect(res.status).toBe(400);
  });

  it("creates a plan with 28 items (7 days × 4 meal types)", async () => {
    mockProfileFindUnique.mockResolvedValueOnce(profile as Awaited<ReturnType<typeof mockProfileFindUnique>>);
    mockMealFindMany.mockResolvedValueOnce(meals as Awaited<ReturnType<typeof mockMealFindMany>>);
    mockMealPlanCreate.mockResolvedValueOnce({ id: "plan-1", userId: "user-1", weekStart: new Date(), createdAt: new Date() } as Awaited<ReturnType<typeof mockMealPlanCreate>>);
    mockMealPlanItemCreateMany.mockResolvedValueOnce({ count: 28 });
    mockMealPlanFindUnique.mockResolvedValueOnce(mealPlanResult as Awaited<ReturnType<typeof mockMealPlanFindUnique>>);

    const token = makeToken("user-1");
    const res = await request(app)
      .post("/api/meal-plans/generate")
      .set("Authorization", `Bearer ${token}`);

    expect(res.status).toBe(201);
    expect(res.body.mealPlan).toBeDefined();
    expect(res.body.mealPlan.items).toHaveLength(28);
    // All items must have a valid matchScore
    for (const item of res.body.mealPlan.items) {
      expect(item.matchScore).toBeGreaterThanOrEqual(0);
      expect(item.matchScore).toBeLessThanOrEqual(100);
    }
  });
});

describe("GET /api/meal-plans/current", () => {
  it("returns 404 when no plan exists", async () => {
    mockMealPlanFindFirst.mockResolvedValueOnce(null);

    const token = makeToken("user-1");
    const res = await request(app)
      .get("/api/meal-plans/current")
      .set("Authorization", `Bearer ${token}`);

    expect(res.status).toBe(404);
  });

  it("returns the most recent plan when one exists", async () => {
    mockMealPlanFindFirst.mockResolvedValueOnce(mealPlanResult as Awaited<ReturnType<typeof mockMealPlanFindFirst>>);

    const token = makeToken("user-1");
    const res = await request(app)
      .get("/api/meal-plans/current")
      .set("Authorization", `Bearer ${token}`);

    expect(res.status).toBe(200);
    expect(res.body.mealPlan.id).toBe("plan-1");
  });
});
