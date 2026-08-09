import { Router, Request, Response } from "express";
import bcrypt from "bcryptjs";
import jwt from "jsonwebtoken";
import { z } from "zod";
import { prisma } from "../config/prisma";

const router = Router();

const registerSchema = z.object({
  name: z.string().min(2),
  email: z.string().email(),
  password: z.string().min(6),
  age: z.number().int().positive().optional(),
  gender: z.enum(["MALE", "FEMALE", "OTHER"]).optional(),
  heightCm: z.number().positive().optional(),
  weightKg: z.number().positive().optional(),
});

function signToken(userId: string): string {
  const secret = process.env.JWT_SECRET ?? "dev-secret-change-me";
  return jwt.sign({ userId }, secret, { expiresIn: "7d" });
}

router.post("/register", async (req: Request, res: Response) => {
  const parsed = registerSchema.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({ error: parsed.error.flatten() });
  }
  const { name, email, password, age, gender, heightCm, weightKg } = parsed.data;

  const existing = await prisma.user.findUnique({ where: { email } });
  if (existing) {
    return res.status(409).json({ error: "Email already registered" });
  }

  const passwordHash = await bcrypt.hash(password, 10);
  const user = await prisma.user.create({
    data: { name, email, passwordHash, age, gender, heightCm, weightKg },
  });

  const token = signToken(user.id);
  return res.status(201).json({
    token,
    user: { id: user.id, name: user.name, email: user.email },
  });
});

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string(),
});

router.post("/login", async (req: Request, res: Response) => {
  const parsed = loginSchema.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({ error: parsed.error.flatten() });
  }
  const { email, password } = parsed.data;

  const user = await prisma.user.findUnique({ where: { email } });
  if (!user) {
    return res.status(401).json({ error: "Invalid credentials" });
  }

  const valid = await bcrypt.compare(password, user.passwordHash);
  if (!valid) {
    return res.status(401).json({ error: "Invalid credentials" });
  }

  const token = signToken(user.id);
  return res.json({ token, user: { id: user.id, name: user.name, email: user.email } });
});

export default router;
