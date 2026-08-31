import React from 'react';
import { Info, ShieldAlert, Heart, Droplets, Activity } from 'lucide-react';
import { DisclaimerBadge } from '../components/DisclaimerBadge';

export const LocalHealthPage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900">Local Health Information & Advisories</h1>
          <p className="text-xs text-slate-500 mt-1">Destination Health Hub: Hyderabad, Telangana</p>
        </div>

        <DisclaimerBadge type="database" text="Verified Local Health Directory" />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        
        {/* Health Advisories */}
        <div className="glass-card rounded-2xl p-6 border border-slate-200 space-y-3">
          <h3 className="font-extrabold text-slate-900 text-sm flex items-center gap-2">
            <Info className="w-4 h-4 text-sky-600" />
            Destination Health Advisories
          </h3>
          
          <ul className="space-y-2 text-xs text-slate-700">
            <li className="p-3 bg-slate-50 rounded-xl border border-slate-200">
              <strong>Seasonal Viral Precaution:</strong> Drink bottled/filtered water and carry mosquito repellent.
            </li>
            <li className="p-3 bg-slate-50 rounded-xl border border-slate-200">
              <strong>International Traveler Vaccination:</strong> Airport Health Office available for yellow fever & polio clearance.
            </li>
          </ul>
        </div>

        {/* Blood Banks */}
        <div className="glass-card rounded-2xl p-6 border border-slate-200 space-y-3">
          <h3 className="font-extrabold text-slate-900 text-sm flex items-center gap-2">
            <Droplets className="w-4 h-4 text-rose-600" />
            24/7 Regional Blood Banks
          </h3>

          <div className="space-y-2 text-xs">
            <div className="p-3 bg-rose-50 rounded-xl border border-rose-200 text-rose-900">
              <p className="font-bold">Chiranjeevi Charitable Blood Bank Central</p>
              <p className="text-[11px]">Phone: +91 40 2355 4545 | Jubilee Hills, Hyderabad</p>
            </div>
            <div className="p-3 bg-rose-50 rounded-xl border border-rose-200 text-rose-900">
              <p className="font-bold">Central Red Cross Blood Bank</p>
              <p className="text-[11px]">Phone: +91 40 2320 2345 | Lakdikapul, Hyderabad</p>
            </div>
          </div>
        </div>

      </div>

    </div>
  );
};
