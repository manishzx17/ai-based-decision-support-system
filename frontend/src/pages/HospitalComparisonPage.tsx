import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  GitCompare, CheckCircle2, XCircle, Sparkles, Star, ArrowRight, ArrowLeft,
  Loader2, Building2, UserCheck, ShieldCheck, MapPin, Award, Calculator, Info
} from 'lucide-react';
import { DisclaimerBadge } from '../components/DisclaimerBadge';
import {
  compareHospitals, compareDoctors, getRecommendedHospitals, getRecommendedDoctors,
  Hospital, Doctor, getCurrentUser, getCurrentUserId
} from '../services/api';

export const HospitalComparisonPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const urlType = searchParams.get('type') === 'doctor' ? 'doctor' : 'hospital';
  const urlIds = searchParams.get('ids');
  const urlSpecialty = searchParams.get('specialty') || 'Cardiology';
  const urlCity = searchParams.get('city') || 'Hyderabad';
  const urlPriorityMode = searchParams.get('priority_mode') || undefined;
  const urlInsurance = searchParams.get('insurance') || undefined;
  const urlMaxBudget = searchParams.get('max_budget') ? Number(searchParams.get('max_budget')) : undefined;
  const urlReportId = searchParams.get('report_id') ? Number(searchParams.get('report_id')) : undefined;

  const [compareType, setCompareType] = useState<'hospital' | 'doctor'>(urlType);
  const [hospitals, setHospitals] = useState<Hospital[]>([]);
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [availableHospitals, setAvailableHospitals] = useState<Hospital[]>([]);
  const [availableDoctors, setAvailableDoctors] = useState<Doctor[]>([]);
  const [recommendationText, setRecommendationText] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const user = getCurrentUser() || { id: getCurrentUserId() || 1 };

  // Sync mode changes to URL
  const handleSwitchType = (type: 'hospital' | 'doctor') => {
    setCompareType(type);
    setSearchParams(prev => {
      const next = new URLSearchParams(prev);
      next.set('type', type);
      next.delete('ids');
      return next;
    });
  };

  // Load comparison data safely
  useEffect(() => {
    let isMounted = true;

    async function loadData() {
      try {
        setLoading(true);
        setErrorMsg(null);

        if (compareType === 'hospital') {
          // Parse IDs from URL if present
          let targetIds: number[] = [];
          if (urlIds) {
            targetIds = urlIds.split(',').map(Number).filter(n => !isNaN(n) && n > 0);
          }

          // Fetch user's personalized recommendation pool for reference/swapping
          const pool = await getRecommendedHospitals({
            specialty: urlSpecialty,
            city: urlCity,
            priority_mode: urlPriorityMode,
            insurance: urlInsurance,
            max_budget: urlMaxBudget,
            report_id: urlReportId,
            user_id: user.id
          });
          if (isMounted) {
            setAvailableHospitals(pool || []);
          }

          // If no specific IDs provided in URL, auto-select top 3 from recommendation pool
          if (targetIds.length === 0 && pool && pool.length > 0) {
            targetIds = pool.slice(0, 3).map(h => h.id);
          }

          if (targetIds.length > 0) {
            const res = await compareHospitals(targetIds, {
              user_id: user.id,
              city: urlCity,
              specialty: urlSpecialty,
              priority_mode: urlPriorityMode,
              insurance: urlInsurance,
              max_budget: urlMaxBudget,
              report_id: urlReportId
            });
            if (isMounted && res?.compared_hospitals) {
              setHospitals(res.compared_hospitals);
              setRecommendationText(res.ai_recommendation || '');
            }
          } else {
            if (isMounted) {
              setHospitals([]);
              setRecommendationText('');
            }
          }
        } else {
          // Doctor comparison
          let targetIds: number[] = [];
          if (urlIds) {
            targetIds = urlIds.split(',').map(Number).filter(n => !isNaN(n) && n > 0);
          }

          const pool = await getRecommendedDoctors({
            specialty: urlSpecialty,
            report_id: urlReportId,
            user_id: user.id
          });
          if (isMounted) {
            setAvailableDoctors(pool || []);
          }

          // If no specific IDs provided in URL, auto-select top 3 from pool
          if (targetIds.length === 0 && pool && pool.length > 0) {
            targetIds = pool.slice(0, 3).map(d => d.id);
          }

          if (targetIds.length > 0) {
            const res = await compareDoctors(targetIds, {
              user_id: user.id,
              specialty: urlSpecialty,
              report_id: urlReportId
            });
            if (isMounted && res?.compared_doctors) {
              setDoctors(res.compared_doctors);
              setRecommendationText(res.ai_recommendation || '');
            }
          } else {
            if (isMounted) {
              setDoctors([]);
              setRecommendationText('');
            }
          }
        }
      } catch (err: any) {
        console.error('Failed to load comparison', err);
        if (isMounted) {
          setErrorMsg('Unable to retrieve comparison data for the selected providers.');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    loadData();

    return () => {
      isMounted = false;
    };
  }, [compareType, urlIds, urlSpecialty, urlCity, urlPriorityMode, urlInsurance, urlMaxBudget, urlReportId, user.id]);

  // Remove an item from comparison
  const handleRemoveHospital = (id: number) => {
    const remaining = hospitals.filter(h => h.id !== id).map(h => h.id);
    setSearchParams(prev => {
      const next = new URLSearchParams(prev);
      if (remaining.length > 0) {
        next.set('ids', remaining.join(','));
      } else {
        next.delete('ids');
      }
      return next;
    });
  };

  const handleRemoveDoctor = (id: number) => {
    const remaining = doctors.filter(d => d.id !== id).map(d => d.id);
    setSearchParams(prev => {
      const next = new URLSearchParams(prev);
      if (remaining.length > 0) {
        next.set('ids', remaining.join(','));
      } else {
        next.delete('ids');
      }
      return next;
    });
  };

  // Add an item from available pool
  const handleAddHospital = (id: number) => {
    if (hospitals.some(h => h.id === id) || hospitals.length >= 3) return;
    const nextIds = [...hospitals.map(h => h.id), id];
    setSearchParams(prev => {
      const next = new URLSearchParams(prev);
      next.set('ids', nextIds.join(','));
      return next;
    });
  };

  const handleAddDoctor = (id: number) => {
    if (doctors.some(d => d.id === id) || doctors.length >= 3) return;
    const nextIds = [...doctors.map(d => d.id), id];
    setSearchParams(prev => {
      const next = new URLSearchParams(prev);
      next.set('ids', nextIds.join(','));
      return next;
    });
  };

  // Load top 3 preset
  const handleLoadTop3 = () => {
    if (compareType === 'hospital') {
      const top3 = availableHospitals.slice(0, 3).map(h => h.id);
      if (top3.length > 0) {
        setSearchParams(prev => {
          const next = new URLSearchParams(prev);
          next.set('ids', top3.join(','));
          return next;
        });
      }
    } else {
      const top3 = availableDoctors.slice(0, 3).map(d => d.id);
      if (top3.length > 0) {
        setSearchParams(prev => {
          const next = new URLSearchParams(prev);
          next.set('ids', top3.join(','));
          return next;
        });
      }
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      
      {/* Top Navigation & Controls */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/hospitals')}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 transition-colors shadow-sm"
          >
            <ArrowLeft className="w-4 h-4 text-slate-500" />
            <span>Back to Hospital Recommendations</span>
          </button>

          <div className="h-4 w-px bg-slate-200 hidden sm:block" />

          <div>
            <h1 className="text-2xl font-black text-slate-900 flex items-center gap-2">
              <span>Side-by-Side Hospital Comparison</span>
            </h1>
            <p className="text-xs text-slate-500 mt-0.5 flex flex-wrap items-center gap-2">
              <span>Personalized multi-criteria comparison for {urlSpecialty} ({urlCity})</span>
              {urlPriorityMode && (
                <span className="font-mono text-[10px] font-bold bg-sky-50 text-sky-700 px-2 py-0.5 rounded border border-sky-200">
                  User Preference: {urlPriorityMode.replace('_', ' ').toUpperCase()}
                </span>
              )}
            </p>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {loading ? (
        <div className="glass-card rounded-2xl p-16 flex flex-col items-center justify-center text-slate-500 gap-3 border border-slate-200">
          <Loader2 className="w-8 h-8 animate-spin text-sky-600" />
          <p className="text-sm font-bold text-slate-800">Computing Side-by-Side Multi-Criteria Matrix...</p>
          <p className="text-xs text-slate-500">Evaluating clinical match, infrastructure, proximity, and cost parameters</p>
        </div>
      ) : errorMsg ? (
        <div className="glass-card rounded-2xl p-8 border border-red-200 bg-red-50/50 text-center">
          <p className="font-bold text-red-800 text-sm mb-2">{errorMsg}</p>
          <button
            onClick={() => handleLoadTop3()}
            className="text-xs font-bold text-white gradient-bg px-4 py-2 rounded-xl shadow hover:opacity-95 mt-2"
          >
            Reload Top Recommendations
          </button>
        </div>
      ) : compareType === 'hospital' ? (
        /* =========================================================================
           HOSPITAL COMPARISON VIEW
           ========================================================================= */
        hospitals.length === 0 ? (
          <div className="glass-card rounded-3xl p-12 text-center border border-slate-200 shadow-sm max-w-2xl mx-auto">
            <div className="w-14 h-14 bg-sky-50 rounded-2xl flex items-center justify-center mx-auto mb-4 border border-sky-100">
              <GitCompare className="w-7 h-7 text-sky-600" />
            </div>
            <h2 className="text-lg font-bold text-slate-900 mb-1">Select 2 to 3 Hospitals for Side-by-Side Comparison</h2>
            <p className="text-xs text-slate-600 mb-6 leading-relaxed">
              Compare accredited medical facilities, clinical specialty capabilities, cost tiers, ICU bed counts, and patient satisfaction ratings.
            </p>
            <div className="flex flex-wrap items-center justify-center gap-3">
              <button
                onClick={handleLoadTop3}
                className="text-xs font-bold text-white gradient-bg px-5 py-2.5 rounded-xl shadow hover:opacity-95 transition-all"
              >
                Compare Top 3 Recommended Hospitals
              </button>
              <button
                onClick={() => navigate('/hospitals')}
                className="text-xs font-bold text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 px-5 py-2.5 rounded-xl transition-colors"
              >
                Browse All Hospitals
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            
            {/* Quick Picker Bar for Switching / Adding Candidates */}
            <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 bg-slate-50 border border-slate-200 rounded-2xl text-xs">
              <div className="flex items-center gap-2 text-slate-700 font-semibold">
                <Building2 className="w-4 h-4 text-sky-600 shrink-0" />
                <span>Comparing <strong className="text-slate-900">{hospitals.length}</strong> of 3 medical centers</span>
              </div>

              {hospitals.length < 3 && availableHospitals.length > 0 && (
                <div className="flex items-center gap-2">
                  <span className="text-slate-500 font-medium">Add to comparison:</span>
                  <select
                    onChange={(e) => {
                      const id = Number(e.target.value);
                      if (id) handleAddHospital(id);
                      e.target.value = '';
                    }}
                    defaultValue=""
                    className="px-3 py-1.5 rounded-lg border border-slate-300 text-xs font-semibold bg-white text-slate-700 focus:ring-2 focus:ring-sky-500"
                  >
                    <option value="" disabled>Select hospital to add...</option>
                    {availableHospitals
                      .filter(h => !hospitals.some(curr => curr.id === h.id))
                      .slice(0, 8)
                      .map(h => (
                        <option key={h.id} value={h.id}>{h.name} ({h.city})</option>
                      ))}
                  </select>
                </div>
              )}
            </div>

            {/* Side-by-Side Hospital Comparison Matrix Table */}
            <div className="glass-card rounded-3xl border border-slate-200 overflow-hidden shadow-xl">
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-100/90 text-slate-700 font-black uppercase text-[11px] border-b border-slate-200 tracking-wider">
                      <th className="p-4 w-52 bg-slate-200/50">Feature / Metric</th>
                      {hospitals.map((h, i) => (
                        <th
                          key={h.id || i}
                          className={`p-4 border-l border-slate-200 min-w-[240px] ${
                            i === 0 ? 'bg-sky-50/70 text-sky-950' : 'bg-white text-slate-900'
                          }`}
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div>
                              <div className="flex items-center gap-1.5 mb-1">
                                {i === 0 && (
                                  <span className="bg-sky-600 text-white font-extrabold px-2 py-0.5 rounded text-[10px] tracking-normal">
                                    Top Recommendation
                                  </span>
                                )}
                                <span className="text-[10px] text-slate-500 font-bold uppercase">
                                  #{i + 1} Ranked
                                </span>
                              </div>
                              <span className="font-bold text-sm text-slate-900 block">{h.name}</span>
                              <span className="text-[11px] text-slate-500 font-medium">{h.city}, {h.state || 'India'}</span>
                            </div>
                            <button
                              onClick={() => handleRemoveHospital(h.id)}
                              title="Remove from comparison"
                              className="text-slate-400 hover:text-red-500 transition-colors p-1 rounded-md hover:bg-red-50"
                            >
                              <XCircle className="w-4 h-4" />
                            </button>
                          </div>
                        </th>
                      ))}
                    </tr>
                  </thead>

                  <tbody className="divide-y divide-slate-200">
                    
                    {/* Overall Score */}
                    <tr className="bg-slate-50/30">
                      <td className="p-4 font-bold text-slate-900 flex items-center gap-1.5">
                        <Award className="w-4 h-4 text-sky-600" />
                        <span>Overall Match Score</span>
                      </td>
                      {hospitals.map((h, i) => (
                        <td key={i} className={`p-4 border-l border-slate-200 ${i === 0 ? 'bg-sky-50/40' : ''}`}>
                          <div className="flex items-baseline gap-1.5">
                            <span className="text-base font-extrabold text-sky-700">
                              {h.recommendation_score !== undefined ? `${h.recommendation_score.toFixed(1)}%` : '—'}
                            </span>
                            <span className="text-[10px] text-slate-500">Multi-Criteria</span>
                          </div>
                          {h.score_breakdown && (
                            <div className="mt-2 text-[10px] text-slate-600 space-y-0.5 bg-white/80 p-2 rounded-lg border border-slate-100">
                              <div>Clinical Match: <span className="font-bold">{h.score_breakdown.clinical_match?.toFixed(1) ?? '35.0'} pts</span></div>
                              <div>Cost & Coverage: <span className="font-bold">{h.score_breakdown.cost_insurance?.toFixed(1) ?? '25.0'} pts</span></div>
                              <div>Proximity: <span className="font-bold">{h.score_breakdown.distance_proximity?.toFixed(1) ?? '20.0'} pts</span></div>
                              <div>Quality & Accr.: <span className="font-bold">{h.score_breakdown.quality_accreditation?.toFixed(1) ?? '20.0'} pts</span></div>
                            </div>
                          )}
                        </td>
                      ))}
                    </tr>

                    {/* Quality Rating */}
                    <tr>
                      <td className="p-4 font-bold text-slate-900">Quality Rating</td>
                      {hospitals.map((h, i) => (
                        <td key={i} className={`p-4 border-l border-slate-200 ${i === 0 ? 'bg-sky-50/20' : ''}`}>
                          <div className="flex items-center gap-1 font-bold text-amber-600 text-sm">
                            <Star className="w-4 h-4 fill-amber-400 text-amber-500" />
                            <span>{(h.quality_rating || h.rating || 4.5).toFixed(1)} / 5.0</span>
                          </div>
                          <span className="text-[10px] text-slate-500 block mt-0.5">Accredited Clinical Benchmark</span>
                        </td>
                      ))}
                    </tr>

                    {/* Accreditation */}
                    <tr>
                      <td className="p-4 font-bold text-slate-900">Accreditation</td>
                      {hospitals.map((h, i) => (
                        <td key={i} className={`p-4 border-l border-slate-200 ${i === 0 ? 'bg-sky-50/20' : ''}`}>
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
                            <ShieldCheck className="w-3.5 h-3.5 text-indigo-600" />
                            {h.accreditation || 'NABH Accredited'}
                          </span>
                        </td>
                      ))}
                    </tr>

                    {/* Cost Tier & Estimated Cost */}
                    <tr>
                      <td className="p-4 font-bold text-slate-900">Cost Tier & Estimates</td>
                      {hospitals.map((h, i) => (
                        <td key={i} className={`p-4 border-l border-slate-200 ${i === 0 ? 'bg-sky-50/20' : ''}`}>
                          <span className="font-bold text-slate-900 text-xs block">{h.cost_tier || 'Moderate'} Tier</span>
                          <span className="text-slate-600 text-[11px] font-semibold">
                            Est: ₹{(h.estimated_cost_tier || 320000).toLocaleString('en-IN')} INR
                          </span>
                        </td>
                      ))}
                    </tr>

                    {/* Treatment Capabilities */}
                    <tr>
                      <td className="p-4 font-bold text-slate-900">Treatment Capabilities</td>
                      {hospitals.map((h, i) => {
                        const caps = (h.treatment_capabilities && h.treatment_capabilities.length > 0)
                          ? h.treatment_capabilities
                          : h.specialties;
                        return (
                          <td key={i} className={`p-4 border-l border-slate-200 ${i === 0 ? 'bg-sky-50/20' : ''}`}>
                            <div className="flex flex-wrap gap-1">
                              {caps && caps.length > 0 ? (
                                caps.slice(0, 5).map((c, idx) => (
                                  <span key={idx} className="bg-slate-100 text-slate-700 font-medium px-2 py-0.5 rounded text-[10px]">
                                    {c}
                                  </span>
                                ))
                              ) : (
                                <span className="text-slate-400 text-xs">Specialty Care</span>
                              )}
                            </div>
                          </td>
                        );
                      })}
                    </tr>

                    {/* ICU Beds */}
                    <tr>
                      <td className="p-4 font-bold text-slate-900">Critical Care (ICU Beds)</td>
                      {hospitals.map((h, i) => (
                        <td key={i} className={`p-4 border-l border-slate-200 font-semibold text-slate-800 ${i === 0 ? 'bg-sky-50/20' : ''}`}>
                          <span className="text-xs font-bold text-slate-900">{h.icu_beds || 50} Intensive Care Beds</span>
                        </td>
                      ))}
                    </tr>

                    {/* Emergency 24x7 */}
                    <tr>
                      <td className="p-4 font-bold text-slate-900">Emergency & Trauma 24x7</td>
                      {hospitals.map((h, i) => (
                        <td key={i} className={`p-4 border-l border-slate-200 ${i === 0 ? 'bg-sky-50/20' : ''}`}>
                          {h.emergency_24x7 !== false ? (
                            <span className="inline-flex items-center gap-1 text-emerald-700 font-bold text-xs">
                              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                              24x7 Emergency Active
                            </span>
                          ) : (
                            <span className="text-slate-400 text-xs">Scheduled Hours</span>
                          )}
                        </td>
                      ))}
                    </tr>

                    {/* Cashless Insurance Empanelment */}
                    <tr>
                      <td className="p-4 font-bold text-slate-900">Cashless Insurance Support</td>
                      {hospitals.map((h, i) => (
                        <td key={i} className={`p-4 border-l border-slate-200 ${i === 0 ? 'bg-sky-50/20' : ''}`}>
                          <div className="flex flex-wrap gap-1">
                            {h.insurance_accepted && h.insurance_accepted.length > 0 ? (
                              h.insurance_accepted.map((ins, idx) => (
                                <span key={idx} className="bg-emerald-50 text-emerald-800 border border-emerald-200 font-medium px-2 py-0.5 rounded text-[10px]">
                                  {ins}
                                </span>
                              ))
                            ) : (
                              <span className="text-slate-500">Reimbursement Desk</span>
                            )}
                          </div>
                        </td>
                      ))}
                    </tr>

                    {/* Proximity / Distance */}
                    <tr>
                      <td className="p-4 font-bold text-slate-900">Distance from Stay</td>
                      {hospitals.map((h, i) => (
                        <td key={i} className={`p-4 border-l border-slate-200 font-semibold text-slate-800 ${i === 0 ? 'bg-sky-50/20' : ''}`}>
                          <div className="flex items-center gap-1">
                            <MapPin className="w-3.5 h-3.5 text-slate-400" />
                            <span>{h.distance_km ? `${h.distance_km.toFixed(1)} km` : 'Local Hub'}</span>
                          </div>
                        </td>
                      ))}
                    </tr>

                    {/* Action Row */}
                    <tr className="bg-slate-50/60">
                      <td className="p-4 font-bold text-slate-900">Treatment Estimation</td>
                      {hospitals.map((h, i) => (
                        <td key={i} className={`p-4 border-l border-slate-200 ${i === 0 ? 'bg-sky-50/40' : ''}`}>
                          <button
                            onClick={() => {
                              const activeRep = sessionStorage.getItem('active_report_id') || '';
                              navigate(`/cost?hospital_id=${h.id}${activeRep ? `&report_id=${activeRep}` : ''}`);
                            }}
                            className={`w-full py-2.5 px-3 rounded-xl font-bold text-xs flex items-center justify-center gap-1.5 shadow-sm transition-all ${
                              i === 0
                                ? 'gradient-bg text-white hover:opacity-95'
                                : 'bg-white text-slate-700 border border-slate-300 hover:border-sky-500 hover:text-sky-600'
                            }`}
                          >
                            <span>Estimate Cost & LOS</span>
                            <ArrowRight className="w-3.5 h-3.5" />
                          </button>
                        </td>
                      ))}
                    </tr>

                  </tbody>
                </table>
              </div>
            </div>

            {/* AI Decision Explanation Box */}
            <div className="glass-card rounded-2xl p-6 border border-sky-200 bg-sky-50/60 shadow-sm">
              <div className="flex items-center gap-2 mb-2 font-extrabold text-slate-900 text-sm">
                <Sparkles className="w-4 h-4 text-sky-600" />
                <span>AI Multi-Criteria Comparison Analysis</span>
              </div>
              <p className="text-xs text-slate-700 leading-relaxed">
                {recommendationText || (hospitals[0] ? `Hospital '${hospitals[0].name}' ranks highest in this comparison based on accredited specialty infrastructure, optimal geographic proximity (${hospitals[0].distance_km} km), and comprehensive cashless insurance compatibility.` : '')}
              </p>
            </div>

          </div>
        )
      ) : (
        /* =========================================================================
           DOCTOR COMPARISON VIEW
           ========================================================================= */
        doctors.length === 0 ? (
          <div className="glass-card rounded-3xl p-12 text-center border border-slate-200 shadow-sm max-w-2xl mx-auto">
            <div className="w-14 h-14 bg-sky-50 rounded-2xl flex items-center justify-center mx-auto mb-4 border border-sky-100">
              <UserCheck className="w-7 h-7 text-sky-600" />
            </div>
            <h2 className="text-lg font-bold text-slate-900 mb-1">Select 2 to 3 Specialists for Side-by-Side Comparison</h2>
            <p className="text-xs text-slate-600 mb-6 leading-relaxed">
              Compare clinical specialists across subspecialty expertise, years of clinical practice, patient satisfaction ratings, consultation fees, and hospital affiliations.
            </p>
            <div className="flex flex-wrap items-center justify-center gap-3">
              <button
                onClick={handleLoadTop3}
                className="text-xs font-bold text-white gradient-bg px-5 py-2.5 rounded-xl shadow hover:opacity-95 transition-all"
              >
                Compare Top 3 Recommended Doctors
              </button>
              <button
                onClick={() => navigate('/doctors')}
                className="text-xs font-bold text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 px-5 py-2.5 rounded-xl transition-colors"
              >
                Browse All Specialists
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            
            {/* Quick Picker Bar for Doctors */}
            <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 bg-slate-50 border border-slate-200 rounded-2xl text-xs">
              <div className="flex items-center gap-2 text-slate-700 font-semibold">
                <UserCheck className="w-4 h-4 text-sky-600 shrink-0" />
                <span>Comparing <strong className="text-slate-900">{doctors.length}</strong> of 3 specialists</span>
              </div>

              {doctors.length < 3 && availableDoctors.length > 0 && (
                <div className="flex items-center gap-2">
                  <span className="text-slate-500 font-medium">Add to comparison:</span>
                  <select
                    onChange={(e) => {
                      const id = Number(e.target.value);
                      if (id) handleAddDoctor(id);
                      e.target.value = '';
                    }}
                    defaultValue=""
                    className="px-3 py-1.5 rounded-lg border border-slate-300 text-xs font-semibold bg-white text-slate-700 focus:ring-2 focus:ring-sky-500"
                  >
                    <option value="" disabled>Select specialist to add...</option>
                    {availableDoctors
                      .filter(d => !doctors.some(curr => curr.id === d.id))
                      .slice(0, 8)
                      .map(d => (
                        <option key={d.id} value={d.id}>{d.name} ({d.specialty})</option>
                      ))}
                  </select>
                </div>
              )}
            </div>

            {/* Side-by-Side Doctor Comparison Matrix Table */}
            <div className="glass-card rounded-3xl border border-slate-200 overflow-hidden shadow-xl">
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-100/90 text-slate-700 font-black uppercase text-[11px] border-b border-slate-200 tracking-wider">
                      <th className="p-4 w-52 bg-slate-200/50">Specialist Metric</th>
                      {doctors.map((d, i) => (
                        <th
                          key={d.id || i}
                          className={`p-4 border-l border-slate-200 min-w-[240px] ${
                            i === 0 ? 'bg-sky-50/70 text-sky-950' : 'bg-white text-slate-900'
                          }`}
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div>
                              <div className="flex items-center gap-1.5 mb-1">
                                {i === 0 && (
                                  <span className="bg-sky-600 text-white font-extrabold px-2 py-0.5 rounded text-[10px] tracking-normal">
                                    Top Specialist Match
                                  </span>
                                )}
                                <span className="text-[10px] text-slate-500 font-bold uppercase">
                                  #{i + 1} Ranked
                                </span>
                              </div>
                              <span className="font-bold text-sm text-slate-900 block">{d.name}</span>
                              <span className="text-[11px] text-slate-500 font-medium">{d.qualification}</span>
                            </div>
                            <button
                              onClick={() => handleRemoveDoctor(d.id)}
                              title="Remove from comparison"
                              className="text-slate-400 hover:text-red-500 transition-colors p-1 rounded-md hover:bg-red-50"
                            >
                              <XCircle className="w-4 h-4" />
                            </button>
                          </div>
                        </th>
                      ))}
                    </tr>
                  </thead>

                  <tbody className="divide-y divide-slate-200">
                    
                    {/* Clinical Match Score */}
                    <tr className="bg-slate-50/30">
                      <td className="p-4 font-bold text-slate-900 flex items-center gap-1.5">
                        <Award className="w-4 h-4 text-sky-600" />
                        <span>Clinical Match Score</span>
                      </td>
                      {doctors.map((d, i) => (
                        <td key={i} className={`p-4 border-l border-slate-200 ${i === 0 ? 'bg-sky-50/40' : ''}`}>
                          <div className="flex items-baseline gap-1.5">
                            <span className="text-base font-extrabold text-sky-700">
                              {d.match_score !== undefined ? `${d.match_score.toFixed(1)}%` : '—'}
                            </span>
                            <span className="text-[10px] text-slate-500">Clinical Fit</span>
                          </div>
                          {d.score_breakdown && (
                            <div className="mt-2 text-[10px] text-slate-600 space-y-0.5 bg-white/80 p-2 rounded-lg border border-slate-100">
                              <div>Specialty Match: <span className="font-bold">{d.score_breakdown.specialty_match?.toFixed(1) ?? '50.0'} pts</span></div>
                              <div>Experience: <span className="font-bold">{d.score_breakdown.experience?.toFixed(1) ?? '25.0'} pts</span></div>
                              <div>Satisfaction: <span className="font-bold">{d.score_breakdown.rating?.toFixed(1) ?? '25.0'} pts</span></div>
                            </div>
                          )}
                        </td>
                      ))}
                    </tr>

                    {/* Primary Specialty */}
                    <tr>
                      <td className="p-4 font-bold text-slate-900">Primary Specialty</td>
                      {doctors.map((d, i) => (
                        <td key={i} className={`p-4 border-l border-slate-200 font-bold text-slate-800 ${i === 0 ? 'bg-sky-50/20' : ''}`}>
                          <span className="inline-flex px-2.5 py-0.5 rounded-full text-xs font-bold bg-sky-50 text-sky-700 border border-sky-200">
                            {d.specialty}
                          </span>
                        </td>
                      ))}
                    </tr>

                    {/* Subspecialty Expertise */}
                    <tr>
                      <td className="p-4 font-bold text-slate-900">Subspecialty Expertise</td>
                      {doctors.map((d, i) => (
                        <td key={i} className={`p-4 border-l border-slate-200 ${i === 0 ? 'bg-sky-50/20' : ''}`}>
                          <div className="flex flex-wrap gap-1">
                            {d.expertise && d.expertise.length > 0 ? (
                              d.expertise.map((exp, idx) => (
                                <span key={idx} className="bg-indigo-50 text-indigo-700 border border-indigo-100 px-2 py-0.5 rounded text-[10px] font-medium">
                                  {exp}
                                </span>
                              ))
                            ) : (
                              <span className="text-slate-400 text-xs">Clinical Specialist</span>
                            )}
                          </div>
                        </td>
                      ))}
                    </tr>

                    {/* Clinical Experience */}
                    <tr>
                      <td className="p-4 font-bold text-slate-900">Clinical Experience</td>
                      {doctors.map((d, i) => (
                        <td key={i} className={`p-4 border-l border-slate-200 font-bold text-slate-800 text-xs ${i === 0 ? 'bg-sky-50/20' : ''}`}>
                          <span>{d.experience_years} Years Practice</span>
                        </td>
                      ))}
                    </tr>

                    {/* Patient Rating */}
                    <tr>
                      <td className="p-4 font-bold text-slate-900">Patient Rating</td>
                      {doctors.map((d, i) => (
                        <td key={i} className={`p-4 border-l border-slate-200 ${i === 0 ? 'bg-sky-50/20' : ''}`}>
                          <div className="flex items-center gap-1 font-bold text-amber-600 text-sm">
                            <Star className="w-4 h-4 fill-amber-400 text-amber-500" />
                            <span>{d.rating.toFixed(1)} / 5.0</span>
                          </div>
                        </td>
                      ))}
                    </tr>

                    {/* Consultation Fee */}
                    <tr>
                      <td className="p-4 font-bold text-slate-900">Consultation Fee</td>
                      {doctors.map((d, i) => (
                        <td key={i} className={`p-4 border-l border-slate-200 font-bold text-slate-900 text-xs ${i === 0 ? 'bg-sky-50/20' : ''}`}>
                          <span>₹{(d.consultation_fee || 1000).toLocaleString('en-IN')} INR</span>
                        </td>
                      ))}
                    </tr>

                    {/* Hospital Affiliation */}
                    <tr>
                      <td className="p-4 font-bold text-slate-900">Hospital Affiliation</td>
                      {doctors.map((d, i) => (
                        <td key={i} className={`p-4 border-l border-slate-200 ${i === 0 ? 'bg-sky-50/20' : ''}`}>
                          <div className="font-semibold text-slate-800 text-xs flex items-center gap-1">
                            <Building2 className="w-3.5 h-3.5 text-sky-600 shrink-0" />
                            <span>{d.hospital_name || 'Accredited Medical Center'}</span>
                          </div>
                          <span className="text-[10px] text-slate-500 block mt-0.5">{d.hospital_city || 'Medical Hub'}</span>
                        </td>
                      ))}
                    </tr>

                    {/* Key Recommendation Drivers */}
                    <tr>
                      <td className="p-4 font-bold text-slate-900">Recommendation Drivers</td>
                      {doctors.map((d, i) => (
                        <td key={i} className={`p-4 border-l border-slate-200 text-slate-600 ${i === 0 ? 'bg-sky-50/20' : ''}`}>
                          <ul className="space-y-1 text-[11px]">
                            {d.reasons && d.reasons.length > 0 ? (
                              d.reasons.slice(0, 3).map((r, idx) => (
                                <li key={idx} className="leading-tight">{r}</li>
                              ))
                            ) : (
                              <li>✓ {d.experience_years} years clinical practice</li>
                            )}
                          </ul>
                        </td>
                      ))}
                    </tr>

                    {/* Action Row */}
                    <tr className="bg-slate-50/60">
                      <td className="p-4 font-bold text-slate-900">Next Clinical Step</td>
                      {doctors.map((d, i) => (
                        <td key={i} className={`p-4 border-l border-slate-200 ${i === 0 ? 'bg-sky-50/40' : ''}`}>
                          <button
                            onClick={() => {
                              const activeRep = sessionStorage.getItem('active_report_id') || '';
                              navigate(`/cost?specialty=${encodeURIComponent(d.specialty)}${activeRep ? `&report_id=${activeRep}` : ''}`);
                            }}
                            className={`w-full py-2.5 px-3 rounded-xl font-bold text-xs flex items-center justify-center gap-1.5 shadow-sm transition-all ${
                              i === 0
                                ? 'gradient-bg text-white hover:opacity-95'
                                : 'bg-white text-slate-700 border border-slate-300 hover:border-sky-500 hover:text-sky-600'
                            }`}
                          >
                            <Calculator className="w-3.5 h-3.5" />
                            <span>Estimate Treatment Cost</span>
                          </button>
                        </td>
                      ))}
                    </tr>

                  </tbody>
                </table>
              </div>
            </div>

            {/* AI Decision Explanation Box */}
            <div className="glass-card rounded-2xl p-6 border border-sky-200 bg-sky-50/60 shadow-sm">
              <div className="flex items-center gap-2 mb-2 font-extrabold text-slate-900 text-sm">
                <Sparkles className="w-4 h-4 text-sky-600" />
                <span>AI Clinical Specialist Analysis</span>
              </div>
              <p className="text-xs text-slate-700 leading-relaxed">
                {recommendationText || (doctors[0] ? `Doctor '${doctors[0].name}' ranks highest in this comparison based on specialty alignment, clinical experience (${doctors[0].experience_years} years), and superior patient satisfaction rating (${doctors[0].rating.toFixed(1)}/5.0).` : '')}
              </p>
            </div>

          </div>
        )
      )}

      {/* Disclaimers */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-500 pt-4 border-t border-slate-200">
        <DisclaimerBadge type="ai" text="Multi-criteria comparative ranking is strictly informational." />
        <span>Algorithm applies multi-criteria 35/25/20/20 hospital matching weights.</span>
      </div>

    </div>
  );
};
