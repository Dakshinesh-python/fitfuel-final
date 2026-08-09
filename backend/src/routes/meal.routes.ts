import { Router, Request, Response } from "express";
import { MealType, Platform, Prisma } from "@prisma/client";
import { prisma } from "../config/prisma";

const router = Router();

// GET /api/meals?mealType=BREAKFAST&cuisine=Indian&platform=SWIGGY
router.get("/", async (req: Request, res: Response) => {
  const { mealType, cuisine, platform } = req.query;

  const where: Prisma.MealWhereInput = {
    ...(mealType ? { mealType: mealType as MealType } : {}),
    ...(cuisine ? { cuisine: cuisine as string } : {}),
    ...(platform ? { platform: platform as Platform } : {}),
  };

  const meals = await prisma.meal.findMany({
    where,
    orderBy: { healthScore: "desc" },
    take: 100,
  });

  return res.json({ meals });
});

router.get("/:id", async (req: Request, res: Response) => {
  const meal = await prisma.meal.findUnique({ where: { id: req.params.id } });
  if (!meal) return res.status(404).json({ error: "Meal not found" });
  return res.json({ meal });
});

export default router;
