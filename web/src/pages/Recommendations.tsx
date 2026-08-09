import { ReactNode, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Layout from '../components/Layout';
import { apiClient, extractErrorMessage } from '../api/client';
import { MEAL_TYPES, MealType, OrderPlatform, OrderResponse, RecommendedMeal } from '../types';

const MEAL_TYPE_LABELS: Record<MealType, string> = {
  BREAKFAST: 'Breakfast',
  LUNCH: 'Lunch',
  DINNER: 'Dinner',
  SNACK: 'Snack',
};

export default function Recommendations() {
  const navigate = useNavigate();
  const [mealType, setMealType] = useState<MealType>('LUNCH');
  const [meals, setMeals] = useState<RecommendedMeal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [orderingId, setOrderingId] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadMeals() {
      setLoading(true);
      setError(null);
      try {
        const res = await apiClient.get<RecommendedMeal[]>('/api/recommendations', {
          params: { mealType },
        });
        if (!cancelled) {
          setMeals(res.data);
        }
      } catch (err: unknown) {
        if (axios.isAxiosError(err) && err.response?.status === 400) {
          navigate('/health-assessment', {
            state: { message: 'Please complete your health assessment first.' },
          });
          return;
        }
        if (!cancelled) {
          setError(extractErrorMessage(err, 'Unable to load recommendations.'));
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadMeals();
    return () => {
      cancelled = true;
    };
  }, [mealType, navigate]);

  async function handleOrder(meal: RecommendedMeal, platform: OrderPlatform) {
    setOrderingId(meal.id);
    setError(null);
    try {
      const res = await apiClient.post<OrderResponse>('/api/orders', {
        mealId: meal.id,
        platform,
      });
      window.open(res.data.deepLink, '_blank');
    } catch (err: unknown) {
      setError(extractErrorMessage(err, 'Unable to start your order. Please try again.'));
    } finally {
      setOrderingId(null);
    }
  }

  return (
    <Layout title="Curated for You">
      <header className="mb-10">
        <h2 className="font-headline-lg-mobile md:font-headline-lg text-headline-lg text-on-background mb-2">
          Curated for You
        </h2>
        <p className="font-body-lg text-body-lg text-on-surface-variant max-w-2xl">
          Based on your macros and budget, here are top-rated meals available for delivery.
        </p>
      </header>

      {/* Meal Type Tabs */}
      <div className="flex bg-surface-variant rounded-full p-1 w-full max-w-xl mb-8 relative">
        {MEAL_TYPES.map((type) => (
          <button
            key={type}
            onClick={() => setMealType(type)}
            className={[
              'flex-1 py-2 px-4 rounded-full font-body-sm text-body-sm font-medium z-10 transition-all',
              mealType === type
                ? 'bg-surface shadow-ambient text-primary'
                : 'text-on-surface-variant hover:text-on-background',
            ].join(' ')}
          >
            {MEAL_TYPE_LABELS[type]}
          </button>
        ))}
      </div>

      {error && (
        <div className="px-4 py-3 rounded-lg bg-error-container text-on-error-container font-body-sm text-body-sm mb-6">
          {error}
        </div>
      )}

      {loading && (
        <p className="font-body-sm text-body-sm text-on-surface-variant">Loading recommendations…</p>
      )}

      {!loading && meals.length === 0 && !error && (
        <p className="font-body-sm text-body-sm text-on-surface-variant">
          No meals found for this meal type yet.
        </p>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {meals.map((meal) => (
          <article
            key={meal.id}
            className="bg-surface rounded-lg card-border overflow-hidden flex flex-col group hover:ambient-shadow transition-shadow duration-300"
          >
            <div className="relative h-48 w-full overflow-hidden bg-surface-variant">
              {meal.imageUrl ? (
                <img
                  alt={meal.name}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                  src={meal.imageUrl}
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <span className="material-symbols-outlined text-on-surface-variant text-5xl">
                    restaurant
                  </span>
                </div>
              )}
              <div className="absolute top-4 right-4 bg-secondary-container text-on-secondary-container px-3 py-1 rounded-full font-match-score text-match-score flex items-center gap-1 ambient-shadow">
                <span className="material-symbols-outlined text-[16px]">bolt</span>
                {Math.round(meal.matchScore)}% Match
              </div>
            </div>

            <div className="p-6 flex flex-col flex-1">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h3 className="font-headline-md text-headline-md text-on-background">
                    {meal.name}
                  </h3>
                  <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">
                    {meal.restaurant} • {meal.cuisine}
                  </p>
                </div>
                <span className="font-headline-md text-headline-md text-primary">
                  ${meal.price}
                </span>
              </div>

              <div className="flex flex-wrap gap-2 mt-4 mb-4">
                <Tag>{meal.calories} kcal</Tag>
                <Tag>{meal.proteinG}g Protein</Tag>
                <Tag>{meal.carbsG}g Carbs</Tag>
                <Tag>{meal.fatG}g Fat</Tag>
              </div>

              {meal.matchBreakdown && (
                <div className="mb-4">
                  <button
                    type="button"
                    onClick={() => setExpanded(expanded === meal.id ? null : meal.id)}
                    className="font-body-sm text-body-sm text-primary hover:text-primary-container transition-colors flex items-center gap-1"
                  >
                    <span className="material-symbols-outlined text-[18px]">
                      {expanded === meal.id ? 'expand_less' : 'expand_more'}
                    </span>
                    Match breakdown
                  </button>
                  {expanded === meal.id && (
                    <div className="mt-3 grid grid-cols-2 gap-2 text-body-sm font-body-sm text-on-surface-variant">
                      <div>Calorie Accuracy: {meal.matchBreakdown.calorieAccuracy}%</div>
                      <div>Protein Quality: {meal.matchBreakdown.proteinQuality}%</div>
                      <div>Budget Fit: {meal.matchBreakdown.budgetFit}%</div>
                      <div>Health Score: {meal.matchBreakdown.healthScore}%</div>
                    </div>
                  )}
                </div>
              )}

              <p className="font-body-sm text-body-sm text-on-surface-variant mb-3">
                Opens {meal.platform === 'SWIGGY' ? 'Swiggy' : 'Zomato'} search — complete your
                order there.
              </p>

              <div className="mt-auto grid grid-cols-2 gap-3">
                <button
                  disabled={orderingId === meal.id}
                  onClick={() => handleOrder(meal, 'SWIGGY')}
                  className="py-2.5 rounded-full bg-primary text-on-primary font-label-caps text-label-caps hover:bg-primary-container transition-colors disabled:opacity-60"
                >
                  Order on Swiggy
                </button>
                <button
                  disabled={orderingId === meal.id}
                  onClick={() => handleOrder(meal, 'ZOMATO')}
                  className="py-2.5 rounded-full bg-surface border border-outline-variant text-on-background font-label-caps text-label-caps hover:bg-surface-container-low transition-colors disabled:opacity-60"
                >
                  Order on Zomato
                </button>
              </div>
            </div>
          </article>
        ))}
      </div>
    </Layout>
  );
}

function Tag({ children }: { children: ReactNode }) {
  return (
    <span className="px-2 py-1 rounded-full bg-surface-variant text-on-surface-variant font-body-sm text-body-sm">
      {children}
    </span>
  );
}
