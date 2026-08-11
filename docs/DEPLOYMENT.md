# FitFuel — Free Deployment Guide

> Deploy the entire FitFuel stack (backend + web + database + mobile APK) at **zero cost**, using only free-tier services. No credit card should be required for any of these platforms.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Prerequisites](#2-prerequisites)
3. [Step 1 — Database: Neon (free PostgreSQL)](#3-step-1--database-neon-free-postgresql)
4. [Step 2 — Push to GitHub](#4-step-2--push-to-github)
5. [Step 3 — Backend: Render (free Node.js hosting)](#5-step-3--backend-render-free-nodejs-hosting)
6. [Step 4 — Web App: Vercel (free React hosting)](#6-step-4--web-app-vercel-free-react-hosting)
7. [Step 5 — Mobile APK: GitHub Actions (free CI build)](#7-step-5--mobile-apk-github-actions-free-ci-build)
8. [Step 6 — Wire Up GitHub Actions Secrets](#8-step-6--wire-up-github-actions-secrets)
9. [Alternative: Supabase (instead of Neon)](#9-alternative-supabase-instead-of-neon)
10. [Alternative: Railway (instead of Render)](#10-alternative-railway-instead-of-render)
11. [Alternative: Netlify (instead of Vercel)](#11-alternative-netlify-instead-of-vercel)
12. [Keeping Everything Alive (Free Tier Limitations)](#12-keeping-everything-alive-free-tier-limitations)
13. [Long-Term / Production Upgrade Path](#13-long-term--production-upgrade-path)
14. [Environment Variables Quick Reference](#14-environment-variables-quick-reference)
15. [Post-Deploy Checklist](#15-post-deploy-checklist)

---

## 1. Overview

| Service | Purpose | Free Tier Limit |
|---|---|---|
| **Neon** | PostgreSQL database | 512 MB storage, 1 project |
| **Render** | Backend Node.js API | 750 hrs/month (1 free service), sleeps after 15 min |
| **Vercel** | React web app | Unlimited projects, 100 GB bandwidth/month |
| **GitHub Actions** | CI/CD + APK build | 2000 min/month (public repos: unlimited) |

---

## 2. Prerequisites

- A **GitHub account** (to host the repo and run CI)
- A **Neon account** — [neon.tech](https://neon.tech) (sign in with GitHub)
- A **Render account** — [render.com](https://render.com) (sign in with GitHub)
- A **Vercel account** — [vercel.com](https://vercel.com) (sign in with GitHub)
- A **Groq account** (optional, for AI features) — [console.groq.com](https://console.groq.com)
- The FitFuel repository cloned locally

---

## 3. Step 1 — Database: Neon (free PostgreSQL)

### 3.1 Create a Neon project

1. Go to [neon.tech](https://neon.tech) → **Sign up**
2. Create a new project (e.g. `fitfuel`) and database
3. Select the region closest to your users
4. Click **Create Project**

### 3.2 Get the connection string

1. In your project dashboard → **Connection Details**
2. Select **Prisma** for the correct format
3. Copy the connection string — it looks like:
   ```
   postgresql://USER:PASSWORD@ep-xxx.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
   ```

### 3.3 Add the URL to your .env

```bash
# backend/.env
DATABASE_URL="postgresql://USER:PASSWORD@ep-xxx.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"
```

> With Neon, you **do not** need `pgbouncer=true` — the standard connection string works.

---

## 4. Step 2 — Push to GitHub

If your project isn't on GitHub yet:

```bash
cd fitfuel

# Initialise git (skip if already initialised)
git init
git add .
git commit -m "Initial FitFuel commit"

# Create a new repo on GitHub, then:
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/fitfuel.git
git push -u origin main
```

> **Security check before pushing**: Make sure `backend/.env` is listed in `.gitignore` (it already is). Never commit real secrets.

---

## 5. Step 3 — Backend: Render (free Node.js hosting)

### 5.1 Create a Web Service

1. Go to [dashboard.render.com](https://dashboard.render.com) → **New +** → **Web Service**
2. Connect your GitHub account and select the `fitfuel` repository
3. Configure the service:

| Setting | Value |
|---|---|
| **Name** | `fitfuel-backend` |
| **Region** | Closest to your users |
| **Branch** | `main` |
| **Root directory** | `backend` |
| **Runtime** | `Node` |
| **Build command** | `npm install && npx prisma generate && npm run build` |
| **Start command** | `npx prisma migrate deploy && npm start` |
| **Instance type** | `Free` |

### 5.2 Add environment variables

In the **Environment** section, add:

| Key | Value |
|---|---|
| `NODE_ENV` | `production` |
| `DATABASE_URL` | Your Neon connection string |
| `JWT_SECRET` | A long random string — generate with: `openssl rand -base64 32` |
| `GROQ_API_KEY` | Your Groq API key (or leave blank to disable AI) |
| `ALLOWED_ORIGINS` | Your Vercel app URL (added after Step 4) |

### 5.3 Deploy

Click **Create Web Service** — Render will:
1. Pull the code from GitHub
2. Run the build command (install → generate Prisma → compile TypeScript)
3. Run the start command (migrate DB → start Node server)

Your backend URL will be: `https://fitfuel-backend.onrender.com`

### 5.4 Seed the database

After the first deploy, run the seed script once to populate the meals database. The easiest way is via Render's **Shell** tab:

```bash
npx prisma db seed
```

Or do it locally while pointing at the production database:
```bash
cd backend
DATABASE_URL="your-neon-url" npx prisma db seed
```

### 5.5 Free tier limitation — cold starts

> ⚠️ Render's free web service **sleeps after 15 minutes of inactivity** and takes **~30 seconds** to wake on the next request. This is expected behaviour. Mention this to evaluators/users. Consider using a free uptime monitor like [UptimeRobot](https://uptimerobot.com) (free, 5-minute intervals) to ping your backend and prevent sleeping.

---

## 6. Step 4 — Web App: GitHub Pages (free React hosting)

The frontend is configured to deploy automatically to GitHub Pages via a GitHub Actions workflow (`web-ci.yml`) whenever you push to the `main` branch. 

### 6.1 Enable GitHub Pages

1. Go to your GitHub repository → **Settings**
2. In the left sidebar, click on **Pages**
3. Under **Build and deployment**:
   - Source: **GitHub Actions**
4. That's it! GitHub Actions will take over the deployment from here.

### 6.2 Set Backend URL Secret

In your GitHub repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**:

| Name | Value |
|---|---|
| `VITE_API_BASE_URL` | `https://fitfuel-backend.onrender.com` |

### 6.3 Update Backend CORS

Now go back to your Render environment variables (for the backend) and update the `ALLOWED_ORIGINS` to point to your new GitHub Pages URL:
```
ALLOWED_ORIGINS=https://your-username.github.io
```
*(e.g., https://Dakshinesh-python.github.io)*

Trigger a manual redeploy on Render after changing env vars.

---

## 7. Step 5 — Mobile APK: GitHub Actions (free CI build)

No Play Store account or signing key is needed to share an APK for evaluation.

### 7.1 Add the backend URL secret

In your GitHub repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**:

| Name | Value |
|---|---|
| `MOBILE_API_BASE_URL` | `https://fitfuel-backend.onrender.com` |

### 7.2 Trigger a build

Push any change to `fitfuel_mobile/` or manually trigger the workflow:

1. GitHub repo → **Actions** tab → `Mobile CI` workflow
2. Click **Run workflow** → **Run workflow**

### 7.3 Download the APK

After the workflow completes (usually 5–8 minutes):
1. Click the workflow run
2. Scroll to **Artifacts**
3. Download `fitfuel-release-apk.zip`
4. Unzip and install the `.apk` on any Android device

> **Sideloading**: The recipient needs to enable "Install from unknown sources" in Android settings. For iOS, a paid Apple Developer account ($99/yr) and TestFlight are required — this is out of scope for the free tier.

---

## 8. Step 6 — Wire Up GitHub Actions Secrets

All CI secrets to add in **GitHub → Settings → Secrets and variables → Actions**:

| Secret name | Where to get it | Used by |
|---|---|---|
| `DATABASE_URL` | Neon connection string | `backend-ci.yml` (runs tests against a temporary DB — actually uses the CI's own Postgres service container, this secret is optional) |
| `VITE_API_BASE_URL` | Your Render backend URL | `web-ci.yml` (build-time env) |
| `MOBILE_API_BASE_URL` | Your Render backend URL | `mobile-ci.yml` (compile-time `--dart-define`) |

---

## 9. Alternative: Supabase (instead of Neon)

[Supabase](https://supabase.com) is another excellent free PostgreSQL provider:

- **Free tier**: 500 MB storage, 2 projects
- Get connection string: Supabase dashboard → **Settings** → **Database** → **Connection string** → **URI** (Transaction pooler)

```bash
DATABASE_URL="postgresql://postgres.xxxx:PASSWORD@aws-0-ap-south-1.pooler.supabase.com:6543/postgres?pgbouncer=true&connection_limit=1"
```

> **Note the query params**: `pgbouncer=true&connection_limit=1` — required for Prisma to work correctly with PgBouncer on Render's free tier.

---

## 10. Alternative: Railway (instead of Render)

[Railway](https://railway.app) offers $5/month free credit which covers a small Node.js service:

1. New project → **Deploy from GitHub repo**
2. Select `fitfuel` repo → Root path: `backend`
3. Railway auto-detects Node.js and runs `npm start`
4. Set environment variables in the Variables tab
5. Add a PostgreSQL plugin directly in Railway (free, included in credit)

Railway advantage: **no cold starts** — the service stays warm. Better for demos.

---

## 11. Alternative: Netlify (instead of Vercel)

[Netlify](https://netlify.com) is an equally capable alternative for the React web app:

1. **New site** → Import from GitHub → select `fitfuel`
2. Build settings:
   - Base directory: `web`
   - Build command: `npm run build`
   - Publish directory: `web/dist`
3. Environment variable: `VITE_API_BASE_URL=https://fitfuel-backend.onrender.com`

Both Vercel and Netlify offer unlimited deployments on free tier.

---

## 12. Keeping Everything Alive (Free Tier Limitations)

### Problem: Render cold starts
Free Render services sleep after 15 min of inactivity. Fix options:

**Option A — UptimeRobot (free)**
1. Sign up at [uptimerobot.com](https://uptimerobot.com)
2. Add a new monitor: `HTTP(S)`, URL = `https://fitfuel-backend.onrender.com/api/health`
3. Monitoring interval: 5 minutes
4. This pings your backend every 5 min, keeping it awake

**Option B — Cron-job.org (free)**
1. Sign up at [cron-job.org](https://cron-job.org)
2. Create a cron job: GET `https://fitfuel-backend.onrender.com/api/health`
3. Schedule: `*/5 * * * *` (every 5 minutes)

> ⚠️ Note: Render's Terms of Service technically disallow using external pings purely to avoid sleeping. Use for demo/project purposes only — upgrade to a paid plan for production use.

### Problem: Neon project pause
Neon pauses projects that have been inactive for some time on the free tier. Fix:
- Set up a UptimeRobot or cron job to do a lightweight DB read every few days
- Or upgrade to a paid plan which disables auto-pause

### Problem: GitHub Pages bandwidth
Free tier allows 100 GB/month on GitHub Pages. For a demo project this is effectively unlimited.

---

## 13. Long-Term / Production Upgrade Path

When you're ready to move beyond free tiers:

| Service | Free → Paid | Monthly Cost | Benefit |
|---|---|---|---|
| **Render** | Starter plan | $7/month | No sleep, always-on |
| **Neon** | Launch plan | $19/month | More compute, no throttling |
| **GitHub Pages** | Vercel Pro | $20/month | More bandwidth, team features (if you switch to Vercel) |
| **Railway** | Hobby plan | $5/month credit included | Easy, no cold starts |

### Moving to a VPS (best long-term value)

For long-term self-hosting, a VPS is more cost-effective:

**DigitalOcean Droplet** (~$6/month):
```
1. Create Ubuntu 22.04 droplet (1 vCPU, 1 GB RAM)
2. Install Node.js 20 + PostgreSQL 15
3. Clone repo, set up .env
4. Use PM2 to keep the Node.js process running:
   npm install -g pm2
   pm2 start dist/server.js --name fitfuel-backend
   pm2 save && pm2 startup
5. Use Nginx as reverse proxy + Certbot for free SSL (Let's Encrypt)
6. Use systemd or crontab for auto-restart
```

**Hetzner Cloud** (~€4/month, better value than DO):
- Same setup process as DigitalOcean
- CAX11 ARM instance is fastest per Euro

---

## 14. Environment Variables Quick Reference

### backend/.env (production)

```env
PORT=4000
NODE_ENV=production

# Neon
DATABASE_URL="postgresql://USER:PASSWORD@ep-xxx.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

# Generate with: openssl rand -base64 32
JWT_SECRET="your-very-long-random-secret-here"

# From https://console.groq.com (leave empty to disable AI)
GROQ_API_KEY="gsk_xxxxxxxxxxxxxxxxxxxx"

# Your GitHub Pages web app URL
ALLOWED_ORIGINS="https://Dakshinesh-python.github.io"
```

### web/.env (production)

```env
VITE_API_BASE_URL=https://fitfuel-backend.onrender.com
```

### Mobile (GitHub Actions secret)

```
MOBILE_API_BASE_URL=https://fitfuel-backend.onrender.com
```

---

## 15. Post-Deploy Checklist

After completing all steps, verify the following:

### Backend
- [ ] `GET https://fitfuel-backend.onrender.com/api/health` returns `{ "status": "ok" }`
- [ ] Database tables exist (check Neon Console)
- [ ] Meals are seeded (check Neon → SQL Editor or Table data)
- [ ] CORS allows your Vercel domain (test in browser Network tab)

### Web App
- [ ] `https://Dakshinesh-python.github.io/fitfuel-final/` loads the landing page
- [ ] Registration and login work (creates a JWT)
- [ ] Health assessment completes and shows dashboard
- [ ] Recommendations page shows meals
- [ ] AI chat responds (if GROQ_API_KEY is set)

### Mobile APK
- [ ] APK downloaded from GitHub Actions artifacts
- [ ] App installs on Android device
- [ ] App connects to production backend (not localhost)
- [ ] All 5 bottom nav tabs navigate correctly
- [ ] Profile screen loads user data

### CI Pipelines
- [ ] Backend CI is green on `main` branch
- [ ] Web CI is green on `main` branch
- [ ] Mobile CI is green and APK artifact is available

---

## Useful Links

| Resource | URL |
|---|---|
| Neon Dashboard | https://console.neon.tech |
| Render Dashboard | https://dashboard.render.com |
| GitHub Repository | https://github.com/Dakshinesh-python/fitfuel-final |
| Groq Console | https://console.groq.com |
| UptimeRobot | https://uptimerobot.com |
| cron-job.org | https://cron-job.org |
| Let's Encrypt (SSL) | https://letsencrypt.org |
| PM2 (process manager) | https://pm2.keymetrics.io |

---

*For the architecture details, see [`ARCHITECTURE.md`](ARCHITECTURE.md).*
*For the API reference, see [`API_REFERENCE.md`](API_REFERENCE.md).*
