/**
 * Progress route integration tests (Task 7).
 * Prisma is mocked — no real database needed in CI.
 *
 * Covers: POST /api/progress, GET /api/progress/summary (pct calculation),
 * GET /api/progress/weight-history, GET /api/progress.
 */

import request from "supertest";
import jwt from "jsonwebtoken";
import { createApp } from "../src/app";

jest.mock("../src/config/prisma", () => ({
  prisma: {
    healthProfile: {
      findUnique: jest.fn(),
    },
    progressLog: {
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

const mockProfileFindUnique = prisma.healthProfile.findUnique as jest.MockedFunction<typeof prisma.healthProfile.findUnique>;
const mockLogCreate = prisma.progressLog.create as jest.MockedFunction<typeof prisma.progressLog.create>;
const mockLogFindMany = prisma.progressLog.findMany as jest.MockedFunction<typeof prisma.progressLog.findMany>;

const sampleProfile = {
  id: "profile-1",
  userId: "user-1",
  currentWeightKg: 80,
  targetWeightKg: 75,
  activityLevel: "MODERATE" as const,
  fitnessGoal: "WEIGHT_LOSS" as const,
  dietaryPreference: "NON_VEGETARIAN" as const,
  allergies: [] as string[],
  dailyBudget: 500,
  bmi: 25.2,
  bmr: 1890,
  tdee: 2000, // round number for easy calculation assertions
  proteinTargetG: 175,
  carbTargetG: 175,
  fatTargetG: 67,
  createdAt: new Date(),
  updatedAt: new Date(),
};

// Build 7 log fixtures, each consuming exactly TDEE (2000 kcal) → pct = 100
const sevenDaysOfLogs = Array.from({ length: 7 }, (_, i) => ({
  id: `log-${i}`,
  userId: "user-1",
  date: new Date(Date.now() - i * 86_400_000),
  weightKg: 80 - i * 0.1,
  caloriesConsumed: 2000,
  proteinConsumedG: 175,
  carbsConsumedG: 175,
  fatConsumedG: 67,
  notes: null,
}));

beforeEach(() => jest.clearAllMocks());

// ─── POST /api/progress ────────────────────────────────────────────────────

describe("POST /api/progress", () => {
  it("returns 401 without auth token", async () => {
    const res = await request(app)
      .post("/api/progress")
      .send({ caloriesConsumed: 500 });

    expect(res.status).toBe(401);
  });

  it("returns 400 on invalid input (negative calories)", async () => {
    const token = makeToken("user-1");
    const res = await request(app)
      .post("/api/progress")
      .set("Authorization", `Bearer ${token}`)
      .send({ caloriesConsumed: -100 });

    expect(res.status).toBe(400);
  });

  it("returns 201 with partial fields (only calories — no weight required)", async () => {
    const createdLog = { id: "log-1", userId: "user-1", date: new Date(), caloriesConsumed: 650, weightKg: null, proteinConsumedG: null, carbsConsumedG: null, fatConsumedG: null, notes: null };
    mockLogCreate.mockResolvedValueOnce(createdLog as Awaited<ReturnType<typeof mockLogCreate>>);

    const token = makeToken("user-1");
    const res = await request(app)
      .post("/api/progress")
      .set("Authorization", `Bearer ${token}`)
      .send({ caloriesConsumed: 650 });

    expect(res.status).toBe(201);
    expect(res.body.log.caloriesConsumed).toBe(650);
  });

  it("returns 201 with only weight (nutrition fields omitted)", async () => {
    const createdLog = { id: "log-2", userId: "user-1", date: new Date(), caloriesConsumed: null, weightKg: 79.5, proteinConsumedG: null, carbsConsumedG: null, fatConsumedG: null, notes: null };
    mockLogCreate.mockResolvedValueOnce(createdLog as Awaited<ReturnType<typeof mockLogCreate>>);

    const token = makeToken("user-1");
    const res = await request(app)
      .post("/api/progress")
      .set("Authorization", `Bearer ${token}`)
      .send({ weightKg: 79.5 });

    expect(res.status).toBe(201);
    expect(res.body.log.weightKg).toBe(79.5);
  });
});

// ─── GET /api/progress/summary ─────────────────────────────────────────────

describe("GET /api/progress/summary", () => {
  it("returns 401 without auth token", async () => {
    const res = await request(app).get("/api/progress/summary");
    expect(res.status).toBe(401);
  });

  it("returns goalAchievementPct = 100 when average calories equals TDEE", async () => {
    mockProfileFindUnique.mockResolvedValueOnce(sampleProfile as Awaited<ReturnType<typeof mockProfileFindUnique>>);
    mockLogFindMany.mockResolvedValueOnce(sevenDaysOfLogs as Awaited<ReturnType<typeof mockLogFindMany>>);

    const token = makeToken("user-1");
    const res = await request(app)
      .get("/api/progress/summary")
      .set("Authorization", `Bearer ${token}`);

    expect(res.status).toBe(200);
    // avg = 2000, TDEE = 2000 → pct = 100
    expect(res.body.goalAchievementPct).toBe(100);
    expect(res.body.weeklyAverageCalories).toBe(2000);
  });

  it("returns goalAchievementPct ~50 when average calories is half of TDEE", async () => {
    const halfCalorieLogs = sevenDaysOfLogs.map((l) => ({ ...l, caloriesConsumed: 1000 }));
    mockProfileFindUnique.mockResolvedValueOnce(sampleProfile as Awaited<ReturnType<typeof mockProfileFindUnique>>);
    mockLogFindMany.mockResolvedValueOnce(halfCalorieLogs as Awaited<ReturnType<typeof mockLogFindMany>>);

    const token = makeToken("user-1");
    const res = await request(app)
      .get("/api/progress/summary")
      .set("Authorization", `Bearer ${token}`);

    expect(res.status).toBe(200);
    expect(res.body.goalAchievementPct).toBe(50);
  });

  it("caps goalAchievementPct at 100 even when overconsumption occurs", async () => {
    // Logs consuming 150% of TDEE
    const overLogs = sevenDaysOfLogs.map((l) => ({ ...l, caloriesConsumed: 3000 }));
    mockProfileFindUnique.mockResolvedValueOnce(sampleProfile as Awaited<ReturnType<typeof mockProfileFindUnique>>);
    mockLogFindMany.mockResolvedValueOnce(overLogs as Awaited<ReturnType<typeof mockLogFindMany>>);

    const token = makeToken("user-1");
    const res = await request(app)
      .get("/api/progress/summary")
      .set("Authorization", `Bearer ${token}`);

    expect(res.status).toBe(200);
    expect(res.body.goalAchievementPct).toBe(100); // capped
  });

  it("returns goalAchievementPct = null when user has no health profile", async () => {
    mockProfileFindUnique.mockResolvedValueOnce(null);
    mockLogFindMany.mockResolvedValueOnce(sevenDaysOfLogs as Awaited<ReturnType<typeof mockLogFindMany>>);

    const token = makeToken("user-1");
    const res = await request(app)
      .get("/api/progress/summary")
      .set("Authorization", `Bearer ${token}`);

    expect(res.status).toBe(200);
    expect(res.body.goalAchievementPct).toBeNull();
  });

  it("returns goalAchievementPct = null and weeklyAverageCalories = 0 when no logs exist", async () => {
    mockProfileFindUnique.mockResolvedValueOnce(sampleProfile as Awaited<ReturnType<typeof mockProfileFindUnique>>);
    mockLogFindMany.mockResolvedValueOnce([]);

    const token = makeToken("user-1");
    const res = await request(app)
      .get("/api/progress/summary")
      .set("Authorization", `Bearer ${token}`);

    expect(res.status).toBe(200);
    expect(res.body.weeklyAverageCalories).toBe(0);
    expect(res.body.goalAchievementPct).toBeNull();
  });
});

// ─── GET /api/progress/weight-history ─────────────────────────────────────

describe("GET /api/progress/weight-history", () => {
  it("returns 401 without auth token", async () => {
    const res = await request(app).get("/api/progress/weight-history");
    expect(res.status).toBe(401);
  });

  it("returns 200 with date+weightKg pairs, no other fields", async () => {
    const weightLogs = sevenDaysOfLogs.map((l) => ({ date: l.date, weightKg: l.weightKg }));
    mockLogFindMany.mockResolvedValueOnce(weightLogs as Awaited<ReturnType<typeof mockLogFindMany>>);

    const token = makeToken("user-1");
    const res = await request(app)
      .get("/api/progress/weight-history")
      .set("Authorization", `Bearer ${token}`);

    expect(res.status).toBe(200);
    expect(Array.isArray(res.body.weightHistory)).toBe(true);
    expect(res.body.weightHistory.length).toBe(7);
    // Each entry should have date and weightKg
    for (const entry of res.body.weightHistory) {
      expect(entry.date).toBeDefined();
      expect(entry.weightKg).toBeDefined();
    }
  });

  it("returns an empty array when no weight logs exist", async () => {
    mockLogFindMany.mockResolvedValueOnce([]);

    const token = makeToken("user-1");
    const res = await request(app)
      .get("/api/progress/weight-history")
      .set("Authorization", `Bearer ${token}`);

    expect(res.status).toBe(200);
    expect(res.body.weightHistory).toHaveLength(0);
  });
});

// ─── GET /api/progress ─────────────────────────────────────────────────────

describe("GET /api/progress", () => {
  it("returns 401 without auth token", async () => {
    const res = await request(app).get("/api/progress");
    expect(res.status).toBe(401);
  });

  it("returns 200 with all logs (most recent first)", async () => {
    mockLogFindMany.mockResolvedValueOnce(sevenDaysOfLogs as Awaited<ReturnType<typeof mockLogFindMany>>);

    const token = makeToken("user-1");
    const res = await request(app)
      .get("/api/progress")
      .set("Authorization", `Bearer ${token}`);

    expect(res.status).toBe(200);
    expect(res.body.logs).toHaveLength(7);
  });
});
