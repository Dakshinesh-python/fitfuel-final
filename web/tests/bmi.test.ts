import { describe, it, expect } from 'vitest';
import { calculateBmi, categorizeBmi } from '../src/utils/bmi';

describe('calculateBmi', () => {
  it('calculates BMI for a normal weight case', () => {
    expect(calculateBmi(70, 175)).toBeCloseTo(22.9, 1);
  });

  it('returns 0 for invalid inputs', () => {
    expect(calculateBmi(0, 175)).toBe(0);
    expect(calculateBmi(70, 0)).toBe(0);
  });
});

describe('categorizeBmi', () => {
  it('categorizes underweight', () => {
    expect(categorizeBmi(17)).toBe('Underweight');
  });

  it('categorizes normal weight', () => {
    expect(categorizeBmi(22)).toBe('Normal weight');
  });

  it('categorizes overweight', () => {
    expect(categorizeBmi(27)).toBe('Overweight');
  });

  it('categorizes obese', () => {
    expect(categorizeBmi(32)).toBe('Obese');
  });
});
