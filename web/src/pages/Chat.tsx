import { useState, useEffect, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';
import Layout from '../components/Layout';
import { apiClient, extractErrorMessage } from '../api/client';
import { HealthProfile, FitnessGoal } from '../types';

// ─── Types ────────────────────────────────────────────────────────────────────

interface ChatMessage {
  id: string;
  role: 'ai' | 'user';
  text: string;
  time: string;
}

interface TodayLog {
  name: string;
  mealType: string;
  calories: number;
  imageUrl?: string;
}

const GOAL_CALORIE_ADJUSTMENT: Record<FitnessGoal, number> = {
  WEIGHT_LOSS: -500,
  WEIGHT_GAIN: 400,
  MUSCLE_GAIN: 300,
  MAINTENANCE: 0,
};

const QUICK_REPLIES = [
  'Yes, show protein shake options',
  'What about Greek yogurt?',
  'No, I want something savory',
  'What should I eat after a workout?',
  'How can I reduce carbs?',
  'Suggest a high-protein breakfast',
];

function now() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// ─── Macro bar ────────────────────────────────────────────────────────────────

function MacroBar({
  label,
  value,
  max,
  color,
}: {
  label: string;
  value: number;
  max: number;
  color: string;
}) {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0;
  return (
    <div className="mb-3">
      <div className="flex justify-between mb-1">
        <span className="font-body-sm text-on-surface-variant">{label}</span>
        <span className="font-body-sm text-on-background font-medium">{Math.round(value)}g</span>
      </div>
      <div className="h-2 rounded-full bg-surface-variant overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
    </div>
  );
}

// ─── Message bubble ───────────────────────────────────────────────────────────

function Bubble({ msg }: { msg: ChatMessage }) {
  const isAI = msg.role === 'ai';
  return (
    <div className={`flex gap-3 ${isAI ? '' : 'flex-row-reverse'} mb-5`}>
      {/* Avatar */}
      <div
        className={`w-9 h-9 rounded-full flex-shrink-0 flex items-center justify-center ${
          isAI ? 'bg-primary text-on-primary' : 'bg-secondary-container text-on-secondary-container'
        }`}
      >
        <span className="material-symbols-outlined text-[18px]">{isAI ? 'smart_toy' : 'person'}</span>
      </div>
      {/* Bubble */}
      <div className={`max-w-[78%] ${isAI ? '' : 'items-end'} flex flex-col gap-1`}>
        <div
          className={`px-4 py-3 rounded-2xl font-body-md text-[14px] leading-relaxed whitespace-pre-wrap ${
            isAI
              ? 'bg-surface border border-outline-variant text-on-background rounded-tl-sm'
              : 'bg-primary text-on-primary rounded-tr-sm'
          }`}
        >
          {msg.text}
        </div>
        <span className="font-body-sm text-on-surface-variant text-[11px] px-1">{msg.time}</span>
      </div>
    </div>
  );
}

// ─── Typing indicator ─────────────────────────────────────────────────────────

function TypingIndicator() {
  return (
    <div className="flex gap-3 mb-5">
      <div className="w-9 h-9 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
        <span className="material-symbols-outlined text-on-primary text-[18px]">smart_toy</span>
      </div>
      <div className="bg-surface border border-outline-variant rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-1.5">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="w-2 h-2 rounded-full bg-on-surface-variant animate-bounce"
            style={{ animationDelay: `${i * 0.15}s` }}
          />
        ))}
      </div>
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '0',
      role: 'ai',
      text: "Hi there! I'm your FitFuel AI nutritionist. How can I help you adjust your meal plan today?",
      time: now(),
    },
  ]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [profile, setProfile] = useState<HealthProfile | null>(null);
  const [todayLogs, setTodayLogs] = useState<TodayLog[]>([]);
  const [quickReplies, setQuickReplies] = useState(QUICK_REPLIES.slice(0, 3));
  const bottomRef = useRef<HTMLDivElement>(null);

  // Load context data
  useEffect(() => {
    async function load() {
      try {
        const [hpRes, logsRes] = await Promise.allSettled([
          apiClient.get('/api/health-profile'),
          apiClient.get('/api/progress/summary'),
        ]);
        if (hpRes.status === 'fulfilled') setProfile(hpRes.value.data.profile);
        if (logsRes.status === 'fulfilled') {
          const logs = logsRes.value.data.logs ?? [];
          // Map latest 2 progress entries to TodayLog shape for display
          setTodayLogs(
            logs.slice(0, 2).map((l: { caloriesConsumed?: number; notes?: string }, i: number) => ({
              name: l.notes || (i === 0 ? 'Breakfast Logged' : 'Lunch Logged'),
              mealType: i === 0 ? 'Breakfast' : 'Lunch',
              calories: l.caloriesConsumed ?? 0,
            }))
          );
        }
      } catch { /* non-fatal */ }
    }
    load();
  }, []);

  // Scroll to bottom on new message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, sending]);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || sending) return;

      const userMsg: ChatMessage = { id: Date.now().toString(), role: 'user', text: text.trim(), time: now() };
      setMessages((prev) => [...prev, userMsg]);
      setInput('');
      setSending(true);
      setQuickReplies([]);

      try {
        const res = await apiClient.post('/api/chat', { message: text.trim() });
        const reply = res.data.reply as string;
        setMessages((prev) => [
          ...prev,
          { id: (Date.now() + 1).toString(), role: 'ai', text: reply, time: now() },
        ]);
        // Rotate quick replies after AI responds
        const start = Math.floor(Math.random() * (QUICK_REPLIES.length - 3));
        setQuickReplies(QUICK_REPLIES.slice(start, start + 3));
      } catch (e) {
        setMessages((prev) => [
          ...prev,
          {
            id: (Date.now() + 1).toString(),
            role: 'ai',
            text: extractErrorMessage(e, "I'm having trouble right now. Please try again in a moment."),
            time: now(),
          },
        ]);
      } finally {
        setSending(false);
      }
    },
    [sending]
  );

  // Compute calorie target
  const calorieTarget = profile?.tdee
    ? Math.max(1200, Math.round(profile.tdee + (GOAL_CALORIE_ADJUSTMENT[profile.fitnessGoal] ?? 0)))
    : null;

  return (
    <Layout title="FitFuel AI">
      <div className="flex gap-6 h-[calc(100vh-120px)]">
        {/* ── Chat panel ─────────────────────────────────────────────────────── */}
        <div className="flex-1 flex flex-col bg-surface border border-outline-variant rounded-2xl overflow-hidden">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-5" id="chat-messages">
            {messages.map((m) => (
              <Bubble key={m.id} msg={m} />
            ))}
            {sending && <TypingIndicator />}
            <div ref={bottomRef} />
          </div>

          {/* Quick reply chips */}
          {quickReplies.length > 0 && !sending && (
            <div className="flex flex-wrap gap-2 px-5 pb-3">
              {quickReplies.map((qr) => (
                <button
                  key={qr}
                  onClick={() => sendMessage(qr)}
                  className="px-3 py-1.5 rounded-full border border-outline-variant text-on-background font-body-sm text-[12px] hover:bg-surface-container-low hover:border-primary hover:text-primary transition-colors"
                >
                  {qr}
                </button>
              ))}
            </div>
          )}

          {/* Input bar */}
          <div className="border-t border-outline-variant p-4 flex items-center gap-3">
            <input
              id="chat-input"
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage(input)}
              placeholder="Type your message…"
              disabled={sending}
              className="flex-1 px-4 py-2.5 rounded-full border border-outline-variant bg-surface-variant text-on-background font-body-md focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-60 transition"
            />
            <button
              id="chat-send"
              onClick={() => sendMessage(input)}
              disabled={sending || !input.trim()}
              className="w-11 h-11 rounded-full bg-primary text-on-primary flex items-center justify-center hover:opacity-90 transition-opacity disabled:opacity-40"
              aria-label="Send message"
            >
              <span className="material-symbols-outlined text-[20px]">send</span>
            </button>
          </div>
        </div>

        {/* ── Context sidebar ─────────────────────────────────────────────────── */}
        <aside className="w-72 flex-shrink-0 flex flex-col gap-4 overflow-y-auto">
          {/* Daily Targets */}
          <div className="bg-surface border border-outline-variant rounded-2xl p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-headline-md text-on-background" style={{ fontSize: '16px' }}>
                Current Plan Context
              </h3>
            </div>

            {profile ? (
              <>
                <p className="font-label-caps text-label-caps text-on-surface-variant mb-1">Daily Targets</p>
                <div className="flex items-center justify-between mb-1">
                  <span
                    className="px-2 py-0.5 rounded-full font-label-caps text-[10px] text-on-primary-container bg-primary-container"
                  >
                    {profile.fitnessGoal.replace('_', ' ')}
                  </span>
                </div>
                <p className="font-headline-md text-on-background mb-4" style={{ fontSize: '34px', fontWeight: 700 }}>
                  {calorieTarget?.toLocaleString()}
                  <span className="font-body-sm text-on-surface-variant text-[14px] ml-1">kcal</span>
                </p>
                <MacroBar label="Protein" value={profile.proteinTargetG ?? 0} max={profile.proteinTargetG ?? 1} color="#2A9D58" />
                <MacroBar label="Carbs" value={profile.carbTargetG ?? 0} max={profile.carbTargetG ?? 1} color="#E76F51" />
                <MacroBar label="Fats" value={profile.fatTargetG ?? 0} max={profile.fatTargetG ?? 1} color="#ADB5BD" />
              </>
            ) : (
              <div className="py-4 text-center">
                <p className="font-body-sm text-on-surface-variant mb-3">
                  Complete your health assessment to see targets.
                </p>
                <Link
                  to="/health-assessment"
                  className="font-label-caps text-label-caps text-primary hover:underline"
                >
                  Start Assessment →
                </Link>
              </div>
            )}
          </div>

          {/* Today's Meals */}
          <div className="bg-surface border border-outline-variant rounded-2xl p-5">
            <h3 className="font-headline-md text-on-background mb-3" style={{ fontSize: '15px' }}>
              Today's Meals Logged
            </h3>
            {todayLogs.length > 0 ? (
              <ul className="flex flex-col gap-3">
                {todayLogs.map((log, i) => (
                  <li key={i} className="flex items-center gap-3">
                    <div className="w-11 h-11 rounded-lg bg-primary-container flex items-center justify-center flex-shrink-0">
                      <span className="material-symbols-outlined text-on-primary-container text-[18px]">
                        {i === 0 ? 'breakfast_dining' : 'lunch_dining'}
                      </span>
                    </div>
                    <div>
                      <p className="font-body-md text-on-background font-medium text-[13px] leading-tight">
                        {log.name}
                      </p>
                      <p className="font-body-sm text-on-surface-variant text-[11px]">
                        {log.mealType} · {log.calories} kcal
                      </p>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="font-body-sm text-on-surface-variant text-[13px]">
                No meals logged today yet.{' '}
                <Link to="/progress" className="text-primary hover:underline">Log one →</Link>
              </p>
            )}
          </div>

          {/* Quick links */}
          <div className="bg-surface border border-outline-variant rounded-2xl p-5">
            <h3 className="font-headline-md text-on-background mb-3" style={{ fontSize: '15px' }}>
              Quick Links
            </h3>
            <div className="flex flex-col gap-2">
              {[
                { to: '/recommendations', icon: 'auto_awesome', label: 'View Recommendations' },
                { to: '/meal-plan', icon: 'restaurant_menu', label: 'Weekly Meal Plan' },
                { to: '/progress', icon: 'insights', label: 'Log Progress' },
              ].map(({ to, icon, label }) => (
                <Link
                  key={to}
                  to={to}
                  className="flex items-center gap-2 px-3 py-2 rounded-xl text-on-surface-variant hover:bg-surface-container-low hover:text-primary transition-colors font-body-sm text-[13px]"
                >
                  <span className="material-symbols-outlined text-[16px]">{icon}</span>
                  {label}
                </Link>
              ))}
            </div>
          </div>
        </aside>
      </div>
    </Layout>
  );
}
