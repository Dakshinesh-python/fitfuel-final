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

export interface HealthProfile {
  id?: string;
  currentWeightKg: number;
  targetWeightKg: number;
  activityLevel: ActivityLevel;
  fitnessGoal: FitnessGoal;
  dietaryPreference: DietaryPreference;
  allergies: string[];
  dailyBudget: number;
  bmi?: number;
  bmiCategory?: string;
  bmr?: number;
  tdee?: number;
  calorieTarget?: number;
  proteinTargetG?: number;
  carbTargetG?: number;
  fatTargetG?: number;
  aiExplanation?: string;
}

export interface MatchBreakdown {
  calorieAccuracy: number;
  proteinQuality: number;
  budgetFit: number;
  healthScore: number;
}

export interface RecommendedMeal {
  id: string;
  name: string;
  restaurant: string;
  cuisine: string;
  calories: number;
  proteinG: number;
  carbsG: number;
  fatG: number;
  price: number;
  platform: OrderPlatform;
  matchScore: number;
  matchBreakdown?: MatchBreakdown;
  imageUrl?: string;
}

export interface OrderResponse {
  id: string;
  deepLink: string;
  platform: OrderPlatform;
}

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

export interface ProgressSummary {
  weeklyAverageCalories: number;
  goalAchievementPercent: number;
  weightHistory: { date: string; weightKg: number }[];
}
