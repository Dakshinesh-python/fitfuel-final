import { Router, Response } from "express";
import { z } from "zod";
import { prisma } from "../config/prisma";
import { requireAuth, AuthRequest } from "../middleware/auth";

const router = Router();

/**
 * IMPORTANT: Swiggy and Zomato do not expose public order-placement APIs.
 * This endpoint logs the user's intent and returns a deep link that opens
 * the relevant app/site with a pre-filled search so the user completes
 * checkout themselves. This is a handoff, not a real order integration.
 */
function buildDeepLink(platform: "SWIGGY" | "ZOMATO", restaurant: string, query: string): string {
  const q = encodeURIComponent(`${restaurant} ${query}`);
  if (platform === "SWIGGY") {
    return `https://www.swiggy.com/search?query=${q}`;
  }
  return `https://www.zomato.com/search?q=${q}`;
}

const orderSchema = z.object({
  mealId: z.string().uuid(),
  platform: z.enum(["SWIGGY", "ZOMATO"]),
});

router.post("/", requireAuth, async (req: AuthRequest, res: Response) => {
  const parsed = orderSchema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ error: parsed.error.flatten() });

  const meal = await prisma.meal.findUnique({ where: { id: parsed.data.mealId } });
  if (!meal) return res.status(404).json({ error: "Meal not found" });

  const order = await prisma.order.create({
    data: {
      userId: req.userId!,
      mealId: meal.id,
      platform: parsed.data.platform,
    },
  });

  const deepLink = buildDeepLink(parsed.data.platform, meal.restaurant, meal.deepLinkQuery);

  return res.status(201).json({ order, deepLink });
});

router.get("/", requireAuth, async (req: AuthRequest, res: Response) => {
  const orders = await prisma.order.findMany({
    where: { userId: req.userId },
    include: { meal: true },
    orderBy: { createdAt: "desc" },
  });
  return res.json({ orders });
});

export default router;
