import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FileText, Activity, ShieldCheck, ArrowRight, BookOpen, Building2,
  CheckCircle2, Sparkles, AlertCircle, Eye
} from 'lucide-react';
import { DisclaimerBadge } from '../components/DisclaimerBadge';

export const ReportAnalysisPage: React.FC = () => {
  const navigate = useNavigate();
  const [showRawOcr, setShowRawOcr] = useState(false);
  const [showRAGSource, setShowRAGSource] = useState(false);

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 glass-card p-6 rounded-3xl border border-slate-200">
        <div>
          <span className="text-[11px] font-bold text-emerald-600 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
            Analysis Complete
          </span>
          <h1 className="text-2xl font-black text-slate-900 mt-1">
            Cardiology Angiography Diagnostic Analysis
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            File: Cardiology_Angiography_Report_RajeshVerma.pdf | Ingested: August 20, 2026
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowRawOcr(!showRawOcr)}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold text-slate-700 bg-slate-100 hover:bg-slate-200 transition-colors"
          >
            <Eye className="w-3.5 h-3.5" />
            <span>{showRawOcr ? "Hide OCR Text" : "View Raw OCR Text"}</span>
          </button>

          <button
            onClick={() => navigate('/hospitals')}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold text-white gradient-bg shadow hover:opacity-95 transition-opacity"
          >
            <span>View Hospital Recommendations</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Raw OCR Text Modal / Drawer */}
      {showRawOcr && (
        <div className="glass-card rounded-2xl p-5 border border-sky-200 bg-sky-50/50">
          <h3 className="font-bold text-slate-900 text-sm mb-2 flex items-center gap-2">
            <FileText className="w-4 h-4 text-sky-600" />
            Extracted OCR Plain Text Stream
          </h3>
          <pre className="p-4 bg-slate-900 text-slate-100 rounded-xl text-xs font-mono whitespace-pre-wrap leading-relaxed max-h-60 overflow-y-auto">
{`PATIENT DIAGNOSTIC REPORT
Name: Rajesh Verma | Age: 48 | Gender: Male
Department: Cardiology & Interventional Medicine
Clinical Findings: Patient presents with exertional angina (CCS Class II) and shortness of breath.
Coronary Angiography Summary:
1. Left Main (LM): Normal
2. Left Anterior Descending (LAD): 85% proximal stenosis with discrete calcified plaque.
3. Left Circumflex (LCx): Minor 30% irregular luminal disease.
4. Right Coronary Artery (RCA): 70% mid-vessel stenosis.
Impression: Severe Double Vessel Disease (DVD).
Recommended Management: Elective Percutaneous Coronary Intervention (PCI) with Drug-Eluting Stents (DES) in LAD and RCA, or Coronary Artery Bypass Grafting (CABG).
Current Medications: Aspirin 75mg OD, Atorvastatin 40mg HS, Metoprolol 50mg BD.`}
          </pre>
        </div>
      )}

      {/* Main Analysis Cards Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Col: Patient Summary & Entities */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Patient Summary */}
          <div className="glass-card rounded-2xl p-6 border border-slate-200">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-base font-extrabold text-slate-900">Executive Patient Summary</h2>
              <DisclaimerBadge type="ai" text="Gemini LLM Summary" />
            </div>

            <p className="text-xs text-slate-700 leading-relaxed bg-slate-50 p-4 rounded-xl border border-slate-200/80">
              The patient (Rajesh Verma, 48M) presents with severe Double Vessel Coronary Artery Disease. Diagnostic angiography demonstrates significant 85% LAD stenosis and 70% RCA stenosis causing exertional angina. Elective Percutaneous Coronary Intervention (PCI) with Drug-Eluting Stents or CABG surgery is advised under Cardiology.
            </p>

            {/* RAG Knowledge Grounding Citation Link */}
            <div className="mt-4 flex items-center justify-between pt-3 border-t border-slate-100">
              <button
                onClick={() => setShowRAGSource(!showRAGSource)}
                className="text-xs font-bold text-sky-600 hover:underline flex items-center gap-1.5"
              >
                <BookOpen className="w-3.5 h-3.5" />
                <span>View RAG Clinical Grounding Source Information</span>
              </button>

              <span className="text-[11px] text-slate-400">Ref: ESC Cardiology Guidelines 2024</span>
            </div>

            {showRAGSource && (
              <div className="mt-3 p-3 bg-slate-100 rounded-xl text-xs text-slate-700 leading-relaxed border border-slate-200 animate-fadeIn">
                <strong>Retrieved Grounding Document:</strong> European Society of Cardiology (ESC) PCI Guidelines. "Patients undergoing PCI with stent placement require DAPT. Commercial air travel is permitted 3-5 days post-uncomplicated PCI if ejection fraction &gt; 40%."
              </div>
            )}
          </div>

          {/* Extracted ClinicalBERT Entities */}
          <div className="glass-card rounded-2xl p-6 border border-slate-200">
            <h2 className="text-base font-extrabold text-slate-900 mb-4 flex items-center gap-2">
              <Activity className="w-4 h-4 text-sky-600" />
              Extracted Clinical Entities (BioBERT Named Entity Recognition)
            </h2>

            <div className="space-y-3">
              {[
                { type: 'Disease', name: 'Severe Double Vessel Disease (DVD)', conf: '98%', snippet: 'Impression: Severe Double Vessel Disease (DVD).' },
                { type: 'Symptom', name: 'Exertional Angina', conf: '95%', snippet: 'Patient presents with exertional angina (CCS Class II)' },
                { type: 'Procedure', name: 'Percutaneous Coronary Intervention (PCI)', conf: '97%', snippet: 'Elective Percutaneous Coronary Intervention (PCI)' },
                { type: 'Medication', name: 'Aspirin 75mg & Atorvastatin 40mg', conf: '94%', snippet: 'Current Medications: Aspirin 75mg OD, Atorvastatin 40mg HS' },
                { type: 'BodyPart', name: 'Left Anterior Descending Artery (LAD)', conf: '96%', snippet: 'LAD: 85% proximal stenosis' },
              ].map((ent, idx) => (
                <div key={idx} className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
                  <div>
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="font-bold text-sky-700 bg-sky-100 px-2 py-0.5 rounded text-[10px] uppercase">
                        {ent.type}
                      </span>
                      <span className="font-bold text-slate-900">{ent.name}</span>
                    </div>
                    <p className="text-[11px] text-slate-500 italic">"{ent.snippet}"</p>
                  </div>

                  <span className="text-[11px] font-extrabold text-emerald-600 shrink-0">
                    Confidence: {ent.conf}
                  </span>
                </div>
              ))}
            </div>
          </div>

        </div>

        {/* Right Col: Specialty & Action Recommendations */}
        <div className="space-y-6">
          
          <div className="glass-card rounded-2xl p-5 border border-slate-200">
            <h3 className="text-xs font-bold uppercase text-slate-400 tracking-wider mb-2">Recommended Specialty</h3>
            <p className="text-xl font-black text-sky-700">Interventional Cardiology</p>
            <p className="text-xs text-slate-600 mt-2">
              Based on LAD 85% stenosis and angina symptoms, specialist consultation with an Interventional Cardiologist is required.
            </p>

            <div className="mt-4 pt-4 border-t border-slate-100 space-y-2">
              <button
                onClick={() => navigate('/doctors')}
                className="w-full py-2.5 rounded-xl font-bold text-xs text-white gradient-bg shadow hover:opacity-95 transition-opacity"
              >
                Find Recommended Doctors
              </button>

              <button
                onClick={() => navigate('/cost')}
                className="w-full py-2.5 rounded-xl font-bold text-xs text-slate-700 bg-slate-100 hover:bg-slate-200 transition-colors"
              >
                Estimate Treatment Cost
              </button>
            </div>
          </div>

          <div className="p-4 bg-amber-50 rounded-2xl border border-amber-200 text-xs text-amber-900 leading-relaxed">
            <strong className="block font-bold mb-1 flex items-center gap-1">
              <AlertCircle className="w-4 h-4 text-amber-600" />
              Medical Safety Note:
            </strong>
            This analysis is generated for medical travel decision support. Please verify findings with a registered physician during your hospital appointment.
          </div>

        </div>

      </div>
    </div>
  );
};
