import React from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  FileText, Building2, UserCheck, Calculator, Plane, PhoneCall,
  Bot, ShieldAlert, Sparkles, ArrowRight, CheckCircle2, Clock, MapPin
} from 'lucide-react';
import { DisclaimerBadge } from '../components/DisclaimerBadge';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="gradient-bg rounded-3xl p-6 sm:p-8 text-white shadow-lg relative overflow-hidden">
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-white/20 backdrop-blur-md rounded-full text-xs font-bold mb-3">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Active Medical Decision Support Session</span>
          </div>

          <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight">
            Welcome back, Rajesh Verma
          </h1>
          <p className="text-sky-100 text-xs sm:text-sm mt-2 leading-relaxed font-medium">
            Primary Condition: <strong>Severe Double Vessel CAD</strong> | Recommended Specialty: <strong>Cardiology</strong>
          </p>

          <div className="flex flex-wrap gap-3 mt-6">
            <button
              onClick={() => navigate('/reports/upload')}
              className="bg-white text-sky-800 hover:bg-sky-50 font-bold text-xs px-4 py-2.5 rounded-xl shadow-md transition-all flex items-center gap-2"
            >
              <FileText className="w-4 h-4 text-sky-600" />
              <span>Upload New Report</span>
            </button>

            <button
              onClick={() => navigate('/assistant')}
              className="bg-slate-900/40 hover:bg-slate-900/60 text-white font-bold text-xs px-4 py-2.5 rounded-xl border border-white/20 transition-all flex items-center gap-2"
            >
              <Bot className="w-4 h-4 text-sky-300" />
              <span>Chat with AI Assistant</span>
            </button>
          </div>
        </div>
      </div>

      {/* Analytics Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-card rounded-2xl p-5 border border-slate-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-500">Latest Medical Report</span>
            <FileText className="w-4 h-4 text-sky-600" />
          </div>
          <p className="font-extrabold text-slate-900 text-base">Angiography_Report.pdf</p>
          <p className="text-[11px] text-emerald-600 font-semibold mt-1 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3" /> Processed via OCR & BioBERT
          </p>
        </div>

        <div className="glass-card rounded-2xl p-5 border border-slate-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-500">Recommended Specialty</span>
            <UserCheck className="w-4 h-4 text-teal-600" />
          </div>
          <p className="font-extrabold text-slate-900 text-base">Interventional Cardiology</p>
          <p className="text-[11px] text-slate-500 mt-1">Matched 5 Top Specialists</p>
        </div>

        <div className="glass-card rounded-2xl p-5 border border-slate-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-500">Top Recommended Hospital</span>
            <Building2 className="w-4 h-4 text-indigo-600" />
          </div>
          <p className="font-extrabold text-slate-900 text-base">Apollo Jubilee Hills</p>
          <p className="text-[11px] text-sky-600 font-bold mt-1">96.5% Weighted Match</p>
        </div>

        <div className="glass-card rounded-2xl p-5 border border-slate-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-500">Est. Procedure Cost</span>
            <Calculator className="w-4 h-4 text-amber-600" />
          </div>
          <p className="font-extrabold text-slate-900 text-base">₹2,20,000 INR</p>
          <p className="text-[11px] text-slate-500 mt-1">XGBoost ML Estimate (±10%)</p>
        </div>
      </div>

      {/* Main Grid: Report Summary & Hospital Recommendations */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column: Report Insights */}
        <div className="lg:col-span-2 space-y-6">
          
          <div className="glass-card rounded-2xl p-6 border border-slate-200">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-lg font-extrabold text-slate-900">Extracted Clinical Report Insights</h2>
                <p className="text-xs text-slate-500">Analyzed by OCR Engine & ClinicalBERT Entity Recognition</p>
              </div>
              <DisclaimerBadge type="ai" text="ClinicalBERT NLP Output" />
            </div>

            <div className="bg-slate-50 rounded-xl p-4 text-xs text-slate-700 mb-4 border border-slate-200/80 leading-relaxed font-mono">
              "Patient presents with exertional angina. Angiography reveals LAD 85% proximal stenosis, RCA 70% stenosis. LVEF 55%. Elective PCI with Drug-Eluting Stents advised under Interventional Cardiology."
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs mb-4">
              <div className="p-3 bg-red-50/80 rounded-xl border border-red-100">
                <span className="text-[10px] font-bold text-red-600 uppercase">Primary Disease</span>
                <p className="font-bold text-slate-900 mt-0.5">Double Vessel CAD</p>
              </div>
              <div className="p-3 bg-amber-50/80 rounded-xl border border-amber-100">
                <span className="text-[10px] font-bold text-amber-600 uppercase">Primary Symptom</span>
                <p className="font-bold text-slate-900 mt-0.5">Exertional Angina</p>
              </div>
              <div className="p-3 bg-sky-50/80 rounded-xl border border-sky-100">
                <span className="text-[10px] font-bold text-sky-600 uppercase">Procedure</span>
                <p className="font-bold text-slate-900 mt-0.5">Angioplasty / PCI</p>
              </div>
              <div className="p-3 bg-emerald-50/80 rounded-xl border border-emerald-100">
                <span className="text-[10px] font-bold text-emerald-600 uppercase">Medication</span>
                <p className="font-bold text-slate-900 mt-0.5">Aspirin 75mg</p>
              </div>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-slate-100">
              <Link to="/reports/1/analysis" className="text-xs font-bold text-sky-600 hover:underline flex items-center gap-1">
                <span>View Full Medical Entity Analysis</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>

          {/* Quick Itinerary & Navigation */}
          <div className="glass-card rounded-2xl p-6 border border-slate-200">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-lg font-extrabold text-slate-900">Medical Travel Itinerary Summary</h2>
                <p className="text-xs text-slate-500">Destination: Hyderabad Medical Hub (Apollo Jubilee Hills)</p>
              </div>
              <Link to="/travel-planner" className="text-xs font-bold text-sky-600 hover:underline">
                View Full Itinerary
              </Link>
            </div>

            <div className="space-y-3">
              {[
                { day: 'Day 1', task: 'Fly in from Bengaluru -> Taj Jubilee Stays Check-in', status: 'Completed' },
                { day: 'Day 2', task: '09:30 AM Doctor Consultation with Dr. K. Srinivas Rao', status: 'Upcoming' },
                { day: 'Day 3', task: 'Elective Angioplasty Procedure & IPD Admission', status: 'Scheduled' },
              ].map((st, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs">
                  <div className="flex items-center gap-3">
                    <span className="font-bold text-sky-700 bg-sky-100 px-2 py-0.5 rounded text-[11px]">{st.day}</span>
                    <span className="font-semibold text-slate-800">{st.task}</span>
                  </div>
                  <span className="text-[11px] font-bold text-slate-500">{st.status}</span>
                </div>
              ))}
            </div>
          </div>

        </div>

        {/* Right Column: Recommended Hospitals & Emergency Panel */}
        <div className="space-y-6">

          {/* Emergency Quick Action */}
          <div className="bg-gradient-to-br from-red-600 to-rose-700 text-white rounded-2xl p-5 shadow-md">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-rose-200 mb-2">
              <ShieldAlert className="w-4 h-4 text-amber-300" />
              <span>Emergency Assistance</span>
            </div>
            <h3 className="text-lg font-extrabold mb-1">Need Immediate Emergency Care?</h3>
            <p className="text-xs text-rose-100 mb-4 leading-relaxed">
              Instantly locate nearest 24/7 cardiac trauma unit or dispatch EMRI 108 ambulance.
            </p>
            <button
              onClick={() => navigate('/emergency')}
              className="w-full bg-white text-red-700 hover:bg-rose-50 font-extrabold text-xs py-2.5 rounded-xl shadow transition-colors flex items-center justify-center gap-2"
            >
              <PhoneCall className="w-4 h-4" />
              <span>Launch Emergency Hotline (108)</span>
            </button>
          </div>

          {/* Top Rated Hospital Card Preview */}
          <div className="glass-card rounded-2xl p-5 border border-slate-200">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-extrabold text-slate-900 text-sm">Top Recommendation</h3>
              <span className="text-[10px] font-bold bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded border border-emerald-200">96.5% Score</span>
            </div>

            <p className="font-bold text-slate-900 text-base">Apollo Hospitals Jubilee Hills</p>
            <p className="text-xs text-slate-500 mb-3">Hyderabad | 4.2 km from stay</p>

            <ul className="text-xs text-slate-600 space-y-1 mb-4">
              <li className="flex items-center gap-1.5 text-emerald-700 font-semibold">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Direct Specialty Match (Cardiology)
              </li>
              <li className="flex items-center gap-1.5 text-slate-700">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Star Health & HDFC ERGO Cashless
              </li>
            </ul>

            <button
              onClick={() => navigate('/hospitals')}
              className="w-full py-2.5 rounded-xl font-bold text-xs text-white gradient-bg shadow hover:opacity-95 transition-opacity"
            >
              Explore Top Hospitals
            </button>
          </div>

          {/* Medical Translation Quick Widget */}
          <div className="glass-card rounded-2xl p-5 border border-slate-200">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-bold text-slate-900 text-sm">Medical Translation</h3>
              <span className="text-[10px] text-sky-600 font-semibold">Telugu / Hindi</span>
            </div>
            <p className="text-xs text-slate-600 mb-3">Translate prescription instructions into local regional languages.</p>
            <button
              onClick={() => navigate('/translate')}
              className="w-full py-2 rounded-xl font-bold text-xs text-slate-700 bg-slate-100 hover:bg-slate-200 transition-colors"
            >
              Open Translator Tool
            </button>
          </div>

        </div>

      </div>
    </div>
  );
};
