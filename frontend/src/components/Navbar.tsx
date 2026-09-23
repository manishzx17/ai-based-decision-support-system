import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Moon, Sun, LogOut } from 'lucide-react';
import { getCurrentUser, logoutApi } from '../services/api';

export const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const [isDark, setIsDark] = useState<boolean>(() => {
    return localStorage.getItem('theme') === 'dark' ||
      (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches);
  });

  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  }, [isDark]);

  const toggleDarkMode = () => {
    setIsDark(prev => !prev);
  };

  const user = getCurrentUser();

  const handleLogout = async () => {
    await logoutApi();
    navigate('/login');
  };

  return (
    <header className="sticky top-0 z-40 w-full bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 shadow-sm transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 relative flex items-center justify-between">
        
        {/* Brand - Centered in navbar header */}
        <div className="absolute left-1/2 -translate-x-1/2 text-center pointer-events-auto">
          <Link to="/dashboard" className="inline-flex flex-col items-center group">
            <div className="font-extrabold text-slate-900 dark:text-white tracking-tight text-base sm:text-lg hover:text-sky-600 dark:hover:text-sky-400 transition-colors">
              AI Based Decision Support System
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 font-medium">V1 Core Pipeline</p>
          </Link>
        </div>

        {/* Empty left spacer for flex layout balance */}
        <div className="w-10 sm:w-16"></div>

        {/* Theme & User Profile Actions */}
        <div className="flex items-center gap-3">
          
          {/* Dark Mode Switch Button */}
          <button
            onClick={toggleDarkMode}
            className="p-2 rounded-xl text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            title={isDark ? "Switch to Light Mode" : "Switch to Dark Mode"}
            aria-label="Toggle Dark Mode"
          >
            {isDark ? (
              <Sun className="w-5 h-5 text-amber-400 fill-amber-400" />
            ) : (
              <Moon className="w-5 h-5 text-slate-600" />
            )}
          </button>

          <div className="h-6 w-px bg-slate-200 dark:bg-slate-800 hidden sm:block"></div>

          {/* Active Demo User Badge */}
          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-[11px] font-bold text-slate-700 dark:text-slate-200">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="truncate max-w-[110px]">{user.full_name?.split(' ')[0]}</span>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-sky-100 dark:bg-sky-950 text-sky-700 dark:text-sky-300 font-semibold uppercase">
              {user.specialty || 'Demo'}
            </span>
          </div>

          {/* Profile Menu */}
          <button
            onClick={() => navigate('/profile')}
            className="flex items-center gap-2 p-1.5 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors text-slate-700 dark:text-slate-200"
            title="View Patient Clinical Profile"
          >
            <div className="w-8 h-8 rounded-full bg-slate-800 dark:bg-sky-700 text-white flex items-center justify-center font-bold text-xs shadow-inner">
              {user.full_name?.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase() || 'RV'}
            </div>
            <span className="text-xs font-bold text-slate-700 dark:text-slate-200 hidden lg:inline">
              {user.full_name?.split(' ')[0] || 'Patient'}
            </span>
          </button>

          {/* Logout / Switch Patient Action */}
          <button
            onClick={handleLogout}
            className="flex items-center gap-1.5 p-2 text-xs font-semibold text-slate-600 dark:text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30 rounded-xl transition-colors"
            title="Switch Demo Patient / Logout"
            aria-label="Logout and switch demo patient"
          >
            <LogOut className="w-4 h-4" />
            <span className="hidden xl:inline text-[11px] font-bold">Logout</span>
          </button>
        </div>

      </div>
    </header>
  );
};
