import React, { useState, useEffect } from 'react';
import {
  User, Phone, MapPin, ShieldAlert, Heart, Save, CheckCircle2, Loader2, AlertCircle,
  Activity, ClipboardList, Pill, Scissors, TestTube2, Thermometer, FileText
} from 'lucide-react';
import { getProfile, updateProfile, getCurrentUser, PatientProfile } from '../services/api';

export const MedicalProfilePage: React.FC = () => {
  const currentUser = getCurrentUser();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [fullName, setFullName] = useState(currentUser.full_name || 'Patient');
  const [profile, setProfile] = useState<PatientProfile>({
    age: 30,
    gender: 'Other',
    blood_group: 'O+',
    allergies: 'None',
    chronic_conditions: 'None',
    current_city: 'Hyderabad',
    preferred_currency: 'INR',
    emergency_contact_name: 'Emergency Contact',
    emergency_contact_phone: '+91 98765 43210',
    conditions: [],
    symptoms: [],
    tests: [],
    test_results: [],
    medications: [],
    procedures: [],
    medical_history: [],
    last_report_id: undefined
  });

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const data = await getProfile(currentUser.id);
        if (data) {
          setFullName(currentUser.full_name || 'Patient');
          setProfile({
            age: data.age !== undefined && data.age !== null ? data.age : 30,
            gender: data.gender || 'Other',
            blood_group: data.blood_group || 'O+',
            allergies: data.allergies || 'None',
            chronic_conditions: data.chronic_conditions || 'None',
            current_city: data.current_city || 'Hyderabad',
            preferred_currency: data.preferred_currency || 'INR',
            emergency_contact_name: data.emergency_contact_name || 'Family Member',
            emergency_contact_phone: data.emergency_contact_phone || '+91 98765 43210',
            conditions: data.conditions || [],
            symptoms: data.symptoms || [],
            tests: data.tests || [],
            test_results: data.test_results || [],
            medications: data.medications || [],
            procedures: data.procedures || [],
            medical_history: data.medical_history || [],
            last_report_id: data.last_report_id
          });
        }
      } catch (err: any) {
        console.warn('Could not load remote profile, using cached defaults', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [currentUser.id]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSaved(false);

    try {
      await updateProfile(profile, currentUser.id);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err: any) {
      setError(err.message || 'Failed to update profile.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12 text-slate-500 gap-2">
        <Loader2 className="w-6 h-6 animate-spin text-sky-600" />
        <span className="text-sm font-semibold">Loading patient medical profile...</span>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-black text-slate-900">Patient Medical Profile</h1>
        <p className="text-xs text-slate-500 mt-1">Manage your health history, emergency contacts, and insurance preferences</p>
      </div>

      {saved && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl text-emerald-800 text-xs font-bold flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>Patient profile successfully updated in database!</span>
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-2xl text-red-800 text-xs font-bold flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
          <span>{error}</span>
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
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
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
                value={profile.blood_group}
                onChange={(e) => setProfile({ ...profile, blood_group: e.target.value })}
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
                value={profile.chronic_conditions}
                onChange={(e) => setProfile({ ...profile, chronic_conditions: e.target.value })}
                className="w-full px-3.5 py-2 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-sky-500"
              />
            </div>
          </div>
        </div>

        {/* Phase 3: Persistent Structured Clinical Profile */}
        {( (profile.conditions && profile.conditions.length > 0) ||
           (profile.symptoms && profile.symptoms.length > 0) ||
           (profile.tests && profile.tests.length > 0) ||
           (profile.test_results && profile.test_results.length > 0) ||
           (profile.medications && profile.medications.length > 0) ||
           (profile.procedures && profile.procedures.length > 0) ||
           (profile.medical_history && profile.medical_history.length > 0) ) && (
          <div className="p-5 rounded-2xl bg-slate-50/80 border border-slate-200 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <ClipboardList className="w-4 h-4 text-sky-600" />
                  Persistent Structured Clinical Profile
                </h3>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Shared patient context derived from report intelligence and medical history.
                </p>
              </div>
              {profile.last_report_id ? (
                <span className="text-[10px] font-bold text-sky-700 bg-sky-100 px-2.5 py-1 rounded-full border border-sky-200">
                  Synced with Report #{profile.last_report_id}
                </span>
              ) : (
                <span className="text-[10px] font-bold text-slate-600 bg-slate-200 px-2.5 py-1 rounded-full">
                  Demo Session (user_id: {currentUser.id})
                </span>
              )}
            </div>

            {/* Conditions */}
            {profile.conditions && profile.conditions.length > 0 && (
              <div>
                <span className="text-[11px] font-bold text-slate-700 block mb-1.5">Explicitly Reported Conditions:</span>
                <div className="flex flex-wrap gap-1.5">
                  {profile.conditions.map((c, i) => (
                    <span key={i} className="px-2.5 py-1 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs font-semibold">
                      {c}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Symptoms */}
            {profile.symptoms && profile.symptoms.length > 0 && (
              <div>
                <span className="text-[11px] font-bold text-slate-700 block mb-1.5 flex items-center gap-1">
                  <Thermometer className="w-3.5 h-3.5 text-amber-500" />
                  Documented Symptoms & Complaints:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {profile.symptoms.map((s, i) => (
                    <span key={i} className="px-2.5 py-1 rounded-lg bg-amber-50 border border-amber-200 text-amber-900 text-xs">
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Tests Performed */}
            {profile.tests && profile.tests.length > 0 && (
              <div>
                <span className="text-[11px] font-bold text-slate-700 block mb-1.5 flex items-center gap-1">
                  <TestTube2 className="w-3.5 h-3.5 text-sky-500" />
                  Diagnostic Investigations:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {profile.tests.map((t, i) => (
                    <span key={i} className="px-2.5 py-1 rounded-lg bg-sky-50 border border-sky-200 text-sky-800 text-xs">
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Structured Lab Measurements */}
            {profile.test_results && profile.test_results.length > 0 && (
              <div>
                <span className="text-[11px] font-bold text-slate-700 block mb-1.5 flex items-center gap-1">
                  <Activity className="w-3.5 h-3.5 text-indigo-500" />
                  Key Laboratory & Diagnostic Measurements:
                </span>
                <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
                      <tr>
                        <th className="px-3 py-1.5">Test</th>
                        <th className="px-3 py-1.5">Value</th>
                        <th className="px-3 py-1.5">Unit</th>
                        <th className="px-3 py-1.5">Ref. Range</th>
                        <th className="px-3 py-1.5">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {profile.test_results.map((tr, i) => (
                        <tr key={i}>
                          <td className="px-3 py-1.5 font-semibold text-slate-900">{tr.test_name}</td>
                          <td className="px-3 py-1.5 font-mono text-slate-800">{tr.value}</td>
                          <td className="px-3 py-1.5 text-slate-500">{tr.unit || '—'}</td>
                          <td className="px-3 py-1.5 text-slate-500">{tr.reference_range || '—'}</td>
                          <td className="px-3 py-1.5">
                            {tr.status ? (
                              <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                tr.status.toLowerCase().includes('critical') || tr.status.toLowerCase().includes('high')
                                  ? 'bg-rose-100 text-rose-700'
                                  : tr.status.toLowerCase().includes('low')
                                  ? 'bg-amber-100 text-amber-700'
                                  : 'bg-emerald-100 text-emerald-700'
                              }`}>
                                {tr.status}
                              </span>
                            ) : '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Medications */}
            {profile.medications && profile.medications.length > 0 && (
              <div>
                <span className="text-[11px] font-bold text-slate-700 block mb-1.5 flex items-center gap-1">
                  <Pill className="w-3.5 h-3.5 text-teal-600" />
                  Active Medications:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {profile.medications.map((m, i) => (
                    <span key={i} className="px-2.5 py-1 rounded-lg bg-teal-50 border border-teal-200 text-teal-800 text-xs">
                      {m}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Procedures */}
            {profile.procedures && profile.procedures.length > 0 && (
              <div>
                <span className="text-[11px] font-bold text-slate-700 block mb-1.5 flex items-center gap-1">
                  <Scissors className="w-3.5 h-3.5 text-purple-600" />
                  Procedures Performed / Planned:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {profile.procedures.map((p, i) => (
                    <span key={i} className="px-2.5 py-1 rounded-lg bg-purple-50 border border-purple-200 text-purple-800 text-xs">
                      {p}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Medical History */}
            {profile.medical_history && profile.medical_history.length > 0 && (
              <div>
                <span className="text-[11px] font-bold text-slate-700 block mb-1.5 flex items-center gap-1">
                  <ClipboardList className="w-3.5 h-3.5 text-slate-600" />
                  Medical History & Comorbidities:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {profile.medical_history.map((h, i) => (
                    <span key={i} className="px-2.5 py-1 rounded-lg bg-slate-100 border border-slate-200 text-slate-800 text-xs">
                      {h}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Emergency & Location */}
        <div>
          <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider text-red-600 mb-4">
            Emergency Contacts & Location
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Current City</label>
              <input
                type="text"
                value={profile.current_city}
                onChange={(e) => setProfile({ ...profile, current_city: e.target.value })}
                className="w-full px-3.5 py-2 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-sky-500"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Emergency Contact Person</label>
              <input
                type="text"
                value={profile.emergency_contact_name}
                onChange={(e) => setProfile({ ...profile, emergency_contact_name: e.target.value })}
                className="w-full px-3.5 py-2 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-sky-500"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Emergency Phone Number</label>
              <input
                type="text"
                value={profile.emergency_contact_phone}
                onChange={(e) => setProfile({ ...profile, emergency_contact_phone: e.target.value })}
                className="w-full px-3.5 py-2 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-sky-500"
              />
            </div>
          </div>
        </div>

        <div className="pt-4 border-t border-slate-100 flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="flex items-center gap-2 font-bold text-xs text-white gradient-bg px-6 py-2.5 rounded-xl shadow hover:opacity-95 transition-all disabled:opacity-60"
          >
            {saving ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Saving Profile...</span>
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                <span>Save Profile Changes</span>
              </>
            )}
          </button>
        </div>

      </form>
    </div>
  );
};
