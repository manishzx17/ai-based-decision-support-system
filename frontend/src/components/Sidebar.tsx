import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, FileText, Upload, Bot, Building2,
  Calculator, FolderHeart, Navigation
} from 'lucide-react';

interface NavItem {
  name: string;
  path: string;
  icon: React.FC<{ className?: string }>;
}

const navItems: NavItem[] = [
  { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { name: 'Medical Report Intelligence', path: '/reports/upload', icon: Upload },
  { name: 'Clinical Profile', path: '/profile', icon: FolderHeart },
  { name: 'Medical Analysis / RAG', path: '/analysis', icon: FileText },
  { name: 'Personalized Hospital Recommendations', path: '/hospitals', icon: Building2 },
  { name: 'Cost & Length of Stay Prediction', path: '/cost', icon: Calculator },
  { name: 'AI Healthcare Assistant', path: '/assistant', icon: Bot },
  { name: 'Medical Travel & Local Connectivity', path: '/travel', icon: Navigation },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 shrink-0 hidden md:block min-h-[calc(100vh-4rem)] p-4 overflow-y-auto transition-colors">
      <div className="space-y-6">
        <div>
          <h3 className="text-[11px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider px-3 mb-3">
            Decision Support Pipeline
          </h3>
          <ul className="space-y-1.5">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <li key={item.path}>
                  <NavLink
                    to={item.path}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                        isActive
                          ? 'bg-sky-50 dark:bg-sky-950/60 text-sky-700 dark:text-sky-400 shadow-sm border border-sky-100 dark:border-sky-800'
                          : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white'
                      }`
                    }
                  >
                    <Icon className="w-4 h-4 text-sky-600 dark:text-sky-400 shrink-0" />
                    <span>{item.name}</span>
                  </NavLink>
                </li>
              );
            })}
          </ul>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;

