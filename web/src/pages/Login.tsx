import { FormEvent, useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { apiClient, extractErrorMessage, saveToken, getToken } from '../api/client';
import { AuthResponse } from '../types';

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
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
      const res = await apiClient.post<AuthResponse>('/api/auth/login', { email, password });
      saveToken(res.data.token);
      navigate('/dashboard');
    } catch (err: unknown) {
      setError(extractErrorMessage(err, 'Unable to sign in. Please check your credentials.'));
    } finally {
      clearTimeout(wakeTimer);
      setLoading(false);
      setWakingUp(false);
    }
  }

  return (
    <div className="h-full bg-background text-on-background font-body-sm font-sans flex items-center justify-center p-4 sm:p-0 min-h-screen">
      <main className="w-full max-w-[1200px] md:h-[720px] bg-surface rounded-xl flex flex-col md:flex-row overflow-hidden border border-outline-variant shadow-ambient">
        {/* Left Side: Branding & Gradient */}
        <div className="hidden md:flex md:w-1/2 split-gradient p-12 flex-col justify-between text-on-primary">
          <div>
            <h1 className="font-headline-lg text-headline-lg text-on-primary tracking-tight mb-2">
              FitFuel AI
            </h1>
            <p className="font-body-lg text-body-lg text-on-primary/80">Premium Nutrition</p>
          </div>
          <div className="max-w-md">
            <h2 className="font-hero-stat text-hero-stat mb-6">Fuel your body, intelligently.</h2>
            <p className="font-body-lg text-body-lg text-on-primary/90">
              Data-driven insights and personalized meal plans to optimize your daily
              performance and long-term health.
            </p>
          </div>
          <div className="flex gap-4 items-center">
            <div className="w-10 h-10 rounded-full bg-on-primary/20 backdrop-blur-sm flex items-center justify-center">
              <span className="material-symbols-outlined text-on-primary">monitoring</span>
            </div>
            <div className="w-10 h-10 rounded-full bg-on-primary/20 backdrop-blur-sm flex items-center justify-center">
              <span className="material-symbols-outlined text-on-primary">restaurant</span>
            </div>
            <div className="w-10 h-10 rounded-full bg-on-primary/20 backdrop-blur-sm flex items-center justify-center">
              <span className="material-symbols-outlined text-on-primary">auto_awesome</span>
            </div>
          </div>
        </div>

        {/* Right Side: Login Form */}
        <div className="w-full md:w-1/2 p-8 sm:p-12 md:p-16 flex flex-col justify-center bg-surface">
          <div className="mb-8 md:hidden">
            <h1 className="font-headline-lg-mobile text-headline-lg-mobile text-primary tracking-tight">
              FitFuel AI
            </h1>
          </div>
          <div className="mb-10">
            <h2 className="font-headline-lg text-headline-lg text-on-background mb-2">
              Welcome back
            </h2>
            <p className="font-body-sm text-body-sm text-on-surface-variant">
              Please enter your details to sign in.
            </p>
          </div>

          <form className="space-y-6" onSubmit={handleSubmit}>
            {error && (
              <div className="px-4 py-3 rounded-lg bg-error-container text-on-error-container font-body-sm text-body-sm">
                {error}
              </div>
            )}

            {/* Email Input */}
            <div className="space-y-2">
              <label
                className="block font-label-caps text-label-caps text-on-surface-variant uppercase"
                htmlFor="email"
              >
                Email Address
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <span className="material-symbols-outlined text-outline">mail</span>
                </span>
                <input
                  className="w-full pl-12 pr-4 py-3 bg-surface-container-lowest border border-outline-variant rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-colors font-body-sm text-body-sm text-on-surface placeholder:text-outline"
                  id="email"
                  name="email"
                  placeholder="name@example.com"
                  required
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
            </div>

            {/* Password Input */}
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <label
                  className="block font-label-caps text-label-caps text-on-surface-variant uppercase"
                  htmlFor="password"
                >
                  Password
                </label>
              </div>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <span className="material-symbols-outlined text-outline">lock</span>
                </span>
                <input
                  className="w-full pl-12 pr-4 py-3 bg-surface-container-lowest border border-outline-variant rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-colors font-body-sm text-body-sm text-on-surface placeholder:text-outline"
                  id="password"
                  name="password"
                  placeholder="••••••••"
                  required
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
            </div>

            {/* Submit Button */}
            <button
              className="w-full py-3 px-6 bg-primary text-on-primary rounded-full font-headline-md text-body-lg hover:bg-primary-container transition-colors duration-200 mt-4 disabled:opacity-60"
              type="submit"
              disabled={loading}
            >
              {loading ? 'Signing in…' : 'Sign In'}
            </button>
            {wakingUp && (
              <p className="text-center font-body-sm text-primary mt-2">
                Waking up the server, this might take a minute...
              </p>
            )}
          </form>

          <div className="mt-8 text-center">
            <p className="font-body-sm text-body-sm text-on-surface-variant">
              Don&apos;t have an account?{' '}
              <Link
                className="text-primary font-headline-md text-body-sm hover:text-primary-container transition-colors ml-1"
                to="/register"
              >
                Register now
              </Link>
            </p>
          </div>

          <div className="mt-auto pt-12 flex justify-center space-x-6">
            <a className="font-body-sm text-[12px] text-outline hover:text-on-surface-variant transition-colors" href="#">
              Privacy Policy
            </a>
            <a className="font-body-sm text-[12px] text-outline hover:text-on-surface-variant transition-colors" href="#">
              Terms of Service
            </a>
          </div>
        </div>
      </main>
    </div>
  );
}
