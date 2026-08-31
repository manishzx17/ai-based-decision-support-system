import React from 'react';
import { useNavigate } from 'react-router-dom';
import { FolderHeart, FileText, Upload, Calendar, ArrowRight } from 'lucide-react';
import { DisclaimerBadge } from '../components/DisclaimerBadge';

export const MedicalRecordsPage: React.FC = () => {
  const navigate = useNavigate();

  const records = [
    {
      id: 1,
      name: "Cardiology_Angiography_Report_RajeshVerma.pdf",
      date: "August 20, 2026",
      specialty: "Cardiology",
      entities: "8 Medical Entities (LAD 85% Stenosis)",
      status: "COMPLETED"
    },
    {
      id: 2,
      name: "Echocardiogram_LVEF_55_Report.pdf",
      date: "August 15, 2026",
      specialty: "Cardiology",
      entities: "4 Medical Entities (Normal Wall Motion)",
      status: "COMPLETED"
    }
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900">My Medical Records Vault</h1>
          <p className="text-xs text-slate-500 mt-1">Secure repository of uploaded reports, OCR text, and extracted ClinicalBERT entities</p>
        </div>

        <button
          onClick={() => navigate('/reports/upload')}
          className="flex items-center gap-2 font-bold text-xs text-white gradient-bg px-4 py-2.5 rounded-xl shadow hover:opacity-95 transition-opacity"
        >
          <Upload className="w-4 h-4" />
          <span>Upload New Report</span>
        </button>
      </div>

      <div className="space-y-4">
        {records.map((r) => (
          <div key={r.id} className="glass-card rounded-2xl p-6 border border-slate-200 hover:shadow-card-hover transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center font-bold shrink-0 border border-sky-100">
                <FileText className="w-5 h-5" />
              </div>

              <div>
                <h3 className="font-bold text-slate-900 text-sm">{r.name}</h3>
                <p className="text-xs text-slate-500 mt-0.5">{r.date} • Specialty: <strong>{r.specialty}</strong></p>
                <p className="text-xs font-semibold text-emerald-600 mt-1">{r.entities}</p>
              </div>
            </div>

            <button
              onClick={() => navigate(`/reports/${r.id}/analysis`)}
              className="flex items-center gap-1.5 text-xs font-bold text-sky-600 hover:underline shrink-0"
            >
              <span>View Analysis</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}
      </div>

    </div>
  );
};
