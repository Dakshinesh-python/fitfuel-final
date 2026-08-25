import express, { Express, Request, Response, NextFunction } from "express";
import cors from "cors";
import helmet from "helmet";
import morgan from "morgan";

import authRoutes from "./routes/auth.routes";
import healthProfileRoutes from "./routes/healthProfile.routes";
import mealRoutes from "./routes/meal.routes";
import recommendationRoutes from "./routes/recommendation.routes";
import mealPlanRoutes from "./routes/mealPlan.routes";
import orderRoutes from "./routes/order.routes";
import progressRoutes from "./routes/progress.routes";


/**
 * Parse the ALLOWED_ORIGINS environment variable (comma-separated list of
 * allowed origins, e.g. "http://localhost:5173,https://fitfuel-web.vercel.app").
 * Falls back to `true` (allow all) in development/test so local dev and CI
 * work without needing the variable explicitly set.
 */
function getAllowedOrigins(): string[] | boolean {
  const raw = process.env.ALLOWED_ORIGINS;
  if (!raw) {
    // In production, log a warning so operators notice the misconfiguration.
    if (process.env.NODE_ENV === "production") {
      console.warn("[CORS] ALLOWED_ORIGINS is not set — defaulting to allow-all. Set it in production.");
    }
    return true; // allow all in dev / test / unset
  }
  return raw.split(",").map((o) => o.trim()).filter(Boolean);
}

export function createApp(): Express {
  const app = express();

  app.use(helmet());
  app.use(cors({ origin: getAllowedOrigins(), credentials: true }));
  app.use(express.json());
  if (process.env.NODE_ENV !== "test") {
    app.use(morgan("dev"));
  }

  app.get("/health", (_req: Request, res: Response) => {
    res.json({ status: "ok", service: "fitfuel-backend", timestamp: new Date().toISOString() });
  });

  app.use("/api/auth", authRoutes);
  app.use("/api/health-profile", healthProfileRoutes);
  app.use("/api/meals", mealRoutes);
  app.use("/api/recommendations", recommendationRoutes);
  app.use("/api/meal-plans", mealPlanRoutes);
  app.use("/api/orders", orderRoutes);
  app.use("/api/progress", progressRoutes);

  // 404 handler
  app.use((_req: Request, res: Response) => {
    res.status(404).json({ error: "Not found" });
  });

  // Central error handler
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  app.use((err: Error, _req: Request, res: Response, _next: NextFunction) => {
    console.error(err);
    res.status(500).json({ error: "Internal server error" });
  });

  return app;
}
