import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Search, Filter, Building2, GitCompare, Sparkles, Loader2, CheckCircle2 } from 'lucide-react';
import { HospitalCard, HospitalData } from '../components/HospitalCard';
import { DisclaimerBadge } from '../components/DisclaimerBadge';
import { getRecommendedHospitals, getOrResolveActiveReport, getPatientProfile, getCurrentUser, Hospital } from '../services/api';

export const HospitalFinderPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const paramSpecialty = searchParams.get('specialty');
  const paramCity = searchParams.get('city');
  const paramReportId = searchParams.get('report_id') ? Number(searchParams.get('report_id')) : undefined;

  const [specialty, setSpecialty] = useState(paramSpecialty || 'Cardiology');
  const [city, setCity] = useState(paramCity || 'Hyderabad');
  const [insurance, setInsurance] = useState('Star Health');
  const [priorityMode, setPriorityMode] = useState('balanced');
  const [maxBudget, setMaxBudget] = useState<number>(500000);
  const [hospitals, setHospitals] = useState<Hospital[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeReportId, setActiveReportId] = useState<number | undefined>(paramReportId);
  const [profileLoaded, setProfileLoaded] = useState(false);
  const [selectedForCompare, setSelectedForCompare] = useState<number[]>([]);

  // Authenticated user session
  const user = getCurrentUser();

  const handleToggleCompare = (h: Hospital | HospitalData) => {
    setSelectedForCompare(prev => {
      if (prev.includes(h.id)) {
        return prev.filter(id => id !== h.id);
      }
      if (prev.length >= 3) {
        // Replace earliest selection when 3 are already selected
        return [...prev.slice(1), h.id];
      }
      return [...prev, h.id];
    });
  };

  const handleGoToCompare = () => {
    const params = new URLSearchParams();
    if (selectedForCompare.length >= 1) {
      params.set('ids', selectedForCompare.join(','));
    }
    params.set('specialty', specialty);
    params.set('city', city);
    params.set('priority_mode', priorityMode);
    params.set('insurance', insurance);
    params.set('max_budget', String(maxBudget));
    if (activeReportId) {
      params.set('report_id', String(activeReportId));
    }
    navigate(`/hospitals/compare?${params.toString()}`);
  };

  useEffect(() => {
    async function loadPatientContext() {
      try {
        const [profile, report] = await Promise.allSettled([
          getPatientProfile(user.id),
          getOrResolveActiveReport(user.id)
        ]);

        if (profile.status === 'fulfilled' && profile.value) {
          if (profile.value.current_city && !paramCity) {
            setCity(profile.value.current_city);
          }
        }

        if (report.status === 'fulfilled' && report.value) {
          if (report.value.recommended_specialty && !paramSpecialty) {
            setSpecialty(report.value.recommended_specialty);
          }
          if (!paramReportId) {
            setActiveReportId(report.value.id);
          }
        }
        setProfileLoaded(true);
      } catch (err) {
        console.warn('Could not auto-load patient context', err);
      }
    }
    loadPatientContext();
  }, [user.id, paramCity, paramSpecialty, paramReportId]);

  useEffect(() => {
    async function loadHospitals() {
      try {
        setLoading(true);
        const data = await getRecommendedHospitals({
          specialty,
          city,
          insurance,
          max_budget: maxBudget,
          priority_mode: priorityMode,
          user_id: user.id,
          report_id: activeReportId
        });
        setHospitals(data || []);
      } catch (e) {
        console.warn('Failed to load recommended hospitals from backend API', e);
        setHospitals([]);
      } finally {
        setLoading(false);
      }
    }
    loadHospitals();
  }, [specialty, city, insurance, priorityMode, maxBudget, activeReportId, user.id]);

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      
      {/* Page Title & Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-black text-slate-900">Hospital Finder & Recommendation Engine</h1>
            {profileLoaded && (
              <span className="hidden sm:inline-flex items-center gap-1 text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
                <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                Profile Context Active
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Personalized Decision Support Baseline Weights: Clinical Match 35%, Cost & Insurance 25%, Proximity 20%, Quality & Accreditation 20%
          </p>
        </div>

        <button
          onClick={handleGoToCompare}
          className={`flex items-center gap-2 font-bold text-xs px-4 py-2.5 rounded-xl shadow-sm transition-all border ${
            selectedForCompare.length > 0
              ? 'bg-sky-600 text-white border-sky-600 shadow-md hover:bg-sky-700'
              : 'text-slate-700 bg-white border-slate-300 hover:bg-slate-50'
          }`}
        >
          <GitCompare className={`w-4 h-4 ${selectedForCompare.length > 0 ? 'text-white' : 'text-sky-600'}`} />
          <span>
            Compare Side-by-Side
            {selectedForCompare.length > 0 ? ` (${selectedForCompare.length}/3)` : ''}
          </span>
        </button>
      </div>

      {/* Synthetic Benchmark Notice */}
      <div className="p-3 bg-amber-50/70 border border-amber-200 rounded-xl text-xs text-amber-900 flex items-start gap-2">
        <span className="font-bold shrink-0 text-amber-800">Research Benchmark:</span>
        <span>
          Hospital facility profiles and provider benchmarks are generated as a synthetic research benchmark dataset for algorithm validation. Verified location and clinical department parameters are preserved. Real-time availability scoring has been excluded.
        </span>
      </div>

      {/* Filter Toolbar */}
      <div className="glass-card rounded-2xl p-4 border border-slate-200 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3">
        <div>
          <label className="block text-xs font-bold text-slate-700 mb-1">Medical Specialty</label>
          <select
            value={specialty}
            onChange={(e) => setSpecialty(e.target.value)}
            className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-sky-500"
          >
            {['Cardiology', 'Neurology', 'Oncology', 'Orthopedics', 'Gastroenterology', 'Nephrology', 'Pulmonology', 'General Medicine'].map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-bold text-slate-700 mb-1">Medical Hub City</label>
          <select
            value={city}
            onChange={(e) => setCity(e.target.value)}
            className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-sky-500"
          >
            {['Hyderabad', 'Bengaluru', 'Chennai', 'Mumbai', 'Delhi-NCR', 'Kolkata'].map(c => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-bold text-slate-700 mb-1">Insurance Provider</label>
          <select
            value={insurance}
            onChange={(e) => setInsurance(e.target.value)}
            className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-sky-500"
          >
            {['Star Health', 'HDFC ERGO', 'ICICI Lombard', 'Care Health', 'Niva Bupa', 'Bajaj Allianz'].map(i => (
              <option key={i} value={i}>{i}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-bold text-slate-700 mb-1">User Preference Mode</label>
          <select
            value={priorityMode}
            onChange={(e) => setPriorityMode(e.target.value)}
            className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-sky-500"
            title="User ranking preference weights"
          >
            <option value="balanced">Balanced (35% Clinical · 25% Cost · 20% Dist · 20% Qual)</option>
            <option value="cost_sensitive">Cost Sensitive (40% Cost · 30% Clinical · 15% Dist · 15% Qual)</option>
            <option value="quality_focused">Quality Focused (35% Qual · 35% Clinical · 15% Cost · 15% Dist)</option>
            <option value="proximity_focused">Proximity Focused (40% Dist · 30% Clinical · 15% Cost · 15% Qual)</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-bold text-slate-700 mb-1">Max Budget (Hard Ceiling)</label>
          <select
            value={maxBudget}
            onChange={(e) => setMaxBudget(Number(e.target.value))}
            className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-sky-500"
          >
            <option value={200000}>Up to ₹2,00,000</option>
            <option value={300000}>Up to ₹3,00,000</option>
            <option value={400000}>Up to ₹4,00,000</option>
            <option value={500000}>Up to ₹5,00,000 (All Tiers)</option>
          </select>
        </div>
      </div>

      {/* Active Weighting & Hard Filter Clarification */}
      <div className="flex flex-wrap items-center justify-between text-[11px] text-slate-500 px-1 -mt-3">
        <span className="flex items-center gap-1.5">
          <span className="font-semibold text-slate-700">Active Ranking Weights:</span>
          {priorityMode === 'balanced' && <span className="font-mono bg-slate-100 text-slate-700 px-2 py-0.5 rounded">35% Clinical · 25% Cost · 20% Proximity · 20% Quality</span>}
          {priorityMode === 'cost_sensitive' && <span className="font-mono bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded border border-emerald-200">30% Clinical · 40% Cost & Insurance · 15% Proximity · 15% Quality</span>}
          {priorityMode === 'quality_focused' && <span className="font-mono bg-purple-50 text-purple-700 px-2 py-0.5 rounded border border-purple-200">35% Quality & Accr. · 35% Clinical · 15% Cost · 15% Proximity</span>}
          {priorityMode === 'proximity_focused' && <span className="font-mono bg-sky-50 text-sky-700 px-2 py-0.5 rounded border border-sky-200">40% Distance Proximity · 30% Clinical · 15% Cost · 15% Quality</span>}
        </span>
        <span className="font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
          Strict Hard Ceiling: Excludes hospitals with baseline tier &gt; ₹{(maxBudget / 100000).toFixed(0)} Lakh
        </span>
      </div>

      {/* Hospital Cards Grid */}
      {loading ? (
        <div className="flex items-center justify-center p-16 text-slate-500 gap-2">
          <Loader2 className="w-6 h-6 animate-spin text-sky-600" />
          <span className="text-sm font-semibold">Calculating personalized multi-criteria hospital recommendations...</span>
        </div>
      ) : hospitals.length === 0 ? (
        <div className="glass-card rounded-2xl p-12 text-center border border-slate-200">
          <Building2 className="w-12 h-12 text-slate-400 mx-auto mb-3" />
          <h3 className="font-bold text-slate-800 text-base">No matching hospitals within selected criteria</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
            No accredited hospital departments for {specialty} meet your strict budget ceiling of ₹{(maxBudget / 100000).toFixed(0)} Lakh in {city}. Try increasing your max budget or adjusting insurance/city filters.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {hospitals.map(h => (
            <HospitalCard
              key={h.id}
              hospital={h}
              isCompareSelected={selectedForCompare.includes(h.id)}
              onToggleCompare={handleToggleCompare}
              onSelect={(selected) => {
                const rep = activeReportId || sessionStorage.getItem('active_report_id') || '';
                navigate(`/hospitals/${selected.id}${rep ? `?report_id=${rep}` : ''}`);
              }}
            />
          ))}
        </div>
      )}

      {/* Floating Comparison Drawer */}
      {selectedForCompare.length > 0 && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 bg-slate-900/95 backdrop-blur-md text-white px-5 py-3.5 rounded-2xl shadow-2xl border border-slate-700 flex items-center gap-4 animate-fadeIn">
          <div className="flex items-center gap-2">
            <GitCompare className="w-5 h-5 text-sky-400" />
            <span className="text-xs font-semibold">
              <strong className="text-white font-bold">{selectedForCompare.length}</strong> of 3 hospitals selected
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
