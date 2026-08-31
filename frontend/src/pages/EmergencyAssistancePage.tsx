import React from 'react';
import { PhoneCall, AlertTriangle, MapPin, Building2, ShieldAlert, Navigation } from 'lucide-react';
import { DisclaimerBadge } from '../components/DisclaimerBadge';

export const EmergencyAssistancePage: React.FC = () => {
  return (
    <div className="max-w-3xl mx-auto space-y-6">
      
      {/* High Visibility Emergency Header */}
      <div className="bg-gradient-to-br from-red-600 via-rose-600 to-red-700 text-white rounded-3xl p-6 sm:p-8 shadow-xl text-center space-y-4">
        <div className="w-16 h-16 bg-white/20 backdrop-blur-md rounded-full flex items-center justify-center mx-auto text-amber-300 animate-pulse">
          <PhoneCall className="w-8 h-8" />
        </div>

        <span className="text-xs font-black uppercase tracking-widest bg-white/20 px-3 py-1 rounded-full border border-white/30">
          Statewide Emergency Hotline
        </span>

        <h1 className="text-4xl sm:text-5xl font-black tracking-tight">DIAL 108</h1>
        <p className="text-xs sm:text-sm font-semibold text-rose-100 max-w-md mx-auto">
          GVK EMRI Medical Emergency Ambulance & Trauma Dispatch Service
        </p>

        <div className="pt-2">
          <a
            href="tel:108"
            className="inline-flex items-center gap-2 bg-white text-red-700 font-black text-sm px-8 py-3.5 rounded-2xl shadow-lg hover:bg-rose-50 transition-all scale-100 hover:scale-105"
          >
            <PhoneCall className="w-5 h-5" />
            <span>Call 108 Now (Toll Free)</span>
          </a>
        </div>
      </div>

      {/* Immediate Nearest Trauma Hospitals */}
      <div className="glass-card rounded-3xl p-6 sm:p-8 border border-red-200 bg-red-50/20 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
            <Building2 className="w-5 h-5 text-red-600" />
            Nearest 24/7 Cardiac Trauma Emergency Centers
          </h2>

          <DisclaimerBadge type="emergency" text="Direct Emergency Access (No AI Delay)" />
        </div>

        <div className="space-y-3">
          {[
            {
              name: "Apollo Emergency Trauma & Critical Care",
              address: "Road No 72, Jubilee Hills, Hyderabad",
              dist: "4.2 km away (12 mins)",
              phone: "+91 40 1066 / +91 40 2360 7777"
            },
            {
              name: "Yashoda Emergency Casualty Department",
              address: "Raj Bhavan Road, Somajiguda, Hyderabad",
              dist: "6.1 km away (18 mins)",
              phone: "+91 40 4567 4567"
            }
          ].map((t, i) => (
            <div key={i} className="p-4 bg-white rounded-2xl border border-red-200 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-sm">
              <div>
                <h3 className="font-extrabold text-slate-900 text-sm">{t.name}</h3>
                <p className="text-slate-500 mt-0.5">{t.address} • <strong>{t.dist}</strong></p>
                <p className="font-bold text-red-700 mt-1">Direct Casualty Line: {t.phone}</p>
              </div>

              <a
                href={`tel:${t.phone.split('/')[0].trim()}`}
                className="flex items-center justify-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold text-white bg-red-600 hover:bg-red-700 transition-colors shrink-0"
              >
                <PhoneCall className="w-3.5 h-3.5" />
                <span>Call Center</span>
              </a>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
};
