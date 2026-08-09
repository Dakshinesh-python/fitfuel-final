-- FitFuel — complete initial schema migration
-- Creates all tables and enums from schema.prisma in a single migration.
-- imageUrl is included on Meal from the start (no separate ALTER TABLE needed).

-- ── Enum types ────────────────────────────────────────────────────────────────

CREATE TYPE "Gender" AS ENUM ('MALE', 'FEMALE', 'OTHER');

CREATE TYPE "ActivityLevel" AS ENUM (
    'SEDENTARY', 'LIGHT', 'MODERATE', 'ACTIVE', 'VERY_ACTIVE'
);

CREATE TYPE "FitnessGoal" AS ENUM (
    'WEIGHT_LOSS', 'WEIGHT_GAIN', 'MUSCLE_GAIN', 'MAINTENANCE'
);

CREATE TYPE "DietaryPreference" AS ENUM (
    'VEGETARIAN', 'NON_VEGETARIAN', 'VEGAN'
);

CREATE TYPE "MealType" AS ENUM ('BREAKFAST', 'LUNCH', 'DINNER', 'SNACK');

CREATE TYPE "Platform" AS ENUM ('SWIGGY', 'ZOMATO');

-- ── User ─────────────────────────────────────────────────────────────────────

CREATE TABLE "User" (
    "id"           TEXT             NOT NULL,
    "name"         TEXT             NOT NULL,
    "email"        TEXT             NOT NULL,
    "passwordHash" TEXT             NOT NULL,
    "age"          INTEGER,
    "gender"       "Gender",
    "heightCm"     DOUBLE PRECISION,
    "weightKg"     DOUBLE PRECISION,
    "createdAt"    TIMESTAMP(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt"    TIMESTAMP(3)     NOT NULL,

    CONSTRAINT "User_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX "User_email_key" ON "User"("email");

-- ── HealthProfile ─────────────────────────────────────────────────────────────

CREATE TABLE "HealthProfile" (
    "id"                TEXT                NOT NULL,
    "userId"            TEXT                NOT NULL,
    "currentWeightKg"   DOUBLE PRECISION    NOT NULL,
    "targetWeightKg"    DOUBLE PRECISION    NOT NULL,
    "activityLevel"     "ActivityLevel"     NOT NULL,
    "fitnessGoal"       "FitnessGoal"       NOT NULL,
    "dietaryPreference" "DietaryPreference" NOT NULL,
    "allergies"         TEXT[]              NOT NULL DEFAULT ARRAY[]::TEXT[],
    "dailyBudget"       DOUBLE PRECISION    NOT NULL,
    "bmi"               DOUBLE PRECISION,
    "bmr"               DOUBLE PRECISION,
    "tdee"              DOUBLE PRECISION,
    "proteinTargetG"    DOUBLE PRECISION,
    "carbTargetG"       DOUBLE PRECISION,
    "fatTargetG"        DOUBLE PRECISION,
    "createdAt"         TIMESTAMP(3)        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt"         TIMESTAMP(3)        NOT NULL,

    CONSTRAINT "HealthProfile_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX "HealthProfile_userId_key" ON "HealthProfile"("userId");

-- ── Meal ──────────────────────────────────────────────────────────────────────

CREATE TABLE "Meal" (
    "id"            TEXT             NOT NULL,
    "name"          TEXT             NOT NULL,
    "restaurant"    TEXT             NOT NULL,
    "platform"      "Platform"       NOT NULL,
    "cuisine"       TEXT             NOT NULL,
    "mealType"      "MealType"       NOT NULL,
    "calories"      DOUBLE PRECISION NOT NULL,
    "proteinG"      DOUBLE PRECISION NOT NULL,
    "carbsG"        DOUBLE PRECISION NOT NULL,
    "fatG"          DOUBLE PRECISION NOT NULL,
    "price"         DOUBLE PRECISION NOT NULL,
    "healthScore"   DOUBLE PRECISION NOT NULL,
    "isVegetarian"  BOOLEAN          NOT NULL DEFAULT false,
    "isVegan"       BOOLEAN          NOT NULL DEFAULT false,
    "allergens"     TEXT[]           NOT NULL DEFAULT ARRAY[]::TEXT[],
    "imageUrl"      TEXT,
    "deepLinkQuery" TEXT             NOT NULL,
    "createdAt"     TIMESTAMP(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Meal_pkey" PRIMARY KEY ("id")
);

-- ── MealPlan ─────────────────────────────────────────────────────────────────

CREATE TABLE "MealPlan" (
    "id"        TEXT         NOT NULL,
    "userId"    TEXT         NOT NULL,
    "weekStart" TIMESTAMP(3) NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "MealPlan_pkey" PRIMARY KEY ("id")
);

-- ── MealPlanItem ─────────────────────────────────────────────────────────────

CREATE TABLE "MealPlanItem" (
    "id"         TEXT             NOT NULL,
    "mealPlanId" TEXT             NOT NULL,
    "mealId"     TEXT             NOT NULL,
    "dayOfWeek"  INTEGER          NOT NULL,
    "mealType"   "MealType"       NOT NULL,
    "matchScore" DOUBLE PRECISION NOT NULL,

    CONSTRAINT "MealPlanItem_pkey" PRIMARY KEY ("id")
);

-- ── Order ─────────────────────────────────────────────────────────────────────

CREATE TABLE "Order" (
    "id"        TEXT         NOT NULL,
    "userId"    TEXT         NOT NULL,
    "mealId"    TEXT         NOT NULL,
    "platform"  "Platform"   NOT NULL,
    "status"    TEXT         NOT NULL DEFAULT 'REDIRECTED',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Order_pkey" PRIMARY KEY ("id")
);

-- ── ProgressLog ──────────────────────────────────────────────────────────────

CREATE TABLE "ProgressLog" (
    "id"               TEXT             NOT NULL,
    "userId"           TEXT             NOT NULL,
    "date"             TIMESTAMP(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "weightKg"         DOUBLE PRECISION,
    "caloriesConsumed" DOUBLE PRECISION,
    "proteinConsumedG" DOUBLE PRECISION,
    "carbsConsumedG"   DOUBLE PRECISION,
    "fatConsumedG"     DOUBLE PRECISION,
    "notes"            TEXT,

    CONSTRAINT "ProgressLog_pkey" PRIMARY KEY ("id")
);

-- ── Foreign keys ──────────────────────────────────────────────────────────────

ALTER TABLE "HealthProfile"
    ADD CONSTRAINT "HealthProfile_userId_fkey"
    FOREIGN KEY ("userId") REFERENCES "User"("id")
    ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE "MealPlan"
    ADD CONSTRAINT "MealPlan_userId_fkey"
    FOREIGN KEY ("userId") REFERENCES "User"("id")
    ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE "MealPlanItem"
    ADD CONSTRAINT "MealPlanItem_mealPlanId_fkey"
    FOREIGN KEY ("mealPlanId") REFERENCES "MealPlan"("id")
    ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE "MealPlanItem"
    ADD CONSTRAINT "MealPlanItem_mealId_fkey"
    FOREIGN KEY ("mealId") REFERENCES "Meal"("id")
    ON DELETE RESTRICT ON UPDATE CASCADE;

ALTER TABLE "Order"
    ADD CONSTRAINT "Order_userId_fkey"
    FOREIGN KEY ("userId") REFERENCES "User"("id")
    ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE "Order"
    ADD CONSTRAINT "Order_mealId_fkey"
    FOREIGN KEY ("mealId") REFERENCES "Meal"("id")
    ON DELETE RESTRICT ON UPDATE CASCADE;

ALTER TABLE "ProgressLog"
    ADD CONSTRAINT "ProgressLog_userId_fkey"
    FOREIGN KEY ("userId") REFERENCES "User"("id")
    ON DELETE CASCADE ON UPDATE CASCADE;
