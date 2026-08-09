/**
 * Meal route integration tests (Task 8).
 * Prisma is mocked — no real database needed.
 *
 * GET /api/meals — public (no auth). Tests: 200 returns array,
 * optional filters accepted without error.
 * GET /api/meals/:id — 200 with meal object, 404 when not found.
 */

import request from "supertest";
import { createApp } from "../src/app";

jest.mock("../src/config/prisma", () => ({
  prisma: {
    meal: {
      findMany: jest.fn(),
      findUnique: jest.fn(),
    },
  },
}));

import { prisma } from "../src/config/prisma";

const app = createApp();

const mockMealFindMany = prisma.meal.findMany as jest.MockedFunction<typeof prisma.meal.findMany>;
const mockMealFindUnique = prisma.meal.findUnique as jest.MockedFunction<typeof prisma.meal.findUnique>;

const sampleMeals = [
  {
    id: "meal-uuid-1",
    name: "Grilled Chicken Bowl",
    restaurant: "FreshFit Kitchen",
    platform: "SWIGGY" as const,
    cuisine: "Healthy Bowls",
    mealType: "LUNCH" as const,
    calories: 420,
    proteinG: 38,
    carbsG: 30,
    fatG: 14,
    price: 220,
    healthScore: 75,
    isVegetarian: false,
    isVegan: false,
    allergens: [] as string[],
    imageUrl: "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=600&q=80",
    deepLinkQuery: "Grilled Chicken Bowl",
    createdAt: new Date(),
  },
  {
    id: "meal-uuid-2",
    name: "Masala Oats",
    restaurant: "Morning Cafe",
    platform: "ZOMATO" as const,
    cuisine: "South Indian",
    mealType: "BREAKFAST" as const,
    calories: 280,
    proteinG: 10,
    carbsG: 45,
    fatG: 6,
    price: 100,
    healthScore: 55,
    isVegetarian: true,
    isVegan: true,
    allergens: [] as string[],
    imageUrl: "https://images.unsplash.com/photo-1517673132405-a56a62b18caf?auto=format&fit=crop&w=600&q=80",
    deepLinkQuery: "Masala Oats",
    createdAt: new Date(),
  },
];

beforeEach(() => jest.clearAllMocks());

// ─── GET /api/meals ────────────────────────────────────────────────────────

describe("GET /api/meals", () => {
  it("returns 200 with meals array (no auth required)", async () => {
    mockMealFindMany.mockResolvedValueOnce(sampleMeals as Awaited<ReturnType<typeof mockMealFindMany>>);

    const res = await request(app).get("/api/meals");

    expect(res.status).toBe(200);
    expect(Array.isArray(res.body.meals)).toBe(true);
    expect(res.body.meals).toHaveLength(2);
  });

  it("accepts mealType filter without error", async () => {
    const lunchOnly = sampleMeals.filter((m) => m.mealType === "LUNCH");
    mockMealFindMany.mockResolvedValueOnce(lunchOnly as Awaited<ReturnType<typeof mockMealFindMany>>);

    const res = await request(app).get("/api/meals?mealType=LUNCH");

    expect(res.status).toBe(200);
    expect(res.body.meals).toHaveLength(1);
    expect(res.body.meals[0].mealType).toBe("LUNCH");
  });

  it("accepts platform filter without error", async () => {
    const swiggyOnly = sampleMeals.filter((m) => m.platform === "SWIGGY");
    mockMealFindMany.mockResolvedValueOnce(swiggyOnly as Awaited<ReturnType<typeof mockMealFindMany>>);

    const res = await request(app).get("/api/meals?platform=SWIGGY");

    expect(res.status).toBe(200);
    expect(res.body.meals[0].platform).toBe("SWIGGY");
  });

  it("returns an empty array when no meals match filter", async () => {
    mockMealFindMany.mockResolvedValueOnce([]);

    const res = await request(app).get("/api/meals?cuisine=Nonexistent");

    expect(res.status).toBe(200);
    expect(res.body.meals).toHaveLength(0);
  });
});

// ─── GET /api/meals/:id ────────────────────────────────────────────────────

describe("GET /api/meals/:id", () => {
  it("returns 200 with the meal object when found", async () => {
    mockMealFindUnique.mockResolvedValueOnce(sampleMeals[0] as Awaited<ReturnType<typeof mockMealFindUnique>>);

    const res = await request(app).get(`/api/meals/${sampleMeals[0].id}`);

    expect(res.status).toBe(200);
    expect(res.body.meal.id).toBe("meal-uuid-1");
    expect(res.body.meal.name).toBe("Grilled Chicken Bowl");
  });

  it("returns 404 when meal is not found", async () => {
    mockMealFindUnique.mockResolvedValueOnce(null);

    const res = await request(app).get("/api/meals/00000000-0000-0000-0000-000000000000");

    expect(res.status).toBe(404);
    expect(res.body.error).toMatch(/not found/i);
  });

  it("includes imageUrl in the returned meal object", async () => {
    mockMealFindUnique.mockResolvedValueOnce(sampleMeals[0] as Awaited<ReturnType<typeof mockMealFindUnique>>);

    const res = await request(app).get(`/api/meals/${sampleMeals[0].id}`);

    expect(res.status).toBe(200);
    // imageUrl should be present in the response (null is acceptable; a URL string is expected for seeded data)
    expect("imageUrl" in res.body.meal).toBe(true);
    expect(res.body.meal.imageUrl).toContain("unsplash.com");
  });
});
