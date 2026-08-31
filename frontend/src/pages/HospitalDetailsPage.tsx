import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Building2, Star, MapPin, Phone, ShieldCheck, Calendar, ArrowRight, CheckCircle2 } from 'lucide-react';
import { DisclaimerBadge } from '../components/DisclaimerBadge';

export const HospitalDetailsPage: React.FC = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      
      {/* Header Info */}
      <div className="glass-card rounded-3xl p-8 border border-slate-200 shadow-lg">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-4">
          <div>
            <span className="text-[11px] font-bold text-sky-600 uppercase tracking-wider bg-sky-50 px-2.5 py-0.5 rounded-full border border-sky-100">
              Hyderabad, Telangana
            </span>
            <h1 className="text-2xl sm:text-3xl font-black text-slate-900 mt-1">
              Apollo Hospitals Jubilee Hills
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              Road No 72, Opposite Bharatiya Vidya Bhavan, Jubilee Hills, Hyderabad
            </p>
          </div>

          <div className="px-4 py-2 bg-gradient-to-r from-sky-600 to-teal-600 text-white rounded-2xl font-black text-lg shadow flex items-center gap-1">
            <span>96.5%</span>
            <span className="text-xs font-normal opacity-90">Match Score</span>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-6 text-xs text-slate-600 border-t border-slate-100 pt-4">
          <div className="flex items-center gap-1 font-bold text-amber-600 bg-amber-50 px-2.5 py-1 rounded-lg border border-amber-200">
            <Star className="w-4 h-4 fill-amber-400 text-amber-500" />
            <span>4.9 / 5.0 Rating</span>
          </div>

          <div className="flex items-center gap-1">
            <MapPin className="w-4 h-4 text-slate-400" />
            <span>4.2 km from stay</span>
          </div>

          <div className="flex items-center gap-1">
            <Phone className="w-4 h-4 text-slate-400" />
            <span>+91 40 2360 7777</span>
          </div>
        </div>
      </div>

      {/* Facilities & Insurance */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        <div className="glass-card rounded-2xl p-6 border border-slate-200">
          <h3 className="font-extrabold text-slate-900 text-sm mb-3">Super-Specialty Care & Facilities</h3>
          <ul className="space-y-2 text-xs text-slate-700">
            {["24x7 Cath Lab & Critical ICU", "Helipad & Emergency Trauma Response", "Dedicated International Patient Lounge", "Robotic Cardiac Surgery Suite", "Medical Translator & Interpreter Team"].map((f, i) => (
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
            {["Star Health Insurance (100% Cashless)", "HDFC ERGO Optima Secure Desk", "ICICI Lombard Health Care", "Care Health Travel Cover", "Bupa Global International"].map((ins, i) => (
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
          <h4 className="font-bold text-slate-900 text-sm">Ready to book a consultation?</h4>
          <p className="text-xs text-slate-500">Select top cardiologists at Apollo Hospitals Jubilee Hills</p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/appointments/book')}
            className="flex items-center gap-2 font-bold text-xs text-white gradient-bg px-6 py-3 rounded-xl shadow hover:opacity-95 transition-opacity"
          >
            <Calendar className="w-4 h-4" />
            <span>Book Appointment Now</span>
          </button>
        </div>
      </div>

    </div>
  );
};
