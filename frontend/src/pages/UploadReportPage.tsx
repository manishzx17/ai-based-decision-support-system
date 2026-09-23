import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, FileText, CheckCircle2, Loader2, Sparkles, ArrowRight, ShieldCheck } from 'lucide-react';
import { uploadReportApi, setActiveReportId } from '../services/api';
import { DisclaimerBadge } from '../components/DisclaimerBadge';

export const UploadReportPage: React.FC = () => {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);

  const steps = [
    "Uploading medical report file...",
    "Extracting OCR text from document...",
    "Running Biomedical NER entity extraction...",
    "Retrieving grounded RAG clinical guidelines...",
    "Generating personalized hospital recommendations..."
  ];

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const processUpload = async () => {
    setIsProcessing(true);
    setCurrentStep(0);

    for (let i = 0; i < steps.length; i++) {
      setCurrentStep(i);
      await new Promise(r => setTimeout(r, 600));
    }

    let reportId: number | null = null;
    try {
      if (file) {
        const res = await uploadReportApi(file);
        if (res && res.id) {
          reportId = res.id;
          setActiveReportId(reportId);
        }
      }
    } catch (e) {
      console.warn("Upload processing error", e);
    }

    setIsProcessing(false);
    if (reportId) {
      navigate(`/reports/${reportId}/analysis`);
    } else {
      navigate('/reports');
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="text-center max-w-xl mx-auto">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-sky-100 text-sky-800 text-xs font-bold mb-3">
          <Sparkles className="w-3.5 h-3.5 text-sky-600" />
          <span>AI OCR & Medical Entity Extraction</span>
        </div>
        <h1 className="text-3xl font-black text-slate-900">Upload Medical Report</h1>
        <p className="text-xs text-slate-500 mt-2">
          Upload PDF, PNG, JPG, or scanned diagnostic lab/hospital reports. Supported files are parsed via OCR and Biomedical NER.
        </p>
        <p className="text-[11px] text-slate-400 mt-1 font-medium">
          Supports typed & scanned medical reports (PDF, JPG, PNG) and standard lab tables. Handwritten reports are not supported.
        </p>
      </div>

      <div className="glass-card rounded-3xl p-8 border border-slate-200 shadow-lg">
        
        {!isProcessing ? (
          <div className="space-y-6">
            
            {/* Drag and Drop Zone */}
            <div className="border-2 border-dashed border-sky-300 hover:border-sky-500 bg-sky-50/50 hover:bg-sky-50 rounded-2xl p-8 text-center transition-colors cursor-pointer relative">
              <input
                type="file"
                accept=".pdf,.png,.jpg,.jpeg"
                onChange={handleFileChange}
                className="absolute inset-0 opacity-0 cursor-pointer"
              />
              <div className="w-14 h-14 bg-white rounded-2xl shadow-sm text-sky-600 flex items-center justify-center mx-auto mb-3 border border-sky-100">
                <Upload className="w-7 h-7" />
              </div>
              
              <h3 className="font-bold text-slate-900 text-base mb-1">
                {file ? file.name : "Choose file or drag & drop"}
              </h3>
              <p className="text-xs text-slate-500">PDF, JPG, PNG scanned documents up to 25MB</p>
            </div>

            {/* Demo Preset Buttons */}
            <div>
              <p className="text-xs font-bold text-slate-700 mb-2">Or select sample medical report:</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setFile(new File([
                    `CARDIOLOGY ANGIOGRAPHY & DIAGNOSTIC REPORT\nPatient Name: Rajesh Verma | Age: 48 | Sex: Male\nDepartment: Cardiology & Interventional Medicine\nClinical Findings: Patient presents with exertional angina (CCS Class II) and dyspnea on exertion.\nCoronary Angiography:\n1. Left Main (LM): Normal caliber.\n2. LAD: 85% proximal stenosis with discrete calcified plaque.\n3. LCx: Minor luminal irregularity (30%).\n4. RCA: 70% mid-vessel stenosis.\nEchocardiogram: LVEF 55%, mild concentric LV hypertrophy.\nImpression: Severe Double Vessel Coronary Artery Disease.\nPlan: Elective Percutaneous Coronary Intervention (PCI) with Drug-Eluting Stents in LAD and RCA.\nMedications: Aspirin 75mg OD, Atorvastatin 40mg HS, Metoprolol 50mg BD.`
                  ], "Cardiology_Angiography_Report.txt", { type: "text/plain" }))}
                  className="p-3 bg-white hover:bg-sky-50 rounded-xl border border-slate-200 text-left text-xs transition-colors flex items-center justify-between"
                >
                  <div>
                    <span className="font-bold text-slate-900 block">Cardiology Angiography Report</span>
                    <span className="text-[11px] text-slate-500">Severe CAD / Exertional Angina</span>
                  </div>
                  <FileText className="w-4 h-4 text-sky-600" />
                </button>

                <button
                  type="button"
                  onClick={() => setFile(new File([
                    `NEUROLOGICAL CONSULTATION & MRI REPORT\nPatient Name: Anitha Rao | Age: 52 | Sex: Female\nDepartment: Neurological Sciences & Brain Spine Center\nClinical Observation: Persistent localized headache, focal motor weakness in left hand, intermittent dizziness for 3 weeks.\nMRI Brain with Contrast Summary:\n- Well-demarcated 2.4 cm extra-axial space-occupying lesion in right parasagittal parietal region.\n- Moderate surrounding vasogenic edema without midline shift.\nImpression: Benign parasagittal Meningioma (WHO Grade I) with focal cerebral edema.\nPlan: Neurosurgical consultation for elective craniotomy and tumor excision.\nPrescription: Levetiracetam 500mg BD.`
                  ], "Brain_MRI_Neurology_Report.txt", { type: "text/plain" }))}
                  className="p-3 bg-white hover:bg-sky-50 rounded-xl border border-slate-200 text-left text-xs transition-colors flex items-center justify-between"
                >
                  <div>
                    <span className="font-bold text-slate-900 block">Brain MRI Neurology Report</span>
                    <span className="text-[11px] text-slate-500">Parasagittal Meningioma</span>
                  </div>
                  <FileText className="w-4 h-4 text-sky-600" />
                </button>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
              <DisclaimerBadge type="ai" text="Secure OCR Analysis" />

              <button
                onClick={processUpload}
                disabled={!file}
                className="flex items-center gap-2 font-bold text-xs text-white gradient-bg px-6 py-3 rounded-xl shadow-md hover:opacity-95 transition-all disabled:opacity-50"
              >
                <span>Process & Analyze Report</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>

          </div>
        ) : (
          /* Live Step-by-Step Progress Pipeline */
          <div className="py-8 text-center space-y-6">
            <Loader2 className="w-12 h-12 text-sky-600 animate-spin mx-auto" />
            
            <div>
              <h3 className="text-lg font-extrabold text-slate-900">AI Medical Pipeline Processing</h3>
              <p className="text-xs text-slate-500 mt-1">{steps[currentStep]}</p>
            </div>

            <div className="max-w-md mx-auto space-y-2 text-left text-xs">
              {steps.map((st, idx) => (
                <div
                  key={idx}
                  className={`flex items-center gap-3 p-2.5 rounded-xl border ${
                    idx < currentStep
                      ? 'bg-emerald-50 border-emerald-200 text-emerald-800 font-semibold'
                      : idx === currentStep
                      ? 'bg-sky-50 border-sky-300 text-sky-900 font-bold animate-pulse'
                      : 'bg-slate-50 border-slate-200 text-slate-400'
                  }`}
                >
                  {idx < currentStep ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border-2 border-slate-300 flex items-center justify-center text-[10px] shrink-0">{idx + 1}</div>
                  )}
                  <span>{st}</span>
                </div>
              ))}
            </div>
          </div>
        )}

      </div>
    </div>
  );
};
