# FitFuel Backend API Reference

Base URL (local): `http://localhost:4000`
Base URL (production): your deployed Render URL, e.g. `https://fitfuel-backend.onrender.com`

All authenticated endpoints require an `Authorization: Bearer <token>` header, where the
token is returned from `/api/auth/register` or `/api/auth/login`.

---

## Auth (Phase 1)

### POST `/api/auth/register`
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
Returns `{ token, user }`.

### POST `/api/auth/login`
```json
{ "email": "jane@example.com", "password": "secret123" }
```
Returns `{ token, user }`.

---

## Health Profile (Phase 2 + 3) — auth required

### POST `/api/health-profile`
Submits the fitness questionnaire; server calculates and returns BMI/BMR/TDEE/macros.
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
Returns `{ profile, targets, explanation }` — `explanation` is the optional Groq-generated
plain-language summary (falls back to a templated string if `GROQ_API_KEY` isn't set).

### GET `/api/health-profile`
Returns the current user's saved profile.

---

## Meals (Phase 4) — public

### GET `/api/meals?mealType=LUNCH&cuisine=Indian&platform=SWIGGY`
All filters optional. Returns `{ meals: [...] }` sorted by health score.

### GET `/api/meals/:id`
Single meal detail.

---

## Recommendations (Phase 5) — auth required

### GET `/api/recommendations?mealType=LUNCH`
Requires a completed health profile. Returns the top 5 scored meals:
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
        "healthScore": 82
      },
      "meal": { "...full meal object..." }
    }
  ]
}
```

---

## Orders (Phase 6) — auth required

### POST `/api/orders`
```json
{ "mealId": "...", "platform": "SWIGGY" }
```
Logs the order intent and returns a deep link:
```json
{
  "order": { "...": "..." },
  "deepLink": "https://www.swiggy.com/search?query=..."
}
```
**Note:** this opens a search on the platform — it does not place a real order, since
Swiggy/Zomato don't expose public ordering APIs to third-party apps.

### GET `/api/orders`
Returns the current user's order history.

---

## Progress (Phase 7) — auth required

### POST `/api/progress`
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

### GET `/api/progress`
Full log history (most recent first).

### GET `/api/progress/summary`
Weekly average calories + goal achievement percentage vs. TDEE.

---

## Health check

### GET `/health`
No auth. Returns `{ status: "ok" }` — used by Render/uptime checks.
