import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Sparkles, Upload, Building2, Calculator, ShieldCheck,
  Bot, ArrowRight, Activity, FileText, UserCheck
} from 'lucide-react';
import { DisclaimerBadge } from '../components/DisclaimerBadge';

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Hero Section */}
      <section className="relative overflow-hidden pt-12 pb-20 bg-gradient-to-b from-sky-50/80 via-white to-slate-50 border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto">
            
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-sky-100/80 border border-sky-200 text-sky-800 text-xs font-extrabold mb-6 animate-pulse">
              <Sparkles className="w-4 h-4 text-sky-600" />
              <span>AI Based Decision Support System</span>
            </div>

            <h1 className="text-4xl sm:text-6xl font-black text-slate-900 tracking-tight leading-tight mb-6">
              AI-Based Clinical <span className="gradient-text">Decision Support</span>
            </h1>

            <p className="text-lg text-slate-600 font-medium mb-8 leading-relaxed">
              Medical Report Intelligence → Clinical Profile → Medical Analysis / RAG → Personalized Hospital Recommendations → Cost & Length of Stay Prediction → AI Healthcare Assistant → Medical Travel & Local Connectivity.
            </p>

            {/* CTAs */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-10">
              <button
                onClick={() => navigate('/reports/upload')}
                className="w-full sm:w-auto flex items-center justify-center gap-2 font-bold text-sm text-white gradient-bg px-7 py-3.5 rounded-xl shadow-lg hover:shadow-sky-200 transition-all scale-100 hover:scale-105"
              >
                <Upload className="w-4 h-4" />
                <span>Upload Medical Report</span>
                <ArrowRight className="w-4 h-4" />
              </button>

              <button
                onClick={() => navigate('/hospitals')}
                className="w-full sm:w-auto flex items-center justify-center gap-2 font-bold text-sm text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 px-7 py-3.5 rounded-xl shadow-sm transition-all"
              >
                <Building2 className="w-4 h-4 text-sky-600" />
                <span>Explore Hospital Matches</span>
              </button>
            </div>

            {/* Source Disclaimers */}
            <div className="flex flex-wrap items-center justify-center gap-3">
              <DisclaimerBadge type="ai" text="Biomedical NER & Semantic RAG" />
              <DisclaimerBadge type="database" text="Verified Hospital Guidelines" />
              <DisclaimerBadge type="ai" text="XGBoost & SHAP Attributions" />
            </div>

          </div>
        </div>
      </section>

      {/* Core V1 Pipeline Stages */}
      <section className="py-16 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900">
            End-to-End Clinical Decision Support Pipeline
          </h2>
          <p className="text-slate-500 text-sm mt-2">Every stage rigorously connected with transparent citations and explainability</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            { title: '1. Medical Report Intelligence', desc: 'Ingests PDF & image medical reports with text quality verification and Biomedical NER.', icon: Upload },
            { title: '2. Clinical Profile', desc: 'Persists patient chronic conditions, demographics, and active diagnoses securely.', icon: FileText },
            { title: '3. Medical Analysis / RAG', desc: 'Retrieves verified clinical practice guidelines and evidence sources with strict grounding.', icon: Sparkles },
            { title: '4. Personalized Hospital Recommendations', desc: 'Transparent multi-criteria hospital matching conditioned on clinical context.', icon: Building2 },
            { title: '5. Cost & LOS Prediction', desc: 'Estimates treatment expense and hospitalization days using pre-operative XGBoost models.', icon: Calculator },
            { title: '6. SHAP Explainability', desc: 'Delivers transparent additive feature impact breakdowns for every cost prediction.', icon: ShieldCheck },
            { title: '7. AI Healthcare Assistant', desc: 'Grounded conversational guidance citing clinical evidence with safety guardrails.', icon: Bot },
            { title: '8. Medical Travel & Connectivity', desc: 'Open-source multimodal route planning, nearby hotels, pharmacies, and emergency services.', icon: Activity },
            { title: '9. Rigorous Evaluation', desc: 'Empirical model metrics, validation splits, and retrieval evaluation benchmark.', icon: UserCheck },
          ].map((item, idx) => {
            const Icon = item.icon;
            return (
              <div key={idx} className="glass-card rounded-2xl p-6 border border-slate-200 hover:shadow-card-hover transition-all">
                <div className="w-10 h-10 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center font-bold mb-4 border border-sky-100">
                  <Icon className="w-5 h-5" />
                </div>
                <h3 className="font-bold text-slate-900 text-base mb-2">{item.title}</h3>
                <p className="text-slate-600 text-xs leading-relaxed">{item.desc}</p>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
};

export default LandingPage;
