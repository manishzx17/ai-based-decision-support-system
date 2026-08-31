import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Shield, PhoneCall, Globe, User, Bell, Sparkles, Moon, Sun } from 'lucide-react';

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

  return (
    <header className="sticky top-0 z-40 w-full bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 shadow-sm transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Brand Logo */}
        <Link to="/dashboard" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-xl gradient-bg flex items-center justify-center text-white font-black text-xl shadow-md group-hover:scale-105 transition-transform">
            12C
          </div>
          <div>
            <div className="flex items-center gap-1.5 font-extrabold text-slate-900 dark:text-white tracking-tight text-lg">
              MedicalTravel <span className="text-sky-600 dark:text-sky-400 font-bold text-xs px-2 py-0.5 bg-sky-50 dark:bg-sky-950/60 rounded-full border border-sky-200 dark:border-sky-800">AI Support</span>
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 font-medium">Decision Support System</p>
          </div>
        </Link>

        {/* Quick Search & Actions */}
        <div className="hidden md:flex items-center gap-6">
          <Link to="/reports/upload" className="flex items-center gap-1.5 text-xs font-semibold text-sky-700 dark:text-sky-300 bg-sky-50 dark:bg-sky-950/50 hover:bg-sky-100 dark:hover:bg-sky-900/60 px-3 py-1.5 rounded-lg transition-colors border border-sky-200 dark:border-sky-800">
            <Sparkles className="w-3.5 h-3.5 text-sky-600 dark:text-sky-400" />
            Analyze Report
          </Link>
          
          <Link to="/hospitals/compare" className="text-xs font-semibold text-slate-600 dark:text-slate-300 hover:text-sky-600 dark:hover:text-sky-400 transition-colors">
            Compare Hospitals
          </Link>

          <Link to="/symptoms" className="text-xs font-semibold text-slate-600 dark:text-slate-300 hover:text-sky-600 dark:hover:text-sky-400 transition-colors">
            Symptom Checker
          </Link>
        </div>

        {/* Right Action Icons & Dark Mode Toggle */}
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

          {/* Emergency Hotline Direct Button */}
          <Link
            to="/emergency"
            className="flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white font-bold text-xs px-3.5 py-2 rounded-xl shadow-md hover:shadow-red-200 transition-all animate-pulse-slow"
          >
            <PhoneCall className="w-4 h-4" />
            <span className="hidden sm:inline">Emergency 108</span>
          </Link>

          <div className="h-6 w-px bg-slate-200 dark:bg-slate-800 hidden sm:block"></div>

          {/* Language Indicator */}
          <Link to="/translate" className="p-2 text-slate-500 dark:text-slate-400 hover:text-sky-600 dark:hover:text-sky-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors" title="Medical Translation">
            <Globe className="w-5 h-5" />
          </Link>

          {/* Profile Menu */}
          <button
            onClick={() => navigate('/profile')}
            className="flex items-center gap-2 p-1.5 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors text-slate-700 dark:text-slate-200"
          >
            <div className="w-8 h-8 rounded-full bg-slate-800 dark:bg-sky-700 text-white flex items-center justify-center font-bold text-xs shadow-inner">
              RV
            </div>
            <span className="text-xs font-bold text-slate-700 dark:text-slate-200 hidden lg:inline">Rajesh V.</span>
          </button>
        </div>

      </div>
    </header>
  );
};
