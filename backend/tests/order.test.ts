/**
 * Order route integration tests (Task 6).
 * Prisma is mocked — no real database needed in CI.
 *
 * Key focus: deepLink correctness — correct domain per platform,
 * restaurant name and meal query are URL-encoded and present.
 *
 * REMINDER: "Order on Swiggy/Zomato" is a search-page deep link handoff only.
 * Swiggy and Zomato provide no public API for third-party order placement.
 */

import request from "supertest";
import jwt from "jsonwebtoken";
import { createApp } from "../src/app";

jest.mock("../src/config/prisma", () => ({
  prisma: {
    meal: {
      findUnique: jest.fn(),
    },
    order: {
      create: jest.fn(),
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

const mockMealFindUnique = prisma.meal.findUnique as jest.MockedFunction<typeof prisma.meal.findUnique>;
const mockOrderCreate = prisma.order.create as jest.MockedFunction<typeof prisma.order.create>;
const mockOrderFindMany = prisma.order.findMany as jest.MockedFunction<typeof prisma.order.findMany>;

const sampleMeal = {
  id: "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
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
  deepLinkQuery: "Grilled Chicken Bowl",
  createdAt: new Date(),
};

const sampleOrder = {
  id: "order-uuid-1",
  userId: "user-1",
  mealId: "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  platform: "SWIGGY" as const,
  status: "REDIRECTED",
  createdAt: new Date(),
};

beforeEach(() => jest.clearAllMocks());

// ─── POST /api/orders ──────────────────────────────────────────────────────

describe("POST /api/orders", () => {
  it("returns 401 without auth token", async () => {
    const res = await request(app)
      .post("/api/orders")
      .send({ mealId: sampleMeal.id, platform: "SWIGGY" });

    expect(res.status).toBe(401);
  });

  it("returns 404 when mealId does not exist", async () => {
    mockMealFindUnique.mockResolvedValueOnce(null);

    const token = makeToken("user-1");
    const res = await request(app)
      .post("/api/orders")
      .set("Authorization", `Bearer ${token}`)
      .send({ mealId: "00000000-0000-0000-0000-000000000000", platform: "SWIGGY" });

    expect(res.status).toBe(404);
    expect(res.body.error).toMatch(/not found/i);
  });

  it("returns 400 on invalid input (mealId not a UUID)", async () => {
    const token = makeToken("user-1");
    const res = await request(app)
      .post("/api/orders")
      .set("Authorization", `Bearer ${token}`)
      .send({ mealId: "not-a-uuid", platform: "SWIGGY" });

    expect(res.status).toBe(400);
  });

  it("returns 201 for SWIGGY with deepLink pointing to swiggy.com with dish query", async () => {
    mockMealFindUnique.mockResolvedValueOnce(sampleMeal as Awaited<ReturnType<typeof mockMealFindUnique>>);
    mockOrderCreate.mockResolvedValueOnce(sampleOrder as Awaited<ReturnType<typeof mockOrderCreate>>);

    const token = makeToken("user-1");
    const res = await request(app)
      .post("/api/orders")
      .set("Authorization", `Bearer ${token}`)
      .send({ mealId: sampleMeal.id, platform: "SWIGGY" });

    expect(res.status).toBe(201);
    expect(res.body.order.status).toBe("REDIRECTED");
    expect(res.body.deepLink).toBeDefined();

    const url = res.body.deepLink as string;
    // Must open Swiggy's search page — never a fake order endpoint
    expect(url).toContain("swiggy.com/search");
    // Dish name must be URL-encoded in the query
    expect(url).toContain(encodeURIComponent("Grilled Chicken Bowl"));
  });

  it("returns 201 for ZOMATO with deepLink pointing to zomato.com with dish search", async () => {
    const zomatoMeal = { ...sampleMeal, platform: "ZOMATO" as const };
    const zomatoOrder = { ...sampleOrder, platform: "ZOMATO" as const };

    mockMealFindUnique.mockResolvedValueOnce(zomatoMeal as Awaited<ReturnType<typeof mockMealFindUnique>>);
    mockOrderCreate.mockResolvedValueOnce(zomatoOrder as Awaited<ReturnType<typeof mockOrderCreate>>);

    const token = makeToken("user-1");
    const res = await request(app)
      .post("/api/orders")
      .set("Authorization", `Bearer ${token}`)
      .send({ mealId: sampleMeal.id, platform: "ZOMATO" });

    expect(res.status).toBe(201);
    const url = res.body.deepLink as string;
    // Must open Zomato's search page — never a fake order endpoint
    expect(url).toContain("zomato.com/chennai/delivery/dish-");
    // Dish name must be URL-encoded (not restaurant name), lowercased with hyphens
    expect(url).toContain("grilled-chicken-bowl");
  });

  it("deepLink never contains 'order' or 'checkout' paths (handoff only, never fake API call)", async () => {
    mockMealFindUnique.mockResolvedValueOnce(sampleMeal as Awaited<ReturnType<typeof mockMealFindUnique>>);
    mockOrderCreate.mockResolvedValueOnce(sampleOrder as Awaited<ReturnType<typeof mockOrderCreate>>);

    const token = makeToken("user-1");
    const res = await request(app)
      .post("/api/orders")
      .set("Authorization", `Bearer ${token}`)
      .send({ mealId: sampleMeal.id, platform: "SWIGGY" });

    const url = res.body.deepLink as string;
    // Verify we're not pretending to place a real order via any API path
    expect(url).not.toContain("/order");
    expect(url).not.toContain("/checkout");
    expect(url).not.toContain("/api/");
  });
});

// ─── GET /api/orders ───────────────────────────────────────────────────────

describe("GET /api/orders", () => {
  it("returns 401 without auth token", async () => {
    const res = await request(app).get("/api/orders");
    expect(res.status).toBe(401);
  });

  it("returns 200 with order history including meal details", async () => {
    const ordersWithMeal = [{ ...sampleOrder, meal: sampleMeal }];
    mockOrderFindMany.mockResolvedValueOnce(ordersWithMeal as Awaited<ReturnType<typeof mockOrderFindMany>>);

    const token = makeToken("user-1");
    const res = await request(app)
      .get("/api/orders")
      .set("Authorization", `Bearer ${token}`);

    expect(res.status).toBe(200);
    expect(Array.isArray(res.body.orders)).toBe(true);
    expect(res.body.orders[0].meal).toBeDefined();
    expect(res.body.orders[0].status).toBe("REDIRECTED");
  });

  it("returns 200 with empty array when user has no orders", async () => {
    mockOrderFindMany.mockResolvedValueOnce([]);

    const token = makeToken("user-1");
    const res = await request(app)
      .get("/api/orders")
      .set("Authorization", `Bearer ${token}`);

    expect(res.status).toBe(200);
    expect(res.body.orders).toHaveLength(0);
  });
});
