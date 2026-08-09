# FitFuel AI — Web App

React + Vite + TypeScript + Tailwind frontend for FitFuel AI, converted 1:1 from the
Stitch-generated "Kinetic Wellness" design (colors, type scale, radii, spacing all mirrored
in `tailwind.config.js`).

## Setup

```bash
cd web
npm install
cp .env.example .env   # points VITE_API_BASE_URL at your backend (defaults to http://localhost:4000)
npm run dev
```

The backend (from TASKS 1-8) must be running at the URL configured in `.env` (default
`http://localhost:4000`).

## Scripts

- `npm run dev` — start the Vite dev server
- `npm run build` — typecheck (`tsc -b`) and build for production into `dist/`
- `npm run lint` — ESLint (zero warnings allowed)
- `npm test` — run the Vitest suite once
- `npm run test:watch` — run Vitest in watch mode
- `npm run preview` — preview the production build locally

## App flow

1. `/register` → creates an account, saves the JWT, redirects to `/health-assessment`
2. `/login` → authenticates, redirects to `/dashboard`
3. `/health-assessment` → submits the health questionnaire (`POST /api/health-profile`),
   shows calculated BMI/BMR/TDEE/macro targets, then continues to `/dashboard`
4. `/dashboard` → fetches `GET /api/health-profile`; redirects back to `/health-assessment`
   on 404 (no profile yet); shows stat cards and links to Recommendations/Progress
5. `/recommendations` → meal-type tabs, fetches `GET /api/recommendations`, renders meal
   cards with match-score breakdowns, and "Order on Swiggy" / "Order on Zomato" buttons
   that call `POST /api/orders` and open the returned `deepLink` in a new tab
6. `/progress` → log-entry form (`POST /api/progress`), weekly summary + goal-achievement
   bar (`GET /api/progress/summary`), a Recharts weight-over-time line chart, and a table
   of recent entries (`GET /api/progress`)

## Project structure

```
src/
  api/client.ts        Axios instance, auth token helpers, extractErrorMessage
  types/index.ts        Shared TS types/enums mirroring the backend
  utils/bmi.ts           Client-side BMI helper (kept in sync with backend formula)
  components/Layout.tsx  Authenticated shell: sidebar nav, topbar, logout
  pages/
    Login.tsx
    Register.tsx
    HealthAssessment.tsx
    Dashboard.tsx
    Recommendations.tsx
    Progress.tsx
  App.tsx                Routes + auth guard
  main.tsx                Entry point
tests/                    Vitest + Testing Library specs for every page + bmi.ts
```
