import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Stethoscope, AlertTriangle, ShieldAlert, CheckCircle2, ArrowRight, PhoneCall } from 'lucide-react';
import { DisclaimerBadge } from '../components/DisclaimerBadge';

export const SymptomGuidancePage: React.FC = () => {
  const navigate = useNavigate();
  const [symptoms, setSymptoms] = useState('');
  const [duration, setDuration] = useState('2 days');
  const [guidance, setGuidance] = useState<any>(null);

  const handleCheck = (e: React.FormEvent) => {
    e.preventDefault();
    const stext = symptoms.toLowerCase();
    
    if (stext.includes("chest pain") || stext.includes("severe pressure") || stext.includes("fainting")) {
      setGuidance({
        urgency: "EMERGENCY",
        specialty: "Emergency Cardiology",
        summary: "High concern for acute cardiac ischemia or myocardial injury.",
        actions: [
          "IMMEDIATELY CALL EMRI 108 AMBULANCE OR GO TO NEAREST TRAUMA CENTER",
          "Do not drive yourself to hospital",
          "Chew Aspirin 300mg if advised by paramedic"
        ]
      });
    } else if (stext.includes("breath") || stext.includes("headache") || stext.includes("dizziness")) {
      setGuidance({
        urgency: "URGENT",
        specialty: "Cardiology / Neurology",
        summary: "Exertional dyspnea or neurological symptoms require specialist evaluation within 24-48 hours.",
        actions: [
          "Schedule specialist consultation within 24-48 hours",
          "Avoid heavy physical exertion or climbing stairs",
          "Keep blood pressure and symptom log"
        ]
      });
    } else {
      setGuidance({
        urgency: "LOW",
        specialty: "General Medicine",
        summary: "Mild symptoms requiring routine outpatient follow-up.",
        actions: [
          "Schedule routine outpatient consultation",
          "Monitor symptoms over next 3 days"
        ]
      });
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      
      <div className="text-center max-w-xl mx-auto">
        <h1 className="text-2xl font-black text-slate-900">AI Symptom Guidance & Urgency Checker</h1>
        <p className="text-xs text-slate-500 mt-1">
          Analyzes symptoms to identify urgency levels (Low, Moderate, Urgent, Emergency) and recommend clinical specialties
        </p>
      </div>

      <form onSubmit={handleCheck} className="glass-card rounded-3xl p-6 sm:p-8 border border-slate-200 shadow-lg space-y-4">
        <div>
          <label className="block text-xs font-bold text-slate-700 mb-1">Describe Symptoms</label>
          <textarea
            value={symptoms}
            onChange={(e) => setSymptoms(e.target.value)}
            placeholder="e.g. Chest pressure on walking, shortness of breath, dizziness when climbing stairs..."
            rows={3}
            required
            className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-sky-500"
          ></textarea>
        </div>

        <div>
          <label className="block text-xs font-bold text-slate-700 mb-1">Symptom Duration</label>
          <input
            type="text"
            value={duration}
            onChange={(e) => setDuration(e.target.value)}
            className="w-full px-3.5 py-2 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-sky-500"
          />
        </div>

        <div className="flex items-center justify-between pt-2">
          <DisclaimerBadge type="ai" text="AI Triage Support Only" />

          <button
            type="submit"
            className="flex items-center gap-2 font-bold text-xs text-white gradient-bg px-6 py-2.5 rounded-xl shadow hover:opacity-95 transition-opacity"
          >
            <Stethoscope className="w-4 h-4" />
            <span>Evaluate Symptoms</span>
          </button>
        </div>
      </form>

      {/* Output Guidance */}
      {guidance && (
        <div className={`glass-card rounded-3xl p-6 sm:p-8 border shadow-lg space-y-4 animate-fadeIn ${
          guidance.urgency === 'EMERGENCY' ? 'border-red-300 bg-red-50/50' : 'border-sky-200 bg-sky-50/40'
        }`}>
          
          <div className="flex items-center justify-between">
            <span className={`text-xs font-extrabold uppercase px-3 py-1 rounded-full ${
              guidance.urgency === 'EMERGENCY' ? 'bg-red-600 text-white animate-pulse' : 'bg-sky-600 text-white'
            }`}>
              Urgency Level: {guidance.urgency}
            </span>

            <span className="text-xs font-bold text-slate-700">Specialty: {guidance.specialty}</span>
          </div>

          <div>
            <h3 className="font-extrabold text-slate-900 text-base">{guidance.summary}</h3>
          </div>

          <div className="space-y-2 pt-2 border-t border-slate-200/80 text-xs">
            <p className="font-bold text-slate-900">Recommended Next Steps:</p>
            {guidance.actions.map((act: string, idx: number) => (
              <div key={idx} className="flex items-start gap-2 font-semibold text-slate-800">
                <CheckCircle2 className="w-4 h-4 text-sky-600 shrink-0 mt-0.5" />
                <span>{act}</span>
              </div>
            ))}
          </div>

          {guidance.urgency === 'EMERGENCY' && (
            <div className="pt-3">
              <button
                onClick={() => navigate('/emergency')}
                className="w-full py-3 bg-red-600 text-white font-extrabold text-xs rounded-xl shadow hover:bg-red-700 transition-colors flex items-center justify-center gap-2"
              >
                <PhoneCall className="w-4 h-4" />
                <span>Emergency 108 Trauma Dispatch</span>
              </button>
            </div>
          )}

        </div>
      )}

    </div>
  );
};
