import { useEffect, useCallback } from 'react';
import { RecommendationItem, OrderPlatform, OrderResponse } from '../types';
import { apiClient, extractErrorMessage } from '../api/client';
import { useState } from 'react';

// ─── Donut chart (pure SVG/CSS, no chart lib needed) ─────────────────────────

function DonutChart({ protein, carbs, fat, calories }: { protein: number; carbs: number; fat: number; calories: number }) {
  const total = protein + carbs + fat || 1;
  const proteinPct = (protein / total) * 100;
  const carbsPct = (carbs / total) * 100;

  // Build conic-gradient segments
  const gradient = `conic-gradient(
    #2A9D58 0% ${proteinPct}%,
    #E76F51 ${proteinPct}% ${proteinPct + carbsPct}%,
    #ADB5BD ${proteinPct + carbsPct}% 100%
  )`;

  return (
    <div className="flex items-center gap-6">
      {/* Donut */}
      <div className="relative w-24 h-24 flex-shrink-0">
        <div
          className="w-24 h-24 rounded-full"
          style={{ background: gradient }}
        />
        {/* Hole */}
        <div className="absolute inset-3 rounded-full bg-surface flex flex-col items-center justify-center">
          <span className="font-headline-md text-on-background leading-none" style={{ fontSize: '16px', fontWeight: 700 }}>
            {calories}
          </span>
          <span className="font-body-sm text-on-surface-variant text-[10px]">KCAL</span>
        </div>
      </div>

      {/* Legend */}
      <div className="flex flex-col gap-2.5 flex-1">
        {[
          { label: 'Protein', value: protein, color: '#2A9D58' },
          { label: 'Carbs', value: carbs, color: '#E76F51' },
          { label: 'Fats', value: fat, color: '#ADB5BD' },
        ].map(({ label, value, color }) => (
          <div key={label} className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: color }} />
              <span className="font-body-sm text-on-surface-variant">{label}</span>
            </div>
            <span className="font-body-md font-semibold text-on-background">{value}g</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Allergen chip ─────────────────────────────────────────────────────────────

function AllergenChip({ label, warn }: { label: string; warn?: boolean }) {
  return (
    <span
      className={`flex items-center gap-1 px-3 py-1 rounded-full font-label-caps text-[11px] border ${
        warn
          ? 'border-error/40 bg-error/10 text-error'
          : 'border-outline-variant bg-surface-variant text-on-surface-variant'
      }`}
    >
      {warn && <span className="material-symbols-outlined text-[13px]">warning</span>}
      {label.toUpperCase()}
    </span>
  );
}

// ─── Ingredient line ──────────────────────────────────────────────────────────

function Ingredient({ label }: { label: string }) {
  return (
    <li className="flex items-center gap-2 font-body-sm text-on-background">
      <span className="material-symbols-outlined text-primary text-[16px]">check_circle</span>
      {label}
    </li>
  );
}

// ─── Similar card ─────────────────────────────────────────────────────────────

function SimilarCard({ item, onClick }: { item: RecommendationItem; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="relative rounded-xl overflow-hidden w-48 h-32 flex-shrink-0 group border border-outline-variant hover:border-primary transition-colors"
    >
      {item.meal.imageUrl ? (
        <img
          src={item.meal.imageUrl}
          alt={item.meal.name}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
        />
      ) : (
        <div className="w-full h-full bg-surface-variant flex items-center justify-center">
          <span className="material-symbols-outlined text-on-surface-variant text-3xl">restaurant</span>
        </div>
      )}
      <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
      <div className="absolute top-2 left-2">
        <span className="px-2 py-0.5 rounded-full bg-secondary-container text-on-secondary-container font-label-caps text-[10px]">
          {Math.round(item.score)}% Match
        </span>
      </div>
    </button>
  );
}

// ─── Main Modal ───────────────────────────────────────────────────────────────

interface MealDetailModalProps {
  item: RecommendationItem;
  similar: RecommendationItem[];
  onClose: () => void;
  onSelectSimilar: (item: RecommendationItem) => void;
}

export default function MealDetailModal({ item, similar, onClose, onSelectSimilar }: MealDetailModalProps) {
  const { meal, score, breakdown } = item;
  const [orderingId, setOrderingId] = useState<string | null>(null);
  const [orderError, setOrderError] = useState<string | null>(null);

  // Close on Escape key
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose();
    }
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [onClose]);

  // Prevent body scroll while open
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = ''; };
  }, []);

  const handleOrder = useCallback(async (platform: OrderPlatform) => {
    setOrderingId(platform);
    setOrderError(null);
    try {
      const res = await apiClient.post<OrderResponse>('/api/orders', { mealId: meal.id, platform });
      window.open(res.data.deepLink, '_blank');
    } catch (e) {
      setOrderError(extractErrorMessage(e, 'Could not open order page. Please try again.'));
    } finally {
      setOrderingId(null);
    }
  }, [meal.id]);

  // Build pseudo-ingredients from meal data (real meals in seed don't have an ingredients field)
  const pseudoIngredients = [
    meal.cuisine && `${meal.cuisine} style preparation`,
    `Approx. ${meal.proteinG}g protein serving`,
    meal.isVegetarian ? 'Vegetarian preparation' : null,
    meal.isVegan ? 'Vegan ingredients' : null,
    `Available on ${meal.platform === 'SWIGGY' ? 'Swiggy' : 'Zomato'}`,
  ].filter(Boolean) as string[];

  // Dynamic tags based on meal data
  const tags: string[] = [];
  if (meal.proteinG >= 30) tags.push('HIGH PROTEIN');
  if (meal.isVegan) tags.push('VEGAN');
  else if (meal.isVegetarian) tags.push('VEGETARIAN');
  if (meal.fatG <= 15) tags.push('LOW FAT');
  if (meal.calories <= 400) tags.push('LOW CALORIE');
  if (meal.carbsG <= 30) tags.push('LOW CARB');
  if (tags.length === 0) tags.push('BALANCED');

  return (
    /* Backdrop */
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: 'rgba(0,0,0,0.55)', backdropFilter: 'blur(4px)' }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
      role="dialog"
      aria-modal="true"
      aria-label={meal.name}
    >
      {/* Sheet */}
      <div className="bg-surface rounded-3xl shadow-2xl w-full max-w-3xl max-h-[92vh] overflow-y-auto relative">

        {/* ── Top section: image + header info ── */}
        <div className="flex flex-col md:flex-row">
          {/* Left — image */}
          <div className="relative md:w-2/5 h-56 md:h-auto flex-shrink-0">
            {meal.imageUrl ? (
              <img
                src={meal.imageUrl}
                alt={meal.name}
                className="w-full h-full object-cover md:rounded-l-3xl rounded-t-3xl md:rounded-tr-none"
              />
            ) : (
              <div className="w-full h-full bg-surface-variant flex items-center justify-center md:rounded-l-3xl rounded-t-3xl md:rounded-tr-none">
                <span className="material-symbols-outlined text-on-surface-variant text-6xl">restaurant</span>
              </div>
            )}
            {/* Match badge */}
            <div
              className="absolute top-4 left-4 px-3 py-1.5 rounded-full font-label-caps text-white text-[12px] font-bold shadow-lg"
              style={{ background: score >= 95 ? '#2A9D58' : score >= 80 ? '#F4A261' : '#E76F51' }}
            >
              {Math.round(score)}% Match
            </div>
          </div>

          {/* Right — info */}
          <div className="flex-1 p-6 flex flex-col">
            {/* Close */}
            <button
              id="meal-detail-close"
              onClick={onClose}
              className="absolute top-4 right-4 w-9 h-9 rounded-full bg-surface-variant flex items-center justify-center hover:bg-surface-container-high transition-colors"
              aria-label="Close"
            >
              <span className="material-symbols-outlined text-on-surface-variant text-[18px]">close</span>
            </button>

            {/* Tags */}
            <div className="flex flex-wrap gap-2 mb-3 mt-2">
              {tags.map((t) => (
                <span
                  key={t}
                  className="px-2.5 py-0.5 rounded-full bg-primary-container text-on-primary-container font-label-caps text-[10px]"
                >
                  {t}
                </span>
              ))}
            </div>

            {/* Name */}
            <h2 className="font-headline-md text-on-background mb-2" style={{ fontSize: '22px', fontWeight: 700 }}>
              {meal.name}
            </h2>

            {/* Description */}
            <p className="font-body-sm text-on-surface-variant mb-5 leading-relaxed">
              {meal.cuisine} cuisine ·{' '}
              {meal.isVegan ? 'Vegan' : meal.isVegetarian ? 'Vegetarian' : 'Non-vegetarian'}
            </p>

            {/* Order buttons */}
            <p className="font-label-caps text-label-caps text-on-surface-variant mb-3 text-[11px] tracking-widest">
              ORDER NOW VIA
            </p>
            <div className="flex gap-3 mb-3">
              <button
                id="modal-order-swiggy"
                onClick={() => handleOrder('SWIGGY')}
                disabled={!!orderingId}
                className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-full border border-outline-variant text-on-background font-label-caps text-label-caps hover:border-[#FC8019] hover:text-[#FC8019] transition-colors disabled:opacity-60"
              >
                {orderingId === 'SWIGGY' ? (
                  <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                ) : (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                    <path d="M12 2C8 7 6 10 6 14a6 6 0 0012 0c0-4-2-7-6-12z" />
                  </svg>
                )}
                Swiggy
              </button>
              <button
                id="modal-order-zomato"
                onClick={() => handleOrder('ZOMATO')}
                disabled={!!orderingId}
                className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-full border border-outline-variant text-on-background font-label-caps text-label-caps hover:border-[#E23744] hover:text-[#E23744] transition-colors disabled:opacity-60"
              >
                {orderingId === 'ZOMATO' ? (
                  <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                ) : (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                    <path d="M4 5h16v2.5L8.5 17H20v2H4v-2.5L15.5 7H4V5z" />
                  </svg>
                )}
                Zomato
              </button>
            </div>
            {orderError && <p className="font-body-sm text-error text-[12px]">{orderError}</p>}
          </div>
        </div>

        {/* ── Body sections ── */}
        <div className="p-6 pt-0 flex flex-col md:flex-row gap-6">

          {/* Left column */}
          <div className="flex-1 flex flex-col gap-5">
            {/* Why we recommend */}
            <div className="rounded-2xl border border-outline-variant bg-surface-container-lowest p-5">
              <h3 className="flex items-center gap-2 font-headline-md text-on-background mb-3" style={{ fontSize: '16px' }}>
                <span className="material-symbols-outlined text-primary text-[18px]">auto_awesome</span>
                Why we recommend this
              </h3>
              <p className="font-body-sm text-on-surface-variant leading-relaxed">
                Based on your current macro goals, this meal aligns well with your{' '}
                <strong className="text-on-background">{Math.round(breakdown.proteinQuality)}% protein quality</strong> and{' '}
                <strong className="text-on-background">{Math.round(breakdown.calorieAccuracy)}% calorie accuracy</strong> targets.
                It fits within your daily budget with a{' '}
                <strong className="text-on-background">{Math.round(breakdown.budgetFit)}% budget score</strong>, and its health
                score of <strong className="text-on-background">{Math.round(breakdown.healthScore)}%</strong> makes it one of our
                top picks for your profile.
              </p>
            </div>

            {/* Nutritional profile */}
            <div>
              <h3 className="font-headline-md text-on-background mb-4" style={{ fontSize: '16px' }}>
                Nutritional Profile
              </h3>
              <DonutChart
                protein={meal.proteinG}
                carbs={meal.carbsG}
                fat={meal.fatG}
                calories={meal.calories}
              />
            </div>
          </div>

          {/* Right column */}
          <div className="md:w-56 flex flex-col gap-5">
            {/* Allergens */}
            <div>
              <h3 className="font-headline-md text-on-background mb-3" style={{ fontSize: '16px' }}>
                Allergens &amp; Dietary
              </h3>
              <div className="flex flex-wrap gap-2">
                {meal.allergens.length > 0
                  ? meal.allergens.map((a) => <AllergenChip key={a} label={a} warn />)
                  : <AllergenChip label="No known allergens" />}
                {meal.isVegetarian && <AllergenChip label="Vegetarian" />}
                {meal.isVegan && <AllergenChip label="Vegan" />}
                {!meal.isVegetarian && <AllergenChip label="Contains Meat" warn />}
              </div>
            </div>

            {/* Key ingredients */}
            <div>
              <h3 className="font-headline-md text-on-background mb-3" style={{ fontSize: '16px' }}>
                Key Ingredients
              </h3>
              <ul className="flex flex-col gap-2">
                {pseudoIngredients.map((ing) => (
                  <Ingredient key={ing} label={ing} />
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* ── Similar recommendations ── */}
        {similar.length > 0 && (
          <div className="px-6 pb-6 border-t border-outline-variant pt-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-headline-md text-on-background" style={{ fontSize: '16px' }}>
                Similar Recommendations
              </h3>
              <span className="font-label-caps text-label-caps text-primary text-[12px]">VIEW ALL</span>
            </div>
            <div className="flex gap-3 overflow-x-auto pb-2">
              {similar.map((s) => (
                <SimilarCard
                  key={s.mealId}
                  item={s}
                  onClick={() => onSelectSimilar(s)}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
