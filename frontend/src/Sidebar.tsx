import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, FileText, Upload, Bot, Building2, UserCheck,
  Calculator, Pill, Stethoscope, ShieldCheck, Languages, Hotel,
  Navigation, Plane, Info, PhoneCall, Contact, FolderHeart, Settings,
  GitCompare, CalendarCheck, Home
} from 'lucide-react';

interface NavGroup {
  title: string;
  items: { name: string; path: string; icon: React.FC<{ className?: string }> }[];
}

const navGroups: NavGroup[] = [
  {
    title: 'Core Platform',
    items: [
      { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
      { name: 'Upload Report', path: '/reports/upload', icon: Upload },
      { name: 'Report Analysis', path: '/reports/1/analysis', icon: FileText },
      { name: 'AI Healthcare Assistant', path: '/assistant', icon: Bot },
      { name: 'Medical Profile', path: '/profile', icon: FolderHeart },
    ]
  },
  {
    title: 'Healthcare Discovery',
    items: [
      { name: 'Hospital Finder', path: '/hospitals', icon: Building2 },
      { name: 'Hospital Compare', path: '/hospitals/compare', icon: GitCompare },
      { name: 'Doctor Recommendations', path: '/doctors', icon: UserCheck },
      { name: 'Book Appointment', path: '/appointments/book', icon: CalendarCheck },
      { name: 'Treatment Cost Estimator', path: '/cost', icon: Calculator },
    ]
  },
  {
    title: 'Travel & Assistance',
    items: [
      { name: 'Medical Travel Planner', path: '/travel-planner', icon: Plane },
      { name: 'Accommodation Stay', path: '/accommodation', icon: Hotel },
      { name: 'A* Navigation Map', path: '/navigation', icon: Navigation },
      { name: 'Pharmacy Finder 24x7', path: '/pharmacies', icon: Pill },
      { name: 'Insurance Coverage', path: '/insurance', icon: ShieldCheck },
    ]
  },
  {
    title: 'Clinical & Emergency',
    items: [
      { name: 'Symptom Guidance', path: '/symptoms', icon: Stethoscope },
      { name: 'Medical Translation', path: '/translate', icon: Languages },
      { name: 'Local Health Info', path: '/local-health', icon: Info },
      { name: 'Emergency Assistance', path: '/emergency', icon: PhoneCall },
      { name: 'Emergency Contacts', path: '/emergency-contacts', icon: Contact },
      { name: 'My Medical Records', path: '/records', icon: FolderHeart },
      { name: 'Settings', path: '/settings', icon: Settings },
    ]
  }
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 shrink-0 hidden md:block min-h-[calc(100vh-4rem)] p-4 overflow-y-auto transition-colors">
      <div className="space-y-6">
        {navGroups.map((group, idx) => (
          <div key={idx}>
            <h3 className="text-[11px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider px-3 mb-2">
              {group.title}
            </h3>
            <ul className="space-y-1">
              {group.items.map((item) => {
                const Icon = item.icon;
                return (
                  <li key={item.path}>
                    <NavLink
                      to={item.path}
                      className={({ isActive }) =>
                        `flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-semibold transition-all ${
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
        ))}
      </div>
    </aside>
  );
};
