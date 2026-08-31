import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Sparkles, Upload, Building2, Calculator, Plane, ShieldCheck,
  Bot, ArrowRight, CheckCircle2, PhoneCall, Globe, Activity
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
              <span>Next-Gen Medical Travel Intelligence System</span>
            </div>

            <h1 className="text-4xl sm:text-6xl font-black text-slate-900 tracking-tight leading-tight mb-6">
              12C – AI-Based Medical Travel <span className="gradient-text">Decision Support</span>
            </h1>

            <p className="text-lg text-slate-600 font-medium mb-8 leading-relaxed">
              Intelligent healthcare guidance for wherever your journey takes you. Analyze medical reports, extract clinical entities, receive weighted hospital recommendations, predict treatment costs, and manage your complete medical travel itinerary.
            </p>

            {/* CTAs */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-10">
              <button
                onClick={() => navigate('/reports/upload')}
                className="w-full sm:w-auto flex items-center justify-center gap-2 font-bold text-sm text-white gradient-bg px-7 py-3.5 rounded-xl shadow-lg hover:shadow-sky-200 transition-all scale-100 hover:scale-105"
              >
                <Upload className="w-4 h-4" />
                <span>Analyze Medical Report</span>
                <ArrowRight className="w-4 h-4" />
              </button>

              <button
                onClick={() => navigate('/hospitals')}
                className="w-full sm:w-auto flex items-center justify-center gap-2 font-bold text-sm text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 px-7 py-3.5 rounded-xl shadow-sm transition-all"
              >
                <Building2 className="w-4 h-4 text-sky-600" />
                <span>Explore Healthcare Facilities</span>
              </button>
            </div>

            {/* Source Disclaimers */}
            <div className="flex flex-wrap items-center justify-center gap-3">
              <DisclaimerBadge type="ai" text="AI Clinical NLP & Gemini Support" />
              <DisclaimerBadge type="database" text="Verified Hospital Records" />
              <DisclaimerBadge type="external" text="A* Travel Navigation" />
            </div>

          </div>
        </div>
      </section>

      {/* 9 Core AI Tech Highlights */}
      <section className="py-16 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900">
            Powered by 9 Core Artificial Intelligence Technologies
          </h2>
          <p className="text-slate-500 text-sm mt-2">Built with rigorous clinical pipelines and transparent explainability</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            { title: '1. OCR Ingestion', desc: 'Ingests PDF, PNG, and scanned report files into clean structured medical text.', icon: Upload },
            { title: '2. ClinicalBERT Entity Extract', desc: 'Identifies diseases, symptoms, medications, procedures, and body parts.', icon: Activity },
            { title: '3. Hybrid RAG Pipeline', desc: 'Retrieves verified clinical guidelines and hospital records with citations.', icon: Sparkles },
            { title: '4. Hybrid BM25 + Vector Search', desc: 'Combines exact keyword matching with semantic embedding vector search.', icon: Globe },
            { title: '5. Google Gemini LLM', desc: 'Generates report summaries, medical translations, and patient guidance.', icon: Bot },
            { title: '6. Multi-Criteria Scoring', desc: 'Scoring formula (0.30 Specialty + 0.20 Treatment + 0.15 Distance + 0.15 Cost).', icon: Building2 },
            { title: '7. XGBoost Cost Estimator', desc: 'Predicts min, max, and average treatment costs by city and room category.', icon: Calculator },
            { title: '8. A* Spatial Navigation', desc: 'Pathfinding between airport, hotel, hospital, pharmacy, and trauma centers.', icon: Plane },
            { title: '9. SHAP Explainability', desc: 'Provides transparent human-readable explanations for all ML recommendations.', icon: ShieldCheck },
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

      {/* Quick Travel Workflow */}
      <section className="py-16 bg-white border-t border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900">
              End-to-End Medical Travel Workflow
            </h2>
            <p className="text-slate-500 text-sm mt-2">From report upload to post-treatment recovery travel</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {[
              { step: '01', title: 'Upload & Extract', text: 'Upload report → OCR text → ClinicalBERT entity extraction.' },
              { step: '02', title: 'Hospital Match', text: 'RAG search → Weighted hospital score → Doctor recommendations.' },
              { step: '03', title: 'Cost & Insurance', text: 'XGBoost cost prediction → SHAP explanation → Cashless insurance check.' },
              { step: '04', title: 'Travel & Care', text: 'Day-by-day itinerary → A* route planning → Medical translation.' },
            ].map((st, i) => (
              <div key={i} className="relative p-6 rounded-2xl bg-slate-50 border border-slate-200">
                <div className="text-3xl font-black text-sky-600/30 mb-2">{st.step}</div>
                <h3 className="font-bold text-slate-900 text-base mb-2">{st.title}</h3>
                <p className="text-slate-600 text-xs leading-relaxed">{st.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
};
