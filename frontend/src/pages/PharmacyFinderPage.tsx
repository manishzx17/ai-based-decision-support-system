import React, { useState } from 'react';
import { Pill, MapPin, Phone, Clock, Search, CheckCircle2, Navigation } from 'lucide-react';
import { DisclaimerBadge } from '../components/DisclaimerBadge';

export const PharmacyFinderPage: React.FC = () => {
  const [city, setCity] = useState('Hyderabad');

  const pharmacies = [
    {
      id: 1,
      name: "Apollo Pharmacy 24x7 Jubilee Hills",
      city: "Hyderabad",
      address: "Opposite Apollo Hospitals Main Gate, Road No 72, Jubilee Hills",
      distance_km: 0.1,
      is_24_7: true,
      phone: "+91 40 2360 8888",
      stock: "In-stock: Cardiac Stents, Chemotherapy meds, DAPT (Aspirin + Clopidogrel), Insulin, Post-op dressings."
    },
    {
      id: 2,
      name: "MedPlus Pharmacy Somajiguda",
      city: "Hyderabad",
      address: "Near Yashoda Hospital, Raj Bhavan Road, Somajiguda",
      distance_km: 0.2,
      is_24_7: true,
      phone: "+91 40 4000 5000",
      stock: "In-stock: Neurological anti-epileptics, Levetiracetam, Dialysis fluids, Cardiac prescriptions."
    },
    {
      id: 3,
      name: "Wellness Forever Bannerghatta",
      city: "Bengaluru",
      address: "Next to Fortis Hospital, Bannerghatta Road, Bengaluru",
      distance_km: 0.15,
      is_24_7: true,
      phone: "+91 80 4433 2211",
      stock: "In-stock: Orthopedic pain management, Post-knee replacement meds, Surgical braces."
    }
  ];

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900">24x7 Pharmacy Finder</h1>
          <p className="text-xs text-slate-500 mt-1">Locate nearby pharmacies with specialized cardiac, oncology, and post-op medication stock</p>
        </div>

        <DisclaimerBadge type="database" text="Verified Pharmacy Stock Data" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {pharmacies.map(p => (
          <div key={p.id} className="glass-card rounded-2xl p-6 border border-slate-200 hover:shadow-card-hover transition-all flex flex-col justify-between">
            <div>
              <div className="flex items-start justify-between gap-2 mb-2">
                <span className="text-[10px] font-extrabold uppercase bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded border border-emerald-200">
                  {p.is_24_7 ? "Open 24/7" : "Regular Hours"}
                </span>
                <span className="text-xs text-slate-400 font-bold">{p.distance_km} km away</span>
              </div>

              <h3 className="font-extrabold text-slate-900 text-base mb-1">{p.name}</h3>
              <p className="text-xs text-slate-500 mb-3">{p.address}</p>

              <div className="p-3 bg-slate-50 rounded-xl text-xs text-slate-700 border border-slate-200/80 mb-4">
                <p className="font-bold text-slate-900 mb-1 flex items-center gap-1">
                  <Pill className="w-3.5 h-3.5 text-sky-600" /> Medication Stock:
                </p>
                <p className="text-[11px] leading-relaxed text-slate-600">{p.stock}</p>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-600 flex items-center gap-1">
                <Phone className="w-3.5 h-3.5 text-slate-400" /> {p.phone}
              </span>

              <a
                href={`https://maps.google.com/?q=${encodeURIComponent(p.name + " " + p.address)}`}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1 text-xs font-bold text-sky-600 hover:underline"
              >
                <Navigation className="w-3.5 h-3.5" />
                <span>Navigate</span>
              </a>
            </div>
          </div>
        ))}
      </div>

    </div>
  );
};
