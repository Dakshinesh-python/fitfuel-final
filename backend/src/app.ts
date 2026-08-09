import express, { Express, Request, Response, NextFunction } from "express";
import cors from "cors";
import helmet from "helmet";
import morgan from "morgan";

import authRoutes from "./routes/auth.routes";
import healthProfileRoutes from "./routes/healthProfile.routes";
import mealRoutes from "./routes/meal.routes";
import recommendationRoutes from "./routes/recommendation.routes";
import orderRoutes from "./routes/order.routes";
import progressRoutes from "./routes/progress.routes";

export function createApp(): Express {
  const app = express();

  app.use(helmet());
  app.use(cors());
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
