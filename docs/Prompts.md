# FitFuel — Agent Task Prompts (for Antigravity)

How to use this file:
1. Paste the **MASTER PROMPT** first in a new Antigravity session (or as the system/project
   context) so the agent understands the whole project before touching any code.
2. Then run each **TASK PROMPT** in order, one at a time, in the same session/workspace.
   Each task prompt is self-contained (repeats the essential context) so you can also run
   them in separate sessions if needed — but running in order in one workspace is best,
   since later tasks depend on earlier ones.
3. After each task, tell the agent to run lint/tests/build before moving to the next prompt.
   Each prompt already ends with a "Definition of done" checklist — hold the agent to it.
4. The repo already has a working scaffold (backend logic, some web pages, some Flutter
   screens, CI workflows). Every prompt tells the agent to **check what already exists
   first**, complete/fix what's missing, and never blindly overwrite working code.

---

## MASTER PROMPT (paste this first, once)

```
You are working on FitFuel — an "Intelligent AI-Based Nutrition & Food Ordering Platform."
This is a final-year academic project that must be a genuinely working, testable,
deployable product — not a mockup.

PROJECT OVERVIEW
FitFuel lets a user sign up, complete a health/fitness questionnaire, and receive:
- Calculated BMI, BMR, TDEE (daily calorie need), and macro (protein/carb/fat) targets
- Personalized meal recommendations pulled from a database of restaurant meals
  (styled after what you'd find on Swiggy/Zomato), ranked by a scoring algorithm
- A weekly meal plan
- "Order on Swiggy" / "Order on Zomato" buttons
- Progress tracking (weight, calories, macros, goal achievement %) over time

IMPORTANT REALITY CONSTRAINT — READ CAREFULLY
Swiggy and Zomato do NOT provide public order-placement APIs to third-party developers.
There is no legitimate way to place a real order on either platform programmatically from
an external app. Therefore "Order on Swiggy/Zomato" must ALWAYS be implemented as a deep
link / URL that opens the platform's search page with the restaurant/meal name pre-filled,
letting the user complete checkout themselves on Swiggy's or Zomato's own site/app. Do NOT
attempt to simulate, mock, or fake a real order-placement API integration — implement the
honest deep-link handoff every time this comes up, and say so in code comments/UI copy.

THE 7 PROJECT PHASES (for reference across all tasks)
1. User Registration & Profile Creation — signup/login, name/age/gender/height/weight
2. Health Assessment — current/target weight, activity level, fitness goal, dietary
   preference, allergies, daily food budget
3. AI Nutrition Engine — calculates BMI, BMR, TDEE, and protein/carb/fat targets from
   Phase 2 data using standard formulas (Mifflin-St Jeor for BMR); generates daily calorie
   target, macro split, and a weekly meal plan
4. Smart Food Database — a database of meals (restaurant, platform, calories, protein,
   carbs, fat, price, cuisine, meal type, health score)
5. Intelligent Meal Recommendation — ranks meals against the user's targets/budget/
   preferences using a transparent weighted-scoring algorithm (not a black-box model)
6. Order Integration — "Order on Swiggy/Zomato" buttons that open a deep link (see
   constraint above)
7. Progress Tracking — daily calorie intake, weekly nutrition summary, weight progress,
   goal achievement %, meal history, personalized insights

TECH STACK (do not deviate without asking the user first)
- Backend: Node.js + TypeScript + Express, Prisma ORM, PostgreSQL (Supabase or Neon free
  tier), JWT auth (jsonwebtoken + bcryptjs), Zod for request validation
- Web app: React + TypeScript + Vite + Tailwind CSS, React Router, Axios
- Mobile app: Flutter (Dart), Provider for state management, http package for API calls,
  shared_preferences for token storage, fl_chart for progress charts, url_launcher for
  deep links
- AI layer: deterministic formulas for all numeric calculations (BMI/BMR/TDEE/macros/
  scoring) — NEVER let an LLM generate the actual numbers. Groq's free API
  (https://console.groq.com, model "llama-3.1-8b-instant", OpenAI-compatible
  /v1/chat/completions endpoint) is used ONLY for natural-language explanations of
  already-calculated numbers, and must gracefully degrade to a templated string if
  GROQ_API_KEY is not set — the app must fully work without it.
- Testing: Jest + Supertest (backend), Vitest + React Testing Library (web), flutter_test
  (mobile)
- CI/CD: GitHub Actions, one workflow per app, path-filtered so each only runs when its
  folder changes
- Everything must run on FREE tiers: Supabase/Neon (DB), Render (backend hosting), Vercel
  (web hosting), GitHub Actions artifacts (APK distribution — no Play Store fee needed)

REPO STRUCTURE
fitfuel/
├── backend/           Express + TypeScript + Prisma REST API
│   ├── src/
│   │   ├── routes/        one file per resource (auth, healthProfile, meal,
│   │                        recommendation, order, progress)
│   │   ├── services/       pure business logic (nutritionCalculator, recommendationEngine,
│   │                        aiExplainerService) — keep these framework-free and unit-testable
│   │   ├── middleware/      auth.ts (JWT verification)
│   │   ├── config/          prisma.ts (PrismaClient singleton)
│   │   ├── app.ts           Express app factory (no app.listen here — testable)
│   │   └── server.ts        entry point, calls app.listen
│   ├── prisma/
│   │   ├── schema.prisma
│   │   └── seed.ts
│   └── tests/              Jest + Supertest
├── web/                React + Vite + TypeScript + Tailwind
│   ├── src/
│   │   ├── pages/           one per screen (Login, Register, HealthAssessment, Dashboard,
│   │                          Recommendations, Progress)
│   │   ├── components/      shared UI (Layout, etc.)
│   │   ├── api/             client.ts (Axios instance + auth token handling)
│   │   ├── types/           shared TS interfaces mirroring backend Prisma models
│   │   └── utils/           client-side helpers (e.g. bmi.ts)
│   └── tests/              Vitest + React Testing Library
├── mobile/             Flutter app
│   ├── lib/
│   │   ├── screens/         one per screen
│   │   ├── services/        api_service.dart, auth_service.dart, api_config.dart,
│   │                          nutrition_helper.dart
│   │   └── models/          models.dart (Dart classes mirroring backend Prisma models)
│   └── test/                flutter_test
├── .github/workflows/  backend-ci.yml, web-ci.yml, mobile-ci.yml
├── docs/               API_REFERENCE.md and any other handover docs
└── README.md

CODING CONVENTIONS
- TypeScript everywhere on backend/web: strict mode on, no `any` — if you don't know a
  type, define an interface/type instead of casting to `any`. This is enforced by ESLint
  (`@typescript-eslint/no-explicit-any` is an error, not a warning) and CI will fail on it.
- All numeric health calculations live in framework-free service functions in
  `backend/src/services/`, unit-tested independently of Express/Prisma so they run fast
  and don't need a database.
- Every route file: validate input with Zod, return proper HTTP status codes (400 for
  validation errors, 401 for auth failures, 404 for not found, 409 for conflicts, 500
  only for unexpected errors), never leak stack traces to the client.
- Every new backend feature needs: the route, a Zod schema, and at least one Jest test.
- Every new web page needs: the component, wiring in App.tsx routing, and at least one
  Vitest test.
- Every new Flutter screen needs: the widget, navigation wiring, and — where there's
  non-trivial logic — a flutter_test.
- Before considering any task complete: run the linter, run the tests, run the build, for
  every app you touched. Fix any failures. Do not report a task as done if lint, tests, or
  build are failing.
- Keep git commits small and scoped to one task each, with clear messages.

DEFINITION OF DONE (applies to every task below)
- Code compiles/builds with zero errors
- Linter passes with zero errors
- All tests pass (existing tests must still pass, new tests must be added for new logic)
- No hardcoded secrets — everything sensitive goes through environment variables, and
  `.env.example` is updated if a new variable is introduced
- No `any` types, no commented-out dead code, no TODO left unresolved without flagging it
  to the user explicitly in your final summary

Acknowledge you've understood this before I give you the first task prompt.
```

---

## TASK 1 — Backend: Verify & Complete Core Setup (Auth, Schema, Config)

```
CONTEXT: Refer to the FitFuel MASTER PROMPT context already given (tech stack, repo
structure, conventions). This task covers Phase 1 (Registration/Login) and the underlying
database schema all other phases depend on.

GOAL: Ensure `backend/` has a fully working, tested Express + TypeScript + Prisma API
skeleton with authentication.

REQUIREMENTS
1. Check `backend/prisma/schema.prisma` for these models (create/fix if missing or
   incomplete): User, HealthProfile, Meal, MealPlan, MealPlanItem, Order, ProgressLog, and
   enums Gender, ActivityLevel, FitnessGoal, DietaryPreference, MealType, Platform.
   - User: id, name, email (unique), passwordHash, age, gender, heightCm, weightKg,
     timestamps, relations to HealthProfile/MealPlan/ProgressLog/Order
2. Check `backend/src/routes/auth.routes.ts`:
   - POST /api/auth/register — Zod-validates name/email/password (min 6 chars)/optional
     age/gender/heightCm/weightKg, rejects duplicate emails with 409, hashes password with
     bcryptjs, returns a signed JWT (7-day expiry) + user object (never the password hash)
   - POST /api/auth/login — validates email/password, returns 401 on any mismatch (don't
     leak whether the email exists), returns JWT + user object on success
3. Check `backend/src/middleware/auth.ts` — `requireAuth` middleware that reads the
   `Authorization: Bearer <token>` header, verifies the JWT, attaches `userId` to the
   request, returns 401 on missing/invalid/expired tokens
4. Check `backend/src/config/prisma.ts` — a PrismaClient singleton that avoids creating
   multiple instances during dev hot-reload
5. Check `backend/src/app.ts` — Express app factory (helmet, cors, json body parsing,
   morgan logging outside test env, a GET /health endpoint, all route files mounted under
   /api/*, a 404 handler, and a central error handler that never leaks stack traces)
6. Check `backend/.env.example` has PORT, NODE_ENV, DATABASE_URL, JWT_SECRET, GROQ_API_KEY
7. Check `backend/package.json` scripts exist: dev, build, start, lint, test, test:watch,
   prisma:generate, prisma:migrate, prisma:deploy, prisma:seed
8. Check `backend/tsconfig.json` — strict mode, rootDir "src", and make sure `include`
   does NOT also list "tests" (that conflicts with rootDir and breaks `npm run build` —
   this exact bug has occurred before, verify it's not present)

TESTING
- Write/verify Jest+Supertest tests in `backend/tests/app.test.ts` for GET /health (200)
  and an unknown route (404)
- Write/verify tests for register (success, duplicate email 409, invalid input 400) and
  login (success, wrong password 401, unknown email 401) — mock or use a test database

DEFINITION OF DONE
- `npm run lint`, `npm test`, `npm run build` all pass with zero errors in `backend/`
- `npx prisma generate` and `npx prisma migrate dev` succeed against a real Postgres
  connection (local Docker Postgres or a free Supabase/Neon instance)
- Registering then logging in with the same credentials via curl/Postman returns a valid
  JWT both times
```

---

## TASK 2 — Backend: Health Assessment & AI Nutrition Engine (Phases 2 & 3)

```
CONTEXT: Builds on TASK 1. Refer to the FitFuel MASTER PROMPT for conventions.

GOAL: Implement the health questionnaire endpoint and the deterministic nutrition
calculation engine (BMI, BMR, TDEE, macros) — this is the "AI Nutrition Engine" core.

REQUIREMENTS
1. Check/create `backend/src/services/nutritionCalculator.ts` as a pure, framework-free
   TypeScript module (no Express/Prisma imports) exporting:
   - calculateBMI(weightKg, heightCm): number — weight / height(m)^2, rounded to 1 decimal
   - bmiCategory(bmi): string — "Underweight" (<18.5) / "Normal weight" (<25) /
     "Overweight" (<30) / "Obese" (>=30)
   - calculateBMR(weightKg, heightCm, age, gender): number — Mifflin-St Jeor equation:
     10*weight + 6.25*height - 5*age, +5 for MALE, -161 for FEMALE, -78 for OTHER
   - calculateTDEE(bmr, activityLevel): number — bmr * activity multiplier
     (SEDENTARY 1.2, LIGHT 1.375, MODERATE 1.55, ACTIVE 1.725, VERY_ACTIVE 1.9)
   - calculateNutritionTargets(metrics): full object combining all of the above, plus a
     goal-adjusted calorie target (WEIGHT_LOSS -500, WEIGHT_GAIN +400, MUSCLE_GAIN +300,
     MAINTENANCE +0 on top of TDEE, never recommend below 1200 kcal), and macro grams
     split by goal-specific percentages (protein/carbs at 4 kcal/g, fat at 9 kcal/g)
2. Check/create `backend/src/routes/healthProfile.routes.ts`:
   - POST /api/health-profile (auth required) — Zod-validates currentWeightKg,
     targetWeightKg, activityLevel, fitnessGoal, dietaryPreference, allergies (string
     array), dailyBudget. Requires the user already has age/gender/heightCm on their
     User record (400 if not — tell them to complete basic profile first). Calculates
     targets via nutritionCalculator, upserts a HealthProfile row, and returns
     { profile, targets, explanation } where explanation is an optional LLM-generated
     plain-language summary (see TASK 5 — call it if it exists, otherwise return null
     without failing the request)
   - GET /api/health-profile (auth required) — returns the current user's profile, 404 if
     none exists yet
3. Design the "weekly meal plan" generation as its own concern for TASK 4 — this task is
   only the numeric targets, not meal selection.

TESTING
- Add `backend/tests/nutritionCalculator.test.ts` covering: BMI calculation accuracy,
  every BMI category boundary, BMR for at least MALE and FEMALE, TDEE for at least two
  activity levels, the 1200-kcal floor under an aggressive cut, and that macro grams
  converted back to calories roughly sum to the calorie target (within ~30 kcal)
- Add/verify an integration test for POST /api/health-profile happy path

DEFINITION OF DONE
- All nutritionCalculator unit tests pass and cover every branch (all 4 BMI categories,
  all 5 activity levels, all 4 fitness goals)
- `npm run lint`, `npm test`, `npm run build` pass in `backend/`
- Manually verify via curl: a 70kg/175cm/25yo male, MODERATE activity, MUSCLE_GAIN goal
  gets sensible non-zero calorie/macro targets back
```

---

## TASK 3 — Backend: Smart Food Database & Seed Data (Phase 4)

```
CONTEXT: Builds on TASKS 1-2. Refer to the FitFuel MASTER PROMPT for conventions and the
Swiggy/Zomato constraint.

GOAL: Build the Meal model, the public meal-browsing endpoints, and a realistic seed
dataset representing restaurant meals across platforms/cuisines/meal types.

REQUIREMENTS
1. Confirm the Meal model in `schema.prisma` has: id, name, restaurant, platform
   (SWIGGY|ZOMATO), cuisine, mealType (BREAKFAST|LUNCH|DINNER|SNACK), calories, proteinG,
   carbsG, fatG, price, healthScore (0-100), isVegetarian, isVegan, allergens (string
   array), deepLinkQuery (string used to build the Swiggy/Zomato search deep link later),
   createdAt
2. Check/create `backend/src/routes/meal.routes.ts` (no auth required — public browsing):
   - GET /api/meals — optional query filters mealType, cuisine, platform; sorted by
     healthScore descending; capped at 100 results. Type query params properly using the
     Prisma-generated MealType/Platform enums and a Prisma.MealWhereInput — do NOT cast to
     `any`.
   - GET /api/meals/:id — single meal, 404 if not found
3. Check/create `backend/prisma/seed.ts`:
   - At least 12 realistic sample meals spanning all 4 meal types, both platforms
     (SWIGGY/ZOMATO), multiple cuisines (e.g. North Indian, South Indian, Continental,
     Chinese, Healthy Bowls), a realistic price range in INR, a mix of veg/non-veg/vegan,
     a mix of allergens (dairy, egg, gluten, soy, nuts, fish, peanuts)
   - Compute healthScore programmatically from macros (e.g. reward protein-to-calorie
     ratio, penalize fat-to-calorie ratio) rather than hardcoding it per meal — write this
     as a small pure function you can unit test if you want
   - Wire `npm run prisma:seed` (already in package.json from TASK 1) to run this file via
     tsx
4. Update `backend/.env.example` and README if any new env vars are needed (should not be,
   this task is DB-only)

TESTING
- If you extract a healthScore-computation function, add a small Jest test for it
  (e.g. a high-protein low-fat meal scores higher than a high-fat low-protein one)
- Add an integration test for GET /api/meals with and without filters, and GET /api/meals/
  :id for a valid id and a 404 case

DEFINITION OF DONE
- `npx prisma db seed` runs cleanly against a real Postgres and inserts all sample meals
- GET /api/meals?mealType=LUNCH returns only lunch meals, sorted by healthScore descending
- `npm run lint`, `npm test`, `npm run build` pass in `backend/`
```

---

## TASK 4 — Backend: Intelligent Meal Recommendation Engine + Weekly Meal Plan (Phase 5 + remaining part of Phase 3)

```
CONTEXT: Builds on TASKS 1-3. Refer to the FitFuel MASTER PROMPT for conventions.

GOAL: Build the transparent weighted-scoring recommendation engine, the recommendations
endpoint, and a weekly meal plan generator.

REQUIREMENTS
1. Check/create `backend/src/services/recommendationEngine.ts` as a pure, framework-free
   module exporting:
   - scoreMeal(meal, context): scores a single meal 0-100 using weighted sub-scores:
     calorieAccuracy (35%), proteinQuality (30%), budgetFit (15%), healthScore (20%).
     calorieAccuracy/proteinQuality use a closeness-to-target formula (100 when exact,
     decaying as the gap grows, floored at 0). budgetFit is 100 if within budget, decaying
     above it. Must return null (excluded, not just a low score) if the meal doesn't match
     dietary preference (VEGAN users only get vegan meals; VEGETARIAN users get vegetarian
     OR vegan meals; NON_VEGETARIAN users get anything) or contains any of the user's
     declared allergens.
   - rankMeals(meals, context, topN=5): maps + filters + sorts descending by score,
     returns top N
2. Check/create GET /api/recommendations?mealType=LUNCH (auth required) in
   `backend/src/routes/recommendation.routes.ts`:
   - Requires the user has a completed HealthProfile (400 if not)
   - Splits daily calorie/protein/budget targets across 4 meals a day to get per-meal
     targets
   - Fetches candidate meals of the requested type, scores/ranks them, returns the top 5
     with their score breakdown and full meal object attached
3. Add a weekly meal plan generator (this was deferred from TASK 2's Phase 3 scope):
   - New endpoint POST /api/meal-plans/generate (auth required) — for each day of the week
     (0=Mon..6=Sun) and each meal type (BREAKFAST/LUNCH/DINNER/SNACK), pick the #1 ranked
     meal recommendation using the same scoring logic, avoiding picking the exact same
     meal twice in the same day where reasonably possible. Persist as a MealPlan with
     MealPlanItem rows (dayOfWeek, mealType, mealId, matchScore). Return the created plan
     with all items populated.
   - GET /api/meal-plans/current (auth required) — returns the user's most recent
     MealPlan with items, or 404 if none exists

TESTING
- Add `backend/tests/recommendationEngine.test.ts` (or extend if it exists) covering:
  a meal that exactly matches targets scores highly (>90), allergen exclusion, dietary
  preference exclusion/inclusion rules (including the VEGAN-satisfies-VEGETARIAN case),
  over-budget penalty, and that rankMeals sorts descending and respects topN
- Add an integration test for GET /api/recommendations (happy path + 400 when no health
  profile exists)
- Add an integration test for POST /api/meal-plans/generate that checks 28 items are
  created (7 days * 4 meal types) and each has a valid matchScore

DEFINITION OF DONE
- All recommendation engine unit tests pass, no `any` types used for query filtering
- `npm run lint`, `npm test`, `npm run build` pass in `backend/`
- Manually verify: two users with different dietary preferences/budgets get visibly
  different top-5 recommendations for the same meal type
```

---

## TASK 5 — Backend: AI Explainer / LLM Layer (Groq)

```
CONTEXT: Builds on TASKS 1-4. Refer to the FitFuel MASTER PROMPT — this is the ONLY place
an LLM is allowed to generate output, and only natural-language text, never numbers.

GOAL: Add an optional Groq-powered layer that explains already-calculated nutrition
targets in plain language, and a basic nutrition chat assistant endpoint.

REQUIREMENTS
1. Check/create `backend/src/services/aiExplainerService.ts`:
   - explainNutritionPlan(targets): calls Groq's /v1/chat/completions endpoint (model
     "llama-3.1-8b-instant") with a prompt containing the exact calculated numbers,
     instructing the model NOT to invent different numbers, just explain them in 2-3
     encouraging sentences. If GROQ_API_KEY is not set, return a templated fallback string
     built from the same numbers — the feature must degrade gracefully, never crash the
     request.
   - chatWithNutritionAssistant(userMessage, contextSummary): a simple system-prompted
     chat call for a "nutrition assistant" chat feature. Same graceful-degradation rule if
     no API key.
   - Type the Groq API response properly with an interface (e.g.
     `GroqChatCompletionResponse { choices?: Array<{ message?: { content?: string } }> }`)
     — do not use `any` or leave the parsed JSON as `unknown` without a type assertion to
     this interface.
2. Wire explainNutritionPlan into POST /api/health-profile (from TASK 2) if not already
   wired — call it in a try/catch so a Groq failure never fails the whole request (log and
   return explanation: null instead).
3. Add a new endpoint POST /api/chat (auth required) — accepts { message }, builds a
   contextSummary from the user's current HealthProfile (goal, targets, dietary
   preference), calls chatWithNutritionAssistant, returns { reply }.
4. Update `backend/.env.example` to confirm GROQ_API_KEY is documented with a comment
   pointing to https://console.groq.com for a free key.

TESTING
- Add a Jest test for explainNutritionPlan's fallback path (no GROQ_API_KEY set) —
  should return a string containing the calorie target and not throw
- Mock `fetch` for a test of the success path parsing a sample Groq response shape
- Add an integration test for POST /api/chat that at least verifies 401 without auth and
  a 200 with a mocked/stubbed AI layer if no real key is available in CI

DEFINITION OF DONE
- The whole app works with GROQ_API_KEY unset (health-profile submission and /api/chat
  both return sensible fallback text, no 500 errors)
- `npm run lint`, `npm test`, `npm run build` pass in `backend/`
- If a real Groq key is provided in `.env`, manually verify a real natural-language
  explanation comes back and matches the calculated numbers (no invented figures)
```

---

## TASK 6 — Backend: Order Integration via Deep Links (Phase 6)

```
CONTEXT: Builds on TASKS 1-5. Refer to the FitFuel MASTER PROMPT's Swiggy/Zomato
constraint — this is critical, re-read it before starting.

GOAL: Implement the honest "Order on Swiggy/Zomato" flow: log order intent, return a
working deep link, never claim or attempt real order placement.

REQUIREMENTS
1. Check/create `backend/src/routes/order.routes.ts`:
   - A `buildDeepLink(platform, restaurant, query)` helper function with a comment block
     explicitly stating Swiggy/Zomato have no public order API and this is a search
     handoff. For SWIGGY: `https://www.swiggy.com/search?query=<url-encoded restaurant +
     query>`. For ZOMATO: `https://www.zomato.com/search?q=<url-encoded restaurant +
     query>`.
   - POST /api/orders (auth required) — Zod-validates { mealId: uuid, platform:
     SWIGGY|ZOMATO }, looks up the meal (404 if missing), creates an Order row (status
     defaults to "REDIRECTED"), returns { order, deepLink }.
   - GET /api/orders (auth required) — returns the current user's order history, most
     recent first, with the related meal included.
2. Confirm the Order model in `schema.prisma` has: id, userId, mealId, platform, status
   (default "REDIRECTED"), createdAt, relations to User and Meal.

TESTING
- Add an integration test for POST /api/orders verifying the returned deepLink contains
  the correctly URL-encoded restaurant name and the right domain for each platform
- Add a test for 404 when mealId doesn't exist, and 401 when unauthenticated

DEFINITION OF DONE
- Manually open a returned deepLink in a browser and confirm it lands on a real Swiggy/
  Zomato search results page (not a 404 or broken URL)
- `npm run lint`, `npm test`, `npm run build` pass in `backend/`
- No code anywhere claims or implies a real order was placed — check route responses,
  comments, and any user-facing copy you touch
```

---

## TASK 7 — Backend: Progress Tracking & Analytics (Phase 7)

```
CONTEXT: Builds on TASKS 1-6. Refer to the FitFuel MASTER PROMPT for conventions.

GOAL: Implement daily logging and weekly summary analytics.

REQUIREMENTS
1. Confirm the ProgressLog model in `schema.prisma` has: id, userId, date (default now),
   weightKg, caloriesConsumed, proteinConsumedG, carbsConsumedG, fatConsumedG, notes — all
   nutrition fields optional (a log entry might only record weight, or only calories).
2. Check/create `backend/src/routes/progress.routes.ts`:
   - POST /api/progress (auth required) — Zod-validates all fields as optional numbers/
     string, creates a ProgressLog row
   - GET /api/progress (auth required) — returns up to 100 most recent logs
   - GET /api/progress/summary (auth required) — computes: logs from the last 7 days,
     weekly average calories consumed (0 if no logs), goalAchievementPct = average
     calories consumed / TDEE * 100 (capped at 100, null if no HealthProfile or no logs).
     Type the reduce callback's parameters explicitly — do not leave them as implicit
     `any`.
3. Consider adding: GET /api/progress/weight-history (auth required) — returns just
   { date, weightKg } pairs over the last N days/weeks, useful for charting on the
   frontend (both web and mobile will need this for a weight-progress chart).

TESTING
- Add an integration test for POST /api/progress (happy path with partial fields)
- Add an integration test for GET /api/progress/summary verifying goalAchievementPct
  calculation against a known TDEE and a known set of logged calories

DEFINITION OF DONE
- `npm run lint`, `npm test`, `npm run build` pass in `backend/`
- Manually verify: logging 7 days of calories close to TDEE yields goalAchievementPct
  close to 100
```

---

## TASK 8 — Backend: Full Test Suite Hardening & CI/CD

```
CONTEXT: Builds on TASKS 1-7. Refer to the FitFuel MASTER PROMPT for conventions.

GOAL: Make sure the backend's automated testing and GitHub Actions pipeline are complete,
correct, and would actually pass on a clean checkout.

REQUIREMENTS
1. Review every route file added in TASKS 1-7 and ensure each has at least one integration
   test covering the happy path and at least one failure path (validation error, auth
   error, or not-found, whichever applies).
2. Review every service file (nutritionCalculator, recommendationEngine,
   aiExplainerService) and ensure meaningful branch coverage in unit tests — not just one
   happy-path test per function.
3. Check/create `backend/jest.config.js` — ts-jest preset, testEnvironment node, roots
   pointed at tests/.
4. Check/create `backend/tsconfig.json` — confirm `include` does not list "tests" while
   rootDir is "src" (known conflict — verify this specific bug isn't present, it silently
   breaks `npm run build`).
5. Check/create `.github/workflows/backend-ci.yml`:
   - Triggers on push/PR to main, path-filtered to backend/** and the workflow file itself
   - Spins up a real `postgres:16` service container for the test job
   - Steps: checkout, setup-node (v20, npm cache), npm install, `npx prisma generate`,
     `npx prisma migrate deploy`, npm run lint, npm test, npm run build
   - A separate deploy job (needs: test, only on push to main) that curls a
     RENDER_DEPLOY_HOOK_URL secret if set, with a comment explaining Render's own
     GitHub auto-deploy usually makes this redundant but it's a safe fallback
6. Run the entire backend test suite locally end-to-end against a real Postgres (Docker or
   free cloud instance) and fix any failures you find — don't just assume it passes.

DEFINITION OF DONE
- `npm run lint`, `npm test`, `npm run build` all pass with zero errors against a real
  database connection
- Every route added across TASKS 1-7 has test coverage
- Pushing to a GitHub repo with this workflow in place results in a green CI run (verify
  by actually pushing to a test repo/branch if you have GitHub access, or carefully
  reasoning through each step if you don't)
```

---

## TASK 9 — Web App: Project Setup & Auth Screens (Phase 1)

```
CONTEXT: Refer to the FitFuel MASTER PROMPT. The backend from TASKS 1-8 is complete and
running at http://localhost:4000 by default. This task starts the web app's screens.

GOAL: Ensure `web/` is a working React + Vite + TypeScript + Tailwind app with login and
registration screens wired to the backend.

REQUIREMENTS
1. Check `web/package.json` has scripts: dev, build, lint, test, test:watch, and deps:
   react, react-dom, react-router-dom, axios; devDeps: vite, @vitejs/plugin-react,
   typescript, tailwindcss + autoprefixer + postcss, vitest, @testing-library/react,
   @testing-library/jest-dom, eslint + typescript-eslint plugin/parser.
2. Check `web/tsconfig.json` includes `"types": ["vitest/globals", "@testing-library/
   jest-dom"]`.
3. Check `web/src/vite-env.d.ts` exists with `/// <reference types="vite/client" />` and
   an ImportMetaEnv interface declaring VITE_API_BASE_URL — without this file,
   `import.meta.env.VITE_API_BASE_URL` fails to typecheck and `npm run build` breaks. This
   exact bug has occurred before — verify the file is present and correct.
4. Check `web/src/api/client.ts`:
   - An Axios instance with baseURL from `import.meta.env.VITE_API_BASE_URL` (fallback
     'http://localhost:4000')
   - A request interceptor that attaches `Authorization: Bearer <token>` from
     localStorage if present
   - saveToken/clearToken helpers
   - An `extractErrorMessage(err: unknown, fallback: string): string` helper that safely
     narrows an Axios error and pulls a readable message out of the backend's Zod
     `{ error: { formErrors, fieldErrors } }` or `{ error: string }` shapes. Use this
     helper in every page's catch block — do NOT write `catch (err: any)` anywhere, it
     will fail lint (`@typescript-eslint/no-explicit-any` is an error). Use
     `catch (err: unknown)` and pass to extractErrorMessage instead.
5. Check/create `web/src/pages/Login.tsx` — email/password form, calls POST /api/auth/
   login, saves token, navigates to /dashboard on success, shows an error message on
   failure using extractErrorMessage.
6. Check/create `web/src/pages/Register.tsx` — name/email/password/age/gender/height/
   weight form, calls POST /api/auth/register, saves token, navigates to
   /health-assessment on success (since a fresh user needs to complete Phase 2 next).
7. Check/create `web/src/components/Layout.tsx` — a simple shared shell (nav bar with
   links, logout button) wrapping authenticated pages.
8. Check/create `web/src/App.tsx` — React Router setup with routes for /login, /register,
   /health-assessment, /dashboard, /recommendations, /progress (later tasks fill these in
   further); a basic auth guard that redirects to /login if no token is present for
   protected routes.
9. Check `web/tailwind.config.js` and `web/postcss.config.js` are correctly wired, and
   `web/src/index.css` has the Tailwind directives.

TESTING
- Add/verify `web/tests/setup.ts` for jest-dom matchers
- Add/verify `web/tests/Login.test.tsx` — renders the form, asserts email/password fields
  are present
- Add a similar basic render test for Register.tsx

DEFINITION OF DONE
- `npm run lint`, `npm test`, `npm run build` all pass with zero errors in `web/`
- With the backend running locally, manually register a new user through the UI, then log
  out and log back in with the same credentials
```

---

## TASK 10 — Web App: Health Assessment & Dashboard (Phases 2 & 3)

```
CONTEXT: Builds on TASK 9. Refer to the FitFuel MASTER PROMPT.

GOAL: Build the health questionnaire screen and a dashboard summarizing the user's
calculated targets.

REQUIREMENTS
1. Check/create `web/src/pages/HealthAssessment.tsx`:
   - Form fields: currentWeightKg, targetWeightKg, activityLevel (select: SEDENTARY/
     LIGHT/MODERATE/ACTIVE/VERY_ACTIVE), fitnessGoal (select: WEIGHT_LOSS/WEIGHT_GAIN/
     MUSCLE_GAIN/MAINTENANCE), dietaryPreference (select: VEGETARIAN/NON_VEGETARIAN/
     VEGAN), allergies (a way to add/remove multiple string tags), dailyBudget
   - Submits to POST /api/health-profile, on success shows the returned targets (BMI
     category, BMR, TDEE, calorie target, protein/carb/fat grams) and the optional AI
     explanation text if present, then a button to continue to /dashboard
2. Check/create `web/src/pages/Dashboard.tsx`:
   - Fetches GET /api/health-profile on mount; if 404 (no profile yet), redirect to
     /health-assessment
   - Displays calorie target and macro targets as a clear visual summary (simple stat
     cards are fine — a full chart library isn't required here, that's for Progress)
   - Links/buttons to Recommendations and Progress pages
3. Check `web/src/types/index.ts` has TypeScript interfaces mirroring the backend's
   HealthProfile shape and the enums (ActivityLevel, FitnessGoal, DietaryPreference) so
   the select options and API calls are properly typed, not stringly-typed with no
   validation.

TESTING
- Add a render test for HealthAssessment.tsx asserting the key form fields are present
- Add a test for Dashboard.tsx covering both the "profile exists" and "no profile yet"
  paths (mock the API client)

DEFINITION OF DONE
- `npm run lint`, `npm test`, `npm run build` all pass with zero errors in `web/`
- Manually complete the health assessment as a fresh user and confirm the dashboard shows
  sensible calculated numbers matching what the backend returned
```

---

## TASK 11 — Web App: Recommendations & Order Integration (Phases 5 & 6)

```
CONTEXT: Builds on TASKS 9-10. Refer to the FitFuel MASTER PROMPT's Swiggy/Zomato
constraint again before writing any order-related UI copy.

GOAL: Build the meal recommendations screen with working order handoff buttons.

REQUIREMENTS
1. Check/create `web/src/pages/Recommendations.tsx`:
   - A meal-type selector (BREAKFAST/LUNCH/DINNER/SNACK tabs or dropdown)
   - Fetches GET /api/recommendations?mealType=... and renders each recommended meal as a
     card: name, restaurant, cuisine, calories/protein/carbs/fat, price, and the match
     score/breakdown (nice-to-have: a small breakdown tooltip or expandable section
     showing calorieAccuracy/proteinQuality/budgetFit/healthScore)
   - Each card has two buttons: "Order on Swiggy" and "Order on Zomato" (only show the
     one matching the meal's actual `platform`, or show both if you want to let the user
     choose regardless — decide and be consistent)
   - Clicking a button calls POST /api/orders with { mealId, platform }, then opens the
     returned `deepLink` in a new browser tab (`window.open(deepLink, '_blank')`).
     Include a small UI note near the buttons, e.g. "Opens Swiggy/Zomato search — complete
     your order there" so the user understands this isn't instant checkout inside FitFuel.
2. Handle the 400 case where the user hasn't completed their health assessment yet
   (redirect to /health-assessment with a message).

TESTING
- Add a render test mocking GET /api/recommendations and asserting meal cards render with
  their key nutrition info
- Add a test that clicking an order button calls the orders API (mock it) — you don't need
  to test the actual window.open call, just that the API call fires with the right payload

DEFINITION OF DONE
- `npm run lint`, `npm test`, `npm run build` all pass with zero errors in `web/`
- Manually verify: selecting a meal type shows relevant recommendations, and clicking
  "Order on Swiggy" opens a real Swiggy search results page in a new tab
```

---

## TASK 12 — Web App: Progress Tracking with Charts (Phase 7)

```
CONTEXT: Builds on TASKS 9-11. Refer to the FitFuel MASTER PROMPT.

GOAL: Build the progress logging and analytics screen, including simple charts.

REQUIREMENTS
1. Add a charting library to `web/package.json` if not already present — `recharts` is a
   good, lightweight choice and works well with React + TypeScript.
2. Check/create `web/src/pages/Progress.tsx`:
   - A form to log a new entry: weightKg, caloriesConsumed, proteinConsumedG,
     carbsConsumedG, fatConsumedG, notes (all optional except at least one value should be
     provided — do simple client-side validation) — submits to POST /api/progress
   - Fetches GET /api/progress/summary and displays: weekly average calories, goal
     achievement % (as a simple progress bar or ring), and a line chart of recent weight
     entries over time (use GET /api/progress or a dedicated weight-history endpoint if
     you built one in TASK 7)
   - Fetches GET /api/progress and shows a simple table/list of recent log entries as
     "meal/entry history"
3. Add `web/src/utils/bmi.ts` (or confirm it exists) with a client-side BMI helper mirrored
   from the backend's logic, useful for instant feedback before hitting the API if needed
   elsewhere in the UI — keep it in sync with the backend formula exactly.

TESTING
- Add a render test for the log-entry form
- Add a test mocking GET /api/progress/summary and asserting the weekly average and goal
  percentage render correctly
- Keep/verify `web/tests/bmi.test.ts` covers the same cases as the backend's BMI tests

DEFINITION OF DONE
- `npm run lint`, `npm test`, `npm run build` all pass with zero errors in `web/`
- Manually log a few days of entries and confirm the chart and summary update correctly
```

---

## TASK 13 — Web App: Testing Hardening & CI/CD

```
CONTEXT: Builds on TASKS 9-12. Refer to the FitFuel MASTER PROMPT.

GOAL: Ensure the web app's test suite and GitHub Actions pipeline are complete and would
pass on a clean checkout.

REQUIREMENTS
1. Review every page added in TASKS 9-12 and ensure each has at least one test.
2. Run `npm run build` and fix ANY TypeScript or build errors — pay special attention to:
   - `import.meta.env` usage without `vite-env.d.ts` (see TASK 9)
   - Any `catch (err: any)` blocks (see TASK 9's extractErrorMessage pattern)
   - Any implicit `any` in array callbacks (.map/.reduce/.filter) — add explicit types
3. Check/create `.github/workflows/web-ci.yml`:
   - Triggers on push/PR to main, path-filtered to web/** and the workflow file itself
   - Steps: checkout, setup-node (v20, npm cache), npm install, npm run lint, npm test,
     npm run build (pass VITE_API_BASE_URL from a repo secret with a sensible fallback)
   - A separate deploy job (needs: test, only on push to main) using the Vercel CLI/action
     with VERCEL_TOKEN, VERCEL_ORG_ID, VERCEL_PROJECT_ID secrets, working-directory web,
     `--prod` flag
4. Run the entire web test suite and build locally end-to-end and fix any failures found.

DEFINITION OF DONE
- `npm run lint`, `npm test`, `npm run build` all pass with zero errors
- Every page has test coverage
- The CI workflow file is syntactically valid and would run successfully on push (verify
  by pushing to a test repo/branch if possible)
```

---

## TASK 14 — Mobile App (Flutter): Project Setup & Auth Screens (Phase 1)

```
CONTEXT: Refer to the FitFuel MASTER PROMPT. The backend from TASKS 1-8 is complete. This
task starts the Flutter app's screens, mirroring the web app's Task 9 but in Dart/Flutter.

GOAL: Ensure `mobile/` is a working Flutter app with login and registration screens wired
to the backend.

REQUIREMENTS
1. Check `mobile/pubspec.yaml` has: http, provider, shared_preferences, url_launcher,
   fl_chart, intl as dependencies, flutter_test + flutter_lints as dev dependencies, SDK
   constraint >=3.3.0 <4.0.0.
2. Check `mobile/lib/services/api_config.dart`:
   - `static const String baseUrl = String.fromEnvironment('API_BASE_URL', defaultValue:
     'http://10.0.2.2:4000');` — 10.0.2.2 is the Android emulator's alias for the host
     machine's localhost; note in a comment that iOS simulator should use
     `--dart-define=API_BASE_URL=http://localhost:4000` instead, and production builds
     override this with the deployed Render URL.
3. Check/create `mobile/lib/services/api_service.dart` — a thin HTTP client wrapper (GET/
   POST/etc.) that reads the base URL from ApiConfig, attaches the stored auth token as an
   Authorization header when present, and throws typed exceptions on non-2xx responses
   with the backend's error message extracted from the JSON body.
4. Check/create `mobile/lib/services/auth_service.dart` — register(...) and login(...)
   methods calling the backend's /api/auth endpoints via api_service, storing the returned
   JWT in shared_preferences, and a currentToken()/isLoggedIn()/logout() set of helpers.
5. Check/create `mobile/lib/models/models.dart` — Dart classes (with fromJson/toJson)
   mirroring the backend's User, HealthProfile, Meal, Order, ProgressLog shapes and the
   relevant enums, kept in sync with the Prisma schema.
6. Check/create `mobile/lib/screens/login_screen.dart` and
   `mobile/lib/screens/register_screen.dart` — forms matching the web app's fields,
   calling auth_service, navigating to the health assessment screen (for a fresh
   registration) or dashboard (for login) on success, showing errors on failure.
7. Check/create `mobile/lib/main.dart` — sets up a Provider-based app root, initial route
   logic (check isLoggedIn() to decide whether to land on login or dashboard), and route
   definitions for all screens (later tasks fill in the rest).

TESTING
- Check/create `mobile/test/login_screen_test.dart` — a widget test asserting the login
  form renders its email/password fields
- Add a similar test for register_screen.dart
- Check/create `mobile/test/nutrition_helper_test.dart` if a client-side BMI helper exists
  (see TASK 15) — otherwise defer this file to that task

DEFINITION OF DONE
- `flutter analyze` and `flutter test` both pass with zero errors
- `flutter build apk --debug` (or `flutter build apk --release` if you have a keystore
  set up) completes successfully
- With the backend running and an emulator using 10.0.2.2, manually register and log in
  through the app
```

---

## TASK 15 — Mobile App: Health Assessment & Dashboard (Phases 2 & 3)

```
CONTEXT: Builds on TASK 14. Refer to the FitFuel MASTER PROMPT.

GOAL: Build the Flutter health questionnaire and dashboard screens.

REQUIREMENTS
1. Check/create `mobile/lib/services/nutrition_helper.dart` — a Dart class mirroring the
   backend's BMI calculation and category logic exactly (same formula, same category
   boundaries: <18.5 Underweight, <25 Normal weight, <30 Overweight, else Obese), used for
   instant client-side feedback before hitting the API.
2. Check/create `mobile/lib/screens/health_assessment_screen.dart`:
   - Form fields matching the web app's HealthAssessment page: currentWeightKg,
     targetWeightKg, activityLevel, fitnessGoal, dietaryPreference, allergies (chip input
     or similar), dailyBudget
   - Submits to POST /api/health-profile via api_service, shows returned targets and the
     optional AI explanation, navigates to the dashboard on continue
3. Check/create `mobile/lib/screens/dashboard_screen.dart`:
   - Fetches GET /api/health-profile on load; redirects to health assessment if none
     exists
   - Displays calorie/macro targets as stat cards/tiles
   - Navigation to Recommendations and Progress screens (bottom nav bar or drawer is fine)

TESTING
- Check/create `mobile/test/nutrition_helper_test.dart` — mirror the backend's BMI test
  cases exactly (same weight/height inputs, same expected BMI and category outputs) so the
  two implementations stay provably in sync
- Add a widget test for health_assessment_screen.dart asserting key fields render
- Add a widget test for dashboard_screen.dart covering both "profile exists" and "no
  profile yet" states (mock the API service)

DEFINITION OF DONE
- `flutter analyze` and `flutter test` pass with zero errors
- Manually complete the health assessment on-device/emulator and confirm the dashboard
  shows numbers matching the backend's calculation
```

---

## TASK 16 — Mobile App: Recommendations & Order Integration (Phases 5 & 6)

```
CONTEXT: Builds on TASKS 14-15. Refer to the FitFuel MASTER PROMPT's Swiggy/Zomato
constraint again before writing any order-related UI copy.

GOAL: Build the Flutter recommendations screen with working order handoff via
url_launcher.

REQUIREMENTS
1. Check/create `mobile/lib/screens/recommendations_screen.dart`:
   - A meal-type selector (tabs or segmented control)
   - Fetches GET /api/recommendations?mealType=... and renders each meal in a card:
     name, restaurant, cuisine, macros, price, match score
   - "Order on Swiggy" / "Order on Zomato" buttons that call POST /api/orders, then use
     `url_launcher`'s `launchUrl()` to open the returned deepLink in an external browser/
     app. Include a small caption near the buttons noting this opens the platform's own
     search so the user completes checkout there — do not imply in-app ordering.
2. Handle the case where the health assessment isn't complete yet (backend returns 400) —
   show a message and a button to go complete it.

TESTING
- Add a widget test mocking the recommendations API response and asserting meal cards
  render with their nutrition info
- Add a test that tapping an order button triggers the orders API call with the correct
  payload (mock api_service; you don't need to test the actual OS-level url launch)

DEFINITION OF DONE
- `flutter analyze` and `flutter test` pass with zero errors
- Manually verify tapping "Order on Swiggy" opens a real Swiggy search page in the
  device's browser or the Swiggy app if installed
```

---

## TASK 17 — Mobile App: Progress Tracking with Charts (Phase 7)

```
CONTEXT: Builds on TASKS 14-16. Refer to the FitFuel MASTER PROMPT.

GOAL: Build the Flutter progress logging and analytics screen using fl_chart.

REQUIREMENTS
1. Check/create `mobile/lib/screens/progress_screen.dart`:
   - A form to log a new entry (weightKg, caloriesConsumed, proteinConsumedG,
     carbsConsumedG, fatConsumedG, notes) — submits to POST /api/progress
   - Fetches GET /api/progress/summary and displays weekly average calories and goal
     achievement % (a simple circular or linear progress indicator is fine)
   - Renders a weight-over-time line chart using `fl_chart`'s LineChart, fed by GET
     /api/progress or a dedicated weight-history endpoint from TASK 7
   - Shows a scrollable list of recent log entries ("meal history" / entry history)

TESTING
- Add a widget test for the log-entry form
- Add a widget test mocking the summary API response and asserting the weekly average and
  goal percentage render

DEFINITION OF DONE
- `flutter analyze` and `flutter test` pass with zero errors
- Manually log a few entries and confirm the chart renders correctly with real data points
```

---

## TASK 18 — Mobile App: Testing Hardening & CI/CD

```
CONTEXT: Builds on TASKS 14-17. Refer to the FitFuel MASTER PROMPT.

GOAL: Ensure the Flutter app's test suite and GitHub Actions pipeline are complete and
would pass on a clean checkout, and produce a downloadable release APK for free.

REQUIREMENTS
1. Review every screen added in TASKS 14-17 and ensure each has at least one widget test.
2. Run `flutter analyze` and fix every warning/error, including lint rules from
   `flutter_lints` (check `mobile/analysis_options.yaml` includes the flutter_lints
   package rules).
3. Check/create `.github/workflows/mobile-ci.yml`:
   - Triggers on push/PR to main, path-filtered to mobile/** and the workflow file itself
   - Test job: checkout, subosito/flutter-action (a recent stable Flutter version),
     `flutter pub get`, `flutter analyze`, `flutter test`
   - build-apk job (needs: test, only on push to main): checkout, flutter-action,
     `flutter pub get`, `flutter build apk --release --dart-define=API_BASE_URL=<a repo
     secret MOBILE_API_BASE_URL>`, then `actions/upload-artifact@v4` uploading
     `mobile/build/app/outputs/flutter-apk/app-release.apk` with a descriptive name and a
     90-day retention (GitHub's free artifact retention limit) — explain in a comment that
     this gives a free downloadable APK without needing the Play Store.
4. Run the entire Flutter test suite locally end-to-end and fix any failures found.

DEFINITION OF DONE
- `flutter analyze` and `flutter test` both pass with zero errors/warnings
- Every screen has widget test coverage
- The CI workflow file is syntactically valid; if you have GitHub access, push and confirm
  a green run producing a downloadable APK artifact
```

---

## TASK 19 — Deployment: Free-Tier Infrastructure Setup

```
CONTEXT: All of TASKS 1-18 are complete and every app's tests/lint/build pass locally.
Refer to the FitFuel MASTER PROMPT.

GOAL: Get the whole system actually deployed and reachable, entirely on free tiers, and
document the exact steps taken so the client can reproduce or maintain it later.

REQUIREMENTS
1. Database — Supabase (or Neon) free Postgres:
   - Create a project, retrieve the connection string, confirm it works with
     `npx prisma migrate deploy` and `npx prisma db seed` run against it
2. Backend — Render free web service:
   - Connect the GitHub repo, root directory `backend`
   - Build command: `npm install && npx prisma generate && npm run build`
   - Start command: `npx prisma migrate deploy && npm start`
   - Environment variables: DATABASE_URL, JWT_SECRET (generate a strong random value, do
     not reuse the dev one), GROQ_API_KEY (optional)
   - Verify GET https://<your-service>.onrender.com/health returns { status: "ok" }
   - Note in the handover docs that Render's free tier sleeps after ~15 min idle and takes
     ~30s to wake on the next request
3. Web app — Vercel free tier:
   - Import the repo, root directory `web`, framework preset Vite
   - Environment variable VITE_API_BASE_URL = the Render backend URL from step 2
   - Verify the deployed URL loads, and that registering/logging in actually reaches the
     live backend (not localhost)
4. Mobile app — GitHub Actions artifact APK (no Play Store needed):
   - Set the MOBILE_API_BASE_URL repo secret to the Render backend URL
   - Push to main, confirm mobile-ci.yml produces a downloadable release APK pointed at
     production, not localhost
5. Wire up GitHub Actions secrets for the backend/web deploy jobs:
   RENDER_DEPLOY_HOOK_URL (optional, Render usually auto-deploys from GitHub directly),
   VERCEL_TOKEN, VERCEL_ORG_ID, VERCEL_PROJECT_ID, VITE_API_BASE_URL,
   MOBILE_API_BASE_URL — confirm all three CI workflows go green end-to-end on a real push
   to main.
6. Update `README.md`'s deployment section with the actual URLs/service names used (not
   just placeholders) so this is a real, working handover document, not just a template.

DEFINITION OF DONE
- All three apps are live and reachable via public URLs
- A brand-new user can complete the full flow end-to-end on the deployed web app: register
  → health assessment → see recommendations → tap an order button and land on a real
  Swiggy/Zomato page → log progress → see it reflected in the summary
- The same flow works on the built APK installed on a real device or emulator, pointed at
  the production backend
- All three GitHub Actions workflows are green on the main branch
```

---

## TASK 20 — Final QA, Integration Testing & Handover Documentation

```
CONTEXT: All previous tasks are complete and deployed. Refer to the FitFuel MASTER PROMPT.

GOAL: Do a full end-to-end quality pass across the whole system and finalize handover
documentation for the client/evaluators.

REQUIREMENTS
1. End-to-end manual QA pass (do this on the deployed environments from TASK 19, not just
   localhost) covering, at minimum:
   - Registration with valid and invalid data (weak password, duplicate email, missing
     required fields)
   - Login with correct and incorrect credentials
   - Completing the health assessment with each of the 4 fitness goals and each of the 3
     dietary preferences, confirming the calculated targets change sensibly each time
   - Viewing recommendations for all 4 meal types, confirming allergen/dietary filtering
     actually excludes meals it should
   - Tapping order buttons and confirming the deep link opens a real, correctly-filled
     Swiggy/Zomato search
   - Logging several days of progress and confirming the weekly summary and charts update
     correctly
   - Testing on both the web app and the mobile app for parity — flag and fix any place
     where they behave inconsistently
2. Cross-check every numeric calculation between the backend, web (if it duplicates any
   logic client-side), and mobile's nutrition_helper.dart — they must all agree exactly
   for the same inputs. Fix any drift you find.
3. Re-run and confirm ALL THREE CI pipelines are green on the current main branch.
4. Finalize `docs/API_REFERENCE.md` — every endpoint documented with example request/
   response bodies, matching the actual current implementation (not stale from an earlier
   task).
5. Finalize `README.md` with: project overview, the Swiggy/Zomato constraint stated
   plainly, architecture diagram/summary, local dev setup for all three apps, the actual
   deployed URLs, and a clear "known limitations / suggested future work" section (e.g.
   password reset flow, more seeded meals, additional cuisines, push notifications, etc.)
   — be honest about what's out of scope rather than implying more than what's built.
6. Do a final security pass: confirm no secrets are committed anywhere in the repo (grep
   for anything that looks like a real API key or connection string), confirm `.env` is
   gitignored everywhere, confirm JWT_SECRET used in production is not the dev default.

DEFINITION OF DONE
- A fresh reviewer with no prior context could clone the repo, follow README.md, and get
  all three apps running locally and understand how to redeploy them
- All three CI pipelines are green
- No known calculation inconsistencies between backend/web/mobile
- No secrets committed to the repository
- The final summary you give back to the user lists explicitly: what was built, what was
  tested, what's deployed and where, and what remains as suggested future work
```