import { FormEvent, useEffect, useState } from 'react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import Layout from '../components/Layout';
import { apiClient, extractErrorMessage } from '../api/client';
import {
  ProgressEntry,
  ProgressLogsResponse,
  ProgressSummary,
  WeightHistoryEntry,
  WeightHistoryResponse,
} from '../types';

// ─── Stat card ────────────────────────────────────────────────────────────────

function StatCard({
  label,
  value,
  sub,
  icon,
  gradient,
}: {
  label: string;
  value: string;
  sub?: string;
  icon: string;
  gradient: string;
}) {
  return (
    <div
      className="relative overflow-hidden rounded-2xl p-5 flex flex-col gap-3"
      style={{ background: gradient }}
    >
      <div className="absolute -right-4 -top-4 w-20 h-20 rounded-full bg-white/10" />
      <div className="w-9 h-9 rounded-xl bg-white/20 flex items-center justify-center flex-shrink-0">
        <span className="material-symbols-outlined text-white text-[18px]">{icon}</span>
      </div>
      <div>
        <p className="text-white/70 text-[11px] font-medium uppercase tracking-wider">{label}</p>
        <p className="text-white font-bold leading-tight mt-0.5" style={{ fontSize: '26px' }}>{value}</p>
        {sub && <p className="text-white/60 text-[12px] mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}

// ─── Field ────────────────────────────────────────────────────────────────────

function Field({
  id,
  label,
  value,
  onChange,
  icon,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (v: string) => void;
  icon: string;
}) {
  return (
    <div className="group">
      <label
        htmlFor={id}
        className="block font-label-caps text-label-caps text-on-surface-variant mb-2 text-[11px] uppercase tracking-wider"
      >
        {label}
      </label>
      <div className="relative">
        <span className="absolute left-3 top-1/2 -translate-y-1/2 material-symbols-outlined text-on-surface-variant text-[16px]">
          {icon}
        </span>
        <input
          id={id}
          type="number"
          step="0.1"
          min="0"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full bg-surface border border-outline-variant rounded-xl py-3 pl-9 pr-3 font-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all placeholder:text-on-surface-variant/40"
          placeholder="0"
        />
      </div>
    </div>
  );
}

// ─── Custom tooltip ───────────────────────────────────────────────────────────

function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: { value: number }[]; label?: string }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-surface border border-outline-variant rounded-xl px-3 py-2 shadow-xl">
      <p className="font-label-caps text-on-surface-variant text-[11px]">
        {label ? new Date(label).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' }) : ''}
      </p>
      <p className="font-headline-md text-on-background font-bold text-[16px]">
        {payload[0].value} kg
      </p>
    </div>
  );
}

// ─── Entry row ────────────────────────────────────────────────────────────────

function EntryRow({ entry, idx }: { entry: ProgressEntry; idx: number }) {
  const chips: { label: string; value: string; color: string }[] = [
    ...(entry.caloriesConsumed ? [{ label: 'Cal', value: `${entry.caloriesConsumed} kcal`, color: '#F59E0B' }] : []),
    ...(entry.proteinConsumedG ? [{ label: 'Pro', value: `${entry.proteinConsumedG}g`, color: '#2A9D58' }] : []),
    ...(entry.carbsConsumedG ? [{ label: 'Carb', value: `${entry.carbsConsumedG}g`, color: '#3B82F6' }] : []),
    ...(entry.fatConsumedG ? [{ label: 'Fat', value: `${entry.fatConsumedG}g`, color: '#EF4444' }] : []),
  ];

  return (
    <div className={`flex flex-col sm:flex-row sm:items-center gap-3 p-4 rounded-2xl border border-outline-variant hover:border-primary/40 hover:bg-surface-container-low transition-all ${idx % 2 === 0 ? 'bg-surface' : 'bg-surface/60'}`}>
      {/* Date + weight */}
      <div className="flex items-center gap-3 min-w-[140px]">
        <div className="w-10 h-10 rounded-xl bg-primary-container flex items-center justify-center flex-shrink-0">
          <span className="material-symbols-outlined text-on-primary-container text-[16px]">calendar_today</span>
        </div>
        <div>
          <p className="font-body-md font-semibold text-on-background text-[13px]">
            {entry.date ? new Date(entry.date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: '2-digit' }) : '—'}
          </p>
          {entry.weightKg && (
            <p className="font-body-sm text-on-surface-variant text-[12px]">{entry.weightKg} kg</p>
          )}
        </div>
      </div>

      {/* Macro chips */}
      <div className="flex flex-wrap gap-2 flex-1">
        {chips.length > 0 ? chips.map(({ label, value, color }) => (
          <span
            key={label}
            className="px-2.5 py-1 rounded-full font-label-caps text-white text-[11px] font-semibold"
            style={{ background: color }}
          >
            {value}
          </span>
        )) : (
          <span className="font-body-sm text-on-surface-variant text-[12px]">No macros logged</span>
        )}
      </div>

      {/* Notes */}
      {entry.notes && (
        <p className="font-body-sm text-on-surface-variant text-[12px] italic max-w-[180px] truncate" title={entry.notes}>
          "{entry.notes}"
        </p>
      )}
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function Progress() {
  const [weightKg, setWeightKg] = useState('');
  const [caloriesConsumed, setCaloriesConsumed] = useState('');
  const [proteinConsumedG, setProteinConsumedG] = useState('');
  const [carbsConsumedG, setCarbsConsumedG] = useState('');
  const [fatConsumedG, setFatConsumedG] = useState('');
  const [notes, setNotes] = useState('');
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState(false);

  const [summary, setSummary] = useState<ProgressSummary | null>(null);
  const [entries, setEntries] = useState<ProgressEntry[]>([]);
  const [weightHistory, setWeightHistory] = useState<WeightHistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  async function loadData() {
    setLoading(true);
    setLoadError(null);
    try {
      const [summaryRes, entriesRes, weightHistoryRes] = await Promise.all([
        apiClient.get<ProgressSummary>('/api/progress/summary'),
        apiClient.get<ProgressLogsResponse>('/api/progress'),
        apiClient.get<WeightHistoryResponse>('/api/progress/weight-history'),
      ]);
      setSummary(summaryRes.data);
      setEntries(entriesRes.data.logs);
      setWeightHistory(weightHistoryRes.data.weightHistory);
    } catch (err: unknown) {
      setLoadError(extractErrorMessage(err, 'Unable to load your progress data.'));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadData(); }, []);

  function resetForm() {
    setWeightKg(''); setCaloriesConsumed(''); setProteinConsumedG('');
    setCarbsConsumedG(''); setFatConsumedG(''); setNotes('');
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setFormError(null);
    const hasAnyValue = weightKg || caloriesConsumed || proteinConsumedG || carbsConsumedG || fatConsumedG;
    if (!hasAnyValue) { setFormError('Please fill at least one value before logging.'); return; }

    setSubmitting(true);
    try {
      await apiClient.post('/api/progress', {
        weightKg: weightKg ? Number(weightKg) : undefined,
        caloriesConsumed: caloriesConsumed ? Number(caloriesConsumed) : undefined,
        proteinConsumedG: proteinConsumedG ? Number(proteinConsumedG) : undefined,
        carbsConsumedG: carbsConsumedG ? Number(carbsConsumedG) : undefined,
        fatConsumedG: fatConsumedG ? Number(fatConsumedG) : undefined,
        notes: notes || undefined,
      });
      resetForm();
      setSuccessMsg(true);
      setTimeout(() => setSuccessMsg(false), 3000);
      await loadData();
    } catch (err: unknown) {
      setFormError(extractErrorMessage(err, 'Unable to log this entry. Please try again.'));
    } finally {
      setSubmitting(false);
    }
  }

  const goalPercent =
    summary?.goalAchievementPct != null
      ? Math.min(100, Math.max(0, Math.round(summary.goalAchievementPct)))
      : 0;

  const latestWeight = weightHistory.length > 0 ? weightHistory[weightHistory.length - 1].weightKg : null;

  return (
    <Layout title="Progress">
      <div className="space-y-6 pb-6">

        {/* ── Hero header ── */}
        <div
          className="relative overflow-hidden rounded-3xl p-7"
          style={{ background: 'linear-gradient(135deg, #1e3a5f 0%, #2563EB 60%, #3B82F6 100%)' }}
        >
          <div className="absolute -right-8 -top-8 w-48 h-48 rounded-full bg-white/10" />
          <div className="absolute right-12 bottom-0 w-28 h-28 rounded-full bg-white/5" />
          <p className="text-white/70 text-[13px] font-medium mb-1 relative z-10">Your journey</p>
          <h2 className="text-white font-bold relative z-10" style={{ fontSize: '26px' }}>
            Track your progress
          </h2>
          <p className="text-white/60 text-[14px] mt-1 relative z-10">
            Log daily entries and watch your trends unfold.
          </p>
        </div>

        {loadError && (
          <div className="px-4 py-3 rounded-xl bg-error-container text-on-error-container font-body-sm">
            {loadError}
          </div>
        )}

        {/* ── Stats row ── */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <StatCard
            label="Weekly Avg"
            value={loading ? '—' : `${Math.round(summary?.weeklyAverageCalories ?? 0)}`}
            sub="kcal / day"
            icon="local_fire_department"
            gradient="linear-gradient(135deg, #F59E0B, #D97706)"
          />
          <StatCard
            label="Goal Progress"
            value={loading ? '—' : `${goalPercent}%`}
            sub="of calorie target"
            icon="emoji_events"
            gradient="linear-gradient(135deg, #2A9D58, #1B7A41)"
          />
          <StatCard
            label="Current Weight"
            value={latestWeight ? `${latestWeight}` : '—'}
            sub="kg logged"
            icon="monitor_weight"
            gradient="linear-gradient(135deg, #8B5CF6, #6D28D9)"
          />
          <StatCard
            label="Entries Logged"
            value={loading ? '—' : `${entries.length}`}
            sub="total records"
            icon="edit_note"
            gradient="linear-gradient(135deg, #EC4899, #BE185D)"
          />
        </div>

        {/* ── Goal achievement bar ── */}
        <div className="bg-surface border border-outline-variant rounded-2xl p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-headline-md text-on-background font-semibold" style={{ fontSize: '15px' }}>
              Goal Achievement
            </h3>
            <span
              className="font-bold text-[18px]"
              style={{ color: goalPercent >= 80 ? '#2A9D58' : goalPercent >= 50 ? '#F59E0B' : '#EF4444' }}
            >
              {loading ? '—' : `${goalPercent}%`}
            </span>
          </div>
          <div
            role="progressbar"
            aria-valuenow={goalPercent}
            aria-valuemin={0}
            aria-valuemax={100}
            className="h-3 rounded-full bg-surface-variant overflow-hidden"
          >
            <div
              className="h-full rounded-full transition-all duration-1000"
              style={{
                width: `${goalPercent}%`,
                background: goalPercent >= 80
                  ? 'linear-gradient(90deg, #2A9D58, #38C172)'
                  : goalPercent >= 50
                  ? 'linear-gradient(90deg, #F59E0B, #FCD34D)'
                  : 'linear-gradient(90deg, #EF4444, #F87171)',
              }}
            />
          </div>
          <p className="font-body-sm text-on-surface-variant mt-2 text-[12px]">
            {goalPercent >= 100
              ? '🎉 Goal achieved! Keep it up.'
              : goalPercent >= 80
              ? '💪 Almost there — great work!'
              : goalPercent >= 50
              ? '📈 Halfway to your goal.'
              : 'Start logging daily to hit your target.'}
          </p>
        </div>

        {/* ── Weight chart ── */}
        <div className="bg-surface border border-outline-variant rounded-2xl p-5">
          <h3 className="font-headline-md text-on-background font-semibold mb-5" style={{ fontSize: '15px' }}>
            Weight Over Time
          </h3>
          {weightHistory.length > 0 ? (
            <div style={{ width: '100%', height: 240 }}>
              <ResponsiveContainer>
                <AreaChart data={weightHistory} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
                  <defs>
                    <linearGradient id="weightGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#2563EB" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="#2563EB" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="#f0f0f0" strokeDasharray="4 4" vertical={false} />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 11, fill: '#999' }}
                    tickFormatter={(d: string) => new Date(d).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fontSize: 11, fill: '#999' }}
                    domain={['auto', 'auto']}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Area
                    type="monotone"
                    dataKey="weightKg"
                    stroke="#2563EB"
                    strokeWidth={3}
                    fill="url(#weightGrad)"
                    dot={{ r: 4, fill: '#2563EB', strokeWidth: 2, stroke: '#fff' }}
                    activeDot={{ r: 6, fill: '#2563EB' }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 gap-3">
              <span className="material-symbols-outlined text-on-surface-variant text-4xl">show_chart</span>
              <p className="font-body-sm text-on-surface-variant">Log a weight entry to see your trend here.</p>
            </div>
          )}
        </div>

        {/* ── Log entry form ── */}
        <div className="bg-surface border border-outline-variant rounded-2xl p-5">
          <div className="flex items-center gap-2 mb-5">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <span className="material-symbols-outlined text-on-primary text-[16px]">add</span>
            </div>
            <h3 className="font-headline-md text-on-background font-semibold" style={{ fontSize: '16px' }}>
              Log a New Entry
            </h3>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {formError && (
              <div className="px-4 py-3 rounded-xl bg-error-container text-on-error-container font-body-sm">
                {formError}
              </div>
            )}
            {successMsg && (
              <div className="px-4 py-3 rounded-xl bg-primary-container text-on-primary-container font-body-sm flex items-center gap-2">
                <span className="material-symbols-outlined text-[16px]">check_circle</span>
                Entry logged successfully!
              </div>
            )}

            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
              <Field id="weightKg" label="Weight (kg)" value={weightKg} onChange={setWeightKg} icon="monitor_weight" />
              <Field id="caloriesConsumed" label="Calories" value={caloriesConsumed} onChange={setCaloriesConsumed} icon="local_fire_department" />
              <Field id="proteinConsumedG" label="Protein (g)" value={proteinConsumedG} onChange={setProteinConsumedG} icon="egg" />
              <Field id="carbsConsumedG" label="Carbs (g)" value={carbsConsumedG} onChange={setCarbsConsumedG} icon="grain" />
              <Field id="fatConsumedG" label="Fat (g)" value={fatConsumedG} onChange={setFatConsumedG} icon="water_drop" />
            </div>

            <div>
              <label htmlFor="notes" className="block font-label-caps text-label-caps text-on-surface-variant mb-2 text-[11px] uppercase tracking-wider">
                Notes (optional)
              </label>
              <textarea
                id="notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={2}
                className="w-full bg-surface border border-outline-variant rounded-xl py-3 px-4 font-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all resize-none placeholder:text-on-surface-variant/50"
                placeholder="How are you feeling today? Any notes about your meals..."
              />
            </div>

            <div className="flex justify-end">
              <button
                type="submit"
                id="progress-log-btn"
                disabled={submitting}
                className="flex items-center gap-2 px-7 py-3 bg-primary text-on-primary rounded-full font-label-caps text-label-caps hover:opacity-90 transition-opacity disabled:opacity-60"
              >
                {submitting ? (
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <span className="material-symbols-outlined text-[16px]">save</span>
                )}
                {submitting ? 'Logging…' : 'Log Entry'}
              </button>
            </div>
          </form>
        </div>

        {/* ── Entry history ── */}
        <div className="bg-surface border border-outline-variant rounded-2xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-headline-md text-on-background font-semibold" style={{ fontSize: '16px' }}>
              Recent Entries
            </h3>
            <span className="font-label-caps text-label-caps text-on-surface-variant text-[11px]">
              {entries.length} total
            </span>
          </div>
          {entries.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 gap-3">
              <span className="material-symbols-outlined text-on-surface-variant text-4xl">history</span>
              <p className="font-body-sm text-on-surface-variant">No entries logged yet. Start by logging one above!</p>
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              {entries.slice(0, 10).map((entry, idx) => (
                <EntryRow key={entry.id ?? idx} entry={entry} idx={idx} />
              ))}
              {entries.length > 10 && (
                <p className="font-body-sm text-on-surface-variant text-center py-2 text-[12px]">
                  Showing 10 of {entries.length} entries
                </p>
              )}
            </div>
          )}
        </div>

      </div>
    </Layout>
  );
}
