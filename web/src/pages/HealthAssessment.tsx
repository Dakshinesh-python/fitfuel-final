import { FormEvent, KeyboardEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient, extractErrorMessage } from '../api/client';
import {
  ACTIVITY_LEVELS,
  DIETARY_PREFERENCES,
  FITNESS_GOALS,
  HealthProfileResponse,
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
  const [result, setResult] = useState<HealthProfileResponse | null>(null);

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
      // Backend returns { profile, targets, explanation } — not a flat HealthProfile.
      const res = await apiClient.post<HealthProfileResponse>('/api/health-profile', {
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
          <form onSubmit={handleSubmit} className="max-w-4xl mx-auto space-y-8 animate-in fade-in duration-500">
            <div className="text-center mb-10">
              <h1 className="font-headline-lg text-headline-lg text-on-background mb-4 tracking-tight">
                Define your approach
              </h1>
              <p className="font-body-lg text-body-lg text-on-surface-variant max-w-2xl mx-auto">
                Help us tailor your meal plans by sharing your goals, activity level, and dietary preferences.
              </p>
            </div>

            {error && (
              <div className="px-5 py-4 rounded-xl bg-error-container/50 border border-error/20 text-on-error-container font-body-sm flex items-center gap-3">
                <span className="material-symbols-outlined text-error">error</span>
                {error}
              </div>
            )}

            <div className="bg-surface-container-lowest rounded-3xl shadow-ambient border border-outline-variant/30 overflow-hidden">
              
              {/* Weight Goals Section */}
              <div className="p-8 md:p-10 border-b border-outline-variant/30 bg-gradient-to-b from-surface-container-lowest to-surface-container-low/30">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                    <span className="material-symbols-outlined">monitor_weight</span>
                  </div>
                  <h2 className="font-headline-md text-headline-md text-on-background">
                    Body Metrics
                  </h2>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="group">
                    <label className="block font-label-caps text-[13px] text-on-surface-variant mb-2 group-focus-within:text-primary transition-colors" htmlFor="currentWeight">
                      Current Weight (kg)
                    </label>
                    <div className="relative">
                      <input
                        id="currentWeight"
                        type="number"
                        step="0.1"
                        required
                        value={currentWeightKg}
                        onChange={(e) => setCurrentWeightKg(e.target.value)}
                        className="w-full bg-surface-container-lowest border border-outline-variant/60 rounded-xl py-3.5 pl-4 pr-12 font-body-lg text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all shadow-sm"
                        placeholder="75"
                      />
                      <span className="absolute right-4 top-1/2 -translate-y-1/2 text-on-surface-variant/50 font-medium select-none pointer-events-none">
                        kg
                      </span>
                    </div>
                  </div>
                  <div className="group">
                    <label className="block font-label-caps text-[13px] text-on-surface-variant mb-2 group-focus-within:text-primary transition-colors" htmlFor="targetWeight">
                      Target Weight (kg)
                    </label>
                    <div className="relative">
                      <input
                        id="targetWeight"
                        type="number"
                        step="0.1"
                        required
                        value={targetWeightKg}
                        onChange={(e) => setTargetWeightKg(e.target.value)}
                        className="w-full bg-surface-container-lowest border border-outline-variant/60 rounded-xl py-3.5 pl-4 pr-12 font-body-lg text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all shadow-sm"
                        placeholder="68"
                      />
                      <span className="absolute right-4 top-1/2 -translate-y-1/2 text-on-surface-variant/50 font-medium select-none pointer-events-none">
                        kg
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Activity Level Section */}
              <div className="p-8 md:p-10 border-b border-outline-variant/30">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                    <span className="material-symbols-outlined">directions_run</span>
                  </div>
                  <h2 className="font-headline-md text-headline-md text-on-background">
                    Activity Level
                  </h2>
                </div>
                <div className="relative group">
                  <select
                    aria-label="Activity Level"
                    value={activityLevel}
                    onChange={(e) => setActivityLevel(e.target.value as ActivityLevel)}
                    className="w-full appearance-none bg-surface-container-lowest border border-outline-variant/60 rounded-xl py-4 pl-5 pr-12 font-body-lg text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all shadow-sm cursor-pointer"
                  >
                    {ACTIVITY_LEVELS.map((level) => (
                      <option key={level} value={level}>
                        {ACTIVITY_LABELS[level]}
                      </option>
                    ))}
                  </select>
                  <span className="material-symbols-outlined absolute right-4 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none group-hover:text-primary transition-colors">
                    expand_more
                  </span>
                </div>
              </div>

              {/* Fitness Goal Section */}
              <div className="p-8 md:p-10 border-b border-outline-variant/30 bg-gradient-to-b from-surface-container-lowest to-surface-container-low/30">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                    <span className="material-symbols-outlined">track_changes</span>
                  </div>
                  <h2 className="font-headline-md text-headline-md text-on-background">
                    Primary Goal
                  </h2>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
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
                            'h-full p-6 rounded-2xl transition-all duration-300 border-2',
                            checked
                              ? 'border-primary bg-primary/5 shadow-md scale-[1.02]'
                              : 'border-outline-variant/30 bg-surface-container-lowest hover:border-primary/40 hover:bg-surface hover:scale-[1.01]',
                          ].join(' ')}
                        >
                          <div className="flex items-start justify-between mb-4">
                            <div
                              className={[
                                'w-12 h-12 rounded-xl flex items-center justify-center transition-colors duration-300',
                                checked ? 'bg-primary text-on-primary shadow-sm' : 'bg-surface-variant text-on-surface-variant group-hover:bg-primary/10 group-hover:text-primary',
                              ].join(' ')}
                            >
                              <span className="material-symbols-outlined text-[24px]">
                                {meta.icon}
                              </span>
                            </div>
                            <div className={[
                              'w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all',
                              checked ? 'border-primary bg-primary' : 'border-outline-variant'
                            ].join(' ')}>
                              {checked && <span className="material-symbols-outlined text-[16px] text-on-primary">check</span>}
                            </div>
                          </div>
                          <h3 className="font-headline-md text-headline-md text-on-background mb-2">
                            {meta.label}
                          </h3>
                          <p className="font-body-sm text-[13px] leading-relaxed text-on-surface-variant/80">
                            {meta.desc}
                          </p>
                        </div>
                      </label>
                    );
                  })}
                </div>
              </div>

              {/* Dietary Preference Section */}
              <div className="p-8 md:p-10 border-b border-outline-variant/30">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                    <span className="material-symbols-outlined">set_meal</span>
                  </div>
                  <h2 className="font-headline-md text-headline-md text-on-background">
                    Dietary Preference
                  </h2>
                </div>
                <div className="flex flex-wrap gap-3">
                  {DIETARY_PREFERENCES.map((pref) => {
                    const checked = dietaryPreference === pref;
                    return (
                      <label key={pref} className="cursor-pointer group">
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
                            'px-6 py-3 rounded-xl border-2 font-label-caps uppercase transition-all duration-300 font-bold tracking-wider',
                            checked
                              ? 'bg-primary border-primary text-on-primary shadow-md scale-105'
                              : 'border-outline-variant/30 bg-surface-container-lowest text-on-surface-variant hover:border-primary/40 hover:bg-primary/5 hover:text-primary',
                          ].join(' ')}
                        >
                          {DIET_LABELS[pref]}
                        </div>
                      </label>
                    );
                  })}
                </div>
              </div>

              {/* Allergies & Budget Section */}
              <div className="p-8 md:p-10 grid grid-cols-1 md:grid-cols-2 gap-10">
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                      <span className="material-symbols-outlined">medical_information</span>
                    </div>
                    <h2 className="font-headline-md text-headline-md text-on-background">
                      Allergies & Restrictions
                    </h2>
                  </div>
                  <p className="font-body-sm text-[13px] text-on-surface-variant/80 mb-4 pl-13">
                    Type an allergy and press Enter to add it.
                  </p>
                  <div className="flex flex-wrap gap-2 items-center">
                    {allergies.map((a) => (
                      <span
                        key={a}
                        className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-error/10 text-error font-label-caps text-label-caps uppercase border border-error/20 shadow-sm animate-in zoom-in-95 duration-200"
                      >
                        {a}
                        <button
                          type="button"
                          onClick={() => removeAllergy(a)}
                          aria-label={`Remove ${a}`}
                          className="material-symbols-outlined text-[16px] hover:text-error-container-on hover:scale-110 transition-transform"
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
                      placeholder="e.g. Peanuts, Gluten"
                      className="min-w-[160px] flex-1 bg-surface-container-lowest border border-outline-variant/60 rounded-xl py-3 px-4 font-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all shadow-sm"
                    />
                  </div>
                </div>

                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                      <span className="material-symbols-outlined">payments</span>
                    </div>
                    <h2 className="font-headline-md text-headline-md text-on-background">
                      Daily Budget
                    </h2>
                  </div>
                  <p className="font-body-sm text-[13px] text-on-surface-variant/80 mb-4 pl-13">
                    Target maximum cost per day (INR).
                  </p>
                  <div className="relative">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-on-surface-variant font-medium select-none pointer-events-none">
                      ₹
                    </span>
                    <input
                      id="dailyBudget"
                      type="number"
                      step="1"
                      required
                      value={dailyBudget}
                      onChange={(e) => setDailyBudget(e.target.value)}
                      className="w-full bg-surface-container-lowest border border-outline-variant/60 rounded-xl py-3 pl-9 pr-4 font-body-lg text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all shadow-sm"
                      placeholder="500"
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-4">
              <button
                type="submit"
                disabled={loading}
                className="group relative inline-flex items-center justify-center gap-3 w-full md:w-auto px-10 py-4 bg-primary text-on-primary rounded-full font-headline-md hover:bg-primary/90 hover:shadow-lg hover:-translate-y-0.5 transition-all duration-300 disabled:opacity-60 disabled:hover:translate-y-0 disabled:hover:shadow-none overflow-hidden"
              >
                <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300 ease-in-out" />
                <span className="relative z-10">{loading ? 'Calculating Targets...' : 'Save & See My Targets'}</span>
                {!loading && (
                  <span className="material-symbols-outlined relative z-10 transition-transform group-hover:translate-x-1">
                    arrow_forward
                  </span>
                )}
              </button>
            </div>
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
              <StatCard label="BMI Category" value={result.targets.bmiCategory} icon="monitor_weight" />
              <StatCard label="BMR" value={`${Math.round(result.targets.bmr)} kcal`} icon="bolt" />
              <StatCard label="TDEE" value={`${Math.round(result.targets.tdee)} kcal`} icon="local_fire_department" />
              <StatCard
                label="Calorie Target"
                value={`${Math.round(result.targets.calorieTarget)} kcal`}
                icon="flag"
              />
              <StatCard
                label="Protein"
                value={`${Math.round(result.targets.proteinTargetG)}g`}
                icon="egg"
              />
              <StatCard
                label="Carbs"
                value={`${Math.round(result.targets.carbTargetG)}g`}
                icon="grain"
              />
              <StatCard
                label="Fat"
                value={`${Math.round(result.targets.fatTargetG)}g`}
                icon="water_drop"
              />
            </div>

            {/* AI explanation — may be null if GROQ_API_KEY is not set; handle gracefully */}
            {result.explanation && (
              <div className="p-6 bg-surface-container-lowest border border-outline-variant rounded-xl">
                <h3 className="font-headline-md text-headline-md text-on-background mb-2">
                  Why these numbers?
                </h3>
                <p className="font-body-sm text-body-sm text-on-surface-variant whitespace-pre-line">
                  {result.explanation}
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
