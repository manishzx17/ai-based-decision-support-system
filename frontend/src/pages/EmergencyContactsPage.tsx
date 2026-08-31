import React from 'react';
import { Contact, Phone, User, ShieldAlert } from 'lucide-react';
import { DisclaimerBadge } from '../components/DisclaimerBadge';

export const EmergencyContactsPage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900">Emergency Contacts Directory</h1>
          <p className="text-xs text-slate-500 mt-1">Personal and municipal emergency helplines</p>
        </div>

        <DisclaimerBadge type="emergency" text="Verified Helpline Directory" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Personal Contacts */}
        <div className="glass-card rounded-2xl p-6 border border-slate-200 space-y-3">
          <h3 className="font-extrabold text-slate-900 text-sm flex items-center gap-2">
            <User className="w-4 h-4 text-sky-600" />
            Personal Primary Emergency Contacts
          </h3>

          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 text-xs space-y-1">
            <p className="font-bold text-slate-900 text-sm">Sunita Verma (Spouse)</p>
            <p className="text-slate-600">Relationship: Primary Next of Kin</p>
            <p className="font-bold text-sky-700 flex items-center gap-1 mt-1">
              <Phone className="w-3.5 h-3.5" /> +91 98765 12345
            </p>
          </div>
        </div>

        {/* Municipal & Public Contacts */}
        <div className="glass-card rounded-2xl p-6 border border-slate-200 space-y-3">
          <h3 className="font-extrabold text-slate-900 text-sm flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-red-600" />
            Public Emergency Helplines
          </h3>

          <div className="space-y-2 text-xs">
            <div className="p-3 bg-red-50 rounded-xl border border-red-200 flex items-center justify-between text-red-900 font-bold">
              <span>GVK EMRI Ambulance Dispatch</span>
              <span>108</span>
            </div>
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between font-bold text-slate-800">
              <span>State Police Control Room</span>
              <span>100</span>
            </div>
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between font-bold text-slate-800">
              <span>National Disaster Response Force (NDRF)</span>
              <span>1078</span>
            </div>
          </div>
        </div>

      </div>

    </div>
  );
};
