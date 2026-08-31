import React from 'react';
import { useNavigate } from 'react-router-dom';
import { GitCompare, CheckCircle2, XCircle, Sparkles, Star, ArrowRight } from 'lucide-react';
import { DisclaimerBadge } from '../components/DisclaimerBadge';

export const HospitalComparisonPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      
      {/* Title */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900">Side-by-Side Hospital Comparison</h1>
          <p className="text-xs text-slate-500 mt-1">Comparing top cardiology centers for Angioplasty (PCI)</p>
        </div>

        <DisclaimerBadge type="ai" text="AI Weighted Comparison Explanation" />
      </div>

      {/* Comparison Matrix Table */}
      <div className="glass-card rounded-3xl border border-slate-200 overflow-hidden shadow-lg">
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-slate-100/80 text-slate-700 font-extrabold uppercase border-b border-slate-200">
              <tr>
                <th className="p-4 w-48">Feature / Metric</th>
                <th className="p-4 border-l border-slate-200 bg-sky-50/50 text-sky-900">
                  <div className="flex items-center justify-between">
                    <span>Apollo Hospitals Jubilee Hills</span>
                    <span className="bg-sky-600 text-white font-bold px-2 py-0.5 rounded text-[10px]">Top Pick</span>
                  </div>
                </th>
                <th className="p-4 border-l border-slate-200">Yashoda Hospitals Somajiguda</th>
                <th className="p-4 border-l border-slate-200">Fortis Hospital Bannerghatta</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              
              <tr>
                <td className="p-4 font-bold text-slate-900">Match Score</td>
                <td className="p-4 border-l border-slate-200 font-extrabold text-sky-600 text-sm bg-sky-50/30">96.5% Match</td>
                <td className="p-4 border-l border-slate-200 font-bold text-slate-800">91.2% Match</td>
                <td className="p-4 border-l border-slate-200 font-bold text-slate-800">84.0% Match</td>
              </tr>

              <tr>
                <td className="p-4 font-bold text-slate-900">Specialty Expertise</td>
                <td className="p-4 border-l border-slate-200 bg-sky-50/30 font-semibold text-slate-800">Interventional Cardiology & Robotic Surgery</td>
                <td className="p-4 border-l border-slate-200 font-semibold text-slate-800">Cardiology & Neurology Center</td>
                <td className="p-4 border-l border-slate-200 font-semibold text-slate-800">Cardiology & Joint Replacement</td>
              </tr>

              <tr>
                <td className="p-4 font-bold text-slate-900">Patient Satisfaction Rating</td>
                <td className="p-4 border-l border-slate-200 bg-sky-50/30 font-bold text-amber-600">4.9 / 5.0 (2,400+ reviews)</td>
                <td className="p-4 border-l border-slate-200 font-bold text-amber-600">4.8 / 5.0 (1,800+ reviews)</td>
                <td className="p-4 border-l border-slate-200 font-bold text-amber-600">4.7 / 5.0 (1,200+ reviews)</td>
              </tr>

              <tr>
                <td className="p-4 font-bold text-slate-900">Distance from Stay</td>
                <td className="p-4 border-l border-slate-200 bg-sky-50/30 font-semibold">4.2 km (12 mins)</td>
                <td className="p-4 border-l border-slate-200 font-semibold">6.1 km (18 mins)</td>
                <td className="p-4 border-l border-slate-200 font-semibold">8.5 km (25 mins)</td>
              </tr>

              <tr>
                <td className="p-4 font-bold text-slate-900">Estimated Procedure Cost</td>
                <td className="p-4 border-l border-slate-200 bg-sky-50/30 font-bold text-slate-900">₹2,20,000 INR</td>
                <td className="p-4 border-l border-slate-200 font-bold text-slate-900">₹2,10,000 INR</td>
                <td className="p-4 border-l border-slate-200 font-bold text-slate-900">₹2,40,000 INR</td>
              </tr>

              <tr>
                <td className="p-4 font-bold text-slate-900">Cashless Insurance Support</td>
                <td className="p-4 border-l border-slate-200 bg-sky-50/30 text-emerald-700 font-bold flex items-center gap-1">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" /> Star Health & HDFC ERGO
                </td>
                <td className="p-4 border-l border-slate-200 text-emerald-700 font-bold flex items-center gap-1">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" /> Star Health & Care Health
                </td>
                <td className="p-4 border-l border-slate-200 text-emerald-700 font-bold flex items-center gap-1">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" /> Star Health & ICICI Lombard
                </td>
              </tr>

              <tr>
                <td className="p-4 font-bold text-slate-900">Bed Availability</td>
                <td className="p-4 border-l border-slate-200 bg-sky-50/30 font-bold text-emerald-600">High Availability</td>
                <td className="p-4 border-l border-slate-200 font-bold text-emerald-600">High Availability</td>
                <td className="p-4 border-l border-slate-200 font-bold text-amber-600">Medium Availability</td>
              </tr>

            </tbody>
          </table>
        </div>
      </div>

      {/* AI Decision Explanation Box */}
      <div className="glass-card rounded-2xl p-6 border border-sky-200 bg-sky-50/50">
        <div className="flex items-center gap-2 mb-2 font-extrabold text-slate-900 text-sm">
          <Sparkles className="w-4 h-4 text-sky-600" />
          <span>AI Hospital Recommendation Synthesis</span>
        </div>
        <p className="text-xs text-slate-700 leading-relaxed">
          <strong>Apollo Hospitals Jubilee Hills</strong> ranks #1 for your Angioplasty treatment because of its dedicated Interventional Cath Lab, direct cashless policy agreement with Star Health Insurance, and closest physical distance (4.2 km) from your hotel stay.
        </p>

        <div className="mt-4 pt-3 border-t border-sky-200/60 flex justify-end">
          <button
            onClick={() => navigate('/appointments/book')}
            className="flex items-center gap-2 font-bold text-xs text-white gradient-bg px-5 py-2.5 rounded-xl shadow hover:opacity-95 transition-opacity"
          >
            <span>Proceed to Book Top Hospital</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>

    </div>
  );
};
