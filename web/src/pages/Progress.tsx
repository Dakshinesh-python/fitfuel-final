import { FormEvent, useEffect, useState } from 'react';
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import Layout from '../components/Layout';
import { apiClient, extractErrorMessage } from '../api/client';
import { ProgressEntry, ProgressSummary } from '../types';

export default function Progress() {
  const [weightKg, setWeightKg] = useState('');
  const [caloriesConsumed, setCaloriesConsumed] = useState('');
  const [proteinConsumedG, setProteinConsumedG] = useState('');
  const [carbsConsumedG, setCarbsConsumedG] = useState('');
  const [fatConsumedG, setFatConsumedG] = useState('');
  const [notes, setNotes] = useState('');
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const [summary, setSummary] = useState<ProgressSummary | null>(null);
  const [entries, setEntries] = useState<ProgressEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  async function loadData() {
    setLoading(true);
    setLoadError(null);
    try {
      const [summaryRes, entriesRes] = await Promise.all([
        apiClient.get<ProgressSummary>('/api/progress/summary'),
        apiClient.get<ProgressEntry[]>('/api/progress'),
      ]);
      setSummary(summaryRes.data);
      setEntries(entriesRes.data);
    } catch (err: unknown) {
      setLoadError(extractErrorMessage(err, 'Unable to load your progress data.'));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  function resetForm() {
    setWeightKg('');
    setCaloriesConsumed('');
    setProteinConsumedG('');
    setCarbsConsumedG('');
    setFatConsumedG('');
    setNotes('');
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setFormError(null);

    const hasAnyValue =
      weightKg || caloriesConsumed || proteinConsumedG || carbsConsumedG || fatConsumedG;

    if (!hasAnyValue) {
      setFormError('Please provide at least one value before logging an entry.');
      return;
    }

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
      await loadData();
    } catch (err: unknown) {
      setFormError(extractErrorMessage(err, 'Unable to log this entry. Please try again.'));
    } finally {
      setSubmitting(false);
    }
  }

  const goalPercent = summary ? Math.min(100, Math.max(0, Math.round(summary.goalAchievementPercent))) : 0;

  return (
    <Layout title="Progress">
      <div className="space-y-10">
        <header>
          <h2 className="font-headline-lg text-headline-lg text-on-background mb-2">
            Track your progress
          </h2>
          <p className="font-body-lg text-body-lg text-on-surface-variant">
            Log daily entries and watch your trends unfold.
          </p>
        </header>

        {loadError && (
          <div className="px-4 py-3 rounded-lg bg-error-container text-on-error-container font-body-sm text-body-sm">
            {loadError}
          </div>
        )}

        {/* Summary Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-gutter">
          <div className="bg-surface-container-lowest border border-outline-variant rounded-lg p-6">
            <span className="font-label-caps text-label-caps text-on-surface-variant uppercase">
              Weekly Avg Calories
            </span>
            <p className="font-hero-stat text-hero-stat text-on-surface mt-2">
              {loading ? '—' : Math.round(summary?.weeklyAverageCalories ?? 0)}
            </p>
            <p className="font-body-sm text-body-sm text-on-surface-variant">kcal / day</p>
          </div>

          <div className="bg-surface-container-lowest border border-outline-variant rounded-lg p-6 md:col-span-2">
            <span className="font-label-caps text-label-caps text-on-surface-variant uppercase">
              Goal Achievement
            </span>
            <div className="flex items-center gap-4 mt-3">
              <div
                role="progressbar"
                aria-valuenow={goalPercent}
                aria-valuemin={0}
                aria-valuemax={100}
                className="flex-1 h-3 rounded-full bg-surface-variant overflow-hidden"
              >
                <div
                  className="h-full bg-primary rounded-full transition-all"
                  style={{ width: `${goalPercent}%` }}
                />
              </div>
              <span className="font-headline-lg text-headline-lg text-primary">{loading ? '—' : `${goalPercent}%`}</span>
            </div>
          </div>
        </div>

        {/* Weight Chart */}
        <div className="bg-surface-container-lowest border border-outline-variant rounded-lg p-6">
          <h3 className="font-headline-md text-headline-md text-on-background mb-4">
            Weight over time
          </h3>
          {summary && summary.weightHistory.length > 0 ? (
            <div style={{ width: '100%', height: 280 }}>
              <ResponsiveContainer>
                <LineChart data={summary.weightHistory}>
                  <CartesianGrid stroke="#eeece7" strokeDasharray="3 3" />
                  <XAxis dataKey="date" tick={{ fontSize: 12, fill: '#3d4943' }} />
                  <YAxis tick={{ fontSize: 12, fill: '#3d4943' }} domain={['auto', 'auto']} />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey="weightKg"
                    stroke="#006c4d"
                    strokeWidth={3}
                    dot={{ r: 4, fill: '#006c4d' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="font-body-sm text-body-sm text-on-surface-variant">
              Log a weight entry to see your trend here.
            </p>
          )}
        </div>

        {/* Log Entry Form */}
        <div className="bg-surface-container-lowest border border-outline-variant rounded-lg p-6">
          <h3 className="font-headline-md text-headline-md text-on-background mb-4">
            Log a new entry
          </h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            {formError && (
              <div className="px-4 py-3 rounded-lg bg-error-container text-on-error-container font-body-sm text-body-sm">
                {formError}
              </div>
            )}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <Field id="weightKg" label="Weight (kg)" value={weightKg} onChange={setWeightKg} />
              <Field
                id="caloriesConsumed"
                label="Calories"
                value={caloriesConsumed}
                onChange={setCaloriesConsumed}
              />
              <Field
                id="proteinConsumedG"
                label="Protein (g)"
                value={proteinConsumedG}
                onChange={setProteinConsumedG}
              />
              <Field
                id="carbsConsumedG"
                label="Carbs (g)"
                value={carbsConsumedG}
                onChange={setCarbsConsumedG}
              />
              <Field id="fatConsumedG" label="Fat (g)" value={fatConsumedG} onChange={setFatConsumedG} />
            </div>
            <div>
              <label className="block font-label-caps text-label-caps text-on-surface-variant mb-2" htmlFor="notes">
                Notes (optional)
              </label>
              <textarea
                id="notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={2}
                className="w-full bg-surface border border-outline-variant rounded-lg py-3 px-4 font-body-sm text-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-colors"
                placeholder="How are you feeling today?"
              />
            </div>
            <button
              type="submit"
              disabled={submitting}
              className="px-8 py-3 bg-primary text-on-primary rounded-full font-headline-md text-body-lg hover:bg-primary-container transition-colors duration-200 disabled:opacity-60"
            >
              {submitting ? 'Logging…' : 'Log Entry'}
            </button>
          </form>
        </div>

        {/* Entry History */}
        <div className="bg-surface-container-lowest border border-outline-variant rounded-lg p-6">
          <h3 className="font-headline-md text-headline-md text-on-background mb-4">
            Recent entries
          </h3>
          {entries.length === 0 ? (
            <p className="font-body-sm text-body-sm text-on-surface-variant">
              No entries logged yet.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-outline-variant">
                    <Th>Date</Th>
                    <Th>Weight</Th>
                    <Th>Calories</Th>
                    <Th>Protein</Th>
                    <Th>Carbs</Th>
                    <Th>Fat</Th>
                    <Th>Notes</Th>
                  </tr>
                </thead>
                <tbody>
                  {entries.map((entry, idx) => (
                    <tr key={entry.id ?? idx} className="border-b border-outline-variant/50">
                      <Td>{entry.date ?? '—'}</Td>
                      <Td>{entry.weightKg ? `${entry.weightKg} kg` : '—'}</Td>
                      <Td>{entry.caloriesConsumed ?? '—'}</Td>
                      <Td>{entry.proteinConsumedG ? `${entry.proteinConsumedG}g` : '—'}</Td>
                      <Td>{entry.carbsConsumedG ? `${entry.carbsConsumedG}g` : '—'}</Td>
                      <Td>{entry.fatConsumedG ? `${entry.fatConsumedG}g` : '—'}</Td>
                      <Td>{entry.notes ?? '—'}</Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}

function Field({
  id,
  label,
  value,
  onChange,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div>
      <label className="block font-label-caps text-label-caps text-on-surface-variant mb-2" htmlFor={id}>
        {label}
      </label>
      <input
        id={id}
        type="number"
        step="0.1"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full bg-surface border border-outline-variant rounded-lg py-2.5 px-3 font-body-sm text-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-colors"
      />
    </div>
  );
}

function Th({ children }: { children: string }) {
  return (
    <th className="py-2 px-3 font-label-caps text-label-caps text-on-surface-variant uppercase">
      {children}
    </th>
  );
}

function Td({ children }: { children: string | number }) {
  return <td className="py-2 px-3 font-body-sm text-body-sm text-on-surface">{children}</td>;
}
