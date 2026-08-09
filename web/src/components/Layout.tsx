import { ReactNode } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { clearToken } from '../api/client';

interface LayoutProps {
  title: string;
  children: ReactNode;
}

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: 'dashboard' },
  { to: '/recommendations', label: 'Recommendations', icon: 'auto_awesome' },
  { to: '/progress', label: 'Progress', icon: 'insights' },
];

export default function Layout({ title, children }: LayoutProps) {
  const navigate = useNavigate();

  function handleLogout() {
    clearToken();
    navigate('/login');
  }

  return (
    <div className="bg-background text-on-background antialiased selection:bg-primary-container selection:text-on-primary-container min-h-screen flex flex-col md:flex-row">
      {/* SideNavBar (Desktop) */}
      <nav className="hidden md:flex flex-col bg-surface border-r border-outline-variant fixed left-0 top-0 h-screen w-64 py-8 px-4 z-50">
        <div className="mb-12 px-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-primary-container flex items-center justify-center">
            <span
              className="material-symbols-outlined text-on-primary-container fill"
            >
              analytics
            </span>
          </div>
          <div>
            <h1
              className="font-headline-lg text-primary tracking-tight"
              style={{ fontSize: '24px', lineHeight: '28px' }}
            >
              FitFuel AI
            </h1>
            <p className="font-label-caps text-label-caps text-on-surface-variant">
              Premium Nutrition
            </p>
          </div>
        </div>
        <ul className="flex flex-col gap-2 flex-grow">
          {navItems.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                className={({ isActive }) =>
                  [
                    'flex items-center gap-3 px-4 py-3 rounded-lg font-medium transition-colors duration-200',
                    isActive
                      ? 'text-primary font-bold border-l-4 border-primary bg-surface-container-low'
                      : 'text-on-surface-variant hover:bg-surface-container-high hover:text-primary',
                  ].join(' ')
                }
              >
                <span className="material-symbols-outlined">{item.icon}</span>
                <span className="font-label-caps text-label-caps">{item.label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
        <div className="mt-auto pt-8">
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-full border border-outline-variant text-on-surface-variant hover:bg-surface-container-low transition-colors duration-200"
          >
            <span className="material-symbols-outlined">logout</span>
            <span className="font-label-caps text-label-caps">Logout</span>
          </button>
        </div>
      </nav>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col md:ml-64 w-full">
        {/* TopNavBar */}
        <header className="sticky top-0 z-40 flex justify-between items-center h-20 px-8 bg-surface/80 backdrop-blur-xl border-b border-outline-variant w-full">
          <div className="md:hidden">
            <h1 className="font-headline-md text-headline-md text-primary">FitFuel AI</h1>
          </div>
          <div className="hidden md:block">
            <h2 className="font-headline-md text-headline-md text-on-surface">{title}</h2>
          </div>
          <div className="flex items-center gap-6">
            <button
              onClick={handleLogout}
              className="md:hidden text-on-surface-variant hover:text-primary transition-opacity duration-200 focus:outline-none focus:ring-2 focus:ring-primary/20 rounded-full p-2"
              aria-label="Logout"
            >
              <span className="material-symbols-outlined">logout</span>
            </button>
            <div className="w-10 h-10 rounded-full bg-primary-container flex items-center justify-center border border-outline-variant">
              <span className="material-symbols-outlined text-on-primary-container">person</span>
            </div>
          </div>
        </header>

        {/* Canvas */}
        <main className="flex-1 p-container-padding-mobile md:p-container-padding-desktop overflow-y-auto">
          <div className="max-w-7xl mx-auto">{children}</div>
        </main>
      </div>
    </div>
  );
}
