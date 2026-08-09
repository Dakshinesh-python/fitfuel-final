# FitFuel — Architecture & Tech Stack

> This document explains the full technical architecture of FitFuel: every layer, every library, the database schema, the recommendation algorithm, and the AI integration.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Backend](#2-backend)
3. [Web Frontend](#3-web-frontend)
4. [Mobile App](#4-mobile-app)
5. [Database Schema](#5-database-schema)
6. [Nutrition Calculation Engine](#6-nutrition-calculation-engine)
7. [Recommendation Algorithm](#7-recommendation-algorithm)
8. [AI Integration (Groq LLM)](#8-ai-integration-groq-llm)
9. [Authentication & Security](#9-authentication--security)
10. [CI/CD Architecture](#10-cicd-architecture)
11. [Data Flow Diagrams](#11-data-flow-diagrams)

---

## 1. System Overview

FitFuel is a **three-client, one-backend** architecture:

```
┌──────────────────────────────────────────────────────────────────┐
│                          CLIENTS                                  │
│                                                                   │
│  ┌─────────────────────┐     ┌────────────────────────────────┐  │
│  │   React Web App     │     │   Flutter Mobile App           │  │
│  │   (Vite + React 18) │     │   (Android & iOS)              │  │
│  │   TailwindCSS UI    │     │   Material Design 3 UI         │  │
│  │   Recharts graphs   │     │   fl_chart graphs              │  │
│  └──────────┬──────────┘     └──────────────┬─────────────────┘  │
└─────────────┼────────────────────────────────┼───────────────────┘
              │  JWT Bearer token               │  JWT Bearer token
              │  HTTPS REST JSON                │  HTTPS REST JSON
              ▼                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Express REST API (Node.js 20)                  │
│                                                                   │
│  Middleware stack:                                                │
│    Helmet (security headers) → CORS → Morgan (logging)           │
│    → JSON body parser → JWT auth guard → Zod validator           │
│                                                                   │
│  Route groups:                                                    │
│    /api/auth        /api/health-profile   /api/meals             │
│    /api/recommendations  /api/meal-plans  /api/orders            │
│    /api/progress    /api/chat                                     │
│                                                                   │
│  Business Logic Services:                                         │
│    nutritionCalculator.ts  │  recommendationEngine.ts            │
│    aiExplainerService.ts                                          │
└───────────────────────────────┬─────────────────────────────────┘
                                │
              ┌─────────────────┼──────────────────┐
              │                 │                   │
              ▼                 ▼                   ▼
  ┌───────────────────┐  ┌─────────────┐  ┌─────────────────┐
  │  PostgreSQL (DB)  │  │  Groq LLM   │  │  Swiggy/Zomato  │
  │  via Prisma ORM   │  │  API (free) │  │  Deep Links     │
  │  Supabase/Neon    │  │  llama3-70b │  │  (no API key)   │
  └───────────────────┘  └─────────────┘  └─────────────────┘
```

---

## 2. Backend

### Runtime & Framework

| Component | Choice | Reason |
|---|---|---|
| Runtime | **Node.js 20** | LTS, async I/O, large ecosystem |
| Language | **TypeScript 5** | Type safety, better IDE experience, compile-time errors |
| Framework | **Express 4** | Minimal, well-understood, large middleware ecosystem |
| ORM | **Prisma 5** | Type-safe DB client, migration system, schema-first |
| Validation | **Zod** | Runtime schema validation + TypeScript type inference |
| Auth | **jsonwebtoken + bcryptjs** | Industry standard JWT + password hashing |
| HTTP security | **Helmet** | Sets 11+ security HTTP response headers automatically |
| CORS | **cors** | Configured per-origin allow-list via `ALLOWED_ORIGINS` |
| Logging | **Morgan** | Request logger (dev: colourised, production: combined) |
| AI | **Groq API** (HTTP) | Free LLM inference, llama-3.3-70b-versatile model |

### Directory Structure

```
backend/
├── prisma/
│   ├── schema.prisma        # Data model + migrations
│   └── seed.ts              # 30+ seeded meals
├── src/
│   ├── server.ts            # Entry point (PORT binding)
│   ├── app.ts               # Express app factory + middleware
│   ├── config/
│   │   └── env.ts           # Typed env vars (throws if required vars missing)
│   ├── middleware/
│   │   └── auth.middleware.ts  # JWT verify → req.userId
│   ├── routes/
│   │   ├── auth.routes.ts        # register, login, profile, password
│   │   ├── healthProfile.routes.ts  # create/get health profile + calculations
│   │   ├── meal.routes.ts        # list meals
│   │   ├── recommendation.routes.ts  # scored meal list
│   │   ├── mealPlan.routes.ts    # get current / generate new plan
│   │   ├── order.routes.ts       # Swiggy/Zomato deep-link builder
│   │   ├── progress.routes.ts    # log entry CRUD + summary + weight history
│   │   └── chat.routes.ts        # AI chat proxy
│   └── services/
│       ├── nutritionCalculator.ts   # Pure functions: BMI, BMR, TDEE, macros
│       ├── recommendationEngine.ts  # Scoring algorithm
│       └── aiExplainerService.ts    # Groq API calls + prompt templates
├── tests/
│   ├── auth.test.ts
│   └── healthProfile.test.ts
├── .env.example
├── package.json
└── tsconfig.json
```

### API Port & Base Path

- Dev: `http://localhost:4000`
- All endpoints are prefixed `/api/`
- Health check: `GET /api/health` → `{ status: "ok" }`

---

## 3. Web Frontend

### Tech Stack

| Component | Choice |
|---|---|
| Bundler | **Vite 5** |
| Framework | **React 18** (functional components, hooks) |
| Language | **TypeScript 5** |
| Routing | **React Router v6** |
| Styling | **TailwindCSS 3** + custom CSS variables |
| HTTP client | **Axios** (with interceptor for JWT injection) |
| Charts | **Recharts** |
| Testing | **Vitest** + **React Testing Library** |
| Linting | **ESLint** + typescript-eslint |

### Design System

- **Colour palette**: Primary green `#006C4D` / `#2A9D58`, with coral accents for scores
- **Typography**: `Inter` (body) + `Manrope` (headings) — loaded from Google Fonts CDN
- **Card style**: White background, 16–24px radius, subtle shadow
- **Sidebar**: Dark green `#003D2E` with white text, icon + label nav items
- **Theme**: Light-mode only

### Directory Structure

```
web/src/
├── api/
│   └── apiClient.ts         # Axios instance + JWT interceptor + error handler
├── pages/
│   ├── Landing.tsx           # Public marketing page
│   ├── Register.tsx / Login.tsx
│   ├── HealthAssessment.tsx  # Multi-step form
│   ├── Dashboard.tsx         # Macro overview + stat cards
│   ├── Recommendations.tsx   # Pill-tab + scored meal cards
│   ├── MealPlan.tsx          # 7-day gradient grid
│   ├── Progress.tsx          # Recharts weight + calorie graphs
│   ├── Chat.tsx              # AI chat UI
│   └── Profile.tsx           # Tabbed settings
├── components/               # Shared UI components
├── contexts/                 # AuthContext (JWT token + user state)
├── App.tsx                   # Router + protected route wrapper
└── index.css                 # Tailwind directives + custom tokens
```

---

## 4. Mobile App

### Tech Stack

| Component | Choice |
|---|---|
| Framework | **Flutter 3.24** |
| Language | **Dart 3** |
| State management | **Provider 6** |
| HTTP | `http` package (custom `ApiService` singleton) |
| Auth storage | `shared_preferences` (JWT persisted locally) |
| Charts | **fl_chart 0.69** |
| Fonts | **google_fonts** (Manrope + Inter) |
| Deep links | `url_launcher` |
| Testing | `flutter_test` |
| Linting | `flutter_lints` |

### Architecture Patterns

- **`ApiService` singleton** — wraps all HTTP calls, injects JWT, throws `ApiException` for non-2xx
- **`AuthService` singleton** — stores/retrieves JWT from `SharedPreferences`
- **Screen-level state** — each screen is a `StatefulWidget` that manages its own loading/error/data state
- **Shared widgets** — `AppCard`, `FitFuelBottomNav`, `GradientHeroCard`, `MacroProgressRow`, `StatChip`, `PillTabSelector` defined in `lib/widgets/app_widgets.dart`
- **Theme** — all colours, text styles, radius values, spacing in `lib/theme/app_theme.dart`

### Bottom Navigation (5 tabs)

```
Home (0) | Meals (1) | Chat (2) | Progress (3) | Profile (4)
```

Tab 2 (Chat) uses a distinctive **raised green gradient pill** to highlight the AI feature.

### Directory Structure

```
fitfuel_mobile/lib/
├── main.dart                 # App entry, theme, named routes
├── models/
│   └── models.dart           # All data models (fromJson/toJson)
├── services/
│   ├── api_service.dart      # HTTP singleton with JWT injection
│   └── auth_service.dart     # SharedPreferences JWT store
├── theme/
│   └── app_theme.dart        # AppColors, AppTextStyles, AppRadius, buildAppTheme()
├── widgets/
│   └── app_widgets.dart      # All shared UI components
└── screens/
    ├── splash_screen.dart
    ├── onboarding_screen.dart
    ├── register_screen.dart / login_screen.dart
    ├── health_assessment_*.dart  (weight, goals, activity, prefs)
    ├── plan_ready_screen.dart
    ├── dashboard_screen.dart
    ├── recommendations_screen.dart
    ├── meal_detail_screen.dart
    ├── weekly_meal_plan_screen.dart
    ├── progress_screen.dart
    ├── chat_screen.dart
    └── profile_screen.dart
```

---

## 5. Database Schema

### Tables

```
User
  id           String   @id @default(cuid())
  email        String   @unique
  passwordHash String
  name         String
  createdAt    DateTime @default(now())
  updatedAt    DateTime @updatedAt

HealthProfile
  id              String   @id @default(cuid())
  userId          String   @unique
  age             Int
  gender          String   (MALE | FEMALE | OTHER)
  heightCm        Float
  currentWeightKg Float
  targetWeightKg  Float?
  activityLevel   String   (SEDENTARY | LIGHTLY_ACTIVE | MODERATELY_ACTIVE | VERY_ACTIVE | EXTRA_ACTIVE)
  fitnessGoal     String   (WEIGHT_LOSS | WEIGHT_GAIN | MUSCLE_GAIN | MAINTENANCE)
  dietaryPref     String   (NONE | VEGETARIAN | VEGAN | KETO | PALEO | GLUTEN_FREE)
  allergies       String[]
  bmi             Float?
  bmr             Float?
  tdee            Float?
  proteinTargetG  Float?
  carbTargetG     Int?
  fatTargetG      Float?
  aiExplanation   String?
  createdAt       DateTime @default(now())
  updatedAt       DateTime @updatedAt

Meal
  id          String   @id @default(cuid())
  name        String
  restaurant  String
  mealType    String   (BREAKFAST | LUNCH | DINNER | SNACK)
  calories    Int
  proteinG    Float
  carbsG      Float
  fatG        Float
  cuisineType String?
  imageUrl    String?
  isVeg       Boolean  @default(false)
  platform    String   (SWIGGY | ZOMATO | BOTH)
  searchQuery String?  (used for deep-link generation)

MealPlan
  id        String   @id @default(cuid())
  userId    String
  weekStart DateTime
  planJson  Json     (7-day nested structure)
  createdAt DateTime @default(now())

ProgressLog
  id                Int      @id @default(autoincrement())
  userId            String
  date              DateTime @default(now())
  weightKg          Float?
  caloriesConsumed  Int?
  proteinConsumedG  Int?
  carbsConsumedG    Int?
  fatConsumedG      Int?
  notes             String?

Order
  id         String   @id @default(cuid())
  userId     String
  mealId     String
  platform   String
  deepLink   String
  createdAt  DateTime @default(now())
```

---

## 6. Nutrition Calculation Engine

All calculations are in `backend/src/services/nutritionCalculator.ts` as pure, unit-tested functions.

### BMI
```
BMI = weight(kg) / (height(m))²
```

### BMR — Mifflin-St Jeor Equation
```
Male:   BMR = (10 × weight) + (6.25 × height) − (5 × age) + 5
Female: BMR = (10 × weight) + (6.25 × height) − (5 × age) − 161
Other:  BMR = average of male/female formulas
```

### TDEE
```
TDEE = BMR × Activity Multiplier

Multipliers:
  SEDENTARY          → 1.2
  LIGHTLY_ACTIVE     → 1.375
  MODERATELY_ACTIVE  → 1.55
  VERY_ACTIVE        → 1.725
  EXTRA_ACTIVE       → 1.9
```

### Calorie Target (Goal Adjustment)
```
WEIGHT_LOSS   → TDEE − 500 kcal  (≥ 1200 kcal floor)
WEIGHT_GAIN   → TDEE + 400 kcal
MUSCLE_GAIN   → TDEE + 300 kcal
MAINTENANCE   → TDEE (no adjustment)
```

### Macro Targets (per day)
```
Protein : 2.0g per kg of body weight  → calories = protein × 4
Fat     : 25% of calorie target        → calories = fat × 9
Carbs   : Remaining calories           → grams = remaining ÷ 4
```

---

## 7. Recommendation Algorithm

Defined in `backend/src/services/recommendationEngine.ts`.

Each meal is scored 0–100 based on four sub-scores, weighted:

```
Total Score = (calorieAccuracy × 0.35)
            + (proteinQuality  × 0.30)
            + (budgetFit       × 0.20)
            + (healthScore     × 0.15)
```

### Sub-score Details

**Calorie Accuracy (35%)** — How close the meal's calories are to the user's per-meal target (total target ÷ meals per day):
```
deviation = |meal.calories - targetPerMeal| / targetPerMeal
score = max(0, 100 − (deviation × 100))
```

**Protein Quality (30%)** — How much of the protein target a single meal contributes:
```
contribution = meal.proteinG / (dailyProteinTarget / mealsPerDay)
score = min(100, contribution × 100)
```

**Budget Fit (20%)** — Static heuristic based on restaurant tier (seeded):
- Premium: 60
- Mid-range: 85
- Budget-friendly: 100

**Health Score (15%)** — Based on fat ratio:
```
fatRatio = meal.fatG × 9 / meal.calories
score = fatRatio < 0.25 → 100 | fatRatio < 0.35 → 75 | else → 50
```

Meals are filtered by `mealType`, sorted descending by total score, top 10 returned.

---

## 8. AI Integration (Groq LLM)

### Provider: Groq Cloud
- **Model**: `llama-3.3-70b-versatile`
- **Free tier**: ~30 requests/min, 6000 tokens/min
- **Endpoint**: `https://api.groq.com/openai/v1/chat/completions` (OpenAI-compatible)

### Feature 1 — Health Profile Explanation
Called when a health profile is saved. Generates a 2–3 sentence personalised explanation of the user's macro targets.

```
System: "You are a professional nutritionist. Be concise and encouraging."
User: "Here are the nutrition targets for [name]: BMI X, BMR Y kcal, TDEE Z kcal,
       goal: WEIGHT_LOSS, protein Xg, carbs Yg, fat Zg per day.
       Explain these results in 2-3 sentences."
```

### Feature 2 — Meal Plan Explanation
Called during 7-day plan generation. Explains why the plan suits the user's goal.

### Feature 3 — AI Chat Coach
Real-time conversation. System prompt injects user health profile as context:
```
System: "You are FitFuel's AI nutrition coach.
         User profile: [name], goal: [goal], BMI: [bmi], protein: [x]g/day...
         Answer questions about nutrition, meal choices, and fitness.
         Be concise, evidence-based, and encouraging. Max 3 paragraphs."
```

Conversation history (last 10 messages) is sent with each request for context continuity.

### Graceful Degradation
If `GROQ_API_KEY` is empty or the API fails, all AI features degrade gracefully:
- Profile explanation: `null` (UI hides the explanation card)
- Chat: Returns `"AI service unavailable"` message
- Meal plan: Plan is generated without an AI explanation

---

## 9. Authentication & Security

### Token Flow
```
1. POST /api/auth/register → bcrypt hash password → create User in DB
                           → sign JWT (userId, 7d expiry) → return token

2. POST /api/auth/login    → bcrypt compare → if match, sign new JWT → return token

3. All protected routes:
   Request header: Authorization: Bearer <token>
   auth.middleware.ts: jwt.verify(token, JWT_SECRET) → set req.userId
   → route handler uses req.userId to scope all queries
```

### Security Measures

| Layer | Control |
|---|---|
| Passwords | bcrypt, cost factor 10 |
| Tokens | JWT HS256, 7-day expiry |
| Transport | HTTPS in production (Render provides TLS) |
| HTTP headers | Helmet.js (CSP, HSTS, X-Frame-Options, etc.) |
| Input validation | Zod schemas on all request bodies |
| SQL injection | Prisma ORM — parameterised queries, no raw SQL |
| CORS | Explicit allow-list via `ALLOWED_ORIGINS` |
| Secrets | `.env` files — never committed (in `.gitignore`) |

---

## 10. CI/CD Architecture

### Workflow: `backend-ci.yml`

Triggers on push/PR when files in `backend/**` change.

```
Steps:
  1. Checkout + Node.js 20 setup
  2. Start PostgreSQL service container (postgres:15)
  3. npm install
  4. prisma generate + prisma migrate deploy (on test DB)
  5. npm run lint (ESLint)
  6. npm test (Jest + Supertest)
  7. npm run build (TypeScript compile)
  8. Deploy to Render via deploy hook (on push to main)
```

### Workflow: `web-ci.yml`

Triggers on push/PR when files in `web/**` change.

```
Steps:
  1. Checkout + Node.js 20 setup
  2. npm install
  3. npm run lint (ESLint)
  4. npm test (Vitest)
  5. npm run build (Vite)
  6. Deploy to Vercel (on push to main)
```

### Workflow: `mobile-ci.yml`

Triggers on push/PR when files in `fitfuel_mobile/**` change.

```
Steps:
  1. Checkout + Flutter 3.24 setup (subosito/flutter-action)
  2. flutter pub get
  3. flutter analyze (must have 0 errors, 0 warnings)
  4. flutter test
  5. flutter build apk --release
     --dart-define=API_BASE_URL=${{ secrets.MOBILE_API_BASE_URL }}
  6. Upload APK as artifact (retained 90 days)
```

---

## 11. Data Flow Diagrams

### User Registration + Health Assessment

```
User fills Register form
    │
    ▼
POST /api/auth/register
    │  bcrypt hash password
    │  INSERT User
    │
    ▼ JWT returned
User completes 4-step health assessment
    │
    ▼
POST /api/health-profile
    │  calculateBMI(weight, height)
    │  calculateBMR(weight, height, age, gender)
    │  calculateTDEE(bmr, activityLevel)
    │  calculateMacros(tdee, goal, weight)
    │  [optional] groqExplain(profile) → aiExplanation
    │  INSERT HealthProfile
    │
    ▼
Redirect to Dashboard — macro targets displayed
```

### Meal Recommendation Flow

```
User selects meal type (Breakfast / Lunch / Dinner / Snack)
    │
    ▼
GET /api/recommendations?mealType=LUNCH
    │  Fetch user HealthProfile (proteinTarget, tdee, goal)
    │  Fetch all Meals WHERE mealType = LUNCH
    │  For each meal: scoreMeal(meal, profile) → 0-100 score
    │  Sort descending, return top 10
    │
    ▼
Scored meal cards displayed
    │
User taps "Order on Swiggy"
    │
    ▼
POST /api/orders { mealId, platform: "SWIGGY" }
    │  Build deep link: https://www.swiggy.com/search?query=<meal.searchQuery>
    │  INSERT Order record
    │  Return { deepLink }
    │
    ▼
App opens deep link in browser → User completes order on Swiggy/Zomato
```

### AI Chat Flow

```
User types message
    │
    ▼
POST /api/chat { message, history: [...last 10 messages] }
    │  Fetch HealthProfile for context
    │  Build system prompt with user stats
    │  POST to Groq API (OpenAI-compatible)
    │  Stream / await completion
    │
    ▼
AI response rendered in chat UI
```

---

*For deployment instructions, see [`docs/DEPLOYMENT.md`](DEPLOYMENT.md).*
*For the full API reference, see [`docs/API_REFERENCE.md`](API_REFERENCE.md).*
