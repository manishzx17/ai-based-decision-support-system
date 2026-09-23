import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  FileText, Building2, UserCheck, Calculator,
  Bot, Sparkles, ArrowRight, CheckCircle2
} from 'lucide-react';
import { DisclaimerBadge } from '../components/DisclaimerBadge';
import {
  getCurrentUser, getProfile, getUserReports, getOrResolveActiveReport, getRecommendedHospitals,
  predictTreatmentCost, Hospital, MedicalReport
} from '../services/api';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const user = getCurrentUser();

  const [loading, setLoading] = useState(true);
  const [profileCity, setProfileCity] = useState('Hyderabad');
  const [latestReport, setLatestReport] = useState<MedicalReport | null>(null);
  const [topHospital, setTopHospital] = useState<Hospital | null>(null);
  const [estCost, setEstCost] = useState<number>(220000);

  useEffect(() => {
    async function loadDashboardData() {
      try {
        setLoading(true);
        // 1. Profile
        try {
          const prof = await getProfile(user.id);
          if (prof?.current_city) setProfileCity(prof.current_city);
        } catch {}

        // 2. Active Report
        let activeSpecialty = 'Cardiology';
        try {
          const rep = await getOrResolveActiveReport(user.id);
          if (rep) {
            setLatestReport(rep);
            if (rep.recommended_specialty) {
              activeSpecialty = rep.recommended_specialty;
            }
          }
        } catch {}

        // 3. Recommended Hospitals
        try {
          const hosps = await getRecommendedHospitals({
            specialty: activeSpecialty,
            city: profileCity
          });
          if (hosps && hosps.length > 0) {
            setTopHospital(hosps[0]);
          } else {
            setTopHospital(null);
          }
        } catch {
          setTopHospital(null);
        }

        // 4. Cost
        try {
          const costData = await predictTreatmentCost({
            treatment_name: activeSpecialty === 'Neurology' ? 'Craniotomy' : 'Coronary Angioplasty',
            city: profileCity
          });
          if (costData?.estimated_avg_cost) {
            setEstCost(costData.estimated_avg_cost);
          }
        } catch {}

      } finally {
        setLoading(false);
      }
    }
    loadDashboardData();
  }, [user.id, profileCity]);

  const conditionDisplay = latestReport ? `${latestReport.recommended_specialty} Diagnosis` : 'Cardiovascular Care';
  const specialtyDisplay = latestReport ? latestReport.recommended_specialty : 'Cardiology';

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="gradient-bg rounded-3xl p-6 sm:p-8 text-white shadow-lg relative overflow-hidden">
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-white/20 backdrop-blur-md rounded-full text-xs font-bold mb-3">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Clinical Decision Support Session</span>
          </div>

          <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight">
            Welcome, {user.full_name || 'Patient'}
          </h1>
          <p className="text-sky-100 text-xs sm:text-sm mt-2 leading-relaxed font-medium">
            Condition Focus: <strong>{conditionDisplay}</strong> | Active Specialty: <strong>{specialtyDisplay}</strong>
          </p>

          <div className="flex flex-wrap gap-3 mt-6">
            <button
              onClick={() => navigate('/reports/upload')}
              className="bg-white text-sky-800 hover:bg-sky-50 font-bold text-xs px-4 py-2.5 rounded-xl shadow-md transition-all flex items-center gap-2"
            >
              <FileText className="w-4 h-4 text-sky-600" />
              <span>Upload Medical Report</span>
            </button>

            <button
              onClick={() => navigate('/assistant')}
              className="bg-slate-900/40 hover:bg-slate-900/60 text-white font-bold text-xs px-4 py-2.5 rounded-xl border border-white/20 transition-all flex items-center gap-2"
            >
              <Bot className="w-4 h-4 text-sky-300" />
              <span>Ask AI Assistant</span>
            </button>
          </div>
        </div>
      </div>

      {/* V1 Pipeline Step Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-card rounded-2xl p-5 border border-slate-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-500">Report Status</span>
            <FileText className="w-4 h-4 text-sky-600" />
          </div>
          <p className="font-extrabold text-slate-900 text-base truncate">
            {latestReport ? latestReport.filename : 'Upload Ready'}
          </p>
          <p className="text-[11px] text-emerald-600 font-semibold mt-1 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3" /> OCR + Biomedical NER
          </p>
        </div>

        <div className="glass-card rounded-2xl p-5 border border-slate-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-500">Clinical Specialty</span>
            <UserCheck className="w-4 h-4 text-teal-600" />
          </div>
          <p className="font-extrabold text-slate-900 text-base">{specialtyDisplay}</p>
          <p className="text-[11px] text-slate-500 mt-1">Grounded via Semantic RAG</p>
        </div>

        <div className="glass-card rounded-2xl p-5 border border-slate-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-500">Top Hospital Match</span>
            <Building2 className="w-4 h-4 text-indigo-600" />
          </div>
          {loading ? (
            <div className="space-y-1.5 mt-1">
              <div className="h-5 w-32 bg-slate-200 dark:bg-slate-700 rounded animate-pulse" />
              <div className="h-3 w-20 bg-slate-100 dark:bg-slate-800 rounded animate-pulse" />
            </div>
          ) : topHospital ? (
            <>
              <p className="font-extrabold text-slate-900 text-base truncate">
                {topHospital.name}
              </p>
              <p className="text-[11px] text-sky-600 font-bold mt-1">
                {topHospital.recommendation_score !== undefined ? `${topHospital.recommendation_score.toFixed(1)}% Recommendation Score` : '—'}
              </p>
            </>
          ) : (
            <>
              <p className="font-extrabold text-slate-700 text-sm mt-1">
                No matching provider
              </p>
              <p className="text-[11px] text-slate-400 mt-1">Check filters or upload report</p>
            </>
          )}
        </div>

        <div className="glass-card rounded-2xl p-5 border border-slate-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-500">Est. Treatment Cost</span>
            <Calculator className="w-4 h-4 text-amber-600" />
          </div>
          <p className="font-extrabold text-slate-900 text-base">₹{estCost.toLocaleString()} INR</p>
          <p className="text-[11px] text-slate-500 mt-1">XGBoost & SHAP Explainability</p>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column: Report Insights */}
        <div className="lg:col-span-2 space-y-6">
          
          <div className="glass-card rounded-2xl p-6 border border-slate-200">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-lg font-extrabold text-slate-900">Extracted Clinical Findings</h2>
                <p className="text-xs text-slate-500">Extracted via OCR Engine and Biomedical Named Entity Recognition</p>
              </div>
              <DisclaimerBadge type="ai" text="Biomedical NER" />
            </div>

            <div className="bg-slate-50 rounded-xl p-4 text-xs text-slate-700 mb-4 border border-slate-200/80 leading-relaxed font-mono">
              "{latestReport?.summary || 'Upload diagnostic records to view automated clinical entity extraction, guideline citations, and personalized specialty mapping.'}"
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs mb-4">
              <div className="p-3 bg-red-50/80 rounded-xl border border-red-100">
                <span className="text-[10px] font-bold text-red-600 uppercase">Primary Disease</span>
                <p className="font-bold text-slate-900 mt-0.5 truncate">
                  {latestReport?.entities?.find(e => e.entity_type === 'Disease')?.entity_name || 'CAD / Cardiac'}
                </p>
              </div>
              <div className="p-3 bg-amber-50/80 rounded-xl border border-amber-100">
                <span className="text-[10px] font-bold text-amber-600 uppercase">Test Result</span>
                <p className="font-bold text-slate-900 mt-0.5 truncate">
                  {latestReport?.entities?.find(e => e.entity_type === 'TestResult')?.entity_name || 'LAD Stenosis'}
                </p>
              </div>
              <div className="p-3 bg-sky-50/80 rounded-xl border border-sky-100">
                <span className="text-[10px] font-bold text-sky-600 uppercase">Procedure</span>
                <p className="font-bold text-slate-900 mt-0.5 truncate">
                  {latestReport?.entities?.find(e => e.entity_type === 'Procedure')?.entity_name || 'Angioplasty'}
                </p>
              </div>
              <div className="p-3 bg-emerald-50/80 rounded-xl border border-emerald-100">
                <span className="text-[10px] font-bold text-emerald-600 uppercase">Medication</span>
                <p className="font-bold text-slate-900 mt-0.5 truncate">
                  {latestReport?.entities?.find(e => e.entity_type === 'Medication')?.entity_name || 'Aspirin'}
                </p>
              </div>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-slate-100">
              <Link
                to={latestReport ? `/reports/${latestReport.id}/analysis` : "/reports/upload"}
                className="text-xs font-bold text-sky-600 hover:underline flex items-center gap-1"
              >
                <span>{latestReport ? "View Full Report Analysis & RAG Citations" : "Upload Medical Report to Start"}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>

          {/* V1 Pipeline Roadmap Card */}
          <div className="glass-card rounded-2xl p-6 border border-slate-200">
            <h2 className="text-lg font-extrabold text-slate-900 mb-2">V1 Clinical Decision Pipeline</h2>
            <p className="text-xs text-slate-500 mb-4">Unbroken end-to-end evidence chain supporting patient treatment planning</p>
            
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <span className="font-bold text-sky-700">1. Ingestion & NLP</span>
                <p className="text-slate-600 mt-1 text-[11px]">OCR text extraction & Biomedical NER entity recognition</p>
              </div>
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <span className="font-bold text-sky-700">2. RAG & Recommendations</span>
                <p className="text-slate-600 mt-1 text-[11px]">Grounded clinical guidelines & weighted hospital scoring</p>
              </div>
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <span className="font-bold text-sky-700">3. Prediction & Chat</span>
                <p className="text-slate-600 mt-1 text-[11px]">XGBoost cost/LOS with SHAP & Contextual AI Assistant</p>
              </div>
            </div>
          </div>

        </div>

        {/* Right Column: Recommendations & AI Assistant Links */}
        <div className="space-y-6">

          {/* Top Rated Hospital Card Preview */}
          <div className="glass-card rounded-2xl p-5 border border-slate-200">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-extrabold text-slate-900 text-sm">Top Hospital Match</h3>
              <span className="text-[10px] font-bold bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded border border-emerald-200">
                {loading ? '...' : (topHospital?.recommendation_score !== undefined ? `${topHospital.recommendation_score.toFixed(1)}% Score` : '—')}
              </span>
            </div>

            {loading ? (
              <div className="space-y-2 py-2">
                <div className="h-5 w-44 bg-slate-200 dark:bg-slate-700 rounded animate-pulse" />
                <div className="h-3 w-32 bg-slate-100 dark:bg-slate-800 rounded animate-pulse" />
              </div>
            ) : topHospital ? (
              <>
                <p className="font-bold text-slate-900 text-base">{topHospital.name}</p>
                <p className="text-xs text-slate-500 mb-3">{topHospital.city} | {topHospital.distance_km ? `${topHospital.distance_km} km` : 'Multi-specialty hub'}</p>
              </>
            ) : (
              <div className="py-2">
                <p className="font-bold text-slate-700 text-sm">No Provider in Current Benchmark</p>
                <p className="text-xs text-slate-400 mb-3">No matching facility in benchmark repository</p>
              </div>
            )}

            <ul className="text-xs text-slate-600 space-y-1 mb-4">
              <li className="flex items-center gap-1.5 text-emerald-700 font-semibold">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" /> Specialty: {specialtyDisplay}
              </li>
              <li className="flex items-center gap-1.5 text-slate-700">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" /> Verified Clinical Guideline Grounding
              </li>
            </ul>

            <button
              onClick={() => navigate('/hospitals')}
              className="w-full py-2.5 rounded-xl font-bold text-xs text-white gradient-bg shadow hover:opacity-95 transition-opacity"
            >
              Explore Hospital Recommendations
            </button>
          </div>

          {/* AI Healthcare Assistant Card */}
          <div className="glass-card rounded-2xl p-5 border border-slate-200">
            <div className="flex items-center gap-2 mb-2">
              <Bot className="w-5 h-5 text-sky-600" />
              <h3 className="font-bold text-slate-900 text-sm">AI Healthcare Assistant</h3>
            </div>
            <p className="text-xs text-slate-600 mb-3 leading-relaxed">
              Ask questions about your clinical report, verified medical guidelines, treatment options, or cost estimates.
            </p>
            <button
              onClick={() => navigate('/assistant')}
              className="w-full py-2.5 rounded-xl font-bold text-xs text-slate-800 bg-sky-50 border border-sky-200 hover:bg-sky-100 transition-colors flex items-center justify-center gap-2"
            >
              <Bot className="w-4 h-4 text-sky-600" />
              <span>Launch AI Assistant</span>
            </button>
          </div>

          {/* Cost Estimator Card */}
          <div className="glass-card rounded-2xl p-5 border border-slate-200">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-bold text-slate-900 text-sm">Treatment Cost & LOS</h3>
              <Calculator className="w-4 h-4 text-amber-600" />
            </div>
            <p className="text-xs text-slate-600 mb-3">
              Predict treatment expenses and length of stay with transparent SHAP feature attributions.
            </p>
            <button
              onClick={() => navigate('/cost')}
              className="w-full py-2 rounded-xl font-bold text-xs text-slate-700 bg-slate-100 hover:bg-slate-200 transition-colors"
            >
              Open Cost & LOS Estimator
            </button>
          </div>

        </div>

      </div>
    </div>
  );
};
