import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Building2, Star, MapPin, Phone, ShieldCheck, ArrowRight, CheckCircle2, Loader2, Calculator, Bot, Navigation } from 'lucide-react';
import { DisclaimerBadge } from '../components/DisclaimerBadge';
import { getHospitalById, Hospital } from '../services/api';

export const HospitalDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [hospital, setHospital] = useState<Hospital | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadHospital() {
      try {
        setLoading(true);
        const data = await getHospitalById(id || 1);
        setHospital(data);
      } catch (e) {
        console.warn('Failed to load hospital details', e);
      } finally {
        setLoading(false);
      }
    }
    loadHospital();
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-16 text-slate-500 gap-2">
        <Loader2 className="w-6 h-6 animate-spin text-sky-600" />
        <span className="text-sm font-semibold">Loading hospital details...</span>
      </div>
    );
  }

  if (!hospital) {
    return (
      <div className="max-w-4xl mx-auto p-12 text-center glass-card rounded-2xl border border-slate-200">
        <h2 className="text-lg font-bold text-slate-800">Hospital Not Found</h2>
        <p className="text-xs text-slate-500 mt-1">The requested hospital record could not be found in the benchmark dataset.</p>
      </div>
    );
  }

  const name = hospital.name;
  const city = hospital.city;
  const state = hospital.state;
  const address = hospital.address || `${hospital.city}, ${hospital.state}`;
  const rating = hospital.quality_rating || hospital.rating || 4.5;
  const dist = hospital.distance_km || 0.0;
  const phone = hospital.contact_phone || "Hospital Directory Desk";
  const score = hospital.recommendation_score !== undefined ? `${hospital.recommendation_score.toFixed(1)}%` : '—';
  const accreditation = hospital.accreditation || "NABH Accredited";
  const icuBeds = hospital.icu_beds || 50;
  const emergency24x7 = hospital.emergency_24x7 !== false;
  const costTier = hospital.cost_tier || "Mid-Tier";
  const estimatedCost = hospital.estimated_cost_tier ? `₹${hospital.estimated_cost_tier.toLocaleString()}` : "₹3,20,000";
  const specialties = hospital.specialties && hospital.specialties.length > 0
    ? hospital.specialties
    : ["Cardiology", "General Medicine"];
  const treatmentCapabilities = hospital.treatment_capabilities && hospital.treatment_capabilities.length > 0
    ? hospital.treatment_capabilities
    : ["Comprehensive Inpatient Care", "Diagnostic Imaging", "Critical Care Telemetry"];
  const facilities = (hospital.facilities && hospital.facilities.length > 0)
    ? hospital.facilities
    : ["24x7 Emergency & Critical ICU", "Accredited Inpatient Care"];
  const insuranceAccepted = (hospital.insurance_accepted && hospital.insurance_accepted.length > 0)
    ? hospital.insurance_accepted
    : ["Direct / Reimbursement basis"];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      
      {/* Header Info */}
      <div className="glass-card rounded-3xl p-8 border border-slate-200 shadow-lg">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-4">
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-1.5">
              <span className="text-[11px] font-bold text-sky-600 uppercase tracking-wider bg-sky-50 px-2.5 py-0.5 rounded-full border border-sky-100">
                {city}, {state}
              </span>
              <span className="text-[11px] font-bold text-indigo-700 bg-indigo-50 px-2.5 py-0.5 rounded-full border border-indigo-200">
                {accreditation}
              </span>
              <span className="text-[11px] font-bold text-slate-700 bg-slate-100 px-2.5 py-0.5 rounded-full border border-slate-200">
                {icuBeds} ICU Beds
              </span>
              <span className="text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
                {costTier} Tier ({estimatedCost} Baseline)
              </span>
              {emergency24x7 && (
                <span className="text-[11px] font-bold text-rose-700 bg-rose-50 px-2.5 py-0.5 rounded-full border border-rose-200">
                  24x7 Emergency Services
                </span>
              )}
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-slate-900 mt-1">
              {name}
            </h1>
            <p className="text-xs text-slate-600 mt-1 flex items-center gap-1 font-medium">
              <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
              <span>{address}</span>
            </p>
          </div>

          <div className="px-4 py-2 bg-gradient-to-r from-sky-600 to-teal-600 text-white rounded-2xl font-black text-lg shadow flex items-center gap-1.5 shrink-0">
            <span>{score}</span>
            <span className="text-xs font-normal opacity-90">Match Score</span>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-6 text-xs text-slate-600 border-t border-slate-100 pt-4">
          <div className="flex items-center gap-1 font-bold text-amber-600 bg-amber-50 px-2.5 py-1 rounded-lg border border-amber-200">
            <Star className="w-4 h-4 fill-amber-400 text-amber-500" />
            <span>{rating} / 5.0 Rating</span>
          </div>

          <div className="flex items-center gap-1 font-medium">
            <MapPin className="w-4 h-4 text-slate-400" />
            <span>{dist} km from stay</span>
          </div>

          <div className="flex items-center gap-1 font-medium">
            <Phone className="w-4 h-4 text-slate-400" />
            <span>{phone}</span>
          </div>
        </div>
      </div>

      {/* Clinical Capabilities & Departments */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        <div className="glass-card rounded-2xl p-6 border border-slate-200">
          <h3 className="font-extrabold text-slate-900 text-sm mb-3">Accredited Clinical Specialties</h3>
          <div className="flex flex-wrap gap-1.5">
            {specialties.map((s, i) => (
              <span key={i} className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-sky-50 text-sky-800 border border-sky-100">
                {s}
              </span>
            ))}
          </div>
        </div>

        <div className="glass-card rounded-2xl p-6 border border-slate-200">
          <h3 className="font-extrabold text-slate-900 text-sm mb-3">Tertiary & Quaternary Capabilities</h3>
          <ul className="space-y-2 text-xs text-slate-700">
            {treatmentCapabilities.map((c, i) => (
              <li key={i} className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-teal-600 shrink-0" />
                <span className="font-medium">{c}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Facilities & Insurance */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        <div className="glass-card rounded-2xl p-6 border border-slate-200">
          <h3 className="font-extrabold text-slate-900 text-sm mb-3">Hospital Facilities & Critical Infrastructure</h3>
          <ul className="space-y-2 text-xs text-slate-700">
            {facilities.map((f, i) => (
              <li key={i} className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>{f}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="glass-card rounded-2xl p-6 border border-slate-200">
          <h3 className="font-extrabold text-slate-900 text-sm mb-3">Accepted Cashless Insurance</h3>
          <ul className="space-y-2 text-xs text-slate-700">
            {insuranceAccepted.map((ins, i) => (
              <li key={i} className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-sky-600 shrink-0" />
                <span>{ins}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Action Footer */}
      <div className="glass-card rounded-2xl p-6 border border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <h4 className="font-bold text-slate-900 text-sm">Ready to explore treatment options?</h4>
          <p className="text-xs text-slate-500">Estimate procedure cost and length of stay or consult our clinical decision assistant</p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={() => {
              const params = new URLSearchParams(window.location.search);
              const repId = params.get('report_id') || sessionStorage.getItem('active_report_id') || '';
              navigate(`/travel?hospital_id=${id}${repId ? `&report_id=${repId}` : ''}`);
            }}
            className="flex items-center gap-2 font-bold text-xs text-sky-700 bg-sky-50 border border-sky-200 hover:bg-sky-100 px-5 py-2.5 rounded-xl transition-colors"
          >
            <Navigation className="w-4 h-4 text-sky-600" />
            <span>Plan Medical Travel</span>
          </button>
          <button
            onClick={() => {
              const params = new URLSearchParams(window.location.search);
              const repId = params.get('report_id') || sessionStorage.getItem('active_report_id') || '';
              navigate(`/cost?hospital_id=${id}${repId ? `&report_id=${repId}` : ''}`);
            }}
            className="flex items-center gap-2 font-bold text-xs text-white gradient-bg px-5 py-2.5 rounded-xl shadow hover:opacity-95 transition-opacity"
          >
            <Calculator className="w-4 h-4" />
            <span>Estimate Cost & LOS</span>
          </button>
          <button
            onClick={() => {
              const params = new URLSearchParams(window.location.search);
              const repId = params.get('report_id') || sessionStorage.getItem('active_report_id') || '';
              navigate(`/assistant?hospital_id=${id}${repId ? `&report_id=${repId}` : ''}`);
            }}
            className="flex items-center gap-2 font-bold text-xs text-slate-700 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:bg-slate-200 dark:hover:bg-slate-700 px-5 py-2.5 rounded-xl transition-colors"
          >
            <Bot className="w-4 h-4 text-sky-600" />
            <span>Ask AI Assistant</span>
          </button>
        </div>
      </div>

    </div>
  );
};
