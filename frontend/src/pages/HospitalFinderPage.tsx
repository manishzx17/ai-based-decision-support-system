import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Filter, Building2, GitCompare, Sparkles } from 'lucide-react';
import { HospitalCard, HospitalData } from '../components/HospitalCard';
import { DisclaimerBadge } from '../components/DisclaimerBadge';

export const HospitalFinderPage: React.FC = () => {
  const navigate = useNavigate();
  const [specialty, setSpecialty] = useState('Cardiology');
  const [city, setCity] = useState('Hyderabad');
  const [insurance, setInsurance] = useState('Star Health');

  const demoHospitals: HospitalData[] = [
    {
      id: 1,
      name: "Apollo Hospitals Jubilee Hills",
      city: "Hyderabad",
      state: "Telangana",
      address: "Road No 72, Jubilee Hills, Hyderabad",
      specialties: ["Cardiology", "Oncology", "Neurology", "Orthopedics"],
      rating: 4.9,
      distance_km: 4.2,
      insurance_accepted: ["Star Health", "HDFC ERGO", "ICICI Lombard", "Care Health"],
      facilities: ["24x7 ICU", "Helipad", "International Lounge", "Cath Lab"],
      contact_phone: "+91 40 2360 7777",
      availability_status: "High",
      recommendation_score: 96.5,
      shap_reasons: [
        "✓ Direct specialty match for Cardiology",
        "✓ Direct cashless support for Star Health",
        "✓ Top patient satisfaction rating (4.9/5.0)",
        "✓ Proximity advantage (4.2 km in Hyderabad)"
      ]
    },
    {
      id: 2,
      name: "Yashoda Hospitals Somajiguda",
      city: "Hyderabad",
      state: "Telangana",
      address: "Raj Bhavan Road, Somajiguda, Hyderabad",
      specialties: ["Neurology", "Cardiology", "Nephrology", "Pulmonology"],
      rating: 4.8,
      distance_km: 6.1,
      insurance_accepted: ["Star Health", "HDFC ERGO", "Care Health"],
      facilities: ["24x7 Emergency", "Organ Transplant Unit", "PET-CT Scan"],
      contact_phone: "+91 40 4567 4567",
      availability_status: "High",
      recommendation_score: 91.2,
      shap_reasons: [
        "✓ Specialty match for Cardiology & Neurology",
        "✓ Cashless insurance accepted",
        "✓ Rating of 4.8/5.0"
      ]
    },
    {
      id: 3,
      name: "Fortis Hospital Bannerghatta",
      city: "Bengaluru",
      state: "Karnataka",
      address: "154/9, Bannerghatta Road, Bengaluru",
      specialties: ["Cardiology", "Orthopedics", "Oncology"],
      rating: 4.7,
      distance_km: 8.5,
      insurance_accepted: ["Star Health", "HDFC ERGO", "ICICI Lombard"],
      facilities: ["24x7 Cath Lab", "Joint Replacement Suite"],
      contact_phone: "+91 80 6621 4444",
      availability_status: "Medium",
      recommendation_score: 84.0,
      shap_reasons: [
        "✓ Advanced Cardiology & Cath Lab",
        "✓ High patient satisfaction"
      ]
    }
  ];

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      
      {/* Page Title & Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900">Hospital Finder & Recommendation Engine</h1>
          <p className="text-xs text-slate-500 mt-1">
            Weighted Multi-Criteria Decision Algorithm (Specialty 30%, Distance 15%, Cost 15%, Rating 10%)
          </p>
        </div>

        <button
          onClick={() => navigate('/hospitals/compare')}
          className="flex items-center gap-2 font-bold text-xs text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 px-4 py-2.5 rounded-xl shadow-sm transition-all"
        >
          <GitCompare className="w-4 h-4 text-sky-600" />
          <span>Compare Side-by-Side</span>
        </button>
      </div>

      {/* Filter Toolbar */}
      <div className="glass-card rounded-2xl p-4 border border-slate-200 grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div>
          <label className="block text-xs font-bold text-slate-700 mb-1">Medical Specialty</label>
          <select
            value={specialty}
            onChange={(e) => setSpecialty(e.target.value)}
            className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-sky-500"
          >
            {['Cardiology', 'Neurology', 'Oncology', 'Orthopedics', 'Gastroenterology'].map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-bold text-slate-700 mb-1">Destination City</label>
          <select
            value={city}
            onChange={(e) => setCity(e.target.value)}
            className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-sky-500"
          >
            {['Hyderabad', 'Bengaluru', 'Delhi', 'Mumbai', 'Chennai'].map(c => (
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
            {['Star Health', 'HDFC ERGO', 'ICICI Lombard', 'Care Health'].map(i => (
              <option key={i} value={i}>{i}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Hospital Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {demoHospitals.map(h => (
          <HospitalCard
            key={h.id}
            hospital={h}
            onSelect={(selected) => navigate(`/hospitals/${selected.id}`)}
          />
        ))}
      </div>

    </div>
  );
};
