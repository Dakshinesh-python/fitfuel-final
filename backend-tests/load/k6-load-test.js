/**
 * k6 load test for the FitFuel backend.
 *
 * Complements test_performance.py (which does light-concurrency smoke
 * checks inside pytest) with real sustained-load characterization:
 * requests/sec, error rate, and p95/p99 latency under ramping concurrent
 * users. Run this separately from the pytest suite.
 *
 * Install k6: https://grafana.com/docs/k6/latest/set-up/install-k6/
 *
 * Usage:
 *   BASE_URL=http://localhost:4000 k6 run load/k6-load-test.js
 *
 * Scenarios (see bottom of file):
 *   - smoke:   1 VU, 30s   -- confirms the script itself works
 *   - baseline: ramps 0->20 VUs over 2m, holds 3m, ramps down 1m
 *   - stress:  ramps 0->100 VUs over 3m, holds 3m, ramps down 1m
 *              (opt-in: set SCENARIO=stress)
 *
 * Every VU registers its own account at the start of its lifetime (no
 * pre-seeded demo accounts exist in this repo -- see backend-inventory.md)
 * then exercises a realistic mix of read-heavy and write endpoints.
 */
import http from "k6/http";
import { check, sleep } from "k6";
import { Counter, Trend } from "k6/metrics";

const BASE_URL = __ENV.BASE_URL || "http://localhost:4000";
const API = `${BASE_URL}/api`;

const registrationFailures = new Counter("registration_failures");
const authFailures = new Counter("auth_failures");
const mealPlanGenDuration = new Trend("meal_plan_generation_duration", true);
const recommendationsDuration = new Trend("recommendations_duration", true);

function uniqueEmail() {
  return `k6-${__VU}-${__ITER}-${Date.now()}@backendtests.local`;
}

function registerUser() {
  const payload = JSON.stringify({
    name: `Load Test VU${__VU}`,
    email: uniqueEmail(),
    password: "validpass1",
    age: 28,
    gender: "FEMALE",
    heightCm: 165,
    weightKg: 60,
  });
  const res = http.post(`${API}/auth/register`, payload, {
    headers: { "Content-Type": "application/json" },
    tags: { name: "register" },
  });
  const ok = check(res, { "register: 201": (r) => r.status === 201 });
  if (!ok) {
    registrationFailures.add(1);
    return null;
  }
  const body = res.json();
  return { token: body.token, headers: { Authorization: `Bearer ${body.token}`, "Content-Type": "application/json" } };
}

function submitHealthProfile(user) {
  const payload = JSON.stringify({
    currentWeightKg: 60,
    targetWeightKg: 57,
    activityLevel: "MODERATE",
    fitnessGoal: "WEIGHT_LOSS",
    dietaryPreference: "NON_VEGETARIAN",
    allergies: [],
    dailyBudget: 500,
  });
  const res = http.post(`${API}/health-profile`, payload, { headers: user.headers, tags: { name: "health-profile" } });
  check(res, { "health-profile: 201": (r) => r.status === 201 });
}

export default function () {
  const user = registerUser();
  if (!user) {
    sleep(1);
    return;
  }

  submitHealthProfile(user);

  // Read-heavy: browse the meal catalog
  const meals = http.get(`${API}/meals`, { tags: { name: "meals-list" } });
  check(meals, { "meals: 200": (r) => r.status === 200 });
  sleep(0.3);

  // Recommendations (heavier: scores up to 200 candidates)
  const recStart = Date.now();
  const recs = http.get(`${API}/recommendations?mealType=LUNCH`, { headers: user.headers, tags: { name: "recommendations" } });
  recommendationsDuration.add(Date.now() - recStart);
  check(recs, { "recommendations: 200": (r) => r.status === 200 });
  sleep(0.3);

  // Heaviest single request: generate a 7-day meal plan
  const planStart = Date.now();
  const plan = http.post(`${API}/meal-plans/generate`, null, { headers: user.headers, tags: { name: "meal-plan-generate" } });
  mealPlanGenDuration.add(Date.now() - planStart);
  check(plan, { "meal-plan-generate: 201": (r) => r.status === 201 });
  sleep(0.5);

  // Auth check under load
  const me = http.get(`${API}/auth/me`, { headers: user.headers, tags: { name: "me" } });
  const meOk = check(me, { "me: 200": (r) => r.status === 200 });
  if (!meOk) authFailures.add(1);

  // A write-heavy action: place an order against the first listed meal
  if (meals.status === 200) {
    const mealId = meals.json().meals[0] && meals.json().meals[0].id;
    if (mealId) {
      const order = http.post(
        `${API}/orders`,
        JSON.stringify({ mealId, platform: "SWIGGY" }),
        { headers: user.headers, tags: { name: "order-create" } }
      );
      check(order, { "order: 201": (r) => r.status === 201 });
    }
  }

  // Log a progress entry
  const progress = http.post(
    `${API}/progress`,
    JSON.stringify({ weightKg: 59.5, caloriesConsumed: 1900 }),
    { headers: user.headers, tags: { name: "progress-create" } }
  );
  check(progress, { "progress: 201": (r) => r.status === 201 });

  sleep(1);
}

const SCENARIO = __ENV.SCENARIO || "baseline";

const scenarios = {
  smoke: {
    executor: "constant-vus",
    vus: 1,
    duration: "30s",
  },
  baseline: {
    executor: "ramping-vus",
    startVUs: 0,
    stages: [
      { duration: "2m", target: 20 },
      { duration: "3m", target: 20 },
      { duration: "1m", target: 0 },
    ],
  },
  stress: {
    executor: "ramping-vus",
    startVUs: 0,
    stages: [
      { duration: "3m", target: 100 },
      { duration: "3m", target: 100 },
      { duration: "1m", target: 0 },
    ],
  },
};

export const options = {
  scenarios: { [SCENARIO]: scenarios[SCENARIO] },
  thresholds: {
    http_req_failed: ["rate<0.05"], // <5% error rate
    http_req_duration: ["p(95)<3000", "p(99)<6000"],
    registration_failures: ["count<10"],
    auth_failures: ["count<5"],
  },
};
