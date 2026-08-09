# FitFuel — Intelligent AI-Based Nutrition & Food Ordering Platform

A final-year project consisting of three apps sharing one backend:

- **`backend/`** — Node.js + TypeScript + Express + Prisma + PostgreSQL REST API
- **`web/`** — React + TypeScript + Vite + Tailwind web app
- **`mobile/`** — Flutter mobile app (Android/iOS)
- **`.github/workflows/`** — GitHub Actions CI/CD for all three apps

## Important note on Swiggy/Zomato integration

Swiggy and Zomato do **not** offer public order-placement APIs to third-party developers.
"Order on Swiggy / Zomato" in this project opens a **deep link** to a pre-filled search
on the chosen platform, and the user completes checkout there themselves. This is the
standard, honest approach for a project like this — there is no way to programmatically
place a real order on either platform from an unaffiliated app.

---

## 1. Architecture

```
User (Web or Mobile)
        │
        ▼
  Express REST API  ───────►  PostgreSQL (Supabase/Neon)
        │
        ├──► Groq LLM API (free) — meal plan explanations / chat
        └──► Deep link builder — Swiggy/Zomato search handoff
```

All business logic (BMI/BMR/TDEE, macro targets, meal scoring) lives in the backend as
plain, deterministic, unit-tested TypeScript functions — see:
- `backend/src/services/nutritionCalculator.ts`
- `backend/src/services/recommendationEngine.ts`
- `backend/src/services/aiExplainerService.ts` (optional LLM narrative layer)

---

## 2. Local development setup

### Prerequisites
- Node.js 20+
- Flutter SDK 3.24+ (`flutter doctor` should pass)
- A free PostgreSQL database (see step 3) or local Postgres via Docker

### Backend
```bash
cd backend
cp .env.example .env       # fill in DATABASE_URL, JWT_SECRET, GROQ_API_KEY
npm install
npx prisma migrate dev     # creates tables
npx prisma db seed         # seeds sample Swiggy/Zomato-style meals
npm run dev                # http://localhost:4000
```

### Web app
```bash
cd web
cp .env.example .env       # VITE_API_BASE_URL=http://localhost:4000
npm install
npm run dev                # http://localhost:5173
```

### Mobile app
```bash
cd mobile
flutter pub get
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:4000   # Android emulator
# iOS simulator: --dart-define=API_BASE_URL=http://localhost:4000
```

---

## 3. Free deployment guide

Everything below uses only free tiers. No credit card should be required for any of these
(Render and Supabase's free tiers do not require one; double check at signup).

### Step 1 — Database: Supabase (free Postgres, 500MB)
1. Create a project at https://supabase.com
2. Go to Project Settings → Database → Connection string (URI, "Transaction" pooler)
3. Copy it into `backend/.env` as `DATABASE_URL`

### Step 2 — Backend: Render (free web service)
1. Push this repo to GitHub (see step 5 below)
2. Create a new **Web Service** at https://render.com, connect your GitHub repo
3. Root directory: `backend`
4. Build command: `npm install && npx prisma generate && npm run build`
5. Start command: `npx prisma migrate deploy && npm start`
6. Add environment variables: `DATABASE_URL`, `JWT_SECRET`, `GROQ_API_KEY`
7. Free tier note: the service sleeps after ~15 min of inactivity and takes ~30s to
   wake on the next request — acceptable for a demo/project, mention this to evaluators.
8. Copy the deployed URL (e.g. `https://fitfuel-backend.onrender.com`)

### Step 3 — Web app: Vercel (free)
1. Import the repo at https://vercel.com/new
2. Root directory: `web`
3. Framework preset: Vite
4. Environment variable: `VITE_API_BASE_URL` = your Render backend URL
5. Deploy — you'll get a URL like `https://fitfuel-web.vercel.app`

### Step 4 — Mobile app: free APK via GitHub Actions
No app-store fee needed for a handover build:
1. Push to `main` — the `mobile-ci.yml` workflow builds a release APK automatically
2. Download it from the workflow run's **Artifacts** section (kept 90 days free)
3. Set the `MOBILE_API_BASE_URL` repo secret to your Render backend URL first, so the
   APK talks to production, not localhost
4. Share the APK file directly with your client/evaluators for sideloading, or
   optionally publish to Google Play Console's free "Internal testing" track

### Step 5 — Push to GitHub and wire up CI secrets
```bash
cd fitfuel
git init
git add .
git commit -m "Initial FitFuel scaffold"
git branch -M main
git remote add origin https://github.com/<your-username>/fitfuel.git
git push -u origin main
```
Then in GitHub: **Settings → Secrets and variables → Actions**, add:
| Secret | Where to get it |
|---|---|
| `RENDER_DEPLOY_HOOK_URL` | Render service → Settings → Deploy Hook (optional, Render auto-deploys from GitHub anyway) |
| `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID` | Vercel account settings / project settings |
| `VITE_API_BASE_URL` | Your Render backend URL |
| `MOBILE_API_BASE_URL` | Your Render backend URL |

---

## 4. CI/CD pipelines

Three independent GitHub Actions workflows, each triggered only when its own folder changes:
- **`backend-ci.yml`** — spins up a throwaway Postgres service container, runs Prisma
  migrations, lints, runs Jest+Supertest tests, builds, then deploys
- **`web-ci.yml`** — lints, runs Vitest + React Testing Library tests, builds, deploys to Vercel
- **`mobile-ci.yml`** — runs `flutter analyze` + `flutter test`, then builds a release APK
  and uploads it as a downloadable artifact

---

## 5. Project phases → code map

| Workflow phase | Where it lives |
|---|---|
| Phase 1 (Registration) | `backend/src/routes/auth.routes.ts`, `web/src/pages/Register.tsx`, `mobile/lib/screens/register_screen.dart` |
| Phase 2 (Health Assessment) + Phase 3 (BMI/BMR/TDEE) | `backend/src/services/nutritionCalculator.ts`, `backend/src/routes/healthProfile.routes.ts` |
| Phase 4 (Food Database) | `backend/prisma/schema.prisma` (Meal model), `backend/prisma/seed.ts` |
| Phase 5 (Recommendation Engine) | `backend/src/services/recommendationEngine.ts` |
| Phase 6 (Order Integration) | `backend/src/routes/order.routes.ts` (deep link builder) |
| Phase 7 (Progress Tracking) | `backend/src/routes/progress.routes.ts` |

---

## 6. What's next (recommended build order)

This scaffold has working core logic (auth, calculations, recommendation scoring, order
handoff, progress tracking) with passing tests and CI wired up end-to-end. Suggested next
steps to flesh it out into a full handover:
1. Wire up remaining Flutter screens' navigation/state (Provider pattern already included)
2. Add password reset / basic validation polish on both frontends
3. Expand the seeded meal database (more restaurants/cuisines)
4. Add a weekly meal-plan generator endpoint (Phase 3's "weekly meal plan")
5. Add charts to the progress screens (`fl_chart` is already in `pubspec.yaml`, `recharts`-style
   chart lib can be added to web)
6. Basic E2E smoke test (Playwright/Cypress) once the web UI is finalized
