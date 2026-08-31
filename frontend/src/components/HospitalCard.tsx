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
  recommendation_score?: number;
  shap_reasons?: string[];
}

interface HospitalCardProps {
  hospital: HospitalData;
  onSelect?: (hospital: HospitalData) => void;
}

export const HospitalCard: React.FC<HospitalCardProps> = ({ hospital, onSelect }) => {
  const [showShap, setShowShap] = useState(false);

  return (
    <div className="glass-card rounded-2xl p-5 hover:shadow-card-hover transition-all duration-300 border border-slate-200/80 flex flex-col justify-between group">
      <div>
        {/* Top Header & Match Score */}
        <div className="flex items-start justify-between gap-3 mb-3">
          <div>
            <span className="text-[11px] font-bold text-sky-600 uppercase tracking-wider bg-sky-50 px-2.5 py-0.5 rounded-full border border-sky-100">
              {hospital.city}, {hospital.state}
            </span>
            <h3 className="text-lg font-bold text-slate-900 mt-1 group-hover:text-sky-600 transition-colors">
              {hospital.name}
            </h3>
          </div>

          {hospital.recommendation_score && (
            <div className="flex flex-col items-end">
              <div className="px-3 py-1 bg-gradient-to-r from-sky-600 to-teal-600 text-white rounded-xl font-extrabold text-sm shadow-sm flex items-center gap-1">
                <span>{hospital.recommendation_score}%</span>
                <span className="text-[10px] font-normal opacity-90">Match</span>
              </div>
              <button
                onClick={() => setShowShap(!showShap)}
                className="text-[11px] text-sky-600 font-semibold hover:underline mt-1 flex items-center gap-0.5"
              >
                <Info className="w-3 h-3" /> Why recommended?
              </button>
            </div>
          )}
        </div>

        {/* Rating & Distance */}
        <div className="flex items-center gap-4 text-xs text-slate-600 mb-4">
          <div className="flex items-center gap-1 font-bold text-amber-600 bg-amber-50 px-2 py-0.5 rounded-md border border-amber-100">
            <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-500" />
            <span>{hospital.rating}</span>
          </div>
          <div className="flex items-center gap-1">
            <MapPin className="w-3.5 h-3.5 text-slate-400" />
            <span>{hospital.distance_km} km away</span>
          </div>
          <div className="flex items-center gap-1 text-emerald-600 font-semibold">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>{hospital.availability_status} Bed Availability</span>
          </div>
        </div>

        {/* SHAP Explanation Banner */}
        {showShap && hospital.shap_reasons && (
          <div className="mb-4 p-3 bg-sky-50/80 rounded-xl border border-sky-200 text-xs text-sky-900 animate-fadeIn">
            <p className="font-bold mb-1 flex items-center gap-1 text-sky-700">
              <Info className="w-3.5 h-3.5" /> Key Recommendation Drivers (SHAP Score):
            </p>
            <ul className="space-y-1">
              {hospital.shap_reasons.map((r, i) => (
                <li key={i} className="text-slate-700">{r}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Specialties Tags */}
        <div className="mb-4">
          <p className="text-[11px] font-semibold text-slate-500 mb-1.5">Specialties & Super-Care:</p>
          <div className="flex flex-wrap gap-1.5">
            {hospital.specialties.map((s, idx) => (
              <span key={idx} className="text-xs bg-slate-100 text-slate-700 px-2.5 py-1 rounded-lg font-medium">
                {s}
              </span>
            ))}
          </div>
        </div>

        {/* Insurance */}
        <div className="mb-4 flex items-center gap-2 text-xs text-slate-600">
          <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
          <span><strong>Cashless Insurance:</strong> {hospital.insurance_accepted.slice(0, 3).join(', ')}</span>
        </div>
      </div>

      {/* Footer Actions */}
      <div className="pt-3 border-t border-slate-100 flex items-center justify-between gap-3">
        <DisclaimerBadge type="database" text="Verified Hospital" />

        <button
          onClick={() => onSelect && onSelect(hospital)}
          className="flex items-center gap-1.5 text-xs font-bold text-white gradient-bg px-4 py-2 rounded-xl shadow-md hover:opacity-95 transition-opacity"
        >
          <span>View Details & Book</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
