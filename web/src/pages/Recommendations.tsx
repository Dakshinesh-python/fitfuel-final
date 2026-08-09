import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Layout from '../components/Layout';
import MealDetailModal from '../components/MealDetailModal';
import { apiClient, extractErrorMessage } from '../api/client';
import {
  MEAL_TYPES,
  MealType,
  OrderPlatform,
  OrderResponse,
  RecommendationItem,
  RecommendationsResponse,
  Meal,
} from '../types';

const MEAL_TYPE_LABELS: Record<MealType, string> = {
  BREAKFAST: 'Breakfast',
  LUNCH: 'Lunch',
  DINNER: 'Dinner',
  SNACK: 'Snack',
};

const MEAL_TYPE_ICONS: Record<MealType, string> = {
  BREAKFAST: 'wb_sunny',
  LUNCH: 'restaurant',
  DINNER: 'nightlight',
  SNACK: 'bakery_dining',
};

function scoreBg(score: number) {
  if (score >= 95) return '#2A9D58';
  if (score >= 80) return '#F59E0B';
  return '#EF4444';
}

function getDietTag(meal: Meal): { label: string; color: string } | null {
  if (meal.isVegan) return { label: 'Vegan', color: '#2A9D58' };
  if (meal.isVegetarian) return { label: 'Veg', color: '#4CAF50' };
  return { label: 'Non-Veg', color: '#EF4444' };
}

// ─── Score mini bar ───────────────────────────────────────────────────────────

function MiniBar({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="flex justify-between mb-1">
        <span className="text-on-surface-variant text-[11px]">{label}</span>
        <span className="text-on-background text-[11px] font-semibold">{Math.round(value)}%</span>
      </div>
      <div className="h-1.5 rounded-full bg-surface-variant overflow-hidden">
        <div
          className="h-full rounded-full"
          style={{ width: `${Math.min(100, value)}%`, background: scoreBg(value) }}
        />
      </div>
    </div>
  );
}

// ─── Meal card ────────────────────────────────────────────────────────────────

function MealCard({
  item,
  orderingId,
  expanded,
  onExpand,
  onViewDetails,
  onOrder,
}: {
  item: RecommendationItem;
  orderingId: string | null;
  expanded: boolean;
  onExpand: () => void;
  onViewDetails: () => void;
  onOrder: (platform: OrderPlatform) => void;
}) {
  const { meal, score, breakdown } = item;
  const dietTag = getDietTag(meal);
  const isBusy = orderingId === meal.id;

  // Dynamic nutrient tags
  const highProtein = meal.proteinG >= 30;
  const lowCalorie = meal.calories <= 400;
  const lowFat = meal.fatG <= 15;

  return (
    <article className="bg-surface border border-outline-variant rounded-2xl overflow-hidden flex flex-col hover:shadow-lg hover:border-primary/30 transition-all duration-300 group">

      {/* ── Image ── */}
      <div className="relative h-48 w-full overflow-hidden bg-surface-variant flex-shrink-0">
        {meal.imageUrl ? (
          <img
            src={meal.imageUrl}
            alt={meal.name}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
            loading="lazy"
            onError={(e) => {
              e.currentTarget.style.display = 'none';
              const fb = e.currentTarget.nextElementSibling as HTMLElement | null;
              if (fb) fb.style.display = 'flex';
            }}
          />
        ) : null}
        <div className="w-full h-full items-center justify-center absolute inset-0" style={{ display: meal.imageUrl ? 'none' : 'flex' }}>
          <span className="material-symbols-outlined text-on-surface-variant text-5xl">restaurant</span>
        </div>

        {/* Gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent" />

        {/* Match score — top right */}
        <div
          className="absolute top-3 right-3 px-2.5 py-1 rounded-full text-white font-bold text-[12px] flex items-center gap-1 shadow-lg"
          style={{ background: scoreBg(score) }}
        >
          <span className="material-symbols-outlined text-[13px]">bolt</span>
          {Math.round(score)}% Match
        </div>

        {/* Diet tag — top left */}
        {dietTag && (
          <div
            className="absolute top-3 left-3 px-2.5 py-1 rounded-full text-white font-semibold text-[11px] shadow"
            style={{ background: dietTag.color }}
          >
            {dietTag.label}
          </div>
        )}

        {/* Bottom: name overlay */}
        <div className="absolute bottom-0 left-0 right-0 px-4 pb-3 pt-8">
          <h3 className="text-white font-bold text-[17px] leading-tight drop-shadow-sm">
            {meal.name}
          </h3>
          <p className="text-white/75 text-[12px] mt-0.5">{meal.restaurant} · {meal.cuisine}</p>
        </div>
      </div>

      {/* ── Body ── */}
      <div className="p-4 flex flex-col flex-1 gap-3">

        {/* Macro chips */}
        <div className="flex flex-wrap gap-1.5">
          {[
            { label: `${meal.calories} kcal`, icon: 'local_fire_department', color: '#F59E0B' },
            { label: `${meal.proteinG}g Pro`, icon: 'fitness_center', color: '#2A9D58' },
            { label: `${meal.carbsG}g Carbs`, icon: 'grain', color: '#3B82F6' },
            { label: `${meal.fatG}g Fat`, icon: 'water_drop', color: '#8B5CF6' },
          ].map(({ label, icon, color }) => (
            <span
              key={label}
              className="flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold text-white"
              style={{ background: color }}
            >
              <span className="material-symbols-outlined text-[12px]">{icon}</span>
              {label}
            </span>
          ))}
          {highProtein && <span className="px-2 py-1 rounded-full bg-emerald-50 text-emerald-700 text-[10px] font-bold border border-emerald-200">HIGH PROTEIN</span>}
          {lowCalorie && <span className="px-2 py-1 rounded-full bg-blue-50 text-blue-700 text-[10px] font-bold border border-blue-200">LOW CAL</span>}
          {lowFat && <span className="px-2 py-1 rounded-full bg-purple-50 text-purple-700 text-[10px] font-bold border border-purple-200">LOW FAT</span>}
        </div>

        {/* Action row: view details + breakdown toggle */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onViewDetails}
            className="flex items-center gap-1 text-primary font-semibold text-[12px] hover:opacity-70 transition-opacity"
          >
            <span className="material-symbols-outlined text-[15px]">open_in_full</span>
            View Details
          </button>
          <span className="w-px h-4 bg-outline-variant" />
          <button
            type="button"
            onClick={onExpand}
            className="flex items-center gap-1 text-on-surface-variant text-[12px] hover:text-on-background transition-colors"
          >
            <span className="material-symbols-outlined text-[15px]">
              {expanded ? 'expand_less' : 'analytics'}
            </span>
            {expanded ? 'Hide breakdown' : 'Why this?'}
          </button>
        </div>

        {/* Breakdown mini bars */}
        {expanded && (
          <div className="bg-surface-variant/50 rounded-xl p-3 grid grid-cols-2 gap-2.5">
            <MiniBar label="Calorie Accuracy" value={breakdown.calorieAccuracy} />
            <MiniBar label="Protein Quality" value={breakdown.proteinQuality} />
            <MiniBar label="Budget Fit" value={breakdown.budgetFit} />
            <MiniBar label="Health Score" value={breakdown.healthScore} />
          </div>
        )}

        {/* Order buttons — pushed to bottom */}
        <div className="mt-auto grid grid-cols-2 gap-2.5 pt-1">
          <button
            id={`order-swiggy-${meal.id}`}
            disabled={isBusy}
            onClick={() => onOrder('SWIGGY')}
            className="flex items-center justify-center gap-1.5 py-2.5 rounded-xl text-white font-bold text-[13px] transition-opacity hover:opacity-90 disabled:opacity-60 active:scale-95"
            style={{ background: '#FC8019' }}
          >
            {isBusy ? (
              <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="white" aria-hidden="true">
                <path d="M12 2C8 7 6 10 6 14a6 6 0 0012 0c0-4-2-7-6-12zm0 16a4 4 0 01-4-4c0-2.5 1.5-5 4-8 2.5 3 4 5.5 4 8a4 4 0 01-4 4z" />
              </svg>
            )}
            Swiggy
          </button>
          <button
            id={`order-zomato-${meal.id}`}
            disabled={isBusy}
            onClick={() => onOrder('ZOMATO')}
            className="flex items-center justify-center gap-1.5 py-2.5 rounded-xl text-white font-bold text-[13px] transition-opacity hover:opacity-90 disabled:opacity-60 active:scale-95"
            style={{ background: '#E23744' }}
          >
            {isBusy ? (
              <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="white" aria-hidden="true">
                <path d="M4 5h16v2.5L8.5 17H20v2H4v-2.5L15.5 7H4V5z" />
              </svg>
            )}
            Zomato
          </button>
        </div>
      </div>
    </article>
  );
}

// ─── Skeleton card ────────────────────────────────────────────────────────────

function SkeletonCard() {
  return (
    <div className="bg-surface border border-outline-variant rounded-2xl overflow-hidden animate-pulse">
      <div className="h-48 bg-surface-variant" />
      <div className="p-4 space-y-3">
        <div className="h-5 bg-surface-variant rounded-full w-3/4" />
        <div className="h-3 bg-surface-variant rounded-full w-1/2" />
        <div className="flex gap-2">
          {[1, 2, 3, 4].map((i) => <div key={i} className="h-6 w-16 bg-surface-variant rounded-full" />)}
        </div>
        <div className="grid grid-cols-2 gap-2 pt-2">
          <div className="h-9 bg-surface-variant rounded-xl" />
          <div className="h-9 bg-surface-variant rounded-xl" />
        </div>
      </div>
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function Recommendations() {
  const navigate = useNavigate();
  const [mealType, setMealType] = useState<MealType>('LUNCH');
  const [items, setItems] = useState<RecommendationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [orderingId, setOrderingId] = useState<string | null>(null);
  const [selectedItem, setSelectedItem] = useState<RecommendationItem | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function loadRecommendations() {
      setLoading(true);
      setError(null);
      try {
        const res = await apiClient.get<RecommendationsResponse>('/api/recommendations', {
          params: { mealType },
        });
        if (!cancelled) setItems(res.data.recommendations);
      } catch (err: unknown) {
        if (axios.isAxiosError(err) && err.response?.status === 400) {
          navigate('/health-assessment', { state: { message: 'Please complete your health assessment first.' } });
          return;
        }
        if (!cancelled) setError(extractErrorMessage(err, 'Unable to load recommendations.'));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    loadRecommendations();
    return () => { cancelled = true; };
  }, [mealType, navigate]);

  async function handleOrder(meal: Meal, platform: OrderPlatform) {
    setOrderingId(meal.id);
    setError(null);
    try {
      const res = await apiClient.post<OrderResponse>('/api/orders', { mealId: meal.id, platform });
      window.open(res.data.deepLink, '_blank');
    } catch (err: unknown) {
      setError(extractErrorMessage(err, 'Unable to start your order. Please try again.'));
    } finally {
      setOrderingId(null);
    }
  }

  return (
    <>
      <Layout title="Recommendations">
        <div className="space-y-6 pb-6">

          {/* ── Hero banner ── */}
          <div
            className="relative overflow-hidden rounded-3xl p-7"
            style={{ background: 'linear-gradient(135deg, #1B5E35 0%, #2A9D58 70%, #38C172 100%)' }}
          >
            <div className="absolute -right-8 -top-8 w-48 h-48 rounded-full bg-white/10" />
            <div className="absolute right-16 bottom-0 w-28 h-28 rounded-full bg-white/5" />
            <p className="text-white/70 text-[13px] font-medium mb-1 relative z-10">Personalised for you</p>
            <h2 className="text-white font-bold relative z-10" style={{ fontSize: '26px' }}>
              Curated Meal Picks 🍽️
            </h2>
            <p className="text-white/65 text-[14px] mt-1 relative z-10 max-w-lg">
              Top-rated meals matched to your macros, budget, and dietary preferences — order directly via Swiggy or Zomato.
            </p>
            {items.length > 0 && (
              <div className="mt-4 flex items-center gap-3 relative z-10">
                <span className="px-3 py-1.5 rounded-full bg-white/20 text-white text-[12px] font-semibold">
                  {items.length} meals found
                </span>
                <span className="px-3 py-1.5 rounded-full bg-white/20 text-white text-[12px] font-semibold">
                  {MEAL_TYPE_LABELS[mealType]}
                </span>
              </div>
            )}
          </div>

          {/* ── Meal type tabs ── */}
          <div className="flex gap-2 flex-wrap">
            {MEAL_TYPES.map((type) => {
              const active = mealType === type;
              return (
                <button
                  key={type}
                  onClick={() => setMealType(type)}
                  className={[
                    'flex items-center gap-1.5 px-4 py-2 rounded-full font-semibold text-[13px] transition-all border',
                    active
                      ? 'bg-primary text-on-primary border-primary shadow-sm'
                      : 'bg-surface text-on-surface-variant border-outline-variant hover:border-primary/40 hover:text-on-background',
                  ].join(' ')}
                >
                  <span className="material-symbols-outlined text-[16px]">{MEAL_TYPE_ICONS[type]}</span>
                  {MEAL_TYPE_LABELS[type]}
                </button>
              );
            })}
          </div>

          {/* ── Error ── */}
          {error && (
            <div className="px-4 py-3 rounded-xl bg-error-container text-on-error-container font-body-sm">
              {error}
            </div>
          )}

          {/* ── Loading skeletons ── */}
          {loading && (
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
              {[1, 2, 3, 4].map((i) => <SkeletonCard key={i} />)}
            </div>
          )}

          {/* ── Empty state ── */}
          {!loading && items.length === 0 && !error && (
            <div className="flex flex-col items-center justify-center py-24 gap-4">
              <span className="material-symbols-outlined text-on-surface-variant text-5xl">restaurant_menu</span>
              <div className="text-center">
                <p className="font-headline-md text-on-background font-semibold">No meals found</p>
                <p className="font-body-sm text-on-surface-variant mt-1">No {MEAL_TYPE_LABELS[mealType].toLowerCase()} recommendations available yet.</p>
              </div>
            </div>
          )}

          {/* ── Cards grid ── */}
          {!loading && items.length > 0 && (
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
              {items.map((item) => (
                <MealCard
                  key={item.mealId}
                  item={item}
                  orderingId={orderingId}
                  expanded={expanded === item.mealId}
                  onExpand={() => setExpanded(expanded === item.mealId ? null : item.mealId)}
                  onViewDetails={() => setSelectedItem(item)}
                  onOrder={(platform) => handleOrder(item.meal, platform)}
                />
              ))}
            </div>
          )}
        </div>
      </Layout>

      {/* Meal detail modal */}
      {selectedItem && (
        <MealDetailModal
          item={selectedItem}
          similar={items.filter((i) => i.mealId !== selectedItem.mealId).slice(0, 4)}
          onClose={() => setSelectedItem(null)}
          onSelectSimilar={(s) => setSelectedItem(s)}
        />
      )}
    </>
  );
}
