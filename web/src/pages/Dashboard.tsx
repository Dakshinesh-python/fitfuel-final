import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import Layout from '../components/Layout';
import { apiClient, extractErrorMessage } from '../api/client';
import { HealthProfile } from '../types';

export default function Dashboard() {
  const navigate = useNavigate();
  const [profile, setProfile] = useState<HealthProfile | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function loadProfile() {
      try {
        const res = await apiClient.get<HealthProfile>('/api/health-profile');
        if (!cancelled) {
          setProfile(res.data);
        }
      } catch (err: unknown) {
        if (axios.isAxiosError(err) && err.response?.status === 404) {
          navigate('/health-assessment');
          return;
        }
        if (!cancelled) {
          setError(extractErrorMessage(err, 'Unable to load your dashboard.'));
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadProfile();
    return () => {
      cancelled = true;
    };
  }, [navigate]);

  return (
    <Layout title="Overview">
      {loading && (
        <p className="font-body-sm text-body-sm text-on-surface-variant">Loading your dashboard…</p>
      )}

      {error && (
        <div
          data-testid="dashboard-error"
          className="px-4 py-3 rounded-lg bg-error-container text-on-error-container font-body-sm text-body-sm mb-6"
        >
          {error}
        </div>
      )}

      {profile && (
        <div className="space-y-8">
          {/* Stat Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-gutter">
            <StatCard
              label="Calorie Target"
              value={profile.calorieTarget ? `${Math.round(profile.calorieTarget)}` : '—'}
              suffix="kcal"
              icon="local_fire_department"
            />
            <StatCard
              label="Protein"
              value={profile.proteinTargetG ? `${Math.round(profile.proteinTargetG)}` : '—'}
              suffix="g"
              icon="egg"
            />
            <StatCard
              label="Carbs"
              value={profile.carbTargetG ? `${Math.round(profile.carbTargetG)}` : '—'}
              suffix="g"
              icon="grain"
            />
            <StatCard
              label="Fat"
              value={profile.fatTargetG ? `${Math.round(profile.fatTargetG)}` : '—'}
              suffix="g"
              icon="water_drop"
            />
          </div>

          {/* Secondary Info */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-gutter">
            <div className="bg-surface-container-lowest border border-outline-variant rounded-lg p-6">
              <span className="font-label-caps text-label-caps text-on-surface-variant uppercase">
                BMI Category
              </span>
              <p className="font-headline-lg text-headline-lg text-on-surface mt-2">
                {profile.bmiCategory ?? '—'}
              </p>
              {profile.bmi && (
                <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">
                  BMI: {profile.bmi}
                </p>
              )}
            </div>
            <div className="bg-surface-container-lowest border border-outline-variant rounded-lg p-6">
              <span className="font-label-caps text-label-caps text-on-surface-variant uppercase">
                BMR
              </span>
              <p className="font-headline-lg text-headline-lg text-on-surface mt-2">
                {profile.bmr ? Math.round(profile.bmr) : '—'}
                <span className="font-body-sm text-body-sm text-on-surface-variant ml-1">kcal</span>
              </p>
            </div>
            <div className="bg-surface-container-lowest border border-outline-variant rounded-lg p-6">
              <span className="font-label-caps text-label-caps text-on-surface-variant uppercase">
                TDEE
              </span>
              <p className="font-headline-lg text-headline-lg text-on-surface mt-2">
                {profile.tdee ? Math.round(profile.tdee) : '—'}
                <span className="font-body-sm text-body-sm text-on-surface-variant ml-1">kcal</span>
              </p>
            </div>
          </div>

          {/* Navigation Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-gutter">
            <Link
              to="/recommendations"
              className="bg-surface-container-lowest border border-outline-variant rounded-lg p-8 flex items-center justify-between hover:border-primary hover:bg-primary/5 transition-all group"
            >
              <div>
                <h3 className="font-headline-md text-headline-md text-on-background mb-1">
                  Meal Recommendations
                </h3>
                <p className="font-body-sm text-body-sm text-on-surface-variant">
                  See meals curated for your macros and budget.
                </p>
              </div>
              <span className="material-symbols-outlined text-primary group-hover:translate-x-1 transition-transform">
                arrow_forward
              </span>
            </Link>
            <Link
              to="/progress"
              className="bg-surface-container-lowest border border-outline-variant rounded-lg p-8 flex items-center justify-between hover:border-primary hover:bg-primary/5 transition-all group"
            >
              <div>
                <h3 className="font-headline-md text-headline-md text-on-background mb-1">
                  Track Progress
                </h3>
                <p className="font-body-sm text-body-sm text-on-surface-variant">
                  Log entries and see your trends over time.
                </p>
              </div>
              <span className="material-symbols-outlined text-primary group-hover:translate-x-1 transition-transform">
                arrow_forward
              </span>
            </Link>
          </div>
        </div>
      )}
    </Layout>
  );
}

function StatCard({
  label,
  value,
  suffix,
  icon,
}: {
  label: string;
  value: string;
  suffix: string;
  icon: string;
}) {
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
      <div>
        <p className="font-hero-stat text-hero-stat text-on-surface">{value}</p>
        <p className="font-body-sm text-body-sm text-on-surface-variant">{suffix}</p>
      </div>
    </div>
  );
}
