import { Router, Response } from "express";
import { z } from "zod";
import { prisma } from "../config/prisma";
import { requireAuth, AuthRequest } from "../middleware/auth";

const router = Router();

const logSchema = z.object({
  weightKg: z.number().positive().optional(),
  caloriesConsumed: z.number().nonnegative().optional(),
  proteinConsumedG: z.number().nonnegative().optional(),
  carbsConsumedG: z.number().nonnegative().optional(),
  fatConsumedG: z.number().nonnegative().optional(),
  notes: z.string().optional(),
});

router.post("/", requireAuth, async (req: AuthRequest, res: Response) => {
  const parsed = logSchema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ error: parsed.error.flatten() });

  const log = await prisma.progressLog.create({
    data: { userId: req.userId!, ...parsed.data },
  });
  return res.status(201).json({ log });
});

// GET /api/progress/summary - weekly nutrition summary + goal achievement %
router.get("/summary", requireAuth, async (req: AuthRequest, res: Response) => {
  const profile = await prisma.healthProfile.findUnique({ where: { userId: req.userId } });
  const sevenDaysAgo = new Date();
  sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);

  const logs = await prisma.progressLog.findMany({
    where: { userId: req.userId, date: { gte: sevenDaysAgo } },
    orderBy: { date: "asc" },
  });

  const avgCalories =
    logs.length > 0
      ? logs.reduce((sum: number, l: { caloriesConsumed: number | null }) => sum + (l.caloriesConsumed ?? 0), 0) /
        logs.length
      : 0;

  const goalAchievementPct =
    profile?.tdee && avgCalories > 0
      ? Math.min(100, Math.round((avgCalories / profile.tdee) * 100))
      : null;

  return res.json({
    logs,
    weeklyAverageCalories: Math.round(avgCalories),
    goalAchievementPct,
  });
});

// GET /api/progress/weight-history — returns { date, weightKg }[] for charting.
// Only entries where weightKg was recorded, last 90 days, ascending order.
router.get("/weight-history", requireAuth, async (req: AuthRequest, res: Response) => {
  const ninetyDaysAgo = new Date();
  ninetyDaysAgo.setDate(ninetyDaysAgo.getDate() - 90);

  const logs = await prisma.progressLog.findMany({
    where: {
      userId: req.userId,
      date: { gte: ninetyDaysAgo },
      weightKg: { not: null },
    },
    select: { date: true, weightKg: true },
    orderBy: { date: "asc" },
  });

  return res.json({ weightHistory: logs });
});

router.get("/", requireAuth, async (req: AuthRequest, res: Response) => {
  const logs = await prisma.progressLog.findMany({
    where: { userId: req.userId },
    orderBy: { date: "desc" },
    take: 100,
  });
  return res.json({ logs });
});

export default router;
