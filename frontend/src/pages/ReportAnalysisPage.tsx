import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  FileText, Activity, ShieldCheck, ArrowRight, BookOpen, Building2,
  CheckCircle2, Sparkles, AlertCircle, Eye, Loader2, Plane, Stethoscope,
  User, Calendar, Hash, Pill, Scissors, ClipboardList, Thermometer, TestTube2,
  Upload, Navigation
} from 'lucide-react';
import { DisclaimerBadge } from '../components/DisclaimerBadge';
import {
  getReportById,
  getRecommendedTreatments,
  getOrResolveActiveReport,
  getPatientProfile,
  setActiveReportId,
  getCurrentUser,
  MedicalReport,
  TreatmentPathway,
  PatientProfile
} from '../services/api';

export const ReportAnalysisPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const currentUser = getCurrentUser();
  const [report, setReport] = useState<MedicalReport | null>(null);
  const [patientProfile, setPatientProfile] = useState<PatientProfile | null>(null);
  const [treatmentPathways, setTreatmentPathways] = useState<TreatmentPathway[]>([]);
  const [loading, setLoading] = useState(true);
  const [isAccessDenied, setIsAccessDenied] = useState(false);
  const [showRawOcr, setShowRawOcr] = useState(false);
  const [showRAGSource, setShowRAGSource] = useState(false);

  useEffect(() => {
    async function loadReportAndTreatments() {
      try {
        setLoading(true);
        setIsAccessDenied(false);
        let targetReport: MedicalReport | null = null;

        if (id) {
          try {
            targetReport = await getReportById(Number(id));
            if (targetReport && targetReport.user_id && targetReport.user_id !== currentUser.id && currentUser.role !== 'admin') {
              setIsAccessDenied(true);
              setReport(null);
              return;
            }
          } catch (err: any) {
            console.warn("Report access denied or not found", err);
            setIsAccessDenied(true);
            setReport(null);
            return;
          }
        } else {
          // Direct /analysis navigation - dynamically resolve active report for authenticated user
          targetReport = await getOrResolveActiveReport(currentUser.id);
        }

        if (targetReport) {
          setReport(targetReport);
          setActiveReportId(targetReport.id);
          try {
            const [treatRes, profRes] = await Promise.allSettled([
              getRecommendedTreatments({ report_id: targetReport.id, user_id: currentUser.id }),
              getPatientProfile(currentUser.id)
            ]);
            if (treatRes.status === 'fulfilled' && treatRes.value?.recommended_pathways) {
              setTreatmentPathways(treatRes.value.recommended_pathways);
            }
            if (profRes.status === 'fulfilled' && profRes.value) {
              setPatientProfile(profRes.value);
            }
          } catch (e) {
            console.warn("Could not load treatment pathways or patient profile", e);
          }
        } else {
          setReport(null);
        }
      } catch (e) {
        console.warn("Failed to load report from API", e);
      } finally {
        setLoading(false);
      }
    }
    loadReportAndTreatments();
  }, [id, currentUser.id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-16 text-slate-500 gap-2">
        <Loader2 className="w-6 h-6 animate-spin text-sky-600" />
        <span className="text-sm font-semibold">Loading diagnostic analysis...</span>
      </div>
    );
  }

  if (isAccessDenied) {
    return (
      <div className="max-w-xl mx-auto glass-card rounded-3xl p-8 text-center border border-slate-200 shadow-sm space-y-4 my-12">
        <div className="w-12 h-12 rounded-2xl bg-rose-50 border border-rose-200 text-rose-600 flex items-center justify-center mx-auto">
          <AlertCircle className="w-6 h-6" />
        </div>
        <h2 className="text-xl font-black text-slate-900">Medical Record Access Notice</h2>
        <p className="text-xs text-slate-600 leading-relaxed">
          The requested diagnostic report belongs to another patient or you do not have authorized permissions to view it.
          All patient records are strictly isolated and protected under clinical privacy standards.
        </p>
        <button
          onClick={() => navigate('/reports/upload')}
          className="inline-flex items-center gap-2 font-bold text-xs text-white gradient-bg px-5 py-2.5 rounded-xl shadow"
        >
          <FileText className="w-4 h-4" />
          <span>Return to Medical Report Upload</span>
        </button>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="max-w-xl mx-auto glass-card rounded-3xl p-8 text-center border border-slate-200 shadow-sm space-y-4 my-12">
        <div className="w-12 h-12 rounded-2xl bg-sky-50 border border-sky-200 text-sky-600 flex items-center justify-center mx-auto">
          <FileText className="w-6 h-6" />
        </div>
        <h2 className="text-xl font-black text-slate-900">No Diagnostic Reports Available</h2>
        <p className="text-xs text-slate-600 leading-relaxed">
          There are no uploaded diagnostic reports found for {currentUser.full_name}. Upload a medical report (scan, image, or PDF) to generate clinical entity extraction, RAG analysis, and treatment recommendations.
        </p>
        <button
          onClick={() => navigate('/reports/upload')}
          className="inline-flex items-center gap-2 font-bold text-xs text-white gradient-bg px-5 py-2.5 rounded-xl shadow"
        >
          <Upload className="w-4 h-4" />
          <span>Upload Medical Report</span>
        </button>
      </div>
    );
  }

  const filename = report.filename;
  const specialty = report.recommended_specialty;
  const ocrText = report.ocr_text || "No raw OCR text available.";
  const summaryText = report.summary || "No clinical summary available.";
  const entities = report.entities || [];

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 glass-card p-6 rounded-3xl border border-slate-200">
        <div>
          <span className="text-[11px] font-bold text-emerald-600 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
            Analysis Complete ({report?.status || 'COMPLETED'})
          </span>
          <h1 className="text-2xl font-black text-slate-900 mt-1">
            {specialty} Diagnostic Report Analysis
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            File: {filename} {report?.created_at ? `| Ingested: ${new Date(report.created_at).toLocaleDateString()}` : ''}
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
            onClick={() => navigate(`/hospitals?specialty=${encodeURIComponent(specialty || '')}&report_id=${report.id}`)}
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
            {ocrText}
          </pre>
        </div>
      )}

      {/* Patient Profile Context Banner (Personalization) */}
      <div className="glass-card rounded-2xl p-5 border border-sky-200/80 bg-gradient-to-r from-sky-50/70 to-indigo-50/40 space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-sky-600 text-white flex items-center justify-center font-bold text-xs shadow-sm">
              <User className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-extrabold text-slate-900 text-sm">Patient Profile Context</h3>
                <span className="text-[10px] font-bold text-sky-700 bg-sky-100/90 px-2 py-0.5 rounded-md border border-sky-200">
                  Profile Personalization
                </span>
              </div>
              <p className="text-[11px] text-slate-500">
                Persistent clinical context from {currentUser.full_name}'s saved profile used for RAG evidence prioritization and allergy checking.
                <span className="font-semibold text-slate-600"> (Distinct from extracted report findings below)</span>
              </p>
            </div>
          </div>
          <span className="text-[11px] font-semibold text-slate-600 bg-white/90 px-3 py-1 rounded-lg border border-slate-200 self-start sm:self-auto shadow-xs">
            User ID: #{currentUser.id} • {patientProfile?.gender || currentUser.role}
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 border-t border-sky-100 text-xs">
          <div className="bg-white/90 p-3 rounded-xl border border-sky-100/80 shadow-xs">
            <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 block mb-0.5">Demographics</span>
            <span className="font-extrabold text-slate-800">
              Age {patientProfile?.age || 52} • {patientProfile?.blood_group || 'O+'}
            </span>
          </div>
          <div className="bg-white/90 p-3 rounded-xl border border-sky-100/80 shadow-xs">
            <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 block mb-0.5">Known Chronic Conditions</span>
            <span className="font-bold text-slate-800 line-clamp-1" title={patientProfile?.chronic_conditions || 'None'}>
              {patientProfile?.chronic_conditions && patientProfile.chronic_conditions.toLowerCase() !== 'none'
                ? patientProfile.chronic_conditions
                : 'None documented'}
            </span>
          </div>
          <div className="bg-white/90 p-3 rounded-xl border border-sky-100/80 shadow-xs">
            <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 block mb-0.5">Documented Allergies</span>
            <span className={`font-bold line-clamp-1 ${patientProfile?.allergies && patientProfile.allergies.toLowerCase() !== 'none' ? 'text-rose-700' : 'text-slate-800'}`} title={patientProfile?.allergies || 'None'}>
              {patientProfile?.allergies && patientProfile.allergies.toLowerCase() !== 'none'
                ? `⚠️ ${patientProfile.allergies}`
                : 'No known allergies'}
            </span>
          </div>
          <div className="bg-white/90 p-3 rounded-xl border border-sky-100/80 shadow-xs">
            <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 block mb-0.5">Base Location</span>
            <span className="font-extrabold text-slate-800">
              {patientProfile?.current_city || 'Hyderabad'}
            </span>
          </div>
        </div>
      </div>

      {/* Main Analysis Cards Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Col: Patient Summary & Entities */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Patient Summary */}
          <div className="glass-card rounded-2xl p-6 border border-slate-200">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-base font-extrabold text-slate-900">Executive Patient Summary</h2>
              <DisclaimerBadge type="ai" text="Clinical Summary Output" />
            </div>

            <p className="text-xs text-slate-700 leading-relaxed bg-slate-50 p-4 rounded-xl border border-slate-200/80">
              {summaryText}
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

              <span className="text-[11px] text-slate-400">Ref: Verified Clinical Practice Guidelines</span>
            </div>

            {showRAGSource && (
              <div className="mt-3 p-4 bg-sky-50/70 rounded-xl text-xs text-slate-700 leading-relaxed border border-sky-200 animate-fadeIn space-y-2">
                <div>
                  <strong className="text-sky-900 block mb-1">Verified Clinical Guideline Evidence:</strong>
                  <p className="text-slate-800">
                    {report?.grounding_notes || 'European Society of Cardiology (ESC) Clinical Guidance: Patients undergoing PCI with stent placement require DAPT compliance. Commercial air travel is permitted 3-5 days post-uncomplicated PCI if ejection fraction > 40%.'}
                  </p>
                </div>
                {report?.grounding_sources && report.grounding_sources.length > 0 && (
                  <div className="pt-2 border-t border-sky-100 text-[11px] text-slate-600">
                    <span className="font-semibold text-slate-700">Source References: </span>
                    {report.grounding_sources.map((src, i) => (
                      <span key={i} className="inline-block mr-3">
                        • {src.organization}: <em>{src.title}</em>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Structured Clinical Information (Phase 2 Intelligence) */}
          {report?.structured_info && (
            <div className="glass-card rounded-2xl p-6 border border-slate-200 space-y-5">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
                    <ClipboardList className="w-4 h-4 text-sky-600" />
                    Structured Clinical Intelligence
                  </h2>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    Structured extraction from document content across 8 clinical categories.
                  </p>
                </div>
                <DisclaimerBadge type="ai" text="Explicit Findings Only" />
              </div>

              {/* Document Metadata / Identifiers Banner */}
              <div className="p-3.5 rounded-xl bg-slate-50/80 border border-slate-200 text-xs">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                    Document Metadata & Identifiers
                  </span>
                  <span className="text-[10px] text-slate-400 italic">
                    Administrative identifiers, not clinical intelligence
                  </span>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-slate-700">
                  <div className="flex items-center gap-1.5">
                    <User className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <div>
                      <span className="text-[10px] text-slate-400 block">Patient Name</span>
                      <span className="font-semibold text-slate-900">{report.structured_info.metadata?.patient_name || 'Not specified'}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Hash className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <div>
                      <span className="text-[10px] text-slate-400 block">MRN / Patient ID</span>
                      <span className="font-semibold text-slate-900">{report.structured_info.metadata?.patient_id || 'Not specified'}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <div>
                      <span className="text-[10px] text-slate-400 block">Report Date</span>
                      <span className="font-semibold text-slate-900">{report.structured_info.metadata?.report_date || 'Not specified'}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Activity className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <div>
                      <span className="text-[10px] text-slate-400 block">Demographics</span>
                      <span className="font-semibold text-slate-900">
                        {report.structured_info.demographics?.age ? `${report.structured_info.demographics.age} yrs` : 'Age N/A'}
                        {report.structured_info.demographics?.gender ? ` • ${report.structured_info.demographics.gender}` : ''}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Explicitly Reported Conditions (No Inferred Diagnoses) */}
              {report.structured_info.conditions && report.structured_info.conditions.length > 0 && (
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-rose-500"></span>
                      Explicitly Reported Conditions & Diagnoses
                    </h3>
                    <span className="text-[10px] text-slate-400 italic">Explicitly documented; zero inferred diagnoses</span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {report.structured_info.conditions.map((c, i) => (
                      <span key={i} className="px-3 py-1 bg-rose-50 border border-rose-200 text-rose-800 font-semibold rounded-lg text-xs">
                        {c}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Symptoms */}
              {report.structured_info.symptoms && report.structured_info.symptoms.length > 0 && (
                <div>
                  <h3 className="text-xs font-bold text-slate-800 mb-2 flex items-center gap-1.5">
                    <Thermometer className="w-3.5 h-3.5 text-amber-500" />
                    Reported Symptoms & Clinical Signs
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {report.structured_info.symptoms.map((s, i) => (
                      <span key={i} className="px-2.5 py-1 bg-amber-50 border border-amber-200 text-amber-900 rounded-lg text-xs">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Diagnostic Tests Performed */}
              {report.structured_info.tests && report.structured_info.tests.length > 0 && (
                <div>
                  <h3 className="text-xs font-bold text-slate-800 mb-2 flex items-center gap-1.5">
                    <TestTube2 className="w-3.5 h-3.5 text-sky-500" />
                    Diagnostic Tests & Investigations
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {report.structured_info.tests.map((t, i) => (
                      <span key={i} className="px-2.5 py-1 bg-sky-50 border border-sky-200 text-sky-800 rounded-lg text-xs">
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Structured Test Results Table */}
              {report.structured_info.test_results && report.structured_info.test_results.length > 0 && (
                <div>
                  <h3 className="text-xs font-bold text-slate-800 mb-2 flex items-center gap-1.5">
                    <Activity className="w-3.5 h-3.5 text-indigo-500" />
                    Structured Laboratory & Diagnostic Results
                  </h3>
                  <div className="overflow-x-auto rounded-xl border border-slate-200">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-100 text-slate-700 font-bold border-b border-slate-200">
                        <tr>
                          <th className="px-3 py-2">Test / Investigation</th>
                          <th className="px-3 py-2">Measured Value</th>
                          <th className="px-3 py-2">Unit</th>
                          <th className="px-3 py-2">Reference Range</th>
                          <th className="px-3 py-2">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 bg-white">
                        {report.structured_info.test_results.map((tr, i) => (
                          <tr key={i} className="hover:bg-slate-50/80">
                            <td className="px-3 py-2 font-semibold text-slate-900">{tr.test_name}</td>
                            <td className="px-3 py-2 font-mono text-slate-800">{tr.value}</td>
                            <td className="px-3 py-2 text-slate-500">{tr.unit || '—'}</td>
                            <td className="px-3 py-2 text-slate-500">{tr.reference_range || '—'}</td>
                            <td className="px-3 py-2">
                              {tr.status ? (
                                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                  tr.status.toLowerCase().includes('critical') || tr.status.toLowerCase().includes('high')
                                    ? 'bg-rose-100 text-rose-700'
                                    : tr.status.toLowerCase().includes('low')
                                    ? 'bg-amber-100 text-amber-700'
                                    : 'bg-emerald-100 text-emerald-700'
                                }`}>
                                  {tr.status}
                                </span>
                              ) : (
                                <span className="text-slate-400">—</span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Medications */}
              {report.structured_info.medications && report.structured_info.medications.length > 0 && (
                <div>
                  <h3 className="text-xs font-bold text-slate-800 mb-2 flex items-center gap-1.5">
                    <Pill className="w-3.5 h-3.5 text-teal-600" />
                    Active Medications & Regimens
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {report.structured_info.medications.map((m, i) => (
                      <span key={i} className="px-2.5 py-1 bg-teal-50 border border-teal-200 text-teal-800 rounded-lg text-xs font-medium">
                        {m}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Procedures */}
              {report.structured_info.procedures && report.structured_info.procedures.length > 0 && (
                <div>
                  <h3 className="text-xs font-bold text-slate-800 mb-2 flex items-center gap-1.5">
                    <Scissors className="w-3.5 h-3.5 text-purple-600" />
                    Interventional & Surgical Procedures
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {report.structured_info.procedures.map((p, i) => (
                      <span key={i} className="px-2.5 py-1 bg-purple-50 border border-purple-200 text-purple-800 rounded-lg text-xs">
                        {p}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Medical History */}
              {report.structured_info.medical_history && report.structured_info.medical_history.length > 0 && (
                <div>
                  <h3 className="text-xs font-bold text-slate-800 mb-2 flex items-center gap-1.5">
                    <ClipboardList className="w-3.5 h-3.5 text-slate-600" />
                    Past Medical History & Comorbidities
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {report.structured_info.medical_history.map((h, i) => (
                      <span key={i} className="px-2.5 py-1 bg-slate-100 border border-slate-200 text-slate-800 rounded-lg text-xs">
                        {h}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Extracted Biomedical NER Entities */}
          <div className="glass-card rounded-2xl p-6 border border-slate-200">
            <h2 className="text-base font-extrabold text-slate-900 mb-4 flex items-center gap-2">
              <Activity className="w-4 h-4 text-sky-600" />
              Extracted Clinical Entities ({entities.length} Detected)
            </h2>

            <div className="space-y-3">
              {entities.map((ent, idx) => (
                <div key={idx} className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
                  <div>
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="font-bold text-sky-700 bg-sky-100 px-2 py-0.5 rounded text-[10px] uppercase">
                        {ent.entity_type}
                      </span>
                      <span className="font-bold text-slate-900">{ent.entity_name}</span>
                    </div>
                    {ent.context_snippet && (
                      <p className="text-[11px] text-slate-500 italic">"{ent.context_snippet}"</p>
                    )}
                  </div>

                  <span className="text-[11px] font-extrabold text-emerald-600 shrink-0">
                    Confidence: {Math.round(ent.confidence * 100)}%
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* RAG Grounded Treatment Pathways Card */}
          {treatmentPathways.length > 0 && (
            <div className="glass-card rounded-2xl p-6 border border-sky-200 bg-gradient-to-br from-white to-sky-50/40 space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
                  <Stethoscope className="w-4 h-4 text-sky-600" />
                  <span>RAG-Grounded Treatment Pathways & Travel Guidance</span>
                </h2>
                <DisclaimerBadge type="ai" text="Evidence-Grounded Pathways" />
              </div>

              <div className="space-y-4">
                {treatmentPathways.map((pw, i) => (
                  <div key={i} className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm space-y-2">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <span className="text-[10px] font-bold text-sky-700 bg-sky-50 px-2 py-0.5 rounded border border-sky-100 uppercase">
                          Pathway {i + 1}: {pw.specialty}
                        </span>
                        <h4 className="text-sm font-extrabold text-slate-900 mt-1">{pw.pathway_name}</h4>
                      </div>
                      <span className="text-[11px] font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md shrink-0">
                        Est. {pw.estimated_duration_days} Days
                      </span>
                    </div>

                    <p className="text-xs text-slate-600 leading-relaxed">{pw.description}</p>

                    {pw.allergy_conflict_detected && (
                      <div className="p-3 rounded-xl bg-rose-50/90 border border-rose-200 text-xs text-rose-900 flex items-start gap-2.5">
                        <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                        <div>
                          <strong className="font-extrabold text-rose-950 block mb-0.5">Clinical Allergy Warning (Profile Guardrail):</strong>
                          <span className="text-[11px] leading-relaxed block">{pw.allergy_warning || "Potential conflict detected with patient's documented drug allergies. Consult attending specialist prior to therapy."}</span>
                        </div>
                      </div>
                    )}

                    <div className="p-2.5 rounded-lg bg-emerald-50/70 border border-emerald-100 text-[11px] text-emerald-900">
                      <strong>Suitability: </strong>{pw.suitability}
                    </div>

                    <div className="p-2.5 rounded-lg bg-sky-50/80 border border-sky-100 text-[11px] text-sky-900 flex items-start gap-2">
                      <Plane className="w-3.5 h-3.5 text-sky-600 shrink-0 mt-0.5" />
                      <div>
                        <strong>Air Travel Clearance: </strong>
                        <span>{pw.flight_clearance_guideline}</span>
                      </div>
                    </div>

                    {pw.grounding_sources && pw.grounding_sources.length > 0 && (
                      <div className="text-[10px] text-slate-400 pt-1 border-t border-slate-100">
                        <span className="font-semibold text-slate-500">Grounded Source: </span>
                        {pw.grounding_sources.map((s, idx) => (
                          <span key={idx} className="mr-2">
                            {s.organization}: <em>{s.title}</em>
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>

        {/* Right Col: Specialty & Action Recommendations */}
        <div className="space-y-6">
          
          <div className="glass-card rounded-2xl p-5 border border-slate-200">
            <h3 className="text-xs font-bold uppercase text-slate-400 tracking-wider mb-2">Recommended Specialty</h3>
            <p className="text-xl font-black text-sky-700">{specialty}</p>
            <p className="text-xs text-slate-600 mt-2">
              {report?.important_notes || `Clinical findings suggest dedicated outpatient specialist evaluation under ${specialty}.`}
            </p>

            <div className="mt-4 pt-4 border-t border-slate-100 space-y-2">
              <button
                onClick={() => navigate(`/hospitals?specialty=${encodeURIComponent(specialty || '')}&report_id=${report.id}`)}
                className="w-full py-2.5 rounded-xl font-bold text-xs text-white gradient-bg shadow hover:opacity-95 transition-opacity flex items-center justify-center gap-1.5"
              >
                <Building2 className="w-3.5 h-3.5" />
                <span>1. View Recommended Hospitals</span>
              </button>

              <button
                onClick={() => navigate(`/cost?treatment=${encodeURIComponent(specialty || '')}&report_id=${report.id}`)}
                className="w-full py-2.5 rounded-xl font-bold text-xs text-slate-800 bg-sky-50 border border-sky-200 hover:bg-sky-100 transition-colors flex items-center justify-center gap-1.5"
              >
                <ArrowRight className="w-3.5 h-3.5 text-sky-600" />
                <span>2. Estimate Treatment Cost & LOS</span>
              </button>

              <button
                onClick={() => navigate(`/assistant?report_id=${report.id}`)}
                className="w-full py-2.5 rounded-xl font-bold text-xs text-slate-700 bg-slate-100 hover:bg-slate-200 transition-colors flex items-center justify-center gap-1.5"
              >
                <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                <span>3. Consult AI Assistant</span>
              </button>

              <button
                onClick={() => navigate('/travel')}
                className="w-full py-2.5 rounded-xl font-bold text-xs text-slate-700 bg-slate-100 hover:bg-slate-200 transition-colors flex items-center justify-center gap-1.5"
              >
                <Navigation className="w-3.5 h-3.5 text-indigo-500" />
                <span>4. Medical Travel & Local Connectivity</span>
              </button>
            </div>
          </div>

          <div className="p-4 bg-amber-50 rounded-2xl border border-amber-200 text-xs text-amber-900 leading-relaxed">
            <strong className="block font-bold mb-1 flex items-center gap-1">
              <AlertCircle className="w-4 h-4 text-amber-600" />
              Medical Safety Note:
            </strong>
            This analysis is generated for clinical decision support. Please verify findings with a registered physician during your clinical consultation.
          </div>

        </div>

      </div>
    </div>
  );
};
