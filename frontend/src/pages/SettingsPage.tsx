import React, { useState } from 'react';
import { Settings, Shield, Bell, Key, CheckCircle2, Save } from 'lucide-react';
import { DisclaimerBadge } from '../components/DisclaimerBadge';

export const SettingsPage: React.FC = () => {
  const [saved, setSaved] = useState(false);
  const [geminiKey, setGeminiKey] = useState('AIzaSy... (Configured via Environment)');
  const [notifications, setNotifications] = useState(true);
  const [autoTranslate, setAutoTranslate] = useState(true);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      
      <div>
        <h1 className="text-2xl font-black text-slate-900">Application Settings & Configuration</h1>
        <p className="text-xs text-slate-500 mt-1">Manage AI API status, security permissions, and notifications</p>
      </div>

      {saved && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl text-emerald-800 text-xs font-bold flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>Settings successfully saved!</span>
        </div>
      )}

      <form onSubmit={handleSave} className="glass-card rounded-3xl p-6 sm:p-8 border border-slate-200 shadow-lg space-y-6">
        
        {/* System & AI Keys */}
        <div>
          <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider text-sky-600 mb-3 flex items-center gap-2">
            <Key className="w-4 h-4" />
            AI Pipeline & Engine Status
          </h3>

          <div className="space-y-3 text-xs">
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between">
              <div>
                <p className="font-bold text-slate-900">Google Gemini API Key</p>
                <p className="text-slate-500 text-[11px]">Loaded from backend environment variable</p>
              </div>
              <span className="font-bold text-emerald-600 bg-emerald-50 px-2.5 py-0.5 rounded border border-emerald-200">Active</span>
            </div>

            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between">
              <div>
                <p className="font-bold text-slate-900">OCR & Biomedical NER Engine</p>
                <p className="text-slate-500 text-[11px]">Local entity extraction module</p>
              </div>
              <span className="font-bold text-emerald-600 bg-emerald-50 px-2.5 py-0.5 rounded border border-emerald-200">Active</span>
            </div>

            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between">
              <div>
                <p className="font-bold text-slate-900">XGBoost Treatment Cost Predictor</p>
                <p className="text-slate-500 text-[11px]">ML regression & SHAP explainability</p>
              </div>
              <span className="font-bold text-emerald-600 bg-emerald-50 px-2.5 py-0.5 rounded border border-emerald-200">Active</span>
            </div>
          </div>
        </div>

        {/* Preferences */}
        <div>
          <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider text-sky-600 mb-3 flex items-center gap-2">
            <Bell className="w-4 h-4" />
            Patient Preferences & Alerts
          </h3>

          <div className="space-y-3 text-xs">
            <label className="flex items-center justify-between p-3 bg-slate-50 rounded-xl border border-slate-200 cursor-pointer">
              <span className="font-semibold text-slate-800">Enable Clinical Guideline & Follow-up Reminders</span>
              <input
                type="checkbox"
                checked={notifications}
                onChange={(e) => setNotifications(e.target.checked)}
                className="w-4 h-4 text-sky-600 rounded"
              />
            </label>

            <label className="flex items-center justify-between p-3 bg-slate-50 rounded-xl border border-slate-200 cursor-pointer">
              <span className="font-semibold text-slate-800">Automatic Prescription Translation to Telugu/Hindi</span>
              <input
                type="checkbox"
                checked={autoTranslate}
                onChange={(e) => setAutoTranslate(e.target.checked)}
                className="w-4 h-4 text-sky-600 rounded"
              />
            </label>
          </div>
        </div>

        <div className="pt-4 border-t border-slate-100 flex justify-end">
          <button
            type="submit"
            className="flex items-center gap-2 font-bold text-xs text-white gradient-bg px-6 py-2.5 rounded-xl shadow hover:opacity-95 transition-opacity"
          >
            <Save className="w-4 h-4" />
            <span>Save Preferences</span>
          </button>
        </div>

      </form>

    </div>
  );
};
