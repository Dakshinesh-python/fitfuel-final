import { ReactNode } from 'react';
import { NavLink, Link, useNavigate } from 'react-router-dom';
import { clearToken } from '../api/client';

interface LayoutProps {
  title: string;
  children: ReactNode;
}

const navItems = [
  { to: '/dashboard',       label: 'Dashboard',       icon: 'dashboard' },
  { to: '/recommendations', label: 'Recommendations', icon: 'auto_awesome' },
  { to: '/meal-plan',       label: 'Meal Plan',        icon: 'restaurant_menu' },
  { to: '/progress',        label: 'Progress',         icon: 'insights' },
  { to: '/chat',            label: 'Chat',             icon: 'chat' },
  { to: '/profile',         label: 'Profile',          icon: 'person' },
];

export default function Layout({ title, children }: LayoutProps) {
  const navigate = useNavigate();

  function handleLogout() {
    clearToken();
    navigate('/login');
  }

  return (
    <div className="bg-background text-on-background antialiased selection:bg-primary-container selection:text-on-primary-container min-h-screen flex flex-col md:flex-row">

      {/* ── SideNavBar (Desktop) ── */}
      <nav
        className="hidden md:flex flex-col fixed left-0 top-0 h-screen w-64 py-8 px-4 z-50"
        style={{
          background: 'linear-gradient(180deg, #0d1f16 0%, #132b1e 60%, #0d1f16 100%)',
          borderRight: '1px solid rgba(255,255,255,0.06)',
        }}
      >
        {/* Brand */}
        <div className="mb-10 px-3 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 overflow-hidden"
            style={{ background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.15)' }}
          >
            <img src={`${import.meta.env.BASE_URL}logo.png`} alt="FitFuel AI logo" className="w-full h-full object-contain" />
          </div>
          <div>
            <h1 className="font-bold text-white tracking-tight" style={{ fontSize: '18px', lineHeight: '22px' }}>
              FitFuel AI
            </h1>
            <p className="text-[11px] font-medium" style={{ color: 'rgba(255,255,255,0.45)', letterSpacing: '0.06em' }}>
              PREMIUM NUTRITION
            </p>
          </div>
        </div>

        {/* Divider */}
        <div className="mx-3 mb-6 h-px" style={{ background: 'rgba(255,255,255,0.07)' }} />

        {/* Nav items */}
        <ul className="flex flex-col gap-1 flex-grow">
          {navItems.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                className={({ isActive }) =>
                  [
                    'flex items-center gap-3 px-3 py-2.5 rounded-xl font-medium transition-all duration-200 group',
                    isActive
                      ? 'text-white'
                      : 'hover:bg-white/5',
                  ].join(' ')
                }
                style={({ isActive }) =>
                  isActive
                    ? { background: 'rgba(42,157,88,0.25)', border: '1px solid rgba(42,157,88,0.35)' }
                    : { border: '1px solid transparent' }
                }
              >
                {({ isActive }) => (
                  <>
                    <span
                      className="material-symbols-outlined text-[20px] flex-shrink-0 transition-colors"
                      style={{ color: isActive ? '#2A9D58' : 'rgba(255,255,255,0.45)' }}
                    >
                      {item.icon}
                    </span>
                    <span
                      className="text-[13px] font-semibold transition-colors"
                      style={{ color: isActive ? 'white' : 'rgba(255,255,255,0.55)' }}
                    >
                      {item.label}
                    </span>
                    {isActive && (
                      <span className="ml-auto w-1.5 h-1.5 rounded-full bg-primary flex-shrink-0" />
                    )}
                  </>
                )}
              </NavLink>
            </li>
          ))}
        </ul>

        {/* Divider */}
        <div className="mx-3 mb-4 h-px" style={{ background: 'rgba(255,255,255,0.07)' }} />

        {/* Logout */}
        <div className="px-0">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 hover:bg-white/5"
            style={{ border: '1px solid transparent' }}
          >
            <span className="material-symbols-outlined text-[20px]" style={{ color: 'rgba(255,255,255,0.35)' }}>
              logout
            </span>
            <span className="text-[13px] font-semibold" style={{ color: 'rgba(255,255,255,0.40)' }}>
              Logout
            </span>
          </button>
        </div>
      </nav>

      {/* ── Main Content Area ── */}
      <div className="flex-1 flex flex-col md:ml-64 w-full">

        {/* Top header bar */}
        <header className="sticky top-0 z-40 flex justify-between items-center h-16 px-8 w-full"
          style={{
            background: 'rgba(255,255,255,0.85)',
            backdropFilter: 'blur(16px)',
            borderBottom: '1px solid rgba(0,0,0,0.06)',
          }}
        >
          {/* Mobile brand */}
          <div className="md:hidden flex items-center gap-2">
            <img src={`${import.meta.env.BASE_URL}logo.png`} alt="FitFuel AI" className="w-7 h-7 object-contain" />
            <h1 className="font-bold text-primary" style={{ fontSize: '18px' }}>FitFuel AI</h1>
          </div>

          {/* Desktop page title */}
          <div className="hidden md:flex items-center gap-2">
            <h2 className="font-semibold text-on-surface" style={{ fontSize: '17px' }}>{title}</h2>
          </div>

          {/* Right: mobile logout + profile avatar */}
          <div className="flex items-center gap-3">
            <button
              onClick={handleLogout}
              className="md:hidden text-on-surface-variant hover:text-primary transition-colors focus:outline-none rounded-full p-2"
              aria-label="Logout"
            >
              <span className="material-symbols-outlined">logout</span>
            </button>
            <Link
              to="/profile"
              id="header-profile-link"
              className="w-9 h-9 rounded-full flex items-center justify-center transition-all hover:ring-2 hover:ring-primary/40"
              style={{ background: 'linear-gradient(135deg, #2A9D58, #1B7A41)', border: '2px solid rgba(42,157,88,0.3)' }}
              aria-label="Go to profile"
            >
              <span className="material-symbols-outlined text-white text-[18px]">person</span>
            </Link>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 p-container-padding-mobile md:p-container-padding-desktop overflow-y-auto">
          <div className="max-w-7xl mx-auto">{children}</div>
        </main>
      </div>
    </div>
  );
}
