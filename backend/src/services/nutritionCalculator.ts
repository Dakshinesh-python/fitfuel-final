/**
 * Core nutrition math for FitFuel.
 * Formulas used are the standard, widely-validated ones:
 * - BMI: weight(kg) / height(m)^2
 * - BMR: Mifflin-St Jeor equation
 * - TDEE: BMR * activity multiplier
 * - Macros: goal-dependent split of TDEE
 */

export type Gender = "MALE" | "FEMALE" | "OTHER";
export type ActivityLevel = "SEDENTARY" | "LIGHT" | "MODERATE" | "ACTIVE" | "VERY_ACTIVE";
export type FitnessGoal = "WEIGHT_LOSS" | "WEIGHT_GAIN" | "MUSCLE_GAIN" | "MAINTENANCE";

const ACTIVITY_MULTIPLIERS: Record<ActivityLevel, number> = {
  SEDENTARY: 1.2,      // little or no exercise
  LIGHT: 1.375,        // light exercise 1-3 days/week
  MODERATE: 1.55,      // moderate exercise 3-5 days/week
  ACTIVE: 1.725,        // hard exercise 6-7 days/week
  VERY_ACTIVE: 1.9,     // very hard exercise + physical job
};

// Calorie adjustment applied on top of TDEE, per goal
const GOAL_CALORIE_ADJUSTMENT: Record<FitnessGoal, number> = {
  WEIGHT_LOSS: -500,   // ~0.5kg/week deficit
  WEIGHT_GAIN: 400,
  MUSCLE_GAIN: 300,
  MAINTENANCE: 0,
};

// Macro split (protein/carbs/fat as % of total calories), per goal
const GOAL_MACRO_SPLIT: Record<FitnessGoal, { protein: number; carbs: number; fat: number }> = {
  WEIGHT_LOSS: { protein: 0.35, carbs: 0.35, fat: 0.3 },
  WEIGHT_GAIN: { protein: 0.25, carbs: 0.5, fat: 0.25 },
  MUSCLE_GAIN: { protein: 0.3, carbs: 0.45, fat: 0.25 },
  MAINTENANCE: { protein: 0.25, carbs: 0.45, fat: 0.3 },
};

export interface UserMetrics {
  weightKg: number;
  heightCm: number;
  age: number;
  gender: Gender;
  activityLevel: ActivityLevel;
  fitnessGoal: FitnessGoal;
}

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

export function calculateBMI(weightKg: number, heightCm: number): number {
  const heightM = heightCm / 100;
  return Number((weightKg / (heightM * heightM)).toFixed(1));
}

export function bmiCategory(bmi: number): string {
  if (bmi < 18.5) return "Underweight";
  if (bmi < 25) return "Normal weight";
  if (bmi < 30) return "Overweight";
  return "Obese";
}

export function calculateBMR(weightKg: number, heightCm: number, age: number, gender: Gender): number {
  // Mifflin-St Jeor
  const base = 10 * weightKg + 6.25 * heightCm - 5 * age;
  if (gender === "MALE") return Math.round(base + 5);
  if (gender === "FEMALE") return Math.round(base - 161);
  // OTHER: average of male/female offsets
  return Math.round(base - 78);
}

export function calculateTDEE(bmr: number, activityLevel: ActivityLevel): number {
  return Math.round(bmr * ACTIVITY_MULTIPLIERS[activityLevel]);
}

export function calculateNutritionTargets(metrics: UserMetrics): NutritionTargets {
  const bmi = calculateBMI(metrics.weightKg, metrics.heightCm);
  const bmr = calculateBMR(metrics.weightKg, metrics.heightCm, metrics.age, metrics.gender);
  const tdee = calculateTDEE(bmr, metrics.activityLevel);

  const adjustment = GOAL_CALORIE_ADJUSTMENT[metrics.fitnessGoal];
  const calorieTarget = Math.max(1200, tdee + adjustment); // never recommend below 1200 kcal

  const split = GOAL_MACRO_SPLIT[metrics.fitnessGoal];
  // protein & carbs = 4 kcal/g, fat = 9 kcal/g
  const proteinTargetG = Math.round((calorieTarget * split.protein) / 4);
  const carbTargetG = Math.round((calorieTarget * split.carbs) / 4);
  const fatTargetG = Math.round((calorieTarget * split.fat) / 9);

  return {
    bmi,
    bmiCategory: bmiCategory(bmi),
    bmr,
    tdee,
    calorieTarget,
    proteinTargetG,
    carbTargetG,
    fatTargetG,
  };
}
