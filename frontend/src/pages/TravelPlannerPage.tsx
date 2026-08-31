import React from 'react';
import { Plane, Calendar, Building2, UserCheck, Hotel, Pill, CheckCircle2, ArrowRight } from 'lucide-react';
import { DisclaimerBadge } from '../components/DisclaimerBadge';

export const TravelPlannerPage: React.FC = () => {
  const itinerary = [
    {
      day: 1,
      title: "Arrival in Destination City & Hotel Check-in",
      location: "Bengaluru -> Hyderabad (Rajiv Gandhi Intl Airport)",
      details: "Fly into Hyderabad. Airport shuttle transfer to Taj Jubilee Stays (800m from Apollo Hospitals). Rest and hydration ahead of morning consultation."
    },
    {
      day: 2,
      title: "Primary Specialist Consultation & Pre-Op Labs",
      location: "Apollo Hospitals Jubilee Hills",
      details: "09:30 AM Appointment with Dr. K. Srinivas Rao. Review angiography report, ECG, cardiac echo, blood panel, and TPA cashless authorization clearance."
    },
    {
      day: 3,
      title: "Medical Procedure Execution (Angioplasty / PCI)",
      location: "Apollo Hospitals Cath Lab & IPD Unit",
      details: "Admit for elective Angioplasty (PCI) with Drug-Eluting Stents. Post-procedure monitoring in Cardiac ICU and deluxe room."
    },
    {
      day: 4,
      title: "Hospital Discharge & Medication Dispensing",
      location: "Apollo Hospitals & 24x7 Pharmacy",
      details: "Discharge summary and fit-to-travel advice. Medication collection at 24/7 Pharmacy. Return to Taj Stays for post-procedure rest."
    },
    {
      day: 5,
      title: "Post-Op Follow-up & Return Journey",
      location: "Taj Stays -> Hyderabad Airport",
      details: "Final check-up by cardiology team. Transfer from hotel to airport for return journey home."
    }
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900">Medical Travel Itinerary Planner</h1>
          <p className="text-xs text-slate-500 mt-1">Generated personalized multi-day medical travel plan for Angioplasty Treatment</p>
        </div>

        <DisclaimerBadge type="ai" text="Planning Estimate Only" />
      </div>

      <div className="space-y-4">
        {itinerary.map((st) => (
          <div key={st.day} className="glass-card rounded-2xl p-6 border border-slate-200 hover:shadow-card-hover transition-all">
            <div className="flex items-center justify-between mb-2">
              <span className="font-extrabold text-sky-700 bg-sky-50 border border-sky-100 px-3 py-1 rounded-full text-xs">
                Day {st.day}
              </span>
              <span className="text-xs font-bold text-slate-500">{st.location}</span>
            </div>

            <h3 className="text-base font-extrabold text-slate-900 mb-2">{st.title}</h3>
            <p className="text-xs text-slate-600 leading-relaxed bg-slate-50 p-3 rounded-xl border border-slate-200/80">
              {st.details}
            </p>
          </div>
        ))}
      </div>

    </div>
  );
};
