/**
 * Recommendation route integration tests (Task 8).
 * Prisma is mocked — no real database needed.
 *
 * Unit-level coverage of the scoring logic lives in recommendationEngine.test.ts.
 * These tests focus on the HTTP layer: auth guard, health-profile guard, and
 * that a valid response returns a ranked recommendations array.
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
  },
}));

import { prisma } from "../src/config/prisma";

const app = createApp();
const JWT_SECRET = "dev-secret-change-me";

function makeToken(userId: string): string {
  return jwt.sign({ userId }, JWT_SECRET, { expiresIn: "7d" });
}

const mockProfileFindUnique = prisma.healthProfile.findUnique as jest.MockedFunction<
  typeof prisma.healthProfile.findUnique
>;
const mockMealFindMany = prisma.meal.findMany as jest.MockedFunction<typeof prisma.meal.findMany>;

const sampleProfile = {
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

const lunchMeals = [
  {
    id: "meal-1",
    name: "Chicken Bowl",
    restaurant: "FreshFit",
    platform: "SWIGGY" as const,
    cuisine: "Healthy Bowls",
    mealType: "LUNCH" as const,
    calories: 500,
    proteinG: 40,
    carbsG: 40,
    fatG: 15,
    price: 200,
    healthScore: 75,
    isVegetarian: false,
    isVegan: false,
    allergens: [] as string[],
    deepLinkQuery: "Chicken Bowl",
    createdAt: new Date(),
  },
  {
    id: "meal-2",
    name: "Paneer Bowl",
    restaurant: "GreenBowl",
    platform: "ZOMATO" as const,
    cuisine: "North Indian",
    mealType: "LUNCH" as const,
    calories: 450,
    proteinG: 25,
    carbsG: 45,
    fatG: 18,
    price: 180,
    healthScore: 60,
    isVegetarian: true,
    isVegan: false,
    allergens: ["dairy"] as string[],
    deepLinkQuery: "Paneer Bowl",
    createdAt: new Date(),
  },
];

beforeEach(() => jest.clearAllMocks());

describe("GET /api/recommendations", () => {
  it("returns 401 without auth token", async () => {
    const res = await request(app).get("/api/recommendations?mealType=LUNCH");
    expect(res.status).toBe(401);
  });

  it("returns 400 when user has no health profile", async () => {
    mockProfileFindUnique.mockResolvedValueOnce(null);

    const token = makeToken("user-1");
    const res = await request(app)
      .get("/api/recommendations?mealType=LUNCH")
      .set("Authorization", `Bearer ${token}`);

    expect(res.status).toBe(400);
    expect(res.body.error).toMatch(/health assessment/i);
  });

  it("returns 200 with scored + ranked recommendations array", async () => {
    mockProfileFindUnique.mockResolvedValueOnce(sampleProfile as Awaited<ReturnType<typeof mockProfileFindUnique>>);
    mockMealFindMany.mockResolvedValueOnce(lunchMeals as Awaited<ReturnType<typeof mockMealFindMany>>);

    const token = makeToken("user-1");
    const res = await request(app)
      .get("/api/recommendations?mealType=LUNCH")
      .set("Authorization", `Bearer ${token}`);

    expect(res.status).toBe(200);
    expect(Array.isArray(res.body.recommendations)).toBe(true);
    expect(res.body.recommendations.length).toBeGreaterThan(0);

    const first = res.body.recommendations[0];
    // Each recommendation must include the score breakdown and the full meal object
    expect(first.score).toBeDefined();
    expect(first.breakdown).toBeDefined();
    expect(first.meal).toBeDefined();
    expect(typeof first.score).toBe("number");
  });

  it("sorts recommendations by descending score", async () => {
    mockProfileFindUnique.mockResolvedValueOnce(sampleProfile as Awaited<ReturnType<typeof mockProfileFindUnique>>);
    mockMealFindMany.mockResolvedValueOnce(lunchMeals as Awaited<ReturnType<typeof mockMealFindMany>>);

    const token = makeToken("user-1");
    const res = await request(app)
      .get("/api/recommendations?mealType=LUNCH")
      .set("Authorization", `Bearer ${token}`);

    const scores = (res.body.recommendations as Array<{ score: number }>).map((r) => r.score);
    for (let i = 1; i < scores.length; i++) {
      expect(scores[i - 1]).toBeGreaterThanOrEqual(scores[i]);
    }
  });

  it("defaults to LUNCH when mealType query param is omitted", async () => {
    mockProfileFindUnique.mockResolvedValueOnce(sampleProfile as Awaited<ReturnType<typeof mockProfileFindUnique>>);
    mockMealFindMany.mockResolvedValueOnce(lunchMeals as Awaited<ReturnType<typeof mockMealFindMany>>);

    const token = makeToken("user-1");
    const res = await request(app)
      .get("/api/recommendations") // no mealType
      .set("Authorization", `Bearer ${token}`);

    expect(res.status).toBe(200);
  });
});
