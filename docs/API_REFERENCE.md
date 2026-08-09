# FitFuel Backend API Reference

Base URL (local): `http://localhost:4000`  
Base URL (production): your deployed Render URL, e.g. `https://fitfuel-backend.onrender.com`

All **authenticated** endpoints require an `Authorization: Bearer <token>` header.  
The token is returned by `/api/auth/register` or `/api/auth/login` and expires in **7 days**.

---

## Error format

All error responses follow this shape:

```json
{ "error": "Human-readable message" }
```

Validation errors (400) return a nested `error.fieldErrors` object from Zod.

| Status | Meaning |
|--------|---------|
| 400 | Validation failed / prerequisite not met |
| 401 | Missing, invalid, or expired JWT |
| 404 | Resource not found |
| 409 | Conflict (e.g. duplicate email) |
| 500 | Unexpected server error (stack trace never exposed) |

---

## Auth — Phase 1

### `POST /api/auth/register`

Creates a new user account. `age`, `gender`, `heightCm`, and `weightKg` are optional at
registration but are required before submitting the health profile.

**Request body**
```json
{
  "name": "Jane Doe",
  "email": "jane@example.com",
  "password": "secret123",
  "age": 28,
  "gender": "FEMALE",
  "heightCm": 165,
  "weightKg": 60
}
```

**Valid `gender` values:** `MALE` | `FEMALE` | `OTHER`

**Response `201`**
```json
{
  "token": "<jwt>",
  "user": { "id": "...", "name": "Jane Doe", "email": "jane@example.com" }
}
```

Errors: `400` (invalid input), `409` (email already registered).

---

### `POST /api/auth/login`

**Request body**
```json
{ "email": "jane@example.com", "password": "secret123" }
```

**Response `200`**
```json
{
  "token": "<jwt>",
  "user": { "id": "...", "name": "Jane Doe", "email": "jane@example.com" }
}
```

Errors: `400` (malformed body), `401` (invalid credentials — same message whether email
unknown or password wrong, to prevent email enumeration).

---

## Health Profile — Phases 2 & 3 — auth required

### `POST /api/health-profile`

Submits (or updates) the fitness questionnaire. The server calculates BMI, BMR, TDEE, and
macro targets deterministically using the Mifflin-St Jeor equation and returns them
immediately. User must have `age`, `gender`, and `heightCm` set on their account first
(supply them at register, or they can be added later via profile update).

**Request body**
```json
{
  "currentWeightKg": 60,
  "targetWeightKg": 55,
  "activityLevel": "MODERATE",
  "fitnessGoal": "WEIGHT_LOSS",
  "dietaryPreference": "VEGETARIAN",
  "allergies": ["dairy"],
  "dailyBudget": 800
}
```

**Valid enum values**

| Field | Values |
|-------|--------|
| `activityLevel` | `SEDENTARY` `LIGHT` `MODERATE` `ACTIVE` `VERY_ACTIVE` |
| `fitnessGoal` | `WEIGHT_LOSS` `WEIGHT_GAIN` `MUSCLE_GAIN` `MAINTENANCE` |
| `dietaryPreference` | `VEGETARIAN` `NON_VEGETARIAN` `VEGAN` |

**Response `201`**
```json
{
  "profile": { "...saved HealthProfile row..." },
  "targets": {
    "bmi": 22.0,
    "bmiCategory": "Normal weight",
    "bmr": 1384,
    "tdee": 2145,
    "calorieTarget": 1645,
    "proteinTargetG": 144,
    "carbTargetG": 144,
    "fatTargetG": 55
  },
  "explanation": "Your daily target of 1645 kcal... (Groq-generated or templated fallback)"
}
```

`explanation` is an optional Groq LLM-generated plain-language summary. It gracefully falls
back to a templated string if `GROQ_API_KEY` is not configured — the request never fails
due to a missing or unavailable LLM.

Errors: `400` (validation or missing age/gender/height), `401`.

---

### `GET /api/health-profile`

Returns the current user's saved health profile.

**Response `200`**
```json
{ "profile": { "...HealthProfile fields..." } }
```

Errors: `401`, `404` (no profile submitted yet).

---

## Meals — Phase 4 — public (no auth)

### `GET /api/meals`

Browse the meal database. All query parameters are optional and can be combined.

**Query params**

| Param | Values | Example |
|-------|--------|---------|
| `mealType` | `BREAKFAST` `LUNCH` `DINNER` `SNACK` | `?mealType=LUNCH` |
| `cuisine` | any string | `?cuisine=South+Indian` |
| `platform` | `SWIGGY` `ZOMATO` | `?platform=ZOMATO` |

Results are sorted by `healthScore` descending, capped at 100.

**Response `200`**
```json
{ "meals": [ { "...Meal fields..." } ] }
```

---

### `GET /api/meals/:id`

Single meal detail.

**Response `200`**
```json
{ "meal": { "...Meal fields..." } }
```

Errors: `404` (meal not found).

---

## Recommendations — Phase 5 — auth required

### `GET /api/recommendations?mealType=LUNCH`

Requires a completed health profile. Splits the user's daily calorie/protein/budget targets
across 4 meals, then scores and ranks every meal of the requested type using the weighted
scoring algorithm (calorie accuracy 35%, protein quality 30%, budget fit 15%, health score
20%). Returns the top 5, including the full score breakdown.

**Query params**

| Param | Default | Values |
|-------|---------|--------|
| `mealType` | `LUNCH` | `BREAKFAST` `LUNCH` `DINNER` `SNACK` |

**Response `200`**
```json
{
  "recommendations": [
    {
      "mealId": "...",
      "score": 92.4,
      "breakdown": {
        "calorieAccuracy": 95.0,
        "proteinQuality": 88.0,
        "budgetFit": 100.0,
        "healthScore": 82.0
      },
      "meal": { "...full Meal object..." }
    }
  ]
}
```

Meals are excluded (not just scored low) if they contain any of the user's declared
allergens, or don't match the user's dietary preference (VEGAN users only see vegan meals;
VEGETARIAN users see vegetarian and vegan meals).

Errors: `400` (no health profile), `401`.

---

## Meal Plans — Phase 3 (weekly plan) — auth required

### `POST /api/meal-plans/generate`

Generates a full 7-day meal plan. For each of the 28 slots (7 days × 4 meal types) the
recommendation engine picks the highest-scoring eligible meal, avoiding the same meal
appearing twice in one day where possible. The plan is persisted and returned.

**Request body:** none.

**Response `201`**
```json
{
  "mealPlan": {
    "id": "...",
    "userId": "...",
    "weekStart": "2024-01-15T00:00:00.000Z",
    "createdAt": "...",
    "items": [
      {
        "id": "...",
        "dayOfWeek": 0,
        "mealType": "BREAKFAST",
        "matchScore": 87.3,
        "meal": { "...full Meal object..." }
      }
    ]
  }
}
```

`dayOfWeek`: 0 = Monday … 6 = Sunday.

Errors: `400` (no health profile), `401`.

---

### `GET /api/meal-plans/current`

Returns the user's most recently generated meal plan with all items and meal details.

**Response `200`**
```json
{ "mealPlan": { "...MealPlan with items[]..." } }
```

Errors: `401`, `404` (no plan generated yet).

---

## Orders — Phase 6 — auth required

> **Important:** Swiggy and Zomato do not provide public order-placement APIs to
> third-party developers. `POST /api/orders` logs the user's intent and returns a **deep
> link** that opens a pre-filled search page on the chosen platform. The user completes
> checkout themselves on Swiggy's or Zomato's own site/app. No real order is ever placed
> or simulated by this backend.

### `POST /api/orders`

**Request body**
```json
{ "mealId": "550e8400-e29b-41d4-a716-446655440000", "platform": "SWIGGY" }
```

`platform`: `SWIGGY` | `ZOMATO`

**Response `201`**
```json
{
  "order": {
    "id": "...",
    "userId": "...",
    "mealId": "...",
    "platform": "SWIGGY",
    "status": "REDIRECTED",
    "createdAt": "..."
  },
  "deepLink": "https://www.swiggy.com/search?query=FreshFit%20Kitchen%20Grilled%20Chicken%20Bowl"
}
```

The `deepLink` URL opens a search on the target platform with the restaurant name and meal
name pre-filled. Open it in a browser or with `url_launcher` in Flutter.

Errors: `400` (invalid input), `401`, `404` (meal not found).

---

### `GET /api/orders`

Returns the current user's order history, most recent first.

**Response `200`**
```json
{ "orders": [ { "...Order fields...", "meal": { "...Meal fields..." } } ] }
```

Errors: `401`.

---

## Progress Tracking — Phase 7 — auth required

### `POST /api/progress`

Logs a daily progress entry. All nutrition fields are optional — a log can record only
weight, only calories, all fields, or any combination.

**Request body**
```json
{
  "weightKg": 59.5,
  "caloriesConsumed": 1800,
  "proteinConsumedG": 90,
  "carbsConsumedG": 200,
  "fatConsumedG": 60,
  "notes": "Felt good today"
}
```

**Response `201`**
```json
{ "log": { "id": "...", "userId": "...", "date": "...", "caloriesConsumed": 1800, "..." } }
```

Errors: `400` (validation — e.g. negative calories), `401`.

---

### `GET /api/progress`

Returns up to 100 most recent progress logs, newest first.

**Response `200`**
```json
{ "logs": [ { "...ProgressLog fields..." } ] }
```

---

### `GET /api/progress/summary`

Returns a weekly nutrition summary and goal achievement percentage.

**Response `200`**
```json
{
  "logs": [ "...last 7 days of logs..." ],
  "weeklyAverageCalories": 1820,
  "goalAchievementPct": 85
}
```

`goalAchievementPct` = `round(avgCalories / TDEE * 100)`, capped at 100.  
Returns `null` if no health profile exists or no logs in the last 7 days.

---

### `GET /api/progress/weight-history`

Returns `{ date, weightKg }` pairs for the last 90 days where a weight was recorded,
ordered oldest → newest. Designed for weight-progress charts on web and mobile.

**Response `200`**
```json
{
  "weightHistory": [
    { "date": "2024-01-10T08:00:00.000Z", "weightKg": 61.2 },
    { "date": "2024-01-13T08:00:00.000Z", "weightKg": 60.8 }
  ]
}
```

Returns an empty array (not 404) if no weight entries exist.

---

## AI Chat — auth required

### `POST /api/chat`

Sends a message to the FitFuel nutrition assistant (powered by Groq's
`llama-3.1-8b-instant`, free tier). The assistant is given a summary of the user's
current health profile as system context so it can give personalised advice.

If `GROQ_API_KEY` is not configured, returns a safe fallback message — the endpoint never
returns a 500 due to a missing or unavailable LLM key.

**Request body**
```json
{ "message": "How much protein should I eat post-workout?" }
```

**Response `200`**
```json
{ "reply": "Based on your MUSCLE_GAIN goal and 200g protein target, aim for 40–50g within 30 minutes post-workout..." }
```

Errors: `400` (missing or empty message), `401`.

---

## Health check

### `GET /health`

No auth required. Used by Render, uptime monitors, and CI smoke tests.

**Response `200`**
```json
{ "status": "ok", "service": "fitfuel-backend", "timestamp": "2024-01-15T10:30:00.000Z" }
```
