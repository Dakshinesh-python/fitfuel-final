import { useEffect, useState, useCallback } from 'react';
import Layout from '../components/Layout';
import { apiClient, extractErrorMessage } from '../api/client';
import { MealType, Meal } from '../types';

// ─── Types ────────────────────────────────────────────────────────────────────

interface MealPlanItem {
  id: string;
  dayOfWeek: number; // 0=Mon … 6=Sun
  mealType: MealType;
  matchScore: number;
  meal: Meal;
}

interface MealPlan {
  id: string;
  weekStart: string;
  items: MealPlanItem[];
}

// ─── Constants ────────────────────────────────────────────────────────────────

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const MEAL_ROWS: MealType[] = ['BREAKFAST', 'LUNCH', 'SNACK', 'DINNER'];
const ROW_LABELS: Record<MealType, string> = {
  BREAKFAST: 'Breakfast',
  LUNCH: 'Lunch',
  SNACK: 'Snack',
  DINNER: 'Dinner',
};

// ─── Score badge color ────────────────────────────────────────────────────────

function scoreBg(score: number): string {
  if (score >= 95) return '#2A9D58'; // green
  if (score >= 80) return '#F4A261'; // amber
  return '#E76F51'; // coral
}

// ─── Meal cell ────────────────────────────────────────────────────────────────

function MealCell({
  item,
  loading,
}: {
  item?: MealPlanItem;
  loading?: boolean;
}) {
  const CELL_H = 'h-28';

  if (loading) {
    return (
      <div className={`rounded-xl border border-dashed border-outline-variant bg-surface-variant ${CELL_H} flex items-center justify-center`}>
        <span className="font-body-sm text-on-surface-variant text-[11px] animate-pulse">Loading…</span>
      </div>
    );
  }

  if (!item) {
    return (
      <div className={`rounded-xl border border-dashed border-outline-variant bg-surface/40 ${CELL_H}`} />
    );
  }

  const score = Math.round(item.matchScore);
  const { meal } = item;

  return (
    <div
      className={`relative rounded-xl overflow-hidden ${CELL_H} group hover:ring-2 hover:ring-primary/50 transition-all cursor-default`}
      title={meal.name}
    >
      {/* Background image */}
      {meal.imageUrl ? (
        <img
          src={meal.imageUrl}
          alt={meal.name}
          className="absolute inset-0 w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          loading="lazy"
        />
      ) : (
        <div className="absolute inset-0 bg-surface-variant flex items-center justify-center">
          <span className="material-symbols-outlined text-on-surface-variant text-3xl">restaurant</span>
        </div>
      )}

      {/* Dark gradient so text is always readable */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />

      {/* Score badge — top right */}
      <span
        className="absolute top-1.5 right-1.5 px-1.5 py-0.5 rounded-full text-white font-bold text-[10px] leading-none"
        style={{ background: scoreBg(score) }}
      >
        {score}%
      </span>

      {/* Name + calories — bottom */}
      <div className="absolute bottom-0 left-0 right-0 px-2 pb-2 pt-4">
        <p className="text-white font-semibold text-[11px] leading-tight line-clamp-2">
          {meal.name}
        </p>
        <p className="text-white/70 text-[10px] mt-0.5">{meal.calories} kcal</p>
      </div>
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function MealPlan() {
  const [plan, setPlan] = useState<MealPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCurrent = useCallback(async () => {
    try {
      const res = await apiClient.get('/api/meal-plans/current');
      setPlan(res.data.mealPlan);
      setError(null);
    } catch {
      setPlan(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchCurrent(); }, [fetchCurrent]);

  async function handleGenerate() {
    setGenerating(true);
    setError(null);
    try {
      const res = await apiClient.post('/api/meal-plans/generate', {});
      setPlan(res.data.mealPlan);
    } catch (e) {
      setError(extractErrorMessage(e, 'Could not generate meal plan. Complete your health assessment first.'));
    } finally {
      setGenerating(false);
    }
  }

  function handleDownload() {
    if (!plan) return;

    const lines: string[] = ['FitFuel — Weekly Meal Plan', '='.repeat(40), ''];
    for (const [dayIdx, day] of DAYS.entries()) {
      lines.push(day);
      for (const mealType of MEAL_ROWS) {
        const item = plan.items.find((i) => i.dayOfWeek === dayIdx && i.mealType === mealType);
        if (item) {
          lines.push(
            `  ${ROW_LABELS[mealType].padEnd(12)} ${item.meal.name} (${item.meal.calories} kcal, ${Math.round(item.matchScore)}% match)`,
          );
        }
      }
      lines.push('');
    }

    const blob = new Blob([lines.join('\n')], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'fitfuel-meal-plan.txt';
    a.click();
    URL.revokeObjectURL(url);
  }

  // Build a lookup: dayIndex → mealType → item
  const grid = new Map<number, Map<MealType, MealPlanItem>>();
  for (let d = 0; d < 7; d++) grid.set(d, new Map());
  if (plan) {
    for (const item of plan.items) {
      grid.get(item.dayOfWeek)?.set(item.mealType, item);
    }
  }

  return (
    <Layout title="Weekly Meal Plan">
      <div className="space-y-6 pb-6">

      {/* ── Hero banner ── */}
      <div
        className="relative overflow-hidden rounded-3xl p-7 flex flex-col sm:flex-row sm:items-center justify-between gap-6"
        style={{ background: 'linear-gradient(135deg, #2d1b69 0%, #5b21b6 60%, #7c3aed 100%)' }}
      >
        <div className="absolute -right-8 -top-8 w-48 h-48 rounded-full bg-white/10" />
        <div className="absolute right-16 bottom-0 w-28 h-28 rounded-full bg-white/5" />
        <div className="relative z-10">
          <p className="text-white/70 text-[13px] font-medium mb-1">AI-powered · 7 days</p>
          <h2 className="text-white font-bold" style={{ fontSize: '26px' }}>Weekly Meal Plan </h2>
          <p className="text-white/60 text-[14px] mt-1">Optimized for your macro goals and flavor profile.</p>
        </div>
        <div className="flex gap-3 relative z-10 flex-shrink-0">
          <button
            id="meal-plan-regenerate"
            onClick={handleGenerate}
            disabled={generating}
            className="flex items-center gap-2 px-5 py-2.5 rounded-full text-white font-semibold text-[13px] transition-all disabled:opacity-60 hover:bg-white/20"
            style={{ background: 'rgba(255,255,255,0.15)', border: '1px solid rgba(255,255,255,0.25)' }}
          >
            <span className={`material-symbols-outlined text-[17px] ${generating ? 'animate-spin' : ''}`}>refresh</span>
            {generating ? 'Generating…' : 'Regenerate'}
          </button>
          <button
            id="meal-plan-download"
            onClick={handleDownload}
            disabled={!plan}
            className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-white text-violet-700 font-bold text-[13px] hover:opacity-90 transition-opacity disabled:opacity-40"
          >
            <span className="material-symbols-outlined text-[17px]">download</span>
            Download
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-error-container text-on-error-container font-body-sm">
          {error}
        </div>
      )}

      {/* Empty state */}
      {!loading && !plan && !generating && (
        <div className="flex flex-col items-center justify-center py-20 gap-5 bg-surface border border-outline-variant rounded-2xl">
          <div className="w-16 h-16 rounded-2xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #5b21b6, #7c3aed)' }}>
            <span className="material-symbols-outlined text-white text-3xl">calendar_month</span>
          </div>
          <div className="text-center">
            <p className="font-bold text-on-background text-[18px]">No meal plan yet</p>
            <p className="font-body-sm text-on-surface-variant mt-1 max-w-xs">
              Generate a personalized 7-day plan tailored to your nutrition goals.
            </p>
          </div>
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="flex items-center gap-2 px-6 py-3 rounded-full text-white font-bold text-[14px] hover:opacity-90 transition-opacity disabled:opacity-60"
            style={{ background: 'linear-gradient(135deg, #5b21b6, #7c3aed)' }}
          >
            <span className="material-symbols-outlined text-[18px]">auto_awesome</span>
            Generate My Plan
          </button>
        </div>
      )}

      {/* Grid */}
      {(plan || loading || generating) && (
        <div className="overflow-x-auto rounded-2xl border border-outline-variant bg-surface">
          <table className="w-full border-collapse" style={{ minWidth: 700 }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(0,0,0,0.06)' }}>
                <th className="w-20 p-3" />
                {DAYS.map((day) => (
                  <th key={day} className="pt-4 pb-3 px-1 text-center">
                    <span className="inline-flex flex-col items-center w-full py-2 px-1 rounded-xl text-[12px] font-bold text-on-surface-variant">
                      {day}
                    </span>
                  </th>
                ))}
              </tr>
            </thead>

            <tbody>
              {MEAL_ROWS.map((mealType, rowIdx) => {
                const rowColors: Record<string, { icon: string; color: string }> = {
                  BREAKFAST: { icon: 'wb_sunny', color: '#F59E0B' },
                  LUNCH:     { icon: 'restaurant', color: '#2A9D58' },
                  SNACK:     { icon: 'bakery_dining', color: '#8B5CF6' },
                  DINNER:    { icon: 'nightlight', color: '#3B82F6' },
                };
                const rc = rowColors[mealType];
                return (
                  <tr
                    key={mealType}
                    style={{
                      borderTop: rowIdx > 0 ? '1px solid rgba(0,0,0,0.05)' : undefined,
                    }}
                  >
                    {/* Row label */}
                    <td className="p-3 pr-2 align-middle">
                      <div className="flex flex-col items-center gap-1">
                        <span
                          className="material-symbols-outlined text-[16px]"
                          style={{ color: rc.color }}
                        >
                          {rc.icon}
                        </span>
                        <span
                          className="text-[10px] font-bold uppercase tracking-wide"
                          style={{ color: rc.color }}
                        >
                          {ROW_LABELS[mealType]}
                        </span>
                      </div>
                    </td>

                    {DAYS.map((_, dayIdx) => {
                      const item = grid.get(dayIdx)?.get(mealType);
                      const isLoadingCell = (loading || generating) && !item;
                      return (
                        <td key={dayIdx} className="pb-3 px-1 align-top pt-2">
                          <MealCell item={item} loading={isLoadingCell} />
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Legend */}
      {plan && (
        <div className="bg-surface border border-outline-variant rounded-2xl px-5 py-4 flex flex-wrap items-center gap-5">
          <span className="font-bold text-on-background text-[13px]">Match Score:</span>
          {[
            { color: '#2A9D58', label: '≥95% Excellent' },
            { color: '#F59E0B', label: '80–94% Good' },
            { color: '#EF4444', label: '<80% Fair' },
          ].map(({ color, label }) => (
            <div key={label} className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full flex-shrink-0" style={{ background: color }} />
              <span className="text-on-surface-variant text-[13px]">{label}</span>
            </div>
          ))}
        </div>
      )}

      </div>
    </Layout>
  );
}
