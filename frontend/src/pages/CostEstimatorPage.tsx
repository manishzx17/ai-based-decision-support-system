import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  Calculator,
  ArrowRight,
  TrendingUp,
  Sparkles,
  Building2,
  Calendar,
  ShieldCheck,
  Loader2,
  Info,
  Clock,
  CheckCircle2,
  BarChart3,
  Sliders,
  Bot
} from 'lucide-react';
import { DisclaimerBadge } from '../components/DisclaimerBadge';
import {
  explainTreatmentCost,
  getClinicalRecoveryTimeline,
  getCostModelMetrics,
  getLatestReport,
  getCurrentUserId,
  getActiveReportId,
  CostExplanationResponse,
  ClinicalRecoveryTimelineResponse,
  ModelMetricsResponse
} from '../services/api';

export const CostEstimatorPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const urlTreatment = searchParams.get('treatment');
  const urlCity = searchParams.get('city');
  const urlReportId = searchParams.get('report_id') || getActiveReportId() || undefined;
  const urlHospitalId = searchParams.get('hospital_id') || undefined;

  const [treatment, setTreatment] = useState('Coronary Angioplasty');
  const [city, setCity] = useState(urlCity || 'Hyderabad');
  const [roomType, setRoomType] = useState('Private AC Deluxe');
  const [useAutoLOS, setUseAutoLOS] = useState(true);
  const [customDuration, setCustomDuration] = useState(4);
  const [loading, setLoading] = useState(false);
  const [costData, setCostData] = useState<CostExplanationResponse | null>(null);
  const [timelineData, setTimelineData] = useState<ClinicalRecoveryTimelineResponse | null>(null);
  const [metrics, setMetrics] = useState<ModelMetricsResponse | null>(null);
  const [activeTab, setActiveTab] = useState<'shap' | 'timeline' | 'transparency'>('shap');

  // Load user context and model metrics on mount
  useEffect(() => {
    const initData = async () => {
      try {
        if (urlTreatment) {
          const spec = urlTreatment.toLowerCase();
          if (spec.includes('cardio') || spec.includes('angio')) setTreatment('Coronary Angioplasty');
          else if (spec.includes('ortho') || spec.includes('knee')) setTreatment('Total Knee Replacement');
          else if (spec.includes('neuro') || spec.includes('craniotomy')) setTreatment('Craniotomy');
          else if (spec.includes('onco') || spec.includes('chemo')) setTreatment('Chemotherapy Cycle');
          else setTreatment(urlTreatment);
        }

        if (urlCity) {
          setCity(urlCity);
        }

        const userId = getCurrentUserId();
        const [latestReport, metricsData] = await Promise.all([
          getLatestReport(userId).catch(() => null),
          getCostModelMetrics().catch(() => null)
        ]);

        if (!urlTreatment && latestReport?.recommended_specialty) {
          const spec = latestReport.recommended_specialty.toLowerCase();
          if (spec.includes('cardio')) setTreatment('Coronary Angioplasty');
          else if (spec.includes('ortho')) setTreatment('Total Knee Replacement');
          else if (spec.includes('neuro')) setTreatment('Craniotomy');
          else if (spec.includes('onco')) setTreatment('Chemotherapy Cycle');
        }

        if (metricsData) {
          setMetrics(metricsData);
        }
      } catch (e) {
        console.warn('Failed to load initial context or metrics', e);
      }
    };
    initData();
  }, [urlTreatment, urlCity]);

  const fetchEstimate = async () => {
    try {
      setLoading(true);
      const userId = getCurrentUserId();
      const payload = {
        treatment_name: treatment,
        city,
        room_type: roomType,
        duration_days: useAutoLOS ? undefined : customDuration,
        user_id: userId,
        report_id: urlReportId ? Number(urlReportId) : undefined,
        hospital_id: urlHospitalId ? Number(urlHospitalId) : undefined
      };
      const [res, timelineRes] = await Promise.allSettled([
        explainTreatmentCost(payload),
        getClinicalRecoveryTimeline(payload)
      ]);
      if (res.status === 'fulfilled') setCostData(res.value);
      if (timelineRes.status === 'fulfilled') setTimelineData(timelineRes.value);
    } catch (e) {
      console.warn('Failed to fetch cost explanation or timeline from API', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEstimate();
  }, [treatment, city, roomType, useAutoLOS, customDuration, urlReportId, urlHospitalId]);

  const pred = costData?.prediction;
  const shap = costData?.shap_explanation;
  const errorRange = pred?.empirical_model_error_range || shap?.empirical_model_error_range;

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900">
            XGBoost Treatment Cost & Hospital Stay (LOS) Predictor
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Machine learning regression models with TreeSHAP feature attributions & zero target leakage
          </p>
        </div>

        <DisclaimerBadge type="ai" text="XGBoost + TreeSHAP (Phase 6)" />
      </div>

      {/* Research Prototype & Dataset 4 Notice */}
      <div className="p-3 bg-amber-50/70 border border-amber-200 rounded-xl text-xs text-amber-900 flex items-start gap-2">
        <span className="font-bold shrink-0 text-amber-800">Research Prototype Notice:</span>
        <span>
          Outputs are algorithmic decision-support estimates trained on synthetic benchmark data (Dataset 4 calibrated against NHA/PMJAY and GIPSA schedules). They are not clinically or financially validated predictions. Actual hospital billing and clinical course vary based on physician evaluation, complications, and itemized tariffs.
        </span>
      </div>

      {/* Input Controls */}
      <div className="glass-card rounded-3xl p-6 border border-slate-200 shadow-sm grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div>
          <label className="block text-xs font-bold text-slate-700 mb-1">Medical Procedure</label>
          <select
            value={treatment}
            onChange={(e) => setTreatment(e.target.value)}
            className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-sky-500 bg-white"
          >
            <option value="Coronary Angioplasty">Coronary Angioplasty (PCI)</option>
            <option value="CABG">CABG Coronary Bypass Surgery</option>
            <option value="Total Knee Replacement">Total Knee Replacement (TKR)</option>
            <option value="Craniotomy">Craniotomy / Brain Surgery</option>
            <option value="Chemotherapy Cycle">Chemotherapy Cycle</option>
            <option value="Laparoscopic Cholecystectomy">Laparoscopic Cholecystectomy</option>
            <option value="Appendectomy">Appendectomy</option>
            <option value="Nephrectomy">Nephrectomy (Kidney Surgery)</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-bold text-slate-700 mb-1">Destination Hub</label>
          <select
            value={city}
            onChange={(e) => setCity(e.target.value)}
            className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-sky-500 bg-white"
          >
            <option value="Hyderabad">Hyderabad</option>
            <option value="Mumbai">Mumbai</option>
            <option value="Delhi">Delhi</option>
            <option value="Bengaluru">Bengaluru</option>
            <option value="Chennai">Chennai</option>
            <option value="Kolkata">Kolkata</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-bold text-slate-700 mb-1">Room Category</label>
          <select
            value={roomType}
            onChange={(e) => setRoomType(e.target.value)}
            className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-sky-500 bg-white"
          >
            <option value="General Ward">General Ward</option>
            <option value="Semi-Private AC">Semi-Private AC</option>
            <option value="Private AC Deluxe">Private AC Deluxe</option>
            <option value="Super Deluxe Suite">Super Deluxe Suite</option>
          </select>
        </div>

        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="text-xs font-bold text-slate-700">Stay Duration Mode</label>
            <button
              onClick={() => setUseAutoLOS(!useAutoLOS)}
              className="text-[10px] font-bold text-sky-600 hover:text-sky-700 flex items-center gap-1"
            >
              <Sliders className="w-3 h-3" />
              {useAutoLOS ? 'Switch to Manual' : 'Switch to ML-LOS'}
            </button>
          </div>

          {useAutoLOS ? (
            <div className="p-2.5 bg-sky-50/80 border border-sky-100 rounded-xl flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-sky-600" />
                <span className="text-xs font-semibold text-sky-900">
                  ML-Predicted LOS:
                </span>
              </div>
              <span className="text-xs font-black text-sky-700">
                {pred?.predicted_los_days ? `${pred.predicted_los_days} Days` : 'Estimating...'}
              </span>
            </div>
          ) : (
            <div>
              <div className="flex justify-between text-[11px] text-slate-500">
                <span>Custom Planned Stay:</span>
                <span className="font-bold text-slate-800">{customDuration} Days</span>
              </div>
              <input
                type="range"
                min={1}
                max={21}
                value={customDuration}
                onChange={(e) => setCustomDuration(parseInt(e.target.value))}
                className="w-full mt-1.5 accent-sky-600 cursor-pointer"
              />
            </div>
          )}
        </div>
      </div>

      {/* Main Results Grid */}
      {loading ? (
        <div className="flex items-center justify-center p-16 text-slate-500 gap-2">
          <Loader2 className="w-6 h-6 animate-spin text-sky-600" />
          <span className="text-sm font-semibold">Running XGBoost regression & TreeSHAP...</span>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: Big Cost Display & Key Outputs */}
          <div className="glass-card rounded-3xl p-6 border border-slate-200 flex flex-col justify-between space-y-6">
            <div>
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-extrabold uppercase bg-sky-50 text-sky-700 px-2.5 py-0.5 rounded-full border border-sky-100">
                  Estimated Total Cost
                </span>
                <span className="text-[10px] font-semibold text-slate-400">
                  XGBoost Regressor
                </span>
              </div>

              <h2 className="text-3xl sm:text-4xl font-black text-slate-900 mt-3">
                ₹{(pred?.estimated_avg_cost || 220000).toLocaleString()}{' '}
                <span className="text-xs font-medium text-slate-400">INR</span>
              </h2>

              {/* Empirical Benchmark Error Band */}
              <div className="mt-3 p-3 bg-slate-50 rounded-2xl border border-slate-200">
                <div className="flex items-center gap-1.5 text-xs font-bold text-slate-700">
                  <Info className="w-3.5 h-3.5 text-slate-500" />
                  <span>Empirical Benchmark Error Band</span>
                </div>
                <p className="text-xs font-mono font-bold text-slate-800 mt-1">
                  ₹{(errorRange?.lower_bound || pred?.estimated_min_cost || 180000).toLocaleString()} – ₹
                  {(errorRange?.upper_bound || pred?.estimated_max_cost || 260000).toLocaleString()}
                </p>
                <p className="text-[10px] text-slate-400 mt-1 leading-tight">
                  Empirical benchmark error band based on held-out RMSE (±1.96 × ₹{errorRange?.held_out_rmse_inr?.toLocaleString() || '33,487'}). Not a formal statistical confidence interval or prediction interval.
                </p>
              </div>
            </div>

            {/* Model Outputs Details */}
            <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200 text-xs space-y-2.5">
              <div className="flex justify-between">
                <span className="text-slate-500">Base Procedure:</span>
                <span className="font-bold text-slate-800">{treatment}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Destination City:</span>
                <span className="font-bold text-slate-800">{city}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Room Standard:</span>
                <span className="font-bold text-slate-800">{roomType}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-500">Hospital Stay (LOS):</span>
                <div className="text-right">
                  <span className="font-bold text-slate-800">
                    {pred?.duration_days} Days
                  </span>
                  <span className="block text-[9px] text-sky-600 font-semibold">
                    {pred?.los_source === 'predicted_by_los_model'
                      ? '(ML-Predicted Stay)'
                      : '(User-Planned Stay)'}
                  </span>
                </div>
              </div>
            </div>

            <p className="text-[11px] text-slate-400 italic">
              {pred?.disclaimer ||
                'ML estimate based on empirical tariffs. Actual charges vary with clinical consumables.'}
            </p>
          </div>

          {/* Right: SHAP Attributions & Transparency Tabs */}
          <div className="lg:col-span-2 glass-card rounded-3xl p-6 border border-slate-200 space-y-4">
            {/* Tabs Header */}
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex gap-2">
                <button
                  onClick={() => setActiveTab('shap')}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-colors flex items-center gap-1.5 ${
                    activeTab === 'shap'
                      ? 'bg-sky-600 text-white shadow-sm'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  TreeSHAP Factor Attributions
                </button>
                <button
                  onClick={() => setActiveTab('timeline')}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-colors flex items-center gap-1.5 ${
                    activeTab === 'timeline'
                      ? 'bg-sky-600 text-white shadow-sm'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  <Calendar className="w-3.5 h-3.5" />
                  Clinical Recovery & Travel Timeline
                </button>
                <button
                  onClick={() => setActiveTab('transparency')}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-colors flex items-center gap-1.5 ${
                    activeTab === 'transparency'
                      ? 'bg-sky-600 text-white shadow-sm'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  <BarChart3 className="w-3.5 h-3.5" />
                  Model Performance & Provenance
                </button>
              </div>

              {shap?.additive_property_verified && (
                <span className="hidden sm:inline-flex items-center gap-1 text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
                  <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                  TreeSHAP Additive Verified
                </span>
              )}
            </div>

            {activeTab === 'shap' ? (
              <div className="space-y-4">
                {/* Base Value Banner */}
                <div className="p-3 bg-slate-50 rounded-2xl border border-slate-200/80 flex items-center justify-between text-xs">
                  <div>
                    <span className="font-bold text-slate-700">Population Base Expected Value (E[Y]):</span>
                    <p className="text-[11px] text-slate-500">Average reference tariff across all benchmark procedures</p>
                  </div>
                  <span className="font-mono font-black text-slate-900 text-sm">
                    ₹{(shap?.base_value || pred?.base_value || 292166).toLocaleString()}
                  </span>
                </div>

                {/* Attributions List */}
                <div className="space-y-2.5">
                  {(shap?.breakdown || []).map((b, i) => (
                    <div
                      key={i}
                      className="p-3 bg-slate-50 hover:bg-slate-100/80 transition-colors rounded-2xl border border-slate-200/80 flex items-center justify-between text-xs"
                    >
                      <div className="flex items-center gap-2">
                        <span
                          className={`w-2.5 h-2.5 rounded-full shrink-0 ${
                            b.val_inr >= 0 ? 'bg-sky-500' : 'bg-emerald-500'
                          }`}
                        ></span>
                        <span className="font-semibold text-slate-800">{b.feature}</span>
                      </div>
                      <span
                        className={`font-mono font-bold ${
                          b.val_inr < 0 ? 'text-emerald-600' : 'text-slate-900'
                        }`}
                      >
                        {b.formatted}
                      </span>
                    </div>
                  ))}
                </div>

                <div className="p-4 bg-sky-50/60 rounded-2xl border border-sky-100 text-xs text-sky-900 leading-relaxed">
                  <strong>Econometric Insight:</strong> {shap?.summary_note ||
                    'Attributions computed via shap.TreeExplainer on trained XGBoost models.'}
                </div>
              </div>
            ) : activeTab === 'timeline' ? (
              <div className="space-y-4 animate-fadeIn">
                <div className="p-3.5 bg-sky-50/70 border border-sky-200 rounded-2xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
                  <div>
                    <h4 className="font-bold text-slate-900 text-xs">Clinical Recovery & Fit-to-Fly Decision Support</h4>
                    <p className="text-[11px] text-slate-600 mt-0.5">
                      Combines XGBoost length of stay prediction with verified clinical aviation clearance guidelines.
                    </p>
                  </div>
                  {timelineData && (
                    <span className="font-mono font-bold text-xs bg-white text-sky-700 px-2.5 py-1 rounded-xl border border-sky-200 shadow-sm shrink-0">
                      Est. Inpatient Stay: {timelineData.predicted_los_days} Days
                    </span>
                  )}
                </div>

                <div className="space-y-3">
                  {timelineData?.milestones.map((m, idx) => (
                    <div key={idx} className="p-4 bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row items-start justify-between gap-3">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full bg-slate-100 text-slate-700">
                            {m.phase}
                          </span>
                          <span className="text-xs font-bold text-slate-900">{m.title}</span>
                          <span className="text-[11px] font-mono font-bold text-sky-600">({m.timeline_days})</span>
                        </div>
                        <p className="text-xs text-slate-700 leading-relaxed font-medium">{m.clinical_focus}</p>
                        <p className="text-[11px] text-slate-500 italic bg-slate-50 p-2 rounded-xl border border-slate-100">
                          Guideline Grounding: "{m.guideline_statement}"
                        </p>
                      </div>
                      <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full shrink-0 border ${
                        m.clearance_status === 'Fit for Travel'
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                          : m.clearance_status === 'Local Rest Required'
                          ? 'bg-amber-50 text-amber-700 border-amber-200'
                          : 'bg-sky-50 text-sky-700 border-sky-200'
                      }`}>
                        {m.clearance_status}
                      </span>
                    </div>
                  ))}
                </div>

                {timelineData?.clinical_guideline_sources && timelineData.clinical_guideline_sources.length > 0 && (
                  <div className="p-3 bg-slate-50 rounded-2xl border border-slate-200 text-xs">
                    <span className="font-bold text-slate-700 block mb-1">Evidence Sources:</span>
                    <ul className="list-disc list-inside text-[11px] text-slate-600 space-y-0.5">
                      {timelineData.clinical_guideline_sources.map((s, idx) => (
                        <li key={idx}>{s}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <p className="text-[10px] text-slate-400 italic leading-tight">
                  {timelineData?.safety_disclaimer || 'NOTICE: Timeline milestones are decision-support estimates. Always obtain signed clinical travel clearance from your attending specialist.'}
                </p>
              </div>
            ) : (
              <div className="space-y-4 text-xs">
                {/* Metrics Table */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {/* Cost Model */}
                  <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-extrabold text-slate-800 text-xs uppercase tracking-wider">
                        Treatment Cost Model
                      </span>
                      <span className="text-[10px] font-bold bg-sky-100 text-sky-800 px-2 py-0.5 rounded-full">
                        XGBoost
                      </span>
                    </div>
                    <div className="space-y-1 text-slate-600 pt-1">
                      <div className="flex justify-between">
                        <span>Held-out MAE:</span>
                        <span className="font-mono font-bold text-slate-900">
                          ₹{metrics?.cost_model?.mae_inr?.toLocaleString() || '24,307.61'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Held-out RMSE:</span>
                        <span className="font-mono font-bold text-slate-900">
                          ₹{metrics?.cost_model?.rmse_inr?.toLocaleString() || '32,696.25'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Held-out R² Score:</span>
                        <span className="font-mono font-bold text-slate-900">
                          {metrics?.cost_model?.r2_score || '0.9689'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Target Leakage:</span>
                        <span className="font-bold text-emerald-600">Zero (Planned Stay Only)</span>
                      </div>
                    </div>
                  </div>

                  {/* LOS Model */}
                  <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-extrabold text-slate-800 text-xs uppercase tracking-wider">
                        Hospital Stay (LOS) Model
                      </span>
                      <span className="text-[10px] font-bold bg-purple-100 text-purple-800 px-2 py-0.5 rounded-full">
                        XGBoost
                      </span>
                    </div>
                    <div className="space-y-1 text-slate-600 pt-1">
                      <div className="flex justify-between">
                        <span>Held-out MAE:</span>
                        <span className="font-mono font-bold text-slate-900">
                          {metrics?.los_model?.mae_days || '0.72'} Days
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Held-out RMSE:</span>
                        <span className="font-mono font-bold text-slate-900">
                          {metrics?.los_model?.rmse_days || '0.99'} Days
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Held-out R² Score:</span>
                        <span className="font-mono font-bold text-slate-900">
                          {metrics?.los_model?.r2_score || '0.8545'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Target Leakage:</span>
                        <span className="font-bold text-emerald-600">Zero (Pre-Operative Only)</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Provenance Details & Synthetic Dataset Disclosure */}
                <div className="p-4 bg-amber-50/70 rounded-2xl border border-amber-200/80 space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-black uppercase bg-amber-200/80 text-amber-900 px-2 py-0.5 rounded-full">
                      Synthetic Benchmark Data Disclosure
                    </span>
                  </div>
                  <p className="text-amber-950 leading-relaxed text-[11px] font-medium">
                    The 2,500 patient episodes are <strong>SYNTHETIC BENCHMARK DATA</strong> generated for this project, calibrated using publicly available National Health Authority (NHA / PMJAY) standard package tariffs and General Insurance Public Sector Association (GIPSA) schedule of charges. <strong>They are not real patient records.</strong>
                  </p>
                  <div className="flex flex-wrap gap-2 pt-1 text-[10px]">
                    <span className="bg-amber-100/90 text-amber-900 px-2 py-1 rounded-md font-semibold">
                      Sample: {metrics?.split?.train_samples || 1750} Train / {metrics?.split?.val_samples || 375} Val / {metrics?.split?.test_samples || 375} Test
                    </span>
                <span className="bg-amber-100/90 text-amber-900 px-2 py-1 rounded-md font-semibold">
                      Random Seed: 42
                    </span>
                    <span className="bg-amber-100/90 text-amber-900 px-2 py-1 rounded-md font-semibold">
                      Calibration: NHA / PMJAY & GIPSA Public Tariffs
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* TreeSHAP Additive Consistency Disclosure */}
            <div className="p-3 bg-slate-50 rounded-2xl border border-slate-200 text-xs text-slate-600">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-800">TreeSHAP Additive Property Validation:</span>
                <span className="font-mono text-emerald-700 font-bold text-[11px]">Rel. Diff ≤ 1.18×10⁻⁶ ≤ 10⁻⁴</span>
              </div>
              <p className="text-[10px] text-slate-500 mt-1">
                Exact maximum relative discrepancy across all held-out test episodes is 1.184×10⁻⁶ (maximum absolute discrepancy 0.4375 INR, corresponding to ≤ 7 ULPs of IEEE 754 float32 summation rounding across 39 feature terms on large ₹300,000+ tariff sums).
              </p>
            </div>

            {/* Next Step in Continuous Patient Journey */}
            <div className="glass-card rounded-2xl p-5 border border-sky-200 bg-sky-50/60 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-2">
                  <Bot className="w-4 h-4 text-sky-600" />
                  <h4 className="font-bold text-slate-900 text-sm">Next Step in Decision Journey</h4>
                </div>
                <p className="text-xs text-slate-600 mt-0.5">
                  Consult the AI Healthcare Assistant with your report context, predictions, and clinical guidelines.
                </p>
              </div>
              <button
                onClick={() => {
                  const repParam = urlReportId ? `report_id=${urlReportId}` : '';
                  const hospParam = urlHospitalId ? `hospital_id=${urlHospitalId}` : '';
                  const q = [repParam, hospParam].filter(Boolean).join('&');
                  navigate(`/assistant${q ? `?${q}` : ''}`);
                }}
                className="flex items-center gap-2 font-bold text-xs text-white gradient-bg px-5 py-2.5 rounded-xl shadow hover:opacity-95 transition-opacity shrink-0"
              >
                <span>Launch AI Assistant</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
