/**
 * Health profile route integration tests.
 * Prisma is mocked — no real database needed.
 */

import request from "supertest";
import jwt from "jsonwebtoken";
import { createApp } from "../src/app";

jest.mock("../src/config/prisma", () => ({
  prisma: {
    user: {
      findUnique: jest.fn(),
    },
    healthProfile: {
      findUnique: jest.fn(),
      upsert: jest.fn(),
    },
  },
}));

// Mock the AI explainer so tests don't require a Groq API key
jest.mock("../src/services/aiExplainerService", () => ({
  explainNutritionPlan: jest.fn().mockResolvedValue("Mock explanation."),
}));

import { prisma } from "../src/config/prisma";

const app = createApp();
const JWT_SECRET = "dev-secret-change-me";

function makeToken(userId: string): string {
  return jwt.sign({ userId }, JWT_SECRET, { expiresIn: "7d" });
}

const mockUserFindUnique = prisma.user.findUnique as jest.MockedFunction<typeof prisma.user.findUnique>;
const mockProfileUpsert = prisma.healthProfile.upsert as jest.MockedFunction<typeof prisma.healthProfile.upsert>;

const completeUser = {
  id: "user-1",
  name: "Bob",
  email: "bob@example.com",
  passwordHash: "hash",
  age: 28,
  gender: "MALE" as const,
  heightCm: 178,
  weightKg: 80,
  createdAt: new Date(),
  updatedAt: new Date(),
};

const profilePayload = {
  currentWeightKg: 80,
  targetWeightKg: 75,
  activityLevel: "MODERATE" as const,
  fitnessGoal: "WEIGHT_LOSS" as const,
  dietaryPreference: "NON_VEGETARIAN" as const,
  allergies: [],
  dailyBudget: 500,
};

const savedProfile = {
  id: "profile-1",
  userId: "user-1",
  ...profilePayload,
  bmi: 25.2,
  bmr: 1890,
  tdee: 2929,
  proteinTargetG: 180,
  carbTargetG: 180,
  fatTargetG: 82,
  createdAt: new Date(),
  updatedAt: new Date(),
};

beforeEach(() => {
  jest.clearAllMocks();
});

describe("POST /api/health-profile", () => {
  it("returns 401 without auth token", async () => {
    const res = await request(app).post("/api/health-profile").send(profilePayload);
    expect(res.status).toBe(401);
  });

  it("returns 400 when user has no age/gender/heightCm on their profile", async () => {
    // User exists but missing bio fields
    mockUserFindUnique.mockResolvedValueOnce({
      ...completeUser,
      age: null,
      gender: null,
      heightCm: null,
    } as Parameters<typeof mockUserFindUnique>[0] extends infer P
      ? P extends { where: unknown }
        ? Awaited<ReturnType<typeof mockUserFindUnique>>
        : never
      : never);

    const token = makeToken("user-1");
    const res = await request(app)
      .post("/api/health-profile")
      .set("Authorization", `Bearer ${token}`)
      .send(profilePayload);

    expect(res.status).toBe(400);
    expect(res.body.error).toMatch(/basic profile/i);
  });

  it("returns 201 with profile, targets, and explanation on success", async () => {
    mockUserFindUnique.mockResolvedValueOnce(completeUser as Awaited<ReturnType<typeof mockUserFindUnique>>);
    mockProfileUpsert.mockResolvedValueOnce(savedProfile as Awaited<ReturnType<typeof mockProfileUpsert>>);

    const token = makeToken("user-1");
    const res = await request(app)
      .post("/api/health-profile")
      .set("Authorization", `Bearer ${token}`)
      .send(profilePayload);

    expect(res.status).toBe(201);
    expect(res.body.profile).toBeDefined();
    expect(res.body.targets.bmi).toBeDefined();
    expect(res.body.targets.calorieTarget).toBeGreaterThan(0);
    expect(res.body.explanation).toBeDefined();
  });
});
