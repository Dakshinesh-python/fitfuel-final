import { FormEvent, useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { apiClient, extractErrorMessage, saveToken, getToken } from '../api/client';
import { AuthResponse } from '../types';

export default function Register() {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [age, setAge] = useState('');
  const [gender, setGender] = useState('');
  const [heightCm, setHeightCm] = useState('');
  const [weightKg, setWeightKg] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [wakingUp, setWakingUp] = useState(false);

  useEffect(() => {
    if (getToken()) {
      navigate('/dashboard');
    }
  }, [navigate]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    setWakingUp(false);
    
    const wakeTimer = setTimeout(() => {
      setWakingUp(true);
    }, 4000);

    try {
      const res = await apiClient.post<AuthResponse>('/api/auth/register', {
        name,
        email,
        password,
        age: age ? Number(age) : undefined,
        gender: gender || undefined,
        heightCm: heightCm ? Number(heightCm) : undefined,
        weightKg: weightKg ? Number(weightKg) : undefined,
      });
      saveToken(res.data.token);
      navigate('/health-assessment');
    } catch (err: unknown) {
      setError(extractErrorMessage(err, 'Unable to create your account. Please try again.'));
    } finally {
      clearTimeout(wakeTimer);
      setLoading(false);
      setWakingUp(false);
    }
  }

  return (
    <div className="bg-background text-on-background min-h-screen flex flex-col md:flex-row antialiased">
      {/* Left: Branding & Imagery */}
      <div className="hidden md:flex md:w-1/2 bg-surface-container-low relative flex-col justify-between p-container-padding-desktop">
        <div className="relative z-10">
          <h1 className="font-headline-lg text-headline-lg text-primary tracking-tight">
            FitFuel AI
          </h1>
          <p className="font-body-lg text-body-lg text-on-surface-variant mt-2 max-w-md">
            Join the premier platform for AI-driven nutrition and wellness management.
          </p>
        </div>
        <div className="absolute inset-0 z-0">
          <div className="w-full h-full split-gradient opacity-90" />
          <div className="absolute inset-0 bg-gradient-to-b from-surface-container-low/80 via-transparent to-surface-container-low/40" />
        </div>
        <div className="relative z-10">
          <div className="inline-flex items-center gap-2 bg-surface/80 backdrop-blur-md px-4 py-2 rounded-full border border-outline-variant shadow-sm">
            <span className="material-symbols-outlined text-primary text-xl">verified</span>
            <span className="font-label-caps text-label-caps text-on-surface">
              Precision Nutrition Tracking
            </span>
          </div>
        </div>
      </div>

      {/* Right: Registration Form */}
      <div className="w-full md:w-1/2 flex flex-col justify-center px-container-padding-mobile py-12 md:px-20 lg:px-32 bg-surface-bright">
        {/* Mobile Logo */}
        <div className="md:hidden mb-8 text-center">
          <h1 className="font-headline-lg-mobile text-headline-lg-mobile text-primary tracking-tight">
            FitFuel AI
          </h1>
          <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">
            Premium Nutrition
          </p>
        </div>

        <div className="max-w-md w-full mx-auto">
          <h2 className="font-headline-md text-headline-md text-on-surface mb-2">
            Create Account
          </h2>
          <p className="font-body-sm text-body-sm text-on-surface-variant mb-8">
            Enter your details to build your personalized profile.
          </p>

          <form className="space-y-6" onSubmit={handleSubmit}>
            {error && (
              <div className="px-4 py-3 rounded-lg bg-error-container text-on-error-container font-body-sm text-body-sm">
                {error}
              </div>
            )}

            {/* Name */}
            <div>
              <label className="block font-label-caps text-label-caps text-on-surface-variant mb-2" htmlFor="name">
                Full Name
              </label>
              <input
                className="w-full bg-surface border border-outline-variant rounded-full py-3 px-4 font-body-sm text-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-colors"
                id="name"
                name="name"
                placeholder="Alex Carter"
                required
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>

            {/* Email */}
            <div>
              <label className="block font-label-caps text-label-caps text-on-surface-variant mb-2" htmlFor="email">
                Email Address
              </label>
              <input
                className="w-full bg-surface border border-outline-variant rounded-full py-3 px-4 font-body-sm text-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-colors"
                id="email"
                name="email"
                placeholder="alex@example.com"
                required
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>

            {/* Password */}
            <div>
              <label className="block font-label-caps text-label-caps text-on-surface-variant mb-2" htmlFor="password">
                Password
              </label>
              <input
                className="w-full bg-surface border border-outline-variant rounded-full py-3 px-4 font-body-sm text-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-colors"
                id="password"
                name="password"
                placeholder="••••••••"
                required
                minLength={8}
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <p className="font-body-sm text-on-surface-variant mt-1 text-xs">
                Password must be at least 8 characters.
              </p>
            </div>

            {/* Biometrics Grid */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block font-label-caps text-label-caps text-on-surface-variant mb-2" htmlFor="age">
                  Age
                </label>
                <input
                  className="w-full bg-surface border border-outline-variant rounded-full py-3 px-4 font-body-sm text-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-colors"
                  id="age"
                  name="age"
                  placeholder="28"
                  type="number"
                  value={age}
                  onChange={(e) => setAge(e.target.value)}
                />
              </div>
              <div>
                <label className="block font-label-caps text-label-caps text-on-surface-variant mb-2" htmlFor="gender">
                  Gender
                </label>
                <select
                  className="w-full bg-surface border border-outline-variant rounded-full py-3 px-4 font-body-sm text-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-colors appearance-none"
                  id="gender"
                  name="gender"
                  value={gender}
                  onChange={(e) => setGender(e.target.value)}
                >
                  <option value="">Select</option>
                  <option value="MALE">Male</option>
                  <option value="FEMALE">Female</option>
                  <option value="OTHER">Other</option>
                </select>
              </div>
              <div>
                <label className="block font-label-caps text-label-caps text-on-surface-variant mb-2" htmlFor="height">
                  Height (cm)
                </label>
                <input
                  className="w-full bg-surface border border-outline-variant rounded-full py-3 px-4 font-body-sm text-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-colors"
                  id="height"
                  name="height"
                  placeholder="175"
                  type="number"
                  value={heightCm}
                  onChange={(e) => setHeightCm(e.target.value)}
                />
              </div>
              <div>
                <label className="block font-label-caps text-label-caps text-on-surface-variant mb-2" htmlFor="weight">
                  Weight (kg)
                </label>
                <input
                  className="w-full bg-surface border border-outline-variant rounded-full py-3 px-4 font-body-sm text-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-colors"
                  id="weight"
                  name="weight"
                  placeholder="70"
                  type="number"
                  value={weightKg}
                  onChange={(e) => setWeightKg(e.target.value)}
                />
              </div>
            </div>

            <div className="pt-4">
              <button
                className="w-full py-3 px-6 bg-primary text-on-primary rounded-full font-headline-md text-body-lg hover:bg-primary-container transition-colors duration-200 mt-4 disabled:opacity-60"
                type="submit"
                disabled={loading}
              >
                {loading ? 'Creating Account…' : 'Create Account'}
              </button>
              {wakingUp && (
                <p className="text-center font-body-sm text-primary mt-2">
                  Waking up the server, this might take a minute...
                </p>
              )}
            </div>
          </form>

          <div className="mt-8 text-center">
            <p className="font-body-sm text-body-sm text-on-surface-variant">
              Already have an account?{' '}
              <Link className="text-primary font-medium hover:underline" to="/login">
                Log In
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
