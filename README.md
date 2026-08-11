# FitFuel 🥗⚡

> **AI-powered nutrition planning, meal recommendations & food ordering assistant.**
> A full-stack final-year project with a Node.js backend, React web app, and Flutter mobile app — all sharing one REST API.

---

## ⚡ What is FitFuel?

FitFuel is a complete nutrition platform that:

1. **Onboards users** with a multi-step health assessment (age, weight, height, activity level, fitness goal)
2. **Calculates** BMI, BMR, TDEE, and personalised daily macro targets (protein/carbs/fat/calories)
3. **Scores and ranks meals** from a curated database using a deterministic recommendation engine, matched to the user's macro targets
4. **Generates 7-day AI meal plans** with explanations powered by the Groq LLM API (free tier)
5. **Provides an AI chat coach** that answers nutrition questions in context of the user's health profile
6. **Deep-links to Swiggy or Zomato** for ordering — the user completes checkout there (see constraint note below)
7. **Tracks progress** — weight logs, calorie logs, weekly averages, goal achievement %, and a weight-over-time chart

---

## ⚠️ Important: Swiggy / Zomato Integration Constraint

Swiggy and Zomato **do not offer public order-placement APIs** to third-party developers.

The "Order on Swiggy / Zomato" feature in FitFuel builds a **deep link that opens a pre-filled search** on the chosen platform. The user completes checkout there themselves. This is the only legally correct approach for an unaffiliated application — there is no way to programmatically place a real order on either platform without an official partnership.

---

## 🏗️ Repository Structure

```
fitfuel/
├── backend/              # Node.js + TypeScript + Express + Prisma REST API
├── web/                  # React 18 + TypeScript + Vite + TailwindCSS web app
├── fitfuel_mobile/       # Flutter 3.x mobile app (Android & iOS)
├── docs/                 # Architecture, API reference, deployment & testing guides
├── .github/workflows/    # GitHub Actions CI/CD (backend, web, mobile)
└── README.md
```

---

## 🚀 Quick Start (Local Development)

### Prerequisites

| Tool | Version |
|---|---|
| Node.js | 20+ |
| npm | 9+ |
| Flutter SDK | 3.24+ |
| PostgreSQL | Any (or use free Neon cloud) |
| Git | Any |

### 1. Clone & configure environment

```bash
git clone https://github.com/<your-username>/fitfuel.git
cd fitfuel
```

### 2. Backend

```bash
cd backend
cp .env.example .env
# Edit .env — fill in DATABASE_URL, JWT_SECRET, GROQ_API_KEY
npm install
npx prisma migrate dev     # creates all tables
npx prisma db seed         # seeds the meals database
npm run dev                # → http://localhost:4000
```

### 3. Web App

```bash
cd web
cp .env.example .env
# Set VITE_API_BASE_URL=http://localhost:4000
npm install
npm run dev                # → http://localhost:5173
```

### 4. Mobile App

```bash
cd fitfuel_mobile
flutter pub get

# Android emulator
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:4000

# iOS simulator
flutter run --dart-define=API_BASE_URL=http://localhost:4000

# Physical Android device (replace with your machine's LAN IP)
flutter run --dart-define=API_BASE_URL=http://192.168.x.x:4000
```

---

## 🔑 Environment Variables

### Backend (`backend/.env`)

| Variable | Description | Required |
|---|---|---|
| `PORT` | HTTP port (default `4000`) | No |
| `NODE_ENV` | `development` or `production` | Yes |
| `DATABASE_URL` | PostgreSQL connection string | **Yes** |
| `JWT_SECRET` | Long random secret for JWT signing | **Yes** |
| `GROQ_API_KEY` | Free API key from [console.groq.com](https://console.groq.com) — for AI chat & meal plan explanations | No (AI features disabled if empty) |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins (e.g. your Vercel URL) | Yes (production) |

### Web App (`web/.env`)

| Variable | Description |
|---|---|
| `VITE_API_BASE_URL` | Full URL to the backend (e.g. `http://localhost:4000`) |

### Mobile App (compile-time `--dart-define`)

| Variable | Description |
|---|---|
| `API_BASE_URL` | Full URL to the backend (default: `http://10.0.2.2:4000`) |

---

## 🧪 Running Tests

```bash
# Backend (Jest + Supertest — requires a TEST database or the dev DB)
cd backend && npm test

# Web (Vitest + React Testing Library)
cd web && npm test

# Mobile (Flutter unit tests)
cd fitfuel_mobile && flutter test

# Lint checks
cd backend && npm run lint
cd web && npm run lint
cd fitfuel_mobile && flutter analyze   # 0 errors, 0 warnings expected
```

---

## 🏛️ Architecture Overview

```
                    ┌─────────────────────────────────────┐
                    │           CLIENTS                   │
                    │  React Web (Vite)  │  Flutter Mobile │
                    └──────────┬──────────────────┬───────┘
                               │ HTTPS REST        │ HTTPS REST
                    ┌──────────▼──────────────────▼───────┐
                    │    Express REST API (Node.js 20)     │
                    │    Helmet · CORS · JWT auth          │
                    │    Zod request validation            │
                    │                                      │
                    │  ┌──────────────────────────────┐   │
                    │  │     Business Logic Layer      │   │
                    │  │  nutritionCalculator.ts       │   │
                    │  │  recommendationEngine.ts      │   │
                    │  │  aiExplainerService.ts        │   │
                    │  └────────────────┬─────────────┘   │
                    └───────────────────┼─────────────────┘
                                        │
                    ┌───────────────────┼─────────────────┐
                    │                  │  Prisma ORM      │
                    │  ┌───────────────▼─────────────┐   │
                    │  │  PostgreSQL (Neon)           │   │
                    │  └─────────────────────────────┘   │
                    │                                      │
                    │  ┌───────────────────────────────┐  │
                    │  │  Groq LLM API (llama-3.3-70b) │  │
                    │  │  AI chat & plan explanations  │  │
                    │  └───────────────────────────────┘  │
                    └──────────────────────────────────────┘
```

---

## 📱 Mobile App — Screen Map

| Screen | Route | Description |
|---|---|---|
| Splash | `/` | Animated logo + auth check |
| Onboarding | `/onboarding` | 3-slide intro carousel |
| Register | `/register` | Sign up form |
| Login | `/login` | JWT login |
| Health Assessment | `/health-*` | 4 steps: weight/height → goal → activity → diet prefs |
| Plan Ready | `/plan-ready` | Macro results + explanation |
| Dashboard | `/dashboard` | Hero calorie card, macro bars, quick actions |
| Recommendations | `/recommendations` | AI-scored meal list by meal type |
| Weekly Meal Plan | `/weekly-plan` | 7-day plan, day tabs, regenerate |
| Progress | `/progress` | Weight chart, log entries, calorie avg |
| AI Chat | `/chat` | Live AI nutrition coach |
| Profile | `/profile` | Edit personal info, health stats, preferences, change password |

Bottom nav: **Home → Meals → Chat → Progress → Profile**

---

## 🌐 Web App — Page Map

| Page | Route | Description |
|---|---|---|
| Landing | `/` | Marketing hero page |
| Register / Login | `/register`, `/login` | Auth forms |
| Health Assessment | `/assessment` | Multi-step flow |
| Dashboard | `/dashboard` | Macro overview, stat cards |
| Recommendations | `/recommendations` | Pill-tab meal type selector, ranked cards |
| Meal Plan | `/meal-plan` | 7-day gradient grid |
| Progress | `/progress` | Recharts weight/calorie graphs |
| AI Chat | `/chat` | GPT-style chat interface |
| Profile | `/profile` | Tabbed settings (personal, health, preferences, security) |

---

## 🔌 API Summary

| Group | Endpoints | Auth |
|---|---|---|
| Auth | `POST /api/auth/register`, `POST /api/auth/login`, `PUT /api/auth/profile`, `PUT /api/auth/password` | Public / JWT |
| Health Profile | `POST /api/health-profile`, `GET /api/health-profile` | JWT |
| Meals | `GET /api/meals` | JWT |
| Recommendations | `GET /api/recommendations` | JWT |
| Meal Plans | `GET /api/meal-plans/current`, `POST /api/meal-plans/generate` | JWT |
| Orders | `POST /api/orders` | JWT |
| Progress | `POST /api/progress`, `GET /api/progress`, `GET /api/progress/summary`, `GET /api/progress/weight-history` | JWT |
| Chat | `POST /api/chat` | JWT |

Full reference: [`docs/API_REFERENCE.md`](docs/API_REFERENCE.md)

---

## 🛠️ CI/CD Pipelines

Three GitHub Actions workflows — each triggered only when its own folder changes:

| Workflow | File | What it does |
|---|---|---|
| Backend CI | `.github/workflows/backend-ci.yml` | Spins up Postgres service container → Prisma migrate → lint → Jest+Supertest tests → TypeScript build → deploy to Render |
| Web CI | `.github/workflows/web-ci.yml` | ESLint → Vitest + RTL tests → Vite build → deploy to Vercel |
| Mobile CI | `.github/workflows/mobile-ci.yml` | `flutter analyze` + `flutter test` → build release APK → upload as artifact |

---

## 🔒 Security Notes

- All passwords are hashed with **bcrypt** (rounds: 10)
- All API routes (except `/api/auth/register` and `/api/auth/login`) require a valid **JWT Bearer token**
- Tokens are signed with `JWT_SECRET` — use a strong, unique value in production
- **Helmet.js** sets security HTTP headers
- **CORS** only allows explicitly listed origins (`ALLOWED_ORIGINS` env var)
- **Zod** validates all incoming request bodies
- `.env` files are in `.gitignore` — no secrets should ever be committed

---

## 📋 Project Phases → Code Map

| Phase | What | Where |
|---|---|---|
| 1 — Registration & Auth | User accounts + JWT | `backend/src/routes/auth.routes.ts` |
| 2 — Health Assessment | Multi-step questionnaire | `backend/src/routes/healthProfile.routes.ts` |
| 3 — BMI/BMR/TDEE | Deterministic calculations | `backend/src/services/nutritionCalculator.ts` |
| 4 — Food Database | Meal model + seed data | `backend/prisma/schema.prisma`, `backend/prisma/seed.ts` |
| 5 — Recommendation Engine | Scoring algorithm | `backend/src/services/recommendationEngine.ts` |
| 6 — Order Integration | Swiggy/Zomato deep links | `backend/src/routes/order.routes.ts` |
| 7 — Progress Tracking | Logs + charts | `backend/src/routes/progress.routes.ts` |
| 8 — AI Chat & Meal Plans | Groq LLM integration | `backend/src/services/aiExplainerService.ts`, `backend/src/routes/chat.routes.ts` |

---

## ✅ What's Built

- [x] Full auth system (register, login, JWT, profile update, password change)
- [x] 4-step health assessment with all BMI/BMR/TDEE/macro calculations
- [x] Meal database with 30+ seeded Swiggy/Zomato-style meals
- [x] AI recommendation engine (calorie accuracy + protein quality + budget fit + health score)
- [x] 7-day meal plan generator with Groq AI explanations
- [x] Swiggy/Zomato deep-link order handoff
- [x] Progress tracking (weight, calories, protein; chart + log history)
- [x] AI chat coach (context-aware, uses user's health profile)
- [x] React web app — all pages, responsive, dark-green design system
- [x] Flutter mobile app — all screens, 5-tab bottom nav, premium UI
- [x] GitHub Actions CI for backend, web, and mobile
- [x] Unit tests: backend (Jest + Supertest), web (Vitest + RTL), mobile (flutter test)

## ⚠️ Known Limitations / Suggested Future Work

- **No real Swiggy/Zomato API** — only deep-links (see constraint note above)
- **No push notifications** — meal reminders/daily logs not yet implemented
- **No password reset flow** — "Forgot password" is UI-only; email delivery not wired
- **Meal database is seeded** — not a live restaurant API; limited cuisines (primarily Indian)
- **Groq free tier limits** — 30 req/min; AI chat may queue at high traffic
- **Render free tier cold starts** — backend sleeps after 15 min; first request takes ~30s
- **No E2E test suite** — Playwright/Cypress coverage not yet added
- **iOS deployment** — not tested on device; requires Apple Developer account ($99/yr) for production

---

## 📚 Documentation

| File | Description |
|---|---|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Full tech stack, data models, algorithm details |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Step-by-step free hosting guide (Neon + Render + Vercel) |
| [`docs/API_REFERENCE.md`](docs/API_REFERENCE.md) | Every endpoint with request/response examples |
| [`docs/TESTING_GUIDE.md`](docs/TESTING_GUIDE.md) | How to run all tests across all three apps |

---

## 👨‍💻 Tech Stack At a Glance

| Layer | Technology |
|---|---|
| Backend runtime | Node.js 20 + TypeScript 5 |
| API framework | Express 4 |
| ORM | Prisma 5 |
| Database | PostgreSQL 15 |
| Auth | JWT (jsonwebtoken) + bcrypt |
| Validation | Zod |
| AI / LLM | Groq API (llama-3.3-70b-versatile) |
| Web frontend | React 18 + Vite + TailwindCSS |
| Web charts | Recharts |
| Mobile | Flutter 3.24 + Dart |
| Mobile HTTP | `http` package |
| Mobile state | `provider` |
| Mobile charts | `fl_chart` |
| Mobile fonts | `google_fonts` (Manrope + Inter) |
| CI/CD | GitHub Actions |
| Hosting (backend) | Render (free tier) |
| Hosting (web) | Vercel (free tier) |
| Hosting (DB) | Neon (free tier) |

---

*FitFuel — Built as a final-year project demonstrating full-stack AI-integrated application development.*
