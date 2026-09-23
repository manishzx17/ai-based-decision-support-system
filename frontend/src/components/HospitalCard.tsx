import React, { useState } from 'react';
import { Building2, Star, MapPin, ShieldCheck, Phone, CheckCircle2, Info, ArrowRight } from 'lucide-react';
import { DisclaimerBadge } from './DisclaimerBadge';

export interface HospitalData {
  id: number;
  name: string;
  city: string;
  state: string;
  address: string;
  specialties: string[];
  rating: number;
  distance_km: number;
  insurance_accepted: string[];
  facilities: string[];
  contact_phone: string;
  availability_status: string;
  cost_tier?: string;
  quality_rating?: number;
  accreditation?: string;
  treatment_capabilities?: string[];
  icu_beds?: number;
  emergency_24x7?: boolean;
  estimated_cost_tier?: number;
  recommendation_score?: number;
  shap_reasons?: string[];
  reasons?: string[];
  score_breakdown?: Record<string, number>;
  provenance?: any;
}

interface HospitalCardProps {
  hospital: HospitalData;
  onSelect?: (hospital: HospitalData) => void;
  isCompareSelected?: boolean;
  onToggleCompare?: (hospital: HospitalData) => void;
}

export const HospitalCard: React.FC<HospitalCardProps> = ({
  hospital,
  onSelect,
  isCompareSelected = false,
  onToggleCompare,
}) => {
  const [showReasons, setShowReasons] = useState(false);
  const isSynthetic = hospital.provenance?.is_synthetic_benchmark ?? true;

  return (
    <div
      className={`glass-card rounded-2xl p-5 hover:shadow-card-hover transition-all duration-300 border flex flex-col justify-between group ${
        isCompareSelected
          ? 'ring-2 ring-sky-500 border-sky-500 bg-sky-50/20 shadow-md'
          : 'border-slate-200/80'
      }`}
    >
      <div>
        {/* Top Header & Match Score */}
        <div className="flex items-start justify-between gap-3 mb-3">
          <div>
            <div className="flex flex-wrap items-center gap-1.5 mb-1">
              <span className="text-[11px] font-bold text-sky-600 uppercase tracking-wider bg-sky-50 px-2.5 py-0.5 rounded-full border border-sky-100">
                {hospital.city}, {hospital.state}
              </span>
              {hospital.accreditation && (
                <span className="text-[10px] font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-full border border-indigo-200">
                  {hospital.accreditation}
                </span>
              )}
              {hospital.icu_beds && (
                <span className="text-[10px] font-bold text-slate-700 bg-slate-100 px-2 py-0.5 rounded-full border border-slate-200">
                  {hospital.icu_beds} ICU Beds
                </span>
              )}
              {hospital.estimated_cost_tier && (
                <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                  ₹{(hospital.estimated_cost_tier / 100000).toFixed(1)}L Tier
                </span>
              )}
            </div>
            <h3 className="text-lg font-bold text-slate-900 mt-1 group-hover:text-sky-600 transition-colors">
              {hospital.name}
            </h3>
          </div>

          {hospital.recommendation_score !== undefined && (
            <div className="flex flex-col items-end">
              <div className="px-3 py-1 bg-gradient-to-r from-sky-600 to-teal-600 text-white rounded-xl font-extrabold text-sm shadow-sm flex items-center gap-1">
                <span>{hospital.recommendation_score.toFixed(1)}%</span>
                <span className="text-[10px] font-normal opacity-90">Match Score</span>
              </div>
              <button
                onClick={() => setShowReasons(!showReasons)}
                className="text-[11px] text-sky-600 font-semibold hover:underline mt-1 flex items-center gap-0.5"
              >
                <Info className="w-3 h-3" /> Match Score factors
              </button>
            </div>
          )}
        </div>

        {/* Rating, Proximity, & ICU/Emergency Info */}
        <div className="flex flex-wrap items-center gap-3 text-xs text-slate-600 mb-3">
          <div className="flex items-center gap-1 font-bold text-amber-600 bg-amber-50 px-2 py-0.5 rounded-md border border-amber-100">
            <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-500" />
            <span>{hospital.quality_rating || hospital.rating}</span>
          </div>
          <div className="flex items-center gap-1">
            <MapPin className="w-3.5 h-3.5 text-slate-400" />
            <span>{hospital.distance_km} km away</span>
          </div>
          {hospital.emergency_24x7 && (
            <div className="flex items-center gap-1 text-emerald-700 font-medium">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              <span>24x7 Emergency & ICU</span>
            </div>
          )}
        </div>

        {/* Transparent Score Breakdown & Reasons */}
        {showReasons && (
          <div className="mb-4 p-3 bg-sky-50/80 rounded-xl border border-sky-200 text-xs text-sky-950 animate-fadeIn space-y-2">
            <p className="font-bold text-sky-900 flex items-center gap-1">
              <Info className="w-3.5 h-3.5" /> Explainable Weighted Score Breakdown:
            </p>
            {hospital.score_breakdown && (
              <div className="grid grid-cols-2 gap-1.5 text-[11px] bg-white/70 p-2 rounded-lg border border-sky-100">
                <div>Clinical Match: <span className="font-bold">{hospital.score_breakdown.clinical_match?.toFixed(1) ?? '35.0'} pts</span></div>
                <div>Cost & Insurance: <span className="font-bold">{hospital.score_breakdown.cost_insurance?.toFixed(1) ?? '25.0'} pts</span></div>
                <div>Proximity: <span className="font-bold">{hospital.score_breakdown.distance_proximity?.toFixed(1) ?? '20.0'} pts</span></div>
                <div>Quality & Accr.: <span className="font-bold">{hospital.score_breakdown.quality_accreditation?.toFixed(1) ?? '20.0'} pts</span></div>
              </div>
            )}
            {hospital.reasons && hospital.reasons.length > 0 && (
              <ul className="space-y-1 text-[11px] text-slate-700 mt-1">
                {hospital.reasons.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            )}
          </div>
        )}

        {/* Treatment Capabilities / Specialties */}
        <div className="mb-3">
          <p className="text-[11px] font-semibold text-slate-500 mb-1">Clinical Specialties & Services:</p>
          <div className="flex flex-wrap gap-1">
            {(hospital.treatment_capabilities && hospital.treatment_capabilities.length > 0 
              ? hospital.treatment_capabilities.slice(0, 3) 
              : hospital.specialties.slice(0, 3)
            ).map((s, idx) => (
              <span key={idx} className="text-[11px] bg-slate-100 text-slate-700 px-2 py-0.5 rounded-md font-medium">
                {s}
              </span>
            ))}
          </div>
        </div>

        {/* Cashless Insurance */}
        <div className="mb-3 flex items-center gap-2 text-xs text-slate-600">
          <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
          <span><strong>Cashless Insurance:</strong> {hospital.insurance_accepted.slice(0, 3).join(', ')}</span>
        </div>
      </div>

      {/* Footer Actions & Synthetic Benchmark Disclosures */}
      <div className="pt-3 border-t border-slate-100 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
        <div>
          {isSynthetic ? (
            <span className="text-[10px] font-semibold text-amber-800 bg-amber-50 px-2 py-0.5 rounded-md border border-amber-200">
              Synthetic Research Dataset
            </span>
          ) : (
            <DisclaimerBadge type="database" text="Verified Hospital Directory" />
          )}
        </div>

        <div className="flex items-center gap-2 self-end sm:self-auto">
          {onToggleCompare && (
            <button
              type="button"
              onClick={() => onToggleCompare(hospital)}
              className={`flex items-center gap-1.5 text-xs font-bold px-3 py-2 rounded-xl transition-all border ${
                isCompareSelected
                  ? 'bg-sky-600 text-white border-sky-600 shadow-sm'
                  : 'bg-white text-slate-700 border-slate-300 hover:border-sky-500 hover:text-sky-600'
              }`}
            >
              <CheckCircle2 className={`w-3.5 h-3.5 ${isCompareSelected ? 'text-white' : 'text-slate-400'}`} />
              <span>{isCompareSelected ? 'Selected' : 'Compare'}</span>
            </button>
          )}

          <button
            onClick={() => onSelect && onSelect(hospital)}
            className="flex items-center gap-1.5 text-xs font-bold text-white gradient-bg px-4 py-2 rounded-xl shadow-md hover:opacity-95 transition-opacity"
          >
            <span>View Details & Plan</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
