import { Router, Request, Response } from "express";
import { z } from "zod";
import { MealType, Platform, Prisma } from "@prisma/client";
import { prisma } from "../config/prisma";

const router = Router();

const mealTypeSchema = z.nativeEnum(MealType).optional();
const platformSchema = z.nativeEnum(Platform).optional();

// GET /api/meals?mealType=BREAKFAST&cuisine=Indian&platform=SWIGGY
router.get("/", async (req: Request, res: Response) => {
  const { mealType, cuisine, platform } = req.query;

  const mealTypeResult = mealTypeSchema.safeParse(mealType);
  const platformResult = platformSchema.safeParse(platform);

  if (!mealTypeResult.success || !platformResult.success) {
    return res.status(400).json({ error: "Invalid mealType or platform value" });
  }

  const where: Prisma.MealWhereInput = {
    ...(mealTypeResult.data ? { mealType: mealTypeResult.data } : {}),
    ...(cuisine ? { cuisine: cuisine as string } : {}),
    ...(platformResult.data ? { platform: platformResult.data } : {}),
  };

  try {
    const meals = await prisma.meal.findMany({
      where,
      orderBy: { healthScore: "desc" },
      take: 100,
    });

    return res.json({ meals });
  } catch (err) {
    console.error(err);
    return res.status(400).json({ error: "Invalid query parameters" });
  }
});

router.get("/:id", async (req: Request, res: Response) => {
  const meal = await prisma.meal.findUnique({ where: { id: req.params.id } });
  if (!meal) return res.status(404).json({ error: "Meal not found" });
  return res.json({ meal });
});

export default router;