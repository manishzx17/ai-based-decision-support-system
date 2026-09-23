import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { UserCheck, Star, Calendar, Building2, CheckCircle2, ShieldCheck, ArrowRight, Loader2, Award, Calculator, GitCompare } from 'lucide-react';
import { DisclaimerBadge } from '../components/DisclaimerBadge';
import { getRecommendedDoctors, getOrResolveActiveReport, getCurrentUser, Doctor } from '../services/api';

export const DoctorRecommendationsPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const paramSpecialty = searchParams.get('specialty');
  const paramReportId = searchParams.get('report_id') ? Number(searchParams.get('report_id')) : undefined;

  const [specialty, setSpecialty] = useState(paramSpecialty || 'Cardiology');
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeReportId, setActiveReportId] = useState<number | undefined>(paramReportId);
  const [selectedForCompare, setSelectedForCompare] = useState<number[]>([]);

  // Load authenticated user session
  const user = getCurrentUser();

  const handleToggleCompare = (id: number) => {
    setSelectedForCompare(prev => {
      if (prev.includes(id)) {
        return prev.filter(x => x !== id);
      }
      if (prev.length >= 3) {
        return [...prev.slice(1), id];
      }
      return [...prev, id];
    });
  };

  const handleGoToCompare = () => {
    const params = new URLSearchParams({ type: 'doctor', specialty });
    if (selectedForCompare.length >= 1) {
      params.set('ids', selectedForCompare.join(','));
    }
    if (activeReportId) {
      params.set('report_id', String(activeReportId));
    }
    navigate(`/hospitals/compare?${params.toString()}`);
  };

  useEffect(() => {
    async function loadPatientContext() {
      try {
        const report = await getOrResolveActiveReport(user.id);
        if (report && report.recommended_specialty) {
          if (!paramSpecialty) {
            setSpecialty(report.recommended_specialty);
          }
          if (!paramReportId) {
            setActiveReportId(report.id);
          }
        }
      } catch (err) {
        console.warn('Could not load report context for doctor recommendations', err);
      }
    }
    loadPatientContext();
  }, [user.id, paramSpecialty, paramReportId]);

  useEffect(() => {
    async function loadDoctors() {
      try {
        setLoading(true);
        const data = await getRecommendedDoctors({
          specialty,
          user_id: user.id,
          report_id: activeReportId
        });
        setDoctors(data || []);
      } catch (e) {
        console.warn('Failed to load recommended doctors from API', e);
        setDoctors([]);
      } finally {
        setLoading(false);
      }
    }
    loadDoctors();
  }, [specialty, activeReportId, user.id]);

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      
      {/* Title */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900">Doctor Recommendations</h1>
          <p className="text-xs text-slate-500 mt-1">
            Clinical specialists matched by clinical findings, subspecialty expertise, and accredited hospital affiliation
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={specialty}
            onChange={(e) => setSpecialty(e.target.value)}
            className="px-3.5 py-2 rounded-xl border border-slate-300 text-xs font-bold bg-white text-slate-700 shadow-sm focus:ring-2 focus:ring-sky-500"
          >
            {['Cardiology', 'Neurology', 'Oncology', 'Orthopedics', 'Gastroenterology', 'Nephrology', 'Pulmonology', 'General Medicine'].map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>

          <button
            onClick={handleGoToCompare}
            className={`flex items-center gap-2 font-bold text-xs px-4 py-2.5 rounded-xl shadow-sm transition-all border ${
              selectedForCompare.length > 0
                ? 'bg-sky-600 text-white border-sky-600 shadow-md hover:bg-sky-700'
                : 'text-slate-700 bg-white border-slate-300 hover:bg-slate-50'
            }`}
          >
            <GitCompare className={`w-4 h-4 ${selectedForCompare.length > 0 ? 'text-white' : 'text-sky-600'}`} />
            <span>Compare {selectedForCompare.length > 0 ? `(${selectedForCompare.length}/3)` : 'Side-by-Side'}</span>
          </button>
        </div>
      </div>

      {/* Synthetic Benchmark Notice */}
      <div className="p-3 bg-amber-50/70 border border-amber-200 rounded-xl text-xs text-amber-900 flex items-start gap-2">
        <span className="font-bold shrink-0 text-amber-800">Research Benchmark:</span>
        <span>
          Doctor credentials, qualifications, and consultation metrics are generated as a synthetic research benchmark dataset for algorithm validation. Verified hospital affiliations and clinical specialties are preserved.
        </span>
      </div>

      {loading ? (
        <div className="flex items-center justify-center p-16 text-slate-500 gap-2">
          <Loader2 className="w-6 h-6 animate-spin text-sky-600" />
          <span className="text-sm font-semibold">Matching qualified doctors with your patient context...</span>
        </div>
      ) : doctors.length === 0 ? (
        <div className="glass-card rounded-2xl p-12 text-center border border-slate-200">
          <UserCheck className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="font-bold text-slate-800 text-base">No matching providers available in the current benchmark dataset</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
            The requested clinical specialty ({specialty}) currently has no accredited doctor records in the benchmark repository. Try selecting another department or updating your clinical report filters.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {doctors.map(doc => {
            const isSynthetic = doc.provenance?.is_synthetic_benchmark ?? true;
            const isSelected = selectedForCompare.includes(doc.id);
            return (
              <div
                key={doc.id}
                className={`glass-card rounded-2xl p-6 border transition-all flex flex-col justify-between ${
                  isSelected
                    ? 'ring-2 ring-sky-500 border-sky-500 bg-sky-50/15 shadow-md'
                    : 'border-slate-200 hover:shadow-card-hover'
                }`}
              >
                <div>
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <div>
                      <div className="flex flex-wrap items-center gap-1.5">
                        <span className="text-[10px] font-bold text-sky-700 bg-sky-50 px-2.5 py-0.5 rounded-full border border-sky-100 uppercase">
                          {doc.specialty}
                        </span>
                        {doc.match_score !== undefined && (
                          <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200 flex items-center gap-1">
                            <Award className="w-3 h-3 text-emerald-600" />
                            Match: {doc.match_score.toFixed(1)}%
                          </span>
                        )}
                        {isSynthetic && (
                          <span className="text-[9px] font-semibold text-amber-800 bg-amber-50 px-2 py-0.5 rounded-md border border-amber-200">
                            Synthetic Record
                          </span>
                        )}
                      </div>
                      <h3 className="text-lg font-bold text-slate-900 mt-1.5">{doc.name}</h3>
                      <p className="text-xs text-slate-500">{doc.qualification}</p>
                    </div>

                    <div className="flex items-center gap-1 font-bold text-xs text-amber-600 bg-amber-50 px-2.5 py-1 rounded-lg border border-amber-200 shrink-0">
                      <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-500" />
                      <span>{doc.rating}</span>
                    </div>
                  </div>

                  {/* Expertise Tags */}
                  {doc.expertise && doc.expertise.length > 0 && (
                    <div className="mb-3">
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Clinical Expertise:</p>
                      <div className="flex flex-wrap gap-1">
                        {doc.expertise.map((exp, idx) => (
                          <span key={idx} className="text-[10px] font-medium bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded-md border border-indigo-100">
                            {exp}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="text-xs text-slate-600 space-y-1.5 mb-4 mt-3 bg-slate-50/70 p-3 rounded-xl border border-slate-100">
                    <p className="flex items-center gap-1.5 font-semibold text-slate-800">
                      <Building2 className="w-3.5 h-3.5 text-sky-600" />
                      <span>{doc.hospital_name ? `${doc.hospital_name} (${doc.hospital_city})` : 'Hospital Network Accredited'}</span>
                    </p>
                    <p><strong>Clinical Experience:</strong> {doc.experience_years} Years Practice</p>
                    <p><strong>Consultation Fee:</strong> ₹{doc.consultation_fee} INR</p>
                    <p><strong>Schedule:</strong> {doc.availability_days}</p>
                  </div>

                  {/* Reasons / Factor Explanations */}
                  <div className="p-3 bg-sky-50/50 rounded-xl border border-sky-100 text-xs text-slate-700 mb-4 space-y-1">
                    <p className="font-bold text-sky-900 mb-1">Key Recommendation Drivers:</p>
                    {doc.reasons && doc.reasons.length > 0 ? (
                      doc.reasons.map((r, i) => <p key={i} className="text-slate-700">{r}</p>)
                    ) : (
                      <>
                        <p>✓ {doc.experience_years} years specialty clinical practice</p>
                        <p>✓ Patient rating of {doc.rating}/5.0</p>
                        <p>✓ Subspecialty alignment with clinical criteria</p>
                      </>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2 mt-2 pt-3 border-t border-slate-100">
                  <button
                    type="button"
                    onClick={() => handleToggleCompare(doc.id)}
                    className={`flex items-center justify-center gap-1.5 py-2.5 px-3.5 rounded-xl font-bold text-xs transition-all border shrink-0 ${
                      isSelected
                        ? 'bg-sky-600 text-white border-sky-600 shadow-sm'
                        : 'bg-white text-slate-700 border-slate-300 hover:border-sky-500 hover:text-sky-600'
                    }`}
                  >
                    <CheckCircle2 className={`w-3.5 h-3.5 ${isSelected ? 'text-white' : 'text-slate-400'}`} />
                    <span>{isSelected ? 'Selected' : 'Compare'}</span>
                  </button>

                  <button
                    onClick={() => {
                      const rep = activeReportId || sessionStorage.getItem('active_report_id') || '';
                      navigate(`/cost?specialty=${encodeURIComponent(specialty)}${rep ? `&report_id=${rep}` : ''}`);
                    }}
                    className="flex-1 py-2.5 rounded-xl font-bold text-xs text-white gradient-bg shadow hover:opacity-95 transition-opacity flex items-center justify-center gap-1.5"
                  >
                    <Calculator className="w-3.5 h-3.5" />
                    <span>Estimate Cost & LOS</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Floating Doctor Comparison Drawer */}
      {selectedForCompare.length > 0 && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 bg-slate-900/95 backdrop-blur-md text-white px-5 py-3.5 rounded-2xl shadow-2xl border border-slate-700 flex items-center gap-4 animate-fadeIn">
          <div className="flex items-center gap-2">
            <GitCompare className="w-5 h-5 text-sky-400" />
            <span className="text-xs font-semibold">
              <strong className="text-white font-bold">{selectedForCompare.length}</strong> of 3 specialists selected
            </span>
          </div>
          <div className="h-4 w-px bg-slate-700" />
          <div className="flex items-center gap-2">
            <button
              onClick={() => setSelectedForCompare([])}
              className="text-xs text-slate-400 hover:text-white transition-colors font-medium px-2 py-1"
            >
              Clear
            </button>
            <button
              onClick={handleGoToCompare}
              className="gradient-bg text-white text-xs font-bold px-4 py-2 rounded-xl shadow hover:opacity-95 transition-all flex items-center gap-1.5"
            >
              <span>Compare Selected ({selectedForCompare.length})</span>
            </button>
          </div>
        </div>
      )}

    </div>
  );
};
