import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import Layout from '../components/Layout';
import { apiClient, extractErrorMessage } from '../api/client';
import { FitnessGoal, HealthProfile } from '../types';
import { categorizeBmi } from '../utils/bmi';

/** Mirrors nutritionCalculator.ts GOAL_CALORIE_ADJUSTMENT — kept in sync manually. */
const GOAL_CALORIE_ADJUSTMENT: Record<FitnessGoal, number> = {
  WEIGHT_LOSS: -500,
  WEIGHT_GAIN: 400,
  MUSCLE_GAIN: 300,
  MAINTENANCE: 0,
};

const GOAL_LABELS: Record<FitnessGoal, string> = {
  WEIGHT_LOSS: 'Weight Loss',
  WEIGHT_GAIN: 'Weight Gain',
  MUSCLE_GAIN: 'Muscle Gain',
  MAINTENANCE: 'Maintenance',
};

function computeCalorieTarget(profile: HealthProfile): number | null {
  if (!profile.tdee) return null;
  const adj = GOAL_CALORIE_ADJUSTMENT[profile.fitnessGoal] ?? 0;
  return Math.max(1200, Math.round(profile.tdee + adj));
}

function getGreeting() {
  const h = new Date().getHours();
  if (h < 12) return 'Good morning';
  if (h < 17) return 'Good afternoon';
  return 'Good evening';
}

// ─── Macro ring (SVG circle) ──────────────────────────────────────────────────

function MacroRing({
  label,
  value,
  suffix,
  color,
  pct,
}: {
  label: string;
  value: string;
  suffix: string;
  color: string;
  pct: number;
}) {
  const R = 28;
  const C = 2 * Math.PI * R;
  const dash = (pct / 100) * C;

  return (
    <div className="flex flex-col items-center gap-1.5">
      <div className="relative w-16 h-16">
        <svg className="w-16 h-16 -rotate-90" viewBox="0 0 64 64">
          <circle cx="32" cy="32" r={R} fill="none" stroke="rgba(255,255,255,0.15)" strokeWidth="5" />
          <circle
            cx="32" cy="32" r={R}
            fill="none"
            stroke={color}
            strokeWidth="5"
            strokeLinecap="round"
            strokeDasharray={`${dash} ${C}`}
            className="transition-all duration-1000"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-white font-bold text-[13px] leading-none">{value}</span>
          <span className="text-white/60 text-[9px]">{suffix}</span>
        </div>
      </div>
      <span className="text-white/80 text-[11px] font-medium">{label}</span>
    </div>
  );
}

// ─── Quick action card ────────────────────────────────────────────────────────

function QuickCard({
  to,
  icon,
  title,
  sub,
  gradient,
}: {
  to: string;
  icon: string;
  title: string;
  sub: string;
  gradient: string;
}) {
  return (
    <Link
      to={to}
      className="group relative overflow-hidden rounded-2xl p-5 flex flex-col gap-3 hover:scale-[1.02] hover:shadow-xl transition-all duration-300"
      style={{ background: gradient }}
    >
      {/* Decorative circle */}
      <div className="absolute -right-4 -top-4 w-24 h-24 rounded-full bg-white/10" />
      <div className="absolute -right-2 -bottom-6 w-16 h-16 rounded-full bg-white/5" />

      <div className="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center flex-shrink-0 relative z-10">
        <span className="material-symbols-outlined text-white text-[22px]">{icon}</span>
      </div>
      <div className="relative z-10">
        <p className="text-white font-bold text-[15px] leading-tight">{title}</p>
        <p className="text-white/70 text-[12px] mt-0.5">{sub}</p>
      </div>
      <span className="material-symbols-outlined text-white/50 group-hover:text-white group-hover:translate-x-1 transition-all text-[18px] relative z-10">
        arrow_forward
      </span>
    </Link>
  );
}

// ─── Info chip ────────────────────────────────────────────────────────────────

function InfoChip({ label, value, icon }: { label: string; value: string; icon: string }) {
  return (
    <div className="bg-surface border border-outline-variant rounded-2xl p-4 flex items-center gap-3">
      <div className="w-9 h-9 rounded-xl bg-primary-container flex items-center justify-center flex-shrink-0">
        <span className="material-symbols-outlined text-on-primary-container text-[18px]">{icon}</span>
      </div>
      <div>
        <p className="font-label-caps text-label-caps text-on-surface-variant text-[10px] uppercase">{label}</p>
        <p className="font-headline-md text-on-background font-bold text-[18px] leading-tight">{value}</p>
      </div>
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function Dashboard() {
  const navigate = useNavigate();
  const [profile, setProfile] = useState<HealthProfile | null>(null);
  const [userName, setUserName] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function loadProfile() {
      try {
        const [hpRes, meRes] = await Promise.allSettled([
          apiClient.get<{ profile: HealthProfile }>('/api/health-profile'),
          apiClient.get('/api/auth/me'),
        ]);

        if (!cancelled) {
          if (hpRes.status === 'fulfilled') {
            setProfile(hpRes.value.data.profile);
          } else if (
            axios.isAxiosError((hpRes as PromiseRejectedResult).reason) &&
            (hpRes as PromiseRejectedResult).reason.response?.status === 404
          ) {
            navigate('/health-assessment');
            return;
          } else {
            setError(extractErrorMessage((hpRes as PromiseRejectedResult).reason, 'Unable to load your dashboard.'));
          }

          if (meRes.status === 'fulfilled') {
            const u = meRes.value.data.user;
            setUserName(u?.name ?? '');
          }
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadProfile();
    return () => { cancelled = true; };
  }, [navigate]);

  const calorieTarget = profile ? computeCalorieTarget(profile) : null;
  const proteinG = profile?.proteinTargetG ? Math.round(profile.proteinTargetG) : 0;
  const carbsG = profile?.carbTargetG ? Math.round(profile.carbTargetG) : 0;
  const fatG = profile?.fatTargetG ? Math.round(profile.fatTargetG) : 0;

  // Rough macro ratios for rings (protein=~30%, carbs=~50%, fat=~20% as reference)
  const proteinPct = Math.min(100, (proteinG / 200) * 100);
  const carbsPct = Math.min(100, (carbsG / 300) * 100);
  const fatPct = Math.min(100, (fatG / 100) * 100);

  return (
    <Layout title="Dashboard">
      {loading && (
        <div className="flex items-center justify-center py-32">
          <span className="material-symbols-outlined animate-spin text-primary text-4xl">progress_activity</span>
        </div>
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
        <div className="space-y-6 pb-6">

          {/* ── Hero banner ── */}
          <div
            className="relative overflow-hidden rounded-3xl p-7 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6"
            style={{ background: 'linear-gradient(135deg, #1B5E35 0%, #2A9D58 60%, #38C172 100%)' }}
          >
            {/* Decorative blobs */}
            <div className="absolute top-0 right-0 w-64 h-64 rounded-full opacity-10"
              style={{ background: 'radial-gradient(circle, #fff 0%, transparent 70%)', transform: 'translate(30%, -30%)' }} />
            <div className="absolute bottom-0 left-1/2 w-40 h-40 rounded-full opacity-5"
              style={{ background: 'radial-gradient(circle, #fff 0%, transparent 70%)' }} />

            {/* Text */}
            <div className="relative z-10">
              <p className="text-white/70 font-medium text-[13px] mb-1">{getGreeting()}{userName ? `, ${userName.split(' ')[0]}` : ''} 👋</p>
              <h2 className="text-white font-bold leading-tight" style={{ fontSize: '26px' }}>
                Your Nutrition<br />Dashboard
              </h2>
              <div className="mt-3 flex flex-wrap gap-2">
                <span className="px-3 py-1 rounded-full bg-white/20 text-white text-[12px] font-medium">
                  Goal: {GOAL_LABELS[profile.fitnessGoal]}
                </span>
                {profile.bmi && (
                  <span className="px-3 py-1 rounded-full bg-white/20 text-white text-[12px] font-medium">
                    BMI {profile.bmi?.toFixed(1)} · {categorizeBmi(profile.bmi)}
                  </span>
                )}
              </div>
            </div>

            {/* Macro rings */}
            <div className="relative z-10 flex gap-5 sm:gap-6 flex-wrap">
              <div className="flex flex-col items-center gap-1.5">
                <div className="relative w-20 h-20">
                  <svg className="w-20 h-20 -rotate-90" viewBox="0 0 80 80">
                    <circle cx="40" cy="40" r="32" fill="none" stroke="rgba(255,255,255,0.15)" strokeWidth="6" />
                    <circle
                      cx="40" cy="40" r="32"
                      fill="none" stroke="white" strokeWidth="6" strokeLinecap="round"
                      strokeDasharray={`${(Math.min(100, ((calorieTarget ?? 2000) / 3500) * 100) / 100) * 2 * Math.PI * 32} ${2 * Math.PI * 32}`}
                    />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-white font-bold text-[14px] leading-none">{calorieTarget ?? '—'}</span>
                    <span className="text-white/60 text-[9px]">kcal</span>
                  </div>
                </div>
                <span className="text-white/80 text-[11px] font-semibold">Target</span>
              </div>
              <MacroRing label="Protein" value={`${proteinG}`} suffix="g" color="#6EE7B7" pct={proteinPct} />
              <MacroRing label="Carbs" value={`${carbsG}`} suffix="g" color="#FCD34D" pct={carbsPct} />
              <MacroRing label="Fat" value={`${fatG}`} suffix="g" color="#FCA5A5" pct={fatPct} />
            </div>
          </div>

          {/* ── Body metrics row ── */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { label: 'BMR', value: profile.bmr ? `${Math.round(profile.bmr)} kcal` : '—', icon: 'favorite' },
              { label: 'TDEE', value: profile.tdee ? `${Math.round(profile.tdee)} kcal` : '—', icon: 'bolt' },
              { label: 'BMI Score', value: profile.bmi ? profile.bmi.toFixed(1) : '—', icon: 'monitor_weight' },
              { label: 'BMI Status', value: profile.bmi ? categorizeBmi(profile.bmi) : '—', icon: 'health_and_safety' },
            ].map(({ label, value, icon }) => (
              <InfoChip key={label} label={label} value={value} icon={icon} />
            ))}
          </div>

          {/* ── Macro progress bars ── */}
          <div className="bg-surface border border-outline-variant rounded-2xl p-5">
            <h3 className="font-headline-md text-on-background font-semibold mb-4" style={{ fontSize: '16px' }}>
              Daily Macro Targets
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
              {[
                { label: 'Protein', value: proteinG, max: 250, color: '#2A9D58', bg: 'bg-emerald-50' },
                { label: 'Carbohydrates', value: carbsG, max: 400, color: '#F59E0B', bg: 'bg-amber-50' },
                { label: 'Fat', value: fatG, max: 120, color: '#EF4444', bg: 'bg-red-50' },
              ].map(({ label, value, max, color }) => (
                <div key={label}>
                  <div className="flex justify-between mb-1.5">
                    <span className="font-body-sm text-on-surface-variant text-[13px]">{label}</span>
                    <span className="font-body-md font-bold text-on-background text-[13px]">{value}g</span>
                  </div>
                  <div className="h-2.5 rounded-full bg-surface-variant overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-1000"
                      style={{ width: `${Math.min(100, (value / max) * 100)}%`, background: color }}
                    />
                  </div>
                  <p className="font-body-sm text-on-surface-variant text-[11px] mt-1">
                    of ~{max}g reference
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* ── Quick actions grid ── */}
          <div>
            <h3 className="font-headline-md text-on-background font-semibold mb-4" style={{ fontSize: '16px' }}>
              Quick Actions
            </h3>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              <QuickCard
                to="/recommendations"
                icon="auto_awesome"
                title="Meal Recommendations"
                sub="Curated for your macros"
                gradient="linear-gradient(135deg, #2A9D58, #1B7A41)"
              />
              <QuickCard
                to="/meal-plan"
                icon="restaurant_menu"
                title="Weekly Meal Plan"
                sub="7-day personalized plan"
                gradient="linear-gradient(135deg, #3B82F6, #1D4ED8)"
              />
              <QuickCard
                to="/progress"
                icon="insights"
                title="Track Progress"
                sub="Log & view trends"
                gradient="linear-gradient(135deg, #8B5CF6, #6D28D9)"
              />
              <QuickCard
                to="/chat"
                icon="smart_toy"
                title="AI Nutritionist"
                sub="Chat with your coach"
                gradient="linear-gradient(135deg, #EC4899, #BE185D)"
              />
            </div>
          </div>

          {/* ── Retake banner ── */}
          <div className="flex items-center justify-between bg-surface border border-outline-variant rounded-2xl px-5 py-4">
            <div className="flex items-center gap-3">
              <span className="material-symbols-outlined text-primary text-[22px]">refresh</span>
              <div>
                <p className="font-body-md font-semibold text-on-background text-[14px]">Update your health profile</p>
                <p className="font-body-sm text-on-surface-variant text-[12px]">Keep your targets accurate as your body changes.</p>
              </div>
            </div>
            <Link
              to="/health-assessment"
              className="flex-shrink-0 px-4 py-2 rounded-full border border-outline-variant text-on-background font-label-caps text-label-caps hover:bg-surface-container-low transition-colors"
            >
              Retake
            </Link>
          </div>

        </div>
      )}
    </Layout>
  );
}
