// ─── Enums & constants ───────────────────────────────────────────────────────

export type ActivityLevel = 'SEDENTARY' | 'LIGHT' | 'MODERATE' | 'ACTIVE' | 'VERY_ACTIVE';
export type FitnessGoal = 'WEIGHT_LOSS' | 'WEIGHT_GAIN' | 'MUSCLE_GAIN' | 'MAINTENANCE';
export type DietaryPreference = 'VEGETARIAN' | 'NON_VEGETARIAN' | 'VEGAN';
export type MealType = 'BREAKFAST' | 'LUNCH' | 'DINNER' | 'SNACK';
export type OrderPlatform = 'SWIGGY' | 'ZOMATO';

export const ACTIVITY_LEVELS: ActivityLevel[] = [
  'SEDENTARY',
  'LIGHT',
  'MODERATE',
  'ACTIVE',
  'VERY_ACTIVE',
];

export const FITNESS_GOALS: FitnessGoal[] = [
  'WEIGHT_LOSS',
  'WEIGHT_GAIN',
  'MUSCLE_GAIN',
  'MAINTENANCE',
];

export const DIETARY_PREFERENCES: DietaryPreference[] = ['VEGETARIAN', 'NON_VEGETARIAN', 'VEGAN'];

export const MEAL_TYPES: MealType[] = ['BREAKFAST', 'LUNCH', 'DINNER', 'SNACK'];

// ─── Auth ────────────────────────────────────────────────────────────────────

export interface User {
  id: string;
  name: string;
  email: string;
  age?: number;
  gender?: string;
  heightCm?: number;
  weightKg?: number;
}

export interface AuthResponse {
  token: string;
  user: User;
}

// ─── Health Profile ──────────────────────────────────────────────────────────

/** Raw HealthProfile row returned by GET /api/health-profile → { profile } */
export interface HealthProfile {
  id: string;
  userId: string;
  currentWeightKg: number;
  targetWeightKg: number;
  activityLevel: ActivityLevel;
  fitnessGoal: FitnessGoal;
  dietaryPreference: DietaryPreference;
  allergies: string[];
  dailyBudget: number;
  /** Stored on the profile row after the first POST /api/health-profile */
  bmi?: number;
  bmr?: number;
  tdee?: number;
  proteinTargetG?: number;
  carbTargetG?: number;
  fatTargetG?: number;
  /**
   * calorieTarget is computed from TDEE + goal adjustment (see nutritionCalculator.ts).
   * It is NOT stored in the DB — only returned in the POST response under 'targets'.
   * The Dashboard derives it from tdee + goal lookup, or shows — if not yet set.
   * NOTE: bmiCategory is NOT stored in the DB — compute it from bmi using bmi.ts.
   */
}

/** Computed nutrition targets returned in the POST /api/health-profile response */
export interface NutritionTargets {
  bmi: number;
  bmiCategory: string;
  bmr: number;
  tdee: number;
  calorieTarget: number;
  proteinTargetG: number;
  carbTargetG: number;
  fatTargetG: number;
}

/** Full response from POST /api/health-profile */
export interface HealthProfileResponse {
  profile: HealthProfile;
  targets: NutritionTargets;
  explanation: string | null;
}

// ─── Meals & Recommendations ─────────────────────────────────────────────────

/** A meal record from the database (used in GET /api/meals and embedded in recommendations) */
export interface Meal {
  id: string;
  name: string;
  restaurant: string;
  cuisine: string;
  mealType: MealType;
  calories: number;
  proteinG: number;
  carbsG: number;
  fatG: number;
  price: number;
  platform: OrderPlatform;
  healthScore: number;
  isVegetarian: boolean;
  isVegan: boolean;
  allergens: string[];
  imageUrl?: string;       // optional: Unsplash CDN URL; null/undefined = show fallback
  deepLinkQuery: string;
}

/** Score breakdown from the recommendation engine */
export interface MatchBreakdown {
  calorieAccuracy: number;
  proteinQuality: number;
  budgetFit: number;
  healthScore: number;
}

/**
 * A single recommendation item as returned by GET /api/recommendations.
 * Backend shape: { mealId, score, breakdown, meal }
 */
export interface RecommendationItem {
  mealId: string;
  score: number;
  breakdown: MatchBreakdown;
  meal: Meal;
}

/** Full response from GET /api/recommendations */
export interface RecommendationsResponse {
  recommendations: RecommendationItem[];
}

// ─── Orders ───────────────────────────────────────────────────────────────────

/** Full response from POST /api/orders */
export interface OrderResponse {
  order: {
    id: string;
    userId: string;
    mealId: string;
    platform: OrderPlatform;
    status: string;
    createdAt: string;
  };
  deepLink: string;
}

// ─── Progress ────────────────────────────────────────────────────────────────

export interface ProgressEntry {
  id?: string;
  date?: string;
  weightKg?: number;
  caloriesConsumed?: number;
  proteinConsumedG?: number;
  carbsConsumedG?: number;
  fatConsumedG?: number;
  notes?: string;
}

/** Response from GET /api/progress → { logs } */
export interface ProgressLogsResponse {
  logs: ProgressEntry[];
}

/**
 * Response from GET /api/progress/summary.
 * NOTE: weightHistory is NOT included here — it comes from a separate call
 * to GET /api/progress/weight-history.
 */
export interface ProgressSummary {
  logs: ProgressEntry[];
  weeklyAverageCalories: number;
  /**
   * Average calories / TDEE * 100, capped at 100.
   * Null when no health profile exists or no logs in the last 7 days.
   */
  goalAchievementPct: number | null;
}

/** A single entry from GET /api/progress/weight-history */
export interface WeightHistoryEntry {
  date: string;
  weightKg: number;
}

/** Response from GET /api/progress/weight-history → { weightHistory } */
export interface WeightHistoryResponse {
  weightHistory: WeightHistoryEntry[];
}
