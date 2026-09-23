import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FolderHeart, FileText, Upload, Calendar, ArrowRight, Loader2 } from 'lucide-react';
import { DisclaimerBadge } from '../components/DisclaimerBadge';
import { getUserReports, getCurrentUserId, setActiveReportId, MedicalReport } from '../services/api';

export const MedicalRecordsPage: React.FC = () => {
  const navigate = useNavigate();
  const userId = getCurrentUserId();
  const [reports, setReports] = useState<MedicalReport[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadReports() {
      try {
        setLoading(true);
        const data = await getUserReports(userId);
        setReports(data || []);
      } catch (e) {
        console.warn("Failed to load user reports, using fallback", e);
      } finally {
        setLoading(false);
      }
    }
    loadReports();
  }, [userId]);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900">Report History/Records</h1>
          <p className="text-xs text-slate-500 mt-1">Repository of uploaded diagnostic reports, OCR extractions, and clinical entities</p>
        </div>

        <button
          onClick={() => navigate('/reports/upload')}
          className="flex items-center gap-2 font-bold text-xs text-white gradient-bg px-4 py-2.5 rounded-xl shadow hover:opacity-95 transition-opacity"
        >
          <Upload className="w-4 h-4" />
          <span>Upload New Report</span>
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center p-12 text-slate-500 gap-2">
          <Loader2 className="w-6 h-6 animate-spin text-sky-600" />
          <span className="text-sm font-semibold">Loading Report History/Records...</span>
        </div>
      ) : reports.length === 0 ? (
        <div className="glass-card rounded-2xl p-8 text-center border border-slate-200">
          <FileText className="w-10 h-10 text-slate-400 mx-auto mb-2" />
          <p className="font-bold text-slate-700 text-sm">No medical records uploaded yet</p>
          <p className="text-xs text-slate-500 mt-1">Upload your diagnostic lab or hospital reports to get started.</p>
          <button
            onClick={() => navigate('/reports/upload')}
            className="mt-4 inline-flex items-center gap-2 font-bold text-xs text-white gradient-bg px-4 py-2 rounded-xl"
          >
            <Upload className="w-4 h-4" /> Upload Report
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {reports.map((r) => (
            <div key={r.id} className="glass-card rounded-2xl p-6 border border-slate-200 hover:shadow-card-hover transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center font-bold shrink-0 border border-sky-100">
                  <FileText className="w-5 h-5" />
                </div>

                <div>
                  <h3 className="font-bold text-slate-900 text-sm">{r.filename}</h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {r.created_at ? new Date(r.created_at).toLocaleDateString() : 'Recent'} • Specialty: <strong>{r.recommended_specialty}</strong>
                  </p>
                  <p className="text-xs font-semibold text-emerald-600 mt-1">
                    {r.entities?.length || 0} Medical Entities Extracted ({r.status})
                  </p>
                </div>
              </div>

              <button
                onClick={() => {
                  setActiveReportId(r.id);
                  navigate(`/reports/${r.id}/analysis`);
                }}
                className="flex items-center gap-1.5 text-xs font-bold text-sky-600 hover:underline shrink-0"
              >
                <span>View Analysis</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}

    </div>
  );
};
