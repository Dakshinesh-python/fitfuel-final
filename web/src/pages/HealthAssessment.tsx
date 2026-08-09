import { FormEvent, KeyboardEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient, extractErrorMessage } from '../api/client';
import {
  ACTIVITY_LEVELS,
  DIETARY_PREFERENCES,
  FITNESS_GOALS,
  HealthProfile,
  ActivityLevel,
  FitnessGoal,
  DietaryPreference,
} from '../types';

const GOAL_META: Record<FitnessGoal, { label: string; desc: string; icon: string }> = {
  WEIGHT_LOSS: {
    label: 'Weight Loss',
    desc: 'Caloric deficit focused. Lean proteins, high fiber, and sustained energy.',
    icon: 'trending_down',
  },
  WEIGHT_GAIN: {
    label: 'Weight Gain',
    desc: 'Caloric surplus focused. Nutrient-dense meals to build mass steadily.',
    icon: 'trending_up',
  },
  MUSCLE_GAIN: {
    label: 'Muscle Gain',
    desc: 'Caloric surplus focused. High protein, complex carbs for recovery.',
    icon: 'fitness_center',
  },
  MAINTENANCE: {
    label: 'Maintenance',
    desc: 'Balanced calories to sustain your current weight and performance.',
    icon: 'balance',
  },
};

const ACTIVITY_LABELS: Record<ActivityLevel, string> = {
  SEDENTARY: 'Sedentary — little or no exercise',
  LIGHT: 'Light — exercise 1-3 days/week',
  MODERATE: 'Moderate — exercise 3-5 days/week',
  ACTIVE: 'Active — exercise 6-7 days/week',
  VERY_ACTIVE: 'Very Active — hard daily exercise',
};

const DIET_LABELS: Record<DietaryPreference, string> = {
  VEGETARIAN: 'Vegetarian',
  NON_VEGETARIAN: 'Non-Vegetarian',
  VEGAN: 'Vegan',
};

export default function HealthAssessment() {
  const navigate = useNavigate();
  const [currentWeightKg, setCurrentWeightKg] = useState('');
  const [targetWeightKg, setTargetWeightKg] = useState('');
  const [activityLevel, setActivityLevel] = useState<ActivityLevel>('MODERATE');
  const [fitnessGoal, setFitnessGoal] = useState<FitnessGoal>('WEIGHT_LOSS');
  const [dietaryPreference, setDietaryPreference] = useState<DietaryPreference>('NON_VEGETARIAN');
  const [allergies, setAllergies] = useState<string[]>([]);
  const [allergyInput, setAllergyInput] = useState('');
  const [dailyBudget, setDailyBudget] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<HealthProfile | null>(null);

  function addAllergy() {
    const value = allergyInput.trim();
    if (value && !allergies.includes(value)) {
      setAllergies([...allergies, value]);
    }
    setAllergyInput('');
  }

  function handleAllergyKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      addAllergy();
    }
  }

  function removeAllergy(value: string) {
    setAllergies(allergies.filter((a) => a !== value));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await apiClient.post<HealthProfile>('/api/health-profile', {
        currentWeightKg: Number(currentWeightKg),
        targetWeightKg: Number(targetWeightKg),
        activityLevel,
        fitnessGoal,
        dietaryPreference,
        allergies,
        dailyBudget: Number(dailyBudget),
      });
      setResult(res.data);
    } catch (err: unknown) {
      setError(extractErrorMessage(err, 'Unable to save your health profile. Please try again.'));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-background text-on-background min-h-screen font-body-sm selection:bg-primary-container selection:text-on-primary-container">
      <header className="sticky top-0 z-40 w-full bg-surface/80 backdrop-blur-xl border-b border-outline-variant px-8 h-20 hidden md:flex justify-between items-center">
        <div className="flex items-center gap-4">
          <span className="material-symbols-outlined text-primary text-[32px] fill">
            restaurant_menu
          </span>
          <span className="font-headline-lg text-headline-lg text-primary tracking-tight">
            FitFuel AI
          </span>
        </div>
      </header>

      <main className="max-w-5xl mx-auto p-container-padding-mobile md:p-container-padding-desktop">
        {!result ? (
          <form onSubmit={handleSubmit} className="space-y-12">
            <div>
              <h1 className="font-headline-lg text-headline-lg text-on-background mb-3 tracking-tight">
                Define your approach.
              </h1>
              <p className="font-body-lg text-body-lg text-on-surface-variant">
                Help us tailor your meal plans by sharing your goals, activity level, and
                dietary preferences.
              </p>
            </div>

            {error && (
              <div className="px-4 py-3 rounded-lg bg-error-container text-on-error-container font-body-sm text-body-sm">
                {error}
              </div>
            )}

            {/* Weight Goals */}
            <div className="space-y-4">
              <h2 className="font-headline-md text-headline-md text-on-background border-b border-outline-variant pb-2 inline-block">
                Weight Goals
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-card-gap">
                <div>
                  <label className="block font-label-caps text-label-caps text-on-surface-variant mb-2" htmlFor="currentWeight">
                    Current Weight (kg)
                  </label>
                  <input
                    id="currentWeight"
                    type="number"
                    step="0.1"
                    required
                    value={currentWeightKg}
                    onChange={(e) => setCurrentWeightKg(e.target.value)}
                    className="w-full bg-surface-container-lowest border border-outline-variant rounded-lg py-3 px-4 font-body-sm text-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-colors"
                    placeholder="75"
                  />
                </div>
                <div>
                  <label className="block font-label-caps text-label-caps text-on-surface-variant mb-2" htmlFor="targetWeight">
                    Target Weight (kg)
                  </label>
                  <input
                    id="targetWeight"
                    type="number"
                    step="0.1"
                    required
                    value={targetWeightKg}
                    onChange={(e) => setTargetWeightKg(e.target.value)}
                    className="w-full bg-surface-container-lowest border border-outline-variant rounded-lg py-3 px-4 font-body-sm text-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-colors"
                    placeholder="68"
                  />
                </div>
              </div>
            </div>

            {/* Activity Level */}
            <div className="space-y-4">
              <h2 className="font-headline-md text-headline-md text-on-background border-b border-outline-variant pb-2 inline-block">
                Activity Level
              </h2>
              <select
                aria-label="Activity Level"
                value={activityLevel}
                onChange={(e) => setActivityLevel(e.target.value as ActivityLevel)}
                className="w-full md:w-2/3 bg-surface-container-lowest border border-outline-variant rounded-lg py-3 px-4 font-body-sm text-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-colors"
              >
                {ACTIVITY_LEVELS.map((level) => (
                  <option key={level} value={level}>
                    {ACTIVITY_LABELS[level]}
                  </option>
                ))}
              </select>
            </div>

            {/* Fitness Goal */}
            <div className="space-y-4">
              <h2 className="font-headline-md text-headline-md text-on-background border-b border-outline-variant pb-2 inline-block">
                Primary Goal
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-card-gap">
                {FITNESS_GOALS.map((goal) => {
                  const meta = GOAL_META[goal];
                  const checked = fitnessGoal === goal;
                  return (
                    <label key={goal} className="relative cursor-pointer group">
                      <input
                        type="radio"
                        name="fitness_goal"
                        value={goal}
                        checked={checked}
                        onChange={() => setFitnessGoal(goal)}
                        className="peer sr-only"
                      />
                      <div
                        className={[
                          'h-full p-6 bg-surface-container-lowest border rounded-xl transition-all duration-200',
                          checked
                            ? 'border-primary bg-primary/5 ring-1 ring-primary'
                            : 'border-outline-variant hover:border-outline hover:bg-surface-container-low',
                        ].join(' ')}
                      >
                        <div
                          className={[
                            'w-12 h-12 rounded-full flex items-center justify-center mb-4',
                            checked ? 'bg-primary-container/20' : 'bg-surface-variant',
                          ].join(' ')}
                        >
                          <span
                            className={[
                              'material-symbols-outlined text-[28px]',
                              checked ? 'text-primary fill' : 'text-on-surface-variant',
                            ].join(' ')}
                          >
                            {meta.icon}
                          </span>
                        </div>
                        <h3 className="font-headline-md text-headline-md text-on-background mb-2">
                          {meta.label}
                        </h3>
                        <p className="font-body-sm text-body-sm text-on-surface-variant">
                          {meta.desc}
                        </p>
                        {checked && (
                          <div className="absolute top-4 right-4 text-primary">
                            <span className="material-symbols-outlined fill">check_circle</span>
                          </div>
                        )}
                      </div>
                    </label>
                  );
                })}
              </div>
            </div>

            {/* Dietary Preference */}
            <div className="space-y-4">
              <h2 className="font-headline-md text-headline-md text-on-background border-b border-outline-variant pb-2 inline-block">
                Dietary Preference
              </h2>
              <div className="flex flex-wrap gap-3">
                {DIETARY_PREFERENCES.map((pref) => {
                  const checked = dietaryPreference === pref;
                  return (
                    <label key={pref} className="cursor-pointer">
                      <input
                        type="radio"
                        name="dietary_preference"
                        value={pref}
                        checked={checked}
                        onChange={() => setDietaryPreference(pref)}
                        className="peer sr-only"
                      />
                      <div
                        className={[
                          'px-5 py-2.5 rounded-full border font-label-caps text-label-caps uppercase transition-all',
                          checked
                            ? 'bg-secondary-container text-on-secondary-container border-secondary-container'
                            : 'border-outline-variant bg-surface-container-lowest text-on-surface-variant hover:bg-surface-container-low',
                        ].join(' ')}
                      >
                        {DIET_LABELS[pref]}
                      </div>
                    </label>
                  );
                })}
              </div>
            </div>

            {/* Allergies */}
            <div className="space-y-4">
              <h2 className="font-headline-md text-headline-md text-on-background border-b border-outline-variant pb-2 inline-block">
                Allergies &amp; Restrictions
              </h2>
              <p className="font-body-sm text-body-sm text-on-surface-variant">
                Type an allergy and press Enter to add it.
              </p>
              <div className="flex flex-wrap gap-3 items-center">
                {allergies.map((a) => (
                  <span
                    key={a}
                    className="flex items-center gap-2 px-4 py-2 rounded-full bg-secondary-container/20 text-on-secondary-container font-label-caps text-label-caps uppercase border border-secondary-container/40"
                  >
                    {a}
                    <button
                      type="button"
                      onClick={() => removeAllergy(a)}
                      aria-label={`Remove ${a}`}
                      className="material-symbols-outlined text-[16px] hover:text-error"
                    >
                      close
                    </button>
                  </span>
                ))}
                <input
                  type="text"
                  value={allergyInput}
                  onChange={(e) => setAllergyInput(e.target.value)}
                  onKeyDown={handleAllergyKeyDown}
                  onBlur={addAllergy}
                  placeholder="e.g. Peanuts"
                  className="min-w-[160px] flex-1 bg-surface-container-lowest border border-outline-variant rounded-full py-2 px-4 font-body-sm text-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-colors"
                />
              </div>
            </div>

            {/* Budget */}
            <div className="space-y-4">
              <h2 className="font-headline-md text-headline-md text-on-background border-b border-outline-variant pb-2 inline-block">
                Daily Budget
              </h2>
              <input
                id="dailyBudget"
                type="number"
                step="1"
                required
                value={dailyBudget}
                onChange={(e) => setDailyBudget(e.target.value)}
                className="w-full md:w-1/3 bg-surface-container-lowest border border-outline-variant rounded-lg py-3 px-4 font-body-sm text-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-colors"
                placeholder="500"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full md:w-auto px-10 py-4 bg-primary text-on-primary rounded-full font-headline-md text-headline-md hover:bg-primary-container transition-colors duration-200 disabled:opacity-60"
            >
              {loading ? 'Calculating…' : 'Save & See My Targets'}
            </button>
          </form>
        ) : (
          <div className="space-y-8">
            <div>
              <h1 className="font-headline-lg text-headline-lg text-on-background mb-3 tracking-tight">
                Your personalized targets
              </h1>
              <p className="font-body-lg text-body-lg text-on-surface-variant">
                Here&apos;s what we calculated based on your profile.
              </p>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-gutter">
              <StatCard label="BMI Category" value={result.bmiCategory ?? '—'} icon="monitor_weight" />
              <StatCard label="BMR" value={result.bmr ? `${Math.round(result.bmr)} kcal` : '—'} icon="bolt" />
              <StatCard label="TDEE" value={result.tdee ? `${Math.round(result.tdee)} kcal` : '—'} icon="local_fire_department" />
              <StatCard
                label="Calorie Target"
                value={result.calorieTarget ? `${Math.round(result.calorieTarget)} kcal` : '—'}
                icon="flag"
              />
              <StatCard
                label="Protein"
                value={result.proteinTargetG ? `${Math.round(result.proteinTargetG)}g` : '—'}
                icon="egg"
              />
              <StatCard
                label="Carbs"
                value={result.carbTargetG ? `${Math.round(result.carbTargetG)}g` : '—'}
                icon="grain"
              />
              <StatCard
                label="Fat"
                value={result.fatTargetG ? `${Math.round(result.fatTargetG)}g` : '—'}
                icon="water_drop"
              />
            </div>

            {result.aiExplanation && (
              <div className="p-6 bg-surface-container-lowest border border-outline-variant rounded-xl">
                <h3 className="font-headline-md text-headline-md text-on-background mb-2">
                  Why these numbers?
                </h3>
                <p className="font-body-sm text-body-sm text-on-surface-variant whitespace-pre-line">
                  {result.aiExplanation}
                </p>
              </div>
            )}

            <button
              onClick={() => navigate('/dashboard')}
              className="px-10 py-4 bg-primary text-on-primary rounded-full font-headline-md text-headline-md hover:bg-primary-container transition-colors duration-200"
            >
              Continue to Dashboard
            </button>
          </div>
        )}
      </main>
    </div>
  );
}

function StatCard({ label, value, icon }: { label: string; value: string; icon: string }) {
  return (
    <div className="bg-surface-container-lowest border border-outline-variant rounded-lg p-6 flex flex-col justify-between">
      <div className="flex justify-between items-start mb-4">
        <span className="font-label-caps text-label-caps text-on-surface-variant uppercase">
          {label}
        </span>
        <div className="w-8 h-8 rounded-full bg-primary-container/20 flex items-center justify-center">
          <span className="material-symbols-outlined text-primary text-sm">{icon}</span>
        </div>
      </div>
      <p className="font-headline-lg text-headline-lg text-on-surface">{value}</p>
    </div>
  );
}
