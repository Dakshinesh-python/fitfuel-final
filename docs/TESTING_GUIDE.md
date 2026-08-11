# FitFuel — Local Development & Testing Guide

> **Audience**: Developers, evaluators, and academic reviewers running FitFuel locally.
> This document covers environment setup, running each layer, seeding data, running tests,
> and a full end-to-end manual walkthrough of every user flow.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Prerequisites](#2-prerequisites)
3. [Repository Structure](#3-repository-structure)
4. [Environment Setup](#4-environment-setup)
5. [Backend — Setup & Run](#5-backend--setup--run)
6. [Web App — Setup & Run](#6-web-app--setup--run)
7. [Mobile App — Setup & Run](#7-mobile-app--setup--run)
8. [Running the Test Suites](#8-running-the-test-suites)
9. [End-to-End Manual Walkthrough](#9-end-to-end-manual-walkthrough)
10. [Common Issues & Fixes](#10-common-issues--fixes)
11. [Key Design Decisions & Constraints](#11-key-design-decisions--constraints)

---

## 1. Architecture Overview

```
fitfuel/
├── backend/          Express + TypeScript + Prisma + PostgreSQL
│                     Runs on http://localhost:4000
├── web/              React + Vite + TypeScript + Tailwind CSS
│                     Runs on http://localhost:5173
└── fitfuel_mobile/   Flutter (Android / iOS)
                      Points to http://10.0.2.2:4000 (Android emulator)
                      or http://localhost:4000 (iOS simulator / physical)
```

**Request flow:**

```
Flutter / React  →  Express API (:4000)  →  PostgreSQL (Neon)
                                         →  Groq LLM (AI chat & explanation)
```

**Authentication:** JWT — returned on register/login, stored in `localStorage` (web) and `SharedPreferences` (mobile), sent as `Authorization: Bearer <token>` on every protected request.

---

## 2. Prerequisites

| Tool | Minimum Version | Notes |
|---|---|---|
| **Node.js** | 18 LTS | Backend + web build |
| **npm** | 9+ | Comes with Node |
| **PostgreSQL** | any | Neon free tier recommended — no local install needed |
| **Flutter SDK** | 3.3.0+ | Mobile app |
| **Dart SDK** | included with Flutter | |
| **Android Studio** / Xcode | latest stable | For emulator / simulator |
| **Git** | any | |

### Free cloud services required

| Service | What for | Sign-up URL |
|---|---|---|
| **Neon** | PostgreSQL database (free tier) | https://neon.tech |
| **Groq** | AI meal explanations & chat (free tier, no credit card) | https://console.groq.com |

---

## 3. Repository Structure

```
fitfuel/
├── backend/
│   ├── prisma/
│   │   ├── schema.prisma       # Database schema (Meal, User, HealthProfile, …)
│   │   ├── seed.ts             # Seed script — 14 sample meals with Unsplash images
│   │   └── migrations/         # SQL migration history
│   ├── src/
│   │   ├── routes/             # auth, healthProfile, meal, recommendation,
│   │   │                       # mealPlan, order, progress, chat
│   │   ├── services/           # nutritionCalculator, recommendationEngine,
│   │   │                       # aiExplainerService
│   │   └── app.ts              # Express app factory (CORS, middleware, routes)
│   ├── tests/                  # Jest integration + unit tests (85 tests)
│   └── .env.example            # Environment variable template
│
├── web/
│   ├── src/
│   │   ├── api/client.ts       # Axios instance + token helpers
│   │   ├── pages/              # Register, Login, HealthAssessment,
│   │   │                       # Dashboard, Recommendations, Progress
│   │   ├── types/index.ts      # TypeScript interfaces matching backend contracts
│   │   └── utils/bmi.ts        # Client-side BMI category helper
│   ├── tests/                  # Vitest + Testing Library (18 tests)
│   ├── index.html              # Vite entry point
│   └── .env / .env.example     # VITE_API_BASE_URL
│
├── fitfuel_mobile/
│   ├── lib/
│   │   ├── main.dart           # App entry, route map
│   │   ├── models/models.dart  # Dart models mirroring Prisma schema
│   │   ├── services/
│   │   │   ├── api_service.dart    # HTTP client + error handling
│   │   │   └── auth_service.dart   # Token storage (SharedPreferences)
│   │   ├── screens/            # All 12 screens
│   │   └── widgets/            # Shared UI widgets
│   └── test/widget_test.dart   # Flutter smoke test
│
└── docs/
    ├── API_REFERENCE.md        # Full REST API documentation
    └── TESTING_GUIDE.md        # ← this file
```

---

## 4. Environment Setup

### 4.1 Get a PostgreSQL connection string

**1. Set up Neon (recommended, instant)**
1. Go to https://neon.tech → Create free account → Create project → Copy the connection string.

The connection string looks like:
```
postgresql://username:password@host.neon.tech/neondb?sslmode=require
```

### 4.2 Get a Groq API key

1. Go to https://console.groq.com → Sign in → API Keys → Create Key.
2. Copy the key — it starts with `gsk_`.

---

## 5. Backend — Setup & Run

### 5.1 Install dependencies

```bash
cd fitfuel/backend
npm install
```

### 5.2 Create your `.env` file

```bash
# Copy the template
cp .env.example .env
```

Then edit `.env`:

```env
PORT=4000
NODE_ENV=development

# Paste your Neon connection string here
DATABASE_URL="postgresql://user:password@host/fitfuel?sslmode=require"

# Generate a strong random secret (e.g. openssl rand -hex 32)
JWT_SECRET="replace-this-with-something-long-and-random"

# Paste your Groq key here
GROQ_API_KEY="gsk_..."

# Origins the web app runs on (comma-separated)
ALLOWED_ORIGINS=http://localhost:5173
```

### 5.3 Run the database migration

```bash
npx prisma migrate deploy
```

This applies the single migration in `prisma/migrations/` which creates **all tables** (User, HealthProfile, Meal, MealPlan, MealPlanItem, Order, ProgressLog), all enum types, indexes, and foreign keys in one step. The `Meal` table includes the `imageUrl` column from the start.

Expected output:
```
1 migration found in prisma/migrations
Applying migration `20260809_add_meal_image_url`
All migrations have been successfully applied.
```

> **If you see `relation "X" does not exist`**: The migration tracking table may have a stale failed entry. Run:
> ```bash
> npx prisma migrate resolve --rolled-back "20260809_add_meal_image_url"
> npx prisma migrate deploy
> ```

### 5.4 Generate the Prisma client

```bash
npx prisma generate
```

### 5.5 Seed the database

```bash
npm run prisma:seed
```

Expected output:
```
Seeding meals...
Seeded 14 meals across 5 cuisines.
All meals have imageUrl ✓
```

> **What gets seeded:** 14 sample restaurant meals across Breakfast / Lunch / Dinner / Snack,
> covering Indian, Continental, Chinese, and Healthy Bowl cuisines — each with a verified
> Unsplash food photo URL. The seed script will **throw and abort** before touching the
> database if any meal is missing an `imageUrl`.

### 5.6 Start the development server

```bash
npm run dev
```

Backend is now live at **http://localhost:4000**.

Verify with:
```bash
curl http://localhost:4000/health
# → { "status": "ok", "timestamp": "..." }
```

Or open http://localhost:4000/api/meals in a browser — you should see the 14 seeded meals including `imageUrl` on each.

---

## 6. Web App — Setup & Run

### 6.1 Install dependencies

```bash
cd fitfuel/web
npm install
```

### 6.2 Create your `.env` file

```bash
cp .env.example .env
```

The default is already correct for local development:
```env
VITE_API_BASE_URL=http://localhost:4000
```

> If you change the backend port, update this value and also add the new web origin to
> `ALLOWED_ORIGINS` in the backend `.env`.

### 6.3 Start the dev server

```bash
npm run dev
```

Web app is now live at **http://localhost:5173**.

### 6.4 Build for production (optional)

```bash
npm run build
# Output goes to web/dist/ — serve with any static host (Vercel, Netlify, etc.)
```

---

## 7. Mobile App — Setup & Run

### 7.1 Install Flutter dependencies

```bash
cd fitfuel/fitfuel_mobile
flutter pub get
```

### 7.2 Configure the backend URL

The mobile app's HTTP client is in `lib/services/api_service.dart`. The base URL is set to point to the backend. For emulators:

| Platform | Use this URL |
|---|---|
| Android Emulator | `http://10.0.2.2:4000` |
| iOS Simulator | `http://localhost:4000` |
| Physical device (same Wi-Fi) | `http://<your-machine-IP>:4000` |

Check and update `lib/services/api_service.dart` if needed.

### 7.3 Start an emulator / simulator

**Android:**
```bash
flutter emulators --launch <emulator_id>
# or open Android Studio → Device Manager → Start
```

**iOS (macOS only):**
```bash
open -a Simulator
```

### 7.4 Run the app

```bash
flutter run
```

To run on a specific device:
```bash
flutter devices          # list connected devices
flutter run -d <device_id>
```

---

## 8. Running the Test Suites

All tests run without a real database — Prisma is mocked in the backend tests, and API calls are mocked in the web and Flutter tests.

### 8.1 Backend tests (Jest)

```bash
cd fitfuel/backend
npm test
```

Expected output:
```
Test Suites: 13 passed, 13 total
Tests:       85 passed, 85 total
```

**Test files:**

| File | What it covers |
|---|---|
| `auth.test.ts` | Register, login, duplicate email, wrong password |
| `healthProfile.test.ts` | BMI/BMR/TDEE calculation, profile upsert |
| `meal.test.ts` | GET /api/meals filters, GET /api/meals/:id, imageUrl field |
| `recommendation.test.ts` | GET /api/recommendations scoring |
| `recommendationEngine.test.ts` | Scoring algorithm unit tests |
| `order.test.ts` | POST /api/orders deep-link generation |
| `progress.test.ts` | Log create, summary, weight-history |
| `mealPlan.test.ts` | Weekly plan generation |
| `seed.test.ts` | `healthScoreFor` heuristic + `validateImageUrls` guard |
| `nutritionCalculator.test.ts` | Mifflin-St Jeor BMR, TDEE, macro split |
| `aiExplainer.test.ts` | AI explanation route |
| `aiExplainerService.test.ts` | Groq service unit |
| `app.test.ts` | Health-check endpoint |

Run a single suite:
```bash
npm test -- --testPathPattern=meal
```

Watch mode:
```bash
npm run test:watch
```

### 8.2 Web tests (Vitest + Testing Library)

```bash
cd fitfuel/web
npm test -- --run
```

Expected output:
```
Test Files  7 passed (7)
Tests       18 passed (18)
```

Watch mode:
```bash
npm run test:watch
```

**Test files:**

| File | What it covers |
|---|---|
| `Recommendations.test.tsx` | API shape, image rendering, fallback on missing image, order button |
| `Dashboard.test.tsx` | Profile load, calorie target computation, 404 redirect |
| `Progress.test.tsx` | Three parallel API calls, summary display, goal % |
| `HealthAssessment.test.tsx` | Form renders |
| `Register.test.tsx` | Field rendering |
| `Login.test.tsx` | Field rendering |
| `bmi.test.ts` | BMI category boundaries |

### 8.3 Flutter tests

```bash
cd fitfuel/fitfuel_mobile
flutter test
```

Expected output:
```
00:00 +1: All tests passed!
```

### 8.4 Lint checks

```bash
# Backend
cd fitfuel/backend && npm run lint

# Web
cd fitfuel/web && npm run lint

# Flutter
cd fitfuel/fitfuel_mobile && flutter analyze
# Expect: 0 errors, 0 warnings (info-level deprecation hints in pre-existing files are expected)
```

---

## 9. End-to-End Manual Walkthrough

With the backend running on `:4000` and the web app on `:5173`, follow this full user journey:

### Step 1 — Register

1. Open http://localhost:5173
2. Click **Get Started** → **Register**
3. Fill in:
   - Name, email, password
   - Age, gender (`Male` / `Female` / `Other`)
   - Height (cm), weight (kg)
4. Submit → you should be redirected to the **Health Assessment** page
5. A JWT token is saved in `localStorage` automatically

### Step 2 — Health Assessment

1. Fill in the 5-step questionnaire:
   - Current weight, target weight
   - Activity level (Sedentary → Very Active)
   - Fitness goal (Weight Loss / Muscle Gain / etc.)
   - Dietary preference
   - Allergies, daily budget
2. Submit → the results panel shows:
   - **BMI** and category (Underweight / Normal / Overweight / Obese)
   - **BMR** (Basal Metabolic Rate) — calories at rest
   - **TDEE** (Total Daily Energy Expenditure) — calories with activity
   - **Calorie Target** — TDEE ± goal adjustment
   - **Protein / Carb / Fat** daily targets (grams)
   - AI-generated explanation (powered by Groq / Llama 3.1)
3. Click **Go to Dashboard**

### Step 3 — Dashboard

- Verify the 4 stat cards show real numbers (Calorie Target, Protein, Carbs, Fat)
- Verify BMI and BMI category appear in the secondary section
- BMR and TDEE displayed

### Step 4 — Meal Recommendations

1. Navigate to **Recommendations** (sidebar or bottom nav)
2. Select a meal type tab (Breakfast / Lunch / Dinner / Snack)
3. Verify:
   - Meal cards appear with **food photos** from Unsplash
   - Each card shows meal name, restaurant, price, and macro chips (protein/carbs/fat/calories)
   - Match score % badge is shown
   - Click **"Why this meal?"** to expand the score breakdown
4. Click **Order on Swiggy** or **Order on Zomato**
   - A loading spinner appears on the button
   - The browser opens the platform's search page in a new tab (search for the meal name)
   - A banner/note confirms: *"Opens the platform's own search — complete checkout there."*

> **Note:** Swiggy and Zomato do not provide a public order-placement API. The buttons
> open a search page on the respective platform — this is the correct, honest implementation.
> See [Key Design Decisions](#11-key-design-decisions--constraints).

### Step 5 — Progress Tracking

1. Navigate to **Progress**
2. Click **Log Entry**
3. Fill in one or more of: weight (kg), calories consumed, protein, carbs, fat, notes
4. Submit → the entry appears in the **Recent Entries** list
5. Log a few more entries on different days to see the **Weight over time** chart populate

### Step 6 — Weekly Meal Plan (web dashboard shortcut)

- The meal plan is generated automatically based on your health profile
- Navigate to `/weekly-plan` or use the mobile bottom sheet

### Step 7 — Mobile app (parallel flow)

Run the Flutter app on an emulator and repeat steps 1–5. The mobile app shares the same backend — any data logged on mobile appears on web and vice versa.

---

## 10. Common Issues & Fixes

### `DATABASE_URL` not found during migration

```
Error: Environment variable not found: DATABASE_URL
```

**Fix:** Make sure `backend/.env` exists and contains a valid `DATABASE_URL`. The `.env.example` file is a template — copy it first: `cp .env.example .env`.

---

### CORS error in browser (`Access-Control-Allow-Origin`)

```
Access to XMLHttpRequest blocked by CORS policy
```

**Fix:** Add the web app's origin to `ALLOWED_ORIGINS` in `backend/.env`:
```env
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```
Then restart the backend.

---

### `Meal not found` or recommendations return empty

**Fix:** The database may not be seeded. Run:
```bash
cd backend && npm run prisma:seed
```

---

### Mobile app `Connection refused` on Android emulator

Android emulators cannot reach `localhost` — use `10.0.2.2` instead.

**Fix:** In `fitfuel_mobile/lib/services/api_service.dart`, confirm the base URL is `http://10.0.2.2:4000` when targeting the Android emulator.

---

### Prisma client out of sync after schema change

```
Unknown field `imageUrl` on model Meal
```

**Fix:** Regenerate the Prisma client:
```bash
cd backend && npx prisma generate
```

---

### Flutter `assets/images/logo.png` not found

**Fix:** Create the missing asset:
```bash
mkdir -p fitfuel_mobile/assets/images
# Add any PNG as logo.png, or run:
flutter pub get
```

---

### Groq API errors (AI explanation returns an error)

- Verify `GROQ_API_KEY` is set correctly in `backend/.env`
- The free Groq tier has rate limits — wait a moment and retry
- The app degrades gracefully: if the AI call fails, the health assessment result still shows BMI/BMR/TDEE

---

## 11. Key Design Decisions & Constraints

### Swiggy / Zomato Order Integration

Swiggy and Zomato **do not provide a public API for order placement** to third-party developers. There is no legitimate way to place a real order on either platform programmatically.

The "Order on Swiggy / Order on Zomato" buttons therefore work as follows:
1. The frontend calls `POST /api/orders` → the backend logs the order intent with status `REDIRECTED` and returns a **deep link** (a pre-built search URL).
2. The app opens the deep link in the user's browser / the platform's own app.
3. The user completes the order within Swiggy or Zomato's native interface.

This is the honest, legally compliant implementation. It is clearly communicated to the user with the note: *"Opens the platform's own search — complete checkout there."*

**Deep link format:**
- Swiggy: `https://www.swiggy.com/search?query=<meal+name>`
- Zomato: `https://www.zomato.com/search?q=<meal+name>`

---

### Nutrition Calculations

All BMI / BMR / TDEE / macro calculations are performed on the backend using the **Mifflin-St Jeor** equation — the gold standard used by modern dietitians:

```
BMR (male)   = 10 × weightKg + 6.25 × heightCm − 5 × age + 5
BMR (female) = 10 × weightKg + 6.25 × heightCm − 5 × age − 161
TDEE         = BMR × activityMultiplier
Calorie goal = max(1200, TDEE + goalAdjustment)
```

Goal adjustments: Weight Loss −500 kcal, Muscle Gain +300, Weight Gain +400, Maintenance 0.

Macros: 30% protein, 45% carbs, 25% fat (of calorie goal, converted to grams).

The same constants are mirrored on the frontend (Dashboard) and mobile (DashboardScreen) so calorie targets are consistent even when displaying from a cached profile.

---

### Meal Image URLs

All 14 seeded meals use Unsplash CDN URLs (`images.unsplash.com/photo-<id>?auto=format&fit=crop&w=600&q=80`). These are:
- Free to use under the Unsplash license
- Served via Unsplash's global CDN — no storage service or file upload needed
- Selected to loosely match each meal's cuisine and type (e.g. grilled chicken for the salad bowl, orange curry for paneer tikka, etc.)

The seed script has a built-in guard: if any meal is missing an `imageUrl`, the script throws before touching the database, so a broken seed never ships silently.

---

### AI Layer

The AI chat and meal explanation feature uses **Groq** (free API) with the **Llama-3.1-8b-instant** model. Groq provides very fast inference with a generous free tier (no credit card required). The model is used for:
- Generating a plain-language explanation of the user's nutrition targets after health assessment
- Answering nutrition questions in the chat feature

---

*Last updated: August 2026 · FitFuel v1.0*
