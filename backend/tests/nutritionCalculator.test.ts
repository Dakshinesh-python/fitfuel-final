import {
  calculateBMI,
  bmiCategory,
  calculateBMR,
  calculateTDEE,
  calculateNutritionTargets,
} from "../src/services/nutritionCalculator";

describe("calculateBMI", () => {
  it("computes BMI correctly", () => {
    // 70kg, 175cm -> 70 / 1.75^2 = 22.9
    expect(calculateBMI(70, 175)).toBeCloseTo(22.9, 1);
  });
});

describe("bmiCategory", () => {
  it.each([
    [17, "Underweight"],
    [22, "Normal weight"],
    [27, "Overweight"],
    [32, "Obese"],
  ])("classifies BMI %i as %s", (bmi, expected) => {
    expect(bmiCategory(bmi)).toBe(expected);
  });
});

describe("calculateBMR", () => {
  it("computes BMR for a male using Mifflin-St Jeor", () => {
    // 70kg, 175cm, 25yo male: 10*70 + 6.25*175 - 5*25 + 5 = 700+1093.75-125+5=1673.75 -> 1674
    expect(calculateBMR(70, 175, 25, "MALE")).toBe(1674);
  });

  it("computes BMR for a female using Mifflin-St Jeor", () => {
    // 60kg, 165cm, 30yo female: 10*60+6.25*165-5*30-161 = 600+1031.25-150-161=1320.25 -> 1320
    expect(calculateBMR(60, 165, 30, "FEMALE")).toBe(1320);
  });
});

describe("calculateTDEE", () => {
  it("applies the activity multiplier", () => {
    expect(calculateTDEE(1600, "SEDENTARY")).toBe(1920);
    expect(calculateTDEE(1600, "MODERATE")).toBe(2480);
  });
});

describe("calculateNutritionTargets", () => {
  it("never recommends below 1200 kcal even on aggressive cuts", () => {
    const targets = calculateNutritionTargets({
      weightKg: 45,
      heightCm: 150,
      age: 20,
      gender: "FEMALE",
      activityLevel: "SEDENTARY",
      fitnessGoal: "WEIGHT_LOSS",
    });
    expect(targets.calorieTarget).toBeGreaterThanOrEqual(1200);
  });

  it("produces macro grams whose calories roughly sum to the target", () => {
    const targets = calculateNutritionTargets({
      weightKg: 80,
      heightCm: 180,
      age: 28,
      gender: "MALE",
      activityLevel: "MODERATE",
      fitnessGoal: "MUSCLE_GAIN",
    });
    const macroCalories =
      targets.proteinTargetG * 4 + targets.carbTargetG * 4 + targets.fatTargetG * 9;
    expect(Math.abs(macroCalories - targets.calorieTarget)).toBeLessThan(30);
  });
});
