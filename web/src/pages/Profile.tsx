import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import { apiClient, extractErrorMessage } from '../api/client';
import { HealthProfile, FitnessGoal, ActivityLevel, DietaryPreference } from '../types';

// ─── Types ────────────────────────────────────────────────────────────────────

interface UserInfo {
  id: string;
  name: string;
  email: string;
  age?: number;
  heightCm?: number;
  weightKg?: number;
}

type Tab = 'personal' | 'health' | 'preferences' | 'security';

const GOAL_LABELS: Record<FitnessGoal, string> = {
  WEIGHT_LOSS: 'Weight Loss',
  WEIGHT_GAIN: 'Weight Gain',
  MUSCLE_GAIN: 'Muscle Gain',
  MAINTENANCE: 'Maintain',
};

const ACTIVITY_LABELS: Record<ActivityLevel, string> = {
  SEDENTARY: 'Sedentary',
  LIGHT: 'Light',
  MODERATE: 'Moderate',
  ACTIVE: 'Active',
  VERY_ACTIVE: 'Very Active',
};

const DIET_LABELS: Record<DietaryPreference, string> = {
  VEGETARIAN: 'Vegetarian',
  NON_VEGETARIAN: 'Non-Vegetarian',
  VEGAN: 'Vegan',
};

// ─── Helpers ──────────────────────────────────────────────────────────────────

function cmToFeet(cm: number) {
  const totalInches = cm / 2.54;
  const feet = Math.floor(totalInches / 12);
  const inches = Math.round(totalInches % 12);
  return `${feet}'${inches}"`;
}

function kgToLbs(kg: number) {
  return Math.round(kg * 2.20462);
}

// ─── Sub-sections ─────────────────────────────────────────────────────────────

function MetricCircle({ label, value, unit }: { label: string; value: string; unit?: string }) {
  return (
    <div className="flex flex-col items-center gap-1">
      <div className="w-24 h-24 rounded-full bg-surface-variant border border-outline-variant flex flex-col items-center justify-center">
        <span className="font-headline-md text-headline-md text-on-background leading-tight">{value}</span>
        {unit && <span className="font-body-sm text-body-sm text-on-surface-variant">{unit}</span>}
      </div>
      <span className="font-label-caps text-label-caps text-on-surface-variant">{label}</span>
    </div>
  );
}

function SectionCard({ title, icon, children }: { title: string; icon: string; children: React.ReactNode }) {
  return (
    <div className="bg-surface border border-outline-variant rounded-2xl p-6 mb-6">
      <h3 className="flex items-center gap-2 font-headline-md text-on-background mb-5" style={{ fontSize: '18px' }}>
        <span className="material-symbols-outlined text-primary text-[20px]">{icon}</span>
        {title}
      </h3>
      {children}
    </div>
  );
}

// ─── Toast ────────────────────────────────────────────────────────────────────

function Toast({ message, onClose }: { message: string; onClose: () => void }) {
  useEffect(() => {
    const t = setTimeout(onClose, 3500);
    return () => clearTimeout(t);
  }, [onClose]);

  return (
    <div className="fixed bottom-6 right-6 z-50 flex items-center gap-3 bg-surface border border-outline-variant rounded-xl shadow-xl px-4 py-3 animate-fade-in">
      <div className="w-6 h-6 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
        <span className="material-symbols-outlined text-on-primary text-[14px]">check</span>
      </div>
      <div>
        <p className="font-label-md font-semibold text-on-background">Profile Updated</p>
        <p className="font-body-sm text-on-surface-variant text-[12px]">{message}</p>
      </div>
      <button onClick={onClose} className="ml-2 text-on-surface-variant hover:text-on-background">
        <span className="material-symbols-outlined text-[18px]">close</span>
      </button>
    </div>
  );
}

// ─── Tab: Personal Info ───────────────────────────────────────────────────────

function PersonalTab({
  user,
  profile,
  onSaved,
}: {
  user: UserInfo;
  profile: HealthProfile | null;
  onSaved: () => void;
}) {
  const navigate = useNavigate();
  const [firstName, setFirstName] = useState(user.name.split(' ')[0] ?? '');
  const [lastName, setLastName] = useState(user.name.split(' ').slice(1).join(' ') ?? '');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      await apiClient.patch('/api/auth/profile', { name: `${firstName} ${lastName}`.trim() });
      onSaved();
    } catch (e) {
      setError(extractErrorMessage(e, 'Failed to save changes.'));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      {/* Profile header card */}
      <div className="bg-surface border border-outline-variant rounded-2xl p-6 mb-6 flex items-center gap-5">
        <div className="w-16 h-16 rounded-full bg-primary-container flex items-center justify-center flex-shrink-0">
          <span className="material-symbols-outlined text-on-primary-container text-3xl">person</span>
        </div>
        <div>
          <p className="font-headline-md text-on-background" style={{ fontSize: '20px' }}>
            {user.name}
          </p>
          <p className="font-body-sm text-on-surface-variant mt-0.5">{user.email}</p>
          <div className="flex gap-2 mt-2 flex-wrap">
            <span className="px-2.5 py-0.5 rounded-full bg-primary-container text-on-primary-container font-label-caps text-label-caps text-[11px]">
              Pro Member
            </span>
            {profile?.fitnessGoal && (
              <span className="px-2.5 py-0.5 rounded-full bg-secondary-container text-on-secondary-container font-label-caps text-label-caps text-[11px]">
                {GOAL_LABELS[profile.fitnessGoal]} Plan
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Basic Information */}
      <SectionCard title="Basic Information" icon="badge">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="font-label-caps text-label-caps text-on-surface-variant block mb-1.5">
              First Name
            </label>
            <input
              id="profile-first-name"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-outline-variant bg-surface text-on-background font-body-md focus:outline-none focus:ring-2 focus:ring-primary/30 transition"
            />
          </div>
          <div>
            <label className="font-label-caps text-label-caps text-on-surface-variant block mb-1.5">
              Last Name
            </label>
            <input
              id="profile-last-name"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-outline-variant bg-surface text-on-background font-body-md focus:outline-none focus:ring-2 focus:ring-primary/30 transition"
            />
          </div>
        </div>
        <div>
          <label className="font-label-caps text-label-caps text-on-surface-variant block mb-1.5">
            Email Address
          </label>
          <input
            id="profile-email"
            value={user.email}
            disabled
            className="w-full px-4 py-3 rounded-xl border border-outline-variant bg-surface-variant text-on-surface-variant font-body-md cursor-not-allowed"
          />
          <p className="font-body-sm text-body-sm text-on-surface-variant mt-1.5">
            Contact support to change your email address.
          </p>
        </div>
      </SectionCard>

      {/* Physical Metrics */}
      {profile && (
        <SectionCard title="Physical Metrics" icon="fitness_center">
          <div className="flex items-center justify-between mb-5">
            <span />
            <button
              onClick={() => navigate('/health-assessment')}
              className="font-label-caps text-label-caps text-primary hover:text-primary/70 transition-colors"
            >
              Retake Assessment
            </button>
          </div>
          <div className="flex flex-wrap gap-6 justify-center sm:justify-start">
            {profile.currentWeightKg && (
              <>
                {user.age && <MetricCircle label="Age" value={String(user.age)} />}
                {user.heightCm && (
                  <MetricCircle label="Height" value={cmToFeet(user.heightCm)} />
                )}
                <MetricCircle
                  label="Weight"
                  value={String(kgToLbs(profile.currentWeightKg))}
                  unit="lbs"
                />
              </>
            )}
            <MetricCircle label="Goal" value={GOAL_LABELS[profile.fitnessGoal]} />
          </div>
        </SectionCard>
      )}

      {/* Actions */}
      {error && (
        <p className="font-body-sm text-error mb-3">{error}</p>
      )}
      <div className="flex justify-end gap-3">
        <button
          onClick={() => {
            setFirstName(user.name.split(' ')[0] ?? '');
            setLastName(user.name.split(' ').slice(1).join(' ') ?? '');
          }}
          className="px-6 py-2.5 rounded-full border border-outline-variant text-on-surface-variant font-label-caps text-label-caps hover:bg-surface-container-low transition-colors"
        >
          Cancel
        </button>
        <button
          id="profile-save-btn"
          onClick={handleSave}
          disabled={saving}
          className="px-6 py-2.5 rounded-full bg-primary text-on-primary font-label-caps text-label-caps hover:opacity-90 transition-opacity disabled:opacity-60"
        >
          {saving ? 'Saving…' : 'Save Changes'}
        </button>
      </div>

      {/* Danger Zone */}
      <div className="mt-8 border border-error/30 rounded-2xl p-6">
        <h3 className="flex items-center gap-2 font-headline-md text-error mb-2" style={{ fontSize: '17px' }}>
          <span className="material-symbols-outlined text-[20px]">warning</span>
          Danger Zone
        </h3>
        <p className="font-body-sm text-on-surface-variant mb-4">
          Deleting your account is permanent and cannot be undone.
        </p>
        <button className="px-5 py-2 rounded-full border border-error text-error font-label-caps text-label-caps hover:bg-error/10 transition-colors">
          Delete Account
        </button>
      </div>
    </div>
  );
}

// ─── Tab: Health Profile ──────────────────────────────────────────────────────

function HealthTab({ profile }: { profile: HealthProfile | null }) {
  const navigate = useNavigate();

  if (!profile) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-4">
        <span className="material-symbols-outlined text-on-surface-variant text-5xl">monitor_heart</span>
        <p className="font-body-md text-on-surface-variant">No health profile found.</p>
        <button
          onClick={() => navigate('/health-assessment')}
          className="px-5 py-2.5 rounded-full bg-primary text-on-primary font-label-caps text-label-caps"
        >
          Complete Assessment
        </button>
      </div>
    );
  }

  const rows: Array<{ label: string; value: string }> = [
    { label: 'Current Weight', value: `${profile.currentWeightKg} kg` },
    { label: 'Target Weight', value: `${profile.targetWeightKg} kg` },
    { label: 'Activity Level', value: ACTIVITY_LABELS[profile.activityLevel] },
    { label: 'Fitness Goal', value: GOAL_LABELS[profile.fitnessGoal] },
    { label: 'Dietary Preference', value: DIET_LABELS[profile.dietaryPreference] },
    { label: 'Daily Budget', value: `₹${profile.dailyBudget}` },
    ...(profile.bmi ? [{ label: 'BMI', value: profile.bmi.toFixed(1) }] : []),
    ...(profile.bmr ? [{ label: 'BMR', value: `${Math.round(profile.bmr)} kcal` }] : []),
    ...(profile.tdee ? [{ label: 'TDEE', value: `${Math.round(profile.tdee)} kcal` }] : []),
    ...(profile.proteinTargetG ? [{ label: 'Protein Target', value: `${Math.round(profile.proteinTargetG)}g` }] : []),
    ...(profile.carbTargetG ? [{ label: 'Carb Target', value: `${Math.round(profile.carbTargetG)}g` }] : []),
    ...(profile.fatTargetG ? [{ label: 'Fat Target', value: `${Math.round(profile.fatTargetG)}g` }] : []),
  ];

  return (
    <div>
      <SectionCard title="Health Profile" icon="monitor_heart">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-y-4 gap-x-8">
          {rows.map(({ label, value }) => (
            <div key={label} className="flex justify-between border-b border-outline-variant pb-3">
              <span className="font-body-sm text-on-surface-variant">{label}</span>
              <span className="font-body-md font-semibold text-on-background">{value}</span>
            </div>
          ))}
        </div>
        <div className="mt-5 flex justify-end">
          <button
            onClick={() => navigate('/health-assessment')}
            className="px-5 py-2.5 rounded-full border border-primary text-primary font-label-caps text-label-caps hover:bg-primary/10 transition-colors"
          >
            Update Assessment
          </button>
        </div>
      </SectionCard>
    </div>
  );
}

// ─── Tab: Preferences ─────────────────────────────────────────────────────────

function PreferencesTab({ profile }: { profile: HealthProfile | null }) {
  const [notifications, setNotifications] = useState(true);
  const [mealReminders, setMealReminders] = useState(true);
  const [weeklyReport, setWeeklyReport] = useState(false);

  function Toggle({ id, checked, onChange, label, sub }: { id: string; checked: boolean; onChange: (v: boolean) => void; label: string; sub: string }) {
    return (
      <div className="flex items-center justify-between py-4 border-b border-outline-variant last:border-0">
        <div>
          <p className="font-body-md text-on-background">{label}</p>
          <p className="font-body-sm text-on-surface-variant">{sub}</p>
        </div>
        <button
          id={id}
          role="switch"
          aria-checked={checked}
          onClick={() => onChange(!checked)}
          className={`relative w-11 h-6 rounded-full transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-primary/30 ${checked ? 'bg-primary' : 'bg-outline-variant'}`}
        >
          <span
            className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform duration-200 ${checked ? 'translate-x-5' : 'translate-x-0'}`}
          />
        </button>
      </div>
    );
  }

  return (
    <div>
      <SectionCard title="Notification Preferences" icon="notifications">
        <Toggle id="pref-notifications" checked={notifications} onChange={setNotifications} label="Push Notifications" sub="Receive push alerts on your device" />
        <Toggle id="pref-meal-reminders" checked={mealReminders} onChange={setMealReminders} label="Meal Reminders" sub="Get reminded at breakfast, lunch & dinner times" />
        <Toggle id="pref-weekly-report" checked={weeklyReport} onChange={setWeeklyReport} label="Weekly Progress Report" sub="Receive a weekly email summary of your nutrition goals" />
      </SectionCard>

      <SectionCard title="Diet Preferences" icon="restaurant">
        <p className="font-body-sm text-on-surface-variant mb-3">
          Current preference: <span className="font-semibold text-on-background">{profile ? DIET_LABELS[profile.dietaryPreference] : '—'}</span>
        </p>
        <p className="font-body-sm text-on-surface-variant">
          To update your dietary preference, retake the health assessment.
        </p>
      </SectionCard>
    </div>
  );
}

// ─── Tab: Security ────────────────────────────────────────────────────────────

function SecurityTab() {
  const [current, setCurrent] = useState('');
  const [next, setNext] = useState('');
  const [confirm, setConfirm] = useState('');
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<{ type: 'ok' | 'err'; text: string } | null>(null);

  async function handleChange() {
    if (next !== confirm) { setMsg({ type: 'err', text: 'New passwords do not match.' }); return; }
    if (next.length < 8) { setMsg({ type: 'err', text: 'Password must be at least 8 characters.' }); return; }
    setSaving(true);
    setMsg(null);
    try {
      await apiClient.patch('/api/auth/password', { currentPassword: current, newPassword: next });
      setMsg({ type: 'ok', text: 'Password changed successfully.' });
      setCurrent(''); setNext(''); setConfirm('');
    } catch (e) {
      setMsg({ type: 'err', text: extractErrorMessage(e, 'Failed to change password.') });
    } finally {
      setSaving(false);
    }
  }

  return (
    <SectionCard title="Change Password" icon="lock">
      <div className="max-w-md flex flex-col gap-4">
        {[
          { id: 'sec-current', label: 'Current Password', value: current, set: setCurrent },
          { id: 'sec-new', label: 'New Password', value: next, set: setNext },
          { id: 'sec-confirm', label: 'Confirm New Password', value: confirm, set: setConfirm },
        ].map(({ id, label, value, set }) => (
          <div key={id}>
            <label htmlFor={id} className="font-label-caps text-label-caps text-on-surface-variant block mb-1.5">{label}</label>
            <input
              id={id}
              type="password"
              value={value}
              onChange={(e) => set(e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-outline-variant bg-surface text-on-background font-body-md focus:outline-none focus:ring-2 focus:ring-primary/30 transition"
            />
          </div>
        ))}
        {msg && (
          <p className={`font-body-sm ${msg.type === 'ok' ? 'text-primary' : 'text-error'}`}>{msg.text}</p>
        )}
        <button
          id="sec-save-btn"
          onClick={handleChange}
          disabled={saving}
          className="self-start px-6 py-2.5 rounded-full bg-primary text-on-primary font-label-caps text-label-caps hover:opacity-90 transition-opacity disabled:opacity-60"
        >
          {saving ? 'Saving…' : 'Update Password'}
        </button>
      </div>
    </SectionCard>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

const TABS: Array<{ id: Tab; label: string; icon: string }> = [
  { id: 'personal', label: 'Personal Info', icon: 'person' },
  { id: 'health', label: 'Health Profile', icon: 'monitor_heart' },
  { id: 'preferences', label: 'Preferences', icon: 'tune' },
  { id: 'security', label: 'Security', icon: 'shield' },
];

export default function Profile() {
  const [tab, setTab] = useState<Tab>('personal');
  const [user, setUser] = useState<UserInfo | null>(null);
  const [profile, setProfile] = useState<HealthProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [meRes, hpRes] = await Promise.allSettled([
          apiClient.get('/api/auth/me'),
          apiClient.get('/api/health-profile'),
        ]);
        if (meRes.status === 'fulfilled') setUser(meRes.value.data.user ?? meRes.value.data);
        if (hpRes.status === 'fulfilled') setProfile(hpRes.value.data.profile);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <Layout title="Account Settings">
        <div className="flex items-center justify-center py-32">
          <span className="material-symbols-outlined animate-spin text-primary text-4xl">progress_activity</span>
        </div>
      </Layout>
    );
  }

  if (!user) {
    return (
      <Layout title="Account Settings">
        <p className="text-on-surface-variant py-16 text-center">Could not load profile.</p>
      </Layout>
    );
  }

  return (
    <Layout title="Account Settings">
      <div className="flex flex-col md:flex-row gap-8 pt-2">
        {/* Sidebar tabs */}
        <nav className="md:w-52 flex-shrink-0">
          <ul className="flex flex-row md:flex-col gap-1 overflow-x-auto md:overflow-visible pb-2 md:pb-0">
            {TABS.map((t) => (
              <li key={t.id}>
                <button
                  id={`profile-tab-${t.id}`}
                  onClick={() => setTab(t.id)}
                  className={[
                    'flex items-center gap-3 w-full px-4 py-3 rounded-xl font-label-caps text-label-caps transition-colors text-left whitespace-nowrap',
                    tab === t.id
                      ? 'bg-primary-container text-on-primary-container font-semibold'
                      : 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-background',
                  ].join(' ')}
                >
                  <span className="material-symbols-outlined text-[18px]">{t.icon}</span>
                  {t.label}
                </button>
              </li>
            ))}
          </ul>
        </nav>

        {/* Tab content */}
        <div className="flex-1 min-w-0">
          {tab === 'personal' && (
            <PersonalTab
              user={user}
              profile={profile}
              onSaved={() => setToast('Your changes have been saved successfully.')}
            />
          )}
          {tab === 'health' && <HealthTab profile={profile} />}
          {tab === 'preferences' && <PreferencesTab profile={profile} />}
          {tab === 'security' && <SecurityTab />}
        </div>
      </div>

      {toast && <Toast message={toast} onClose={() => setToast(null)} />}
    </Layout>
  );
}
