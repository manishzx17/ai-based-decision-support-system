import React from 'react';
import { Hotel, MapPin, Star, CheckCircle2, ShieldCheck } from 'lucide-react';
import { DisclaimerBadge } from '../components/DisclaimerBadge';

export const AccommodationPage: React.FC = () => {
  const stays = [
    {
      id: 1,
      name: "Taj Jubilee Stays & Executive Apartments",
      hospital: "Apollo Hospitals Jubilee Hills (800m away)",
      price: "₹3,800 / night",
      rating: 4.8,
      facilities: ["Wheelchair Accessible", "Patient Kitchenette", "Free Hospital Shuttle", "24/7 Nurse on Call"]
    },
    {
      id: 2,
      name: "Treebo Trend MedStay Jubilee",
      hospital: "Apollo Hospitals Jubilee Hills (1.2 km away)",
      price: "₹2,200 / night",
      rating: 4.5,
      facilities: ["Elevator Access", "Free Breakfast", "Doctor Consultation Room", "High-speed Wi-Fi"]
    },
    {
      id: 3,
      name: "Fortune Park Raj Bhavan Stay",
      hospital: "Yashoda Hospital Somajiguda (400m away)",
      price: "₹3,100 / night",
      rating: 4.7,
      facilities: ["Wheelchair Ramp", "Elevator", "Sterilized Linen", "Airport Shuttle"]
    }
  ];

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900">Accommodation & Medical Stays</h1>
          <p className="text-xs text-slate-500 mt-1">Patient-centric hotel rooms and executive service apartments near accredited hospitals</p>
        </div>

        <DisclaimerBadge type="database" text="Verified Hotel Partners" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {stays.map(s => (
          <div key={s.id} className="glass-card rounded-2xl p-6 border border-slate-200 hover:shadow-card-hover transition-all flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between gap-2 mb-2">
                <span className="text-xs font-bold text-amber-600 bg-amber-50 px-2 py-0.5 rounded border border-amber-200 flex items-center gap-1">
                  <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-500" /> {s.rating}
                </span>
                <span className="text-xs font-extrabold text-slate-900">{s.price}</span>
              </div>

              <h3 className="font-extrabold text-slate-900 text-base mb-1">{s.name}</h3>
              <p className="text-xs text-slate-500 mb-3 flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5 text-slate-400" /> {s.hospital}
              </p>

              <div className="space-y-1.5 text-xs text-slate-700 mb-4">
                <p className="font-bold text-slate-900 mb-1">Patient Amenities:</p>
                {s.facilities.map((fac, idx) => (
                  <div key={idx} className="flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                    <span>{fac}</span>
                  </div>
                ))}
              </div>
            </div>

            <button
              onClick={() => alert(`Pre-booking query sent for ${s.name}`)}
              className="w-full py-2.5 rounded-xl font-bold text-xs text-white gradient-bg shadow hover:opacity-95 transition-opacity"
            >
              Reserve Medical Stay
            </button>
          </div>
        ))}
      </div>

    </div>
  );
};
