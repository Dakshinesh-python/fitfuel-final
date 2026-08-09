export type BmiCategory = 'Underweight' | 'Normal weight' | 'Overweight' | 'Obese';

/**
 * Calculates BMI given weight in kilograms and height in centimeters.
 * Mirrors the backend's BMI formula exactly: weight(kg) / (height(m))^2
 */
export function calculateBmi(weightKg: number, heightCm: number): number {
  if (weightKg <= 0 || heightCm <= 0) {
    return 0;
  }
  const heightM = heightCm / 100;
  const bmi = weightKg / (heightM * heightM);
  return Math.round(bmi * 10) / 10;
}

export function categorizeBmi(bmi: number): BmiCategory {
  if (bmi < 18.5) return 'Underweight';
  if (bmi < 25) return 'Normal weight';
  if (bmi < 30) return 'Overweight';
  return 'Obese';
}
