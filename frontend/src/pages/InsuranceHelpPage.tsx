import React from 'react';
import { ShieldCheck, FileCheck, Phone, CheckCircle2, HelpCircle } from 'lucide-react';
import { DisclaimerBadge } from '../components/DisclaimerBadge';

export const InsuranceHelpPage: React.FC = () => {
  const providers = [
    {
      name: "Star Health Insurance",
      policy: "Comprehensive Medical Travel & Cashless Care",
      hospitals: "14,000+ Network Hospitals",
      contact: "1800 425 2255",
      details: "Full cashless hospitalization approval within 30 minutes at Apollo Hospitals Jubilee Hills."
    },
    {
      name: "HDFC ERGO Optima Secure",
      policy: "2X Coverage Health Plan",
      hospitals: "12,000+ Network Hospitals",
      contact: "1800 266 6000",
      details: "Instant cashless pre-authorization, international emergency add-on cover included."
    },
    {
      name: "ICICI Lombard Health Care",
      policy: "Complete Health Insurance",
      hospitals: "10,500+ Network Hospitals",
      contact: "1800 2666",
      details: "No sub-limits on room rent for superspecialty hospitals."
    }
  ];

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900">Insurance & Cashless Desk Guidance</h1>
          <p className="text-xs text-slate-500 mt-1">Pre-authorization document checklist and insurance network verification</p>
        </div>

        <DisclaimerBadge type="ai" text="RAG Insurance Guidance" />
      </div>

      {/* Cashless Claim Document Checklist */}
      <div className="glass-card rounded-3xl p-6 sm:p-8 border border-slate-200">
        <h2 className="text-base font-extrabold text-slate-900 mb-3 flex items-center gap-2">
          <FileCheck className="w-5 h-5 text-sky-600" />
          Mandatory Cashless Claim Pre-Authorization Checklist
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          {[
            "1. Doctor Consultation Advice Note / Admission Order",
            "2. Diagnostic Reports (Angiography / MRI / CT Scan)",
            "3. Hospital Cost Breakdown Estimate on Official Letterhead",
            "4. Government Photo ID (Aadhaar / Passport) & Insurance Policy Card",
            "5. Duly Signed TPA Pre-Authorization Form (Submitted 48 hrs prior)",
            "6. KYC Form & Cancelled Cheque for Reimbursement"
          ].map((chk, i) => (
            <div key={i} className="p-3 bg-slate-50 rounded-xl border border-slate-200 font-semibold text-slate-800 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>{chk}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Network Providers */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {providers.map((p, idx) => (
          <div key={idx} className="glass-card rounded-2xl p-6 border border-slate-200 flex flex-col justify-between">
            <div>
              <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold mb-3 border border-emerald-100">
                <ShieldCheck className="w-5 h-5" />
              </div>

              <h3 className="font-extrabold text-slate-900 text-base mb-1">{p.name}</h3>
              <p className="text-xs font-bold text-sky-600 mb-2">{p.policy}</p>
              <p className="text-xs text-slate-600 leading-relaxed mb-4">{p.details}</p>
            </div>

            <div className="pt-3 border-t border-slate-100 text-xs text-slate-500 flex items-center justify-between">
              <span>{p.hospitals}</span>
              <span className="font-bold text-slate-800 flex items-center gap-1">
                <Phone className="w-3.5 h-3.5 text-slate-400" /> {p.contact}
              </span>
            </div>
          </div>
        ))}
      </div>

    </div>
  );
};
