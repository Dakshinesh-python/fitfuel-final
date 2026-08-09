/**
 * Tests for the AI Explainer service (unit-level) and the /api/chat route (integration).
 *
 * Service tests are run in a completely separate jest worker via isolateModules()
 * so the module-level mock for the route integration tests doesn't bleed through.
 */

// ─── /api/chat ROUTE INTEGRATION TESTS ───────────────────────────────────
// These need Prisma and the AI service mocked at module level.

jest.mock("../src/config/prisma", () => ({
  prisma: {
    healthProfile: {
      findUnique: jest.fn(),
    },
  },
}));

jest.mock("../src/services/aiExplainerService", () => ({
  explainNutritionPlan: jest.fn().mockResolvedValue("Mock nutrition explanation."),
  chatWithNutritionAssistant: jest.fn().mockResolvedValue("Here is your nutrition advice."),
}));

import request from "supertest";
import jwt from "jsonwebtoken";
import { createApp } from "../src/app";
import { prisma } from "../src/config/prisma";

const app = createApp();
const JWT_SECRET = "dev-secret-change-me";

function makeToken(userId: string): string {
  return jwt.sign({ userId }, JWT_SECRET, { expiresIn: "7d" });
}

const mockProfileFindUnique = prisma.healthProfile.findUnique as jest.MockedFunction<
  typeof prisma.healthProfile.findUnique
>;

beforeEach(() => {
  jest.clearAllMocks();
});

describe("POST /api/chat", () => {
  it("returns 401 without an auth token", async () => {
    const res = await request(app).post("/api/chat").send({ message: "What should I eat?" });
    expect(res.status).toBe(401);
  });

  it("returns 400 when message is missing", async () => {
    const token = makeToken("user-1");
    const res = await request(app)
      .post("/api/chat")
      .set("Authorization", `Bearer ${token}`)
      .send({});

    expect(res.status).toBe(400);
  });

  it("returns 200 with { reply } when user has no profile (fallback context)", async () => {
    mockProfileFindUnique.mockResolvedValueOnce(null);

    const token = makeToken("user-1");
    const res = await request(app)
      .post("/api/chat")
      .set("Authorization", `Bearer ${token}`)
      .send({ message: "How much protein do I need?" });

    expect(res.status).toBe(200);
    expect(res.body.reply).toBeDefined();
    expect(typeof res.body.reply).toBe("string");
  });

  it("returns 200 with the mocked reply when profile exists", async () => {
    mockProfileFindUnique.mockResolvedValueOnce({
      id: "p1",
      userId: "user-1",
      currentWeightKg: 80,
      targetWeightKg: 75,
      activityLevel: "MODERATE" as const,
      fitnessGoal: "WEIGHT_LOSS" as const,
      dietaryPreference: "NON_VEGETARIAN" as const,
      allergies: [],
      dailyBudget: 500,
      bmi: 25.2,
      bmr: 1890,
      tdee: 2929,
      proteinTargetG: 180,
      carbTargetG: 180,
      fatTargetG: 82,
      createdAt: new Date(),
      updatedAt: new Date(),
    } as Awaited<ReturnType<typeof mockProfileFindUnique>>);

    const token = makeToken("user-1");
    const res = await request(app)
      .post("/api/chat")
      .set("Authorization", `Bearer ${token}`)
      .send({ message: "Should I eat more carbs?" });

    expect(res.status).toBe(200);
    expect(res.body.reply).toBe("Here is your nutrition advice.");
  });
});
