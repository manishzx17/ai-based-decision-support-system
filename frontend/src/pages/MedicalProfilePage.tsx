import React, { useState } from 'react';
import { User, Phone, MapPin, ShieldAlert, Heart, Save, CheckCircle2 } from 'lucide-react';

export const MedicalProfilePage: React.FC = () => {
  const [saved, setSaved] = useState(false);
  const [profile, setProfile] = useState({
    fullName: 'Rajesh Verma',
    age: 48,
    gender: 'Male',
    bloodGroup: 'B+',
    allergies: 'Penicillin',
    chronicConditions: 'Hypertension, Type 2 Diabetes',
    currentCity: 'Hyderabad',
    emergencyContactName: 'Sunita Verma (Spouse)',
    emergencyContactPhone: '+91 98765 12345',
    preferredInsurance: 'Star Health Insurance'
  });

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-black text-slate-900">Patient Medical Profile</h1>
        <p className="text-xs text-slate-500 mt-1">Manage your health history, emergency contacts, and insurance preferences</p>
      </div>

      {saved && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl text-emerald-800 text-xs font-bold flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>Patient profile successfully updated!</span>
        </div>
      )}

      <form onSubmit={handleSave} className="glass-card rounded-3xl p-6 sm:p-8 border border-slate-200 space-y-6">
        
        {/* Personal Details */}
        <div>
          <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider text-sky-600 mb-4">
            Personal & Health Vitals
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Full Name</label>
              <input
                type="text"
                value={profile.fullName}
                onChange={(e) => setProfile({ ...profile, fullName: e.target.value })}
                className="w-full px-3.5 py-2 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-sky-500"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Age</label>
              <input
                type="number"
                value={profile.age}
                onChange={(e) => setProfile({ ...profile, age: parseInt(e.target.value) || 0 })}
                className="w-full px-3.5 py-2 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-sky-500"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Blood Group</label>
              <select
                value={profile.bloodGroup}
                onChange={(e) => setProfile({ ...profile, bloodGroup: e.target.value })}
                className="w-full px-3.5 py-2 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-sky-500"
              >
                {['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-'].map(b => (
                  <option key={b} value={b}>{b}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Clinical History */}
        <div>
          <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider text-sky-600 mb-4">
            Clinical History & Allergies
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Known Drug Allergies</label>
              <input
                type="text"
                value={profile.allergies}
                onChange={(e) => setProfile({ ...profile, allergies: e.target.value })}
                className="w-full px-3.5 py-2 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-sky-500"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Chronic Conditions</label>
              <input
                type="text"
                value={profile.chronicConditions}
                onChange={(e) => setProfile({ ...profile, chronicConditions: e.target.value })}
                className="w-full px-3.5 py-2 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-sky-500"
              />
            </div>
          </div>
        </div>

        {/* Emergency & Location */}
        <div>
          <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider text-red-600 mb-4">
            Emergency Contacts & Insurance
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Emergency Contact Person</label>
              <input
                type="text"
                value={profile.emergencyContactName}
                onChange={(e) => setProfile({ ...profile, emergencyContactName: e.target.value })}
                className="w-full px-3.5 py-2 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-sky-500"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Emergency Phone Number</label>
              <input
                type="text"
                value={profile.emergencyContactPhone}
                onChange={(e) => setProfile({ ...profile, emergencyContactPhone: e.target.value })}
                className="w-full px-3.5 py-2 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-sky-500"
              />
            </div>
          </div>
        </div>

        <div className="pt-4 border-t border-slate-100 flex justify-end">
          <button
            type="submit"
            className="flex items-center gap-2 font-bold text-xs text-white gradient-bg px-6 py-2.5 rounded-xl shadow hover:opacity-95 transition-all"
          >
            <Save className="w-4 h-4" />
            <span>Save Profile Changes</span>
          </button>
        </div>

      </form>
    </div>
  );
};
