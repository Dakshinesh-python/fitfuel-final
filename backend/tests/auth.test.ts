/**
 * Auth route integration tests.
 * Prisma is mocked so no real database connection is needed in CI.
 */

import request from "supertest";
import bcrypt from "bcryptjs";
import { createApp } from "../src/app";

// Mock Prisma before the app is imported so all route handlers get the mock
jest.mock("../src/config/prisma", () => ({
  prisma: {
    user: {
      findUnique: jest.fn(),
      create: jest.fn(),
    },
  },
}));

import { prisma } from "../src/config/prisma";

const app = createApp();

const mockFindUnique = prisma.user.findUnique as jest.MockedFunction<typeof prisma.user.findUnique>;
const mockCreate = prisma.user.create as jest.MockedFunction<typeof prisma.user.create>;

const validUser = {
  id: "user-1",
  name: "Alice",
  email: "alice@example.com",
  passwordHash: bcrypt.hashSync("password123", 10),
  age: 25,
  gender: "FEMALE" as const,
  heightCm: 165,
  weightKg: 60,
  createdAt: new Date(),
  updatedAt: new Date(),
  healthProfile: null,
  mealPlans: [],
  progressLogs: [],
  orders: [],
};

beforeEach(() => {
  jest.clearAllMocks();
});

// ─── REGISTER ──────────────────────────────────────────────────────────────

describe("POST /api/auth/register", () => {
  it("creates a user and returns 201 with token + user (no passwordHash)", async () => {
    mockFindUnique.mockResolvedValueOnce(null); // no existing user
    mockCreate.mockResolvedValueOnce(validUser);

    const res = await request(app).post("/api/auth/register").send({
      name: "Alice",
      email: "alice@example.com",
      password: "password123",
    });

    expect(res.status).toBe(201);
    expect(res.body.token).toBeDefined();
    expect(res.body.user.email).toBe("alice@example.com");
    expect(res.body.user.passwordHash).toBeUndefined(); // must never be returned
  });

  it("returns 409 when email is already registered", async () => {
    mockFindUnique.mockResolvedValueOnce(validUser); // existing user found

    const res = await request(app).post("/api/auth/register").send({
      name: "Alice",
      email: "alice@example.com",
      password: "password123",
    });

    expect(res.status).toBe(409);
    expect(res.body.error).toMatch(/already registered/i);
  });

  it("returns 400 on invalid input (password too short)", async () => {
    const res = await request(app).post("/api/auth/register").send({
      name: "Alice",
      email: "alice@example.com",
      password: "abc", // < 6 chars
    });

    expect(res.status).toBe(400);
  });

  it("returns 400 when email is malformed", async () => {
    const res = await request(app).post("/api/auth/register").send({
      name: "Alice",
      email: "not-an-email",
      password: "password123",
    });

    expect(res.status).toBe(400);
  });
});

// ─── LOGIN ─────────────────────────────────────────────────────────────────

describe("POST /api/auth/login", () => {
  it("returns 200 with token + user on correct credentials", async () => {
    mockFindUnique.mockResolvedValueOnce(validUser);

    const res = await request(app).post("/api/auth/login").send({
      email: "alice@example.com",
      password: "password123",
    });

    expect(res.status).toBe(200);
    expect(res.body.token).toBeDefined();
    expect(res.body.user.id).toBe("user-1");
    expect(res.body.user.passwordHash).toBeUndefined();
  });

  it("returns 401 on wrong password (does not leak email existence)", async () => {
    mockFindUnique.mockResolvedValueOnce(validUser);

    const res = await request(app).post("/api/auth/login").send({
      email: "alice@example.com",
      password: "wrongpassword",
    });

    expect(res.status).toBe(401);
    expect(res.body.error).toBe("Invalid credentials");
  });

  it("returns 401 on unknown email (does not leak email existence)", async () => {
    mockFindUnique.mockResolvedValueOnce(null); // no user found

    const res = await request(app).post("/api/auth/login").send({
      email: "nobody@example.com",
      password: "password123",
    });

    expect(res.status).toBe(401);
    expect(res.body.error).toBe("Invalid credentials");
  });

  it("returns 400 when request body is invalid", async () => {
    const res = await request(app).post("/api/auth/login").send({
      email: "not-valid",
    });

    expect(res.status).toBe(400);
  });
});
