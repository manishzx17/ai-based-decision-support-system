import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { UserCheck, Star, Calendar, Building2, CheckCircle2, ShieldCheck, ArrowRight } from 'lucide-react';
import { DisclaimerBadge } from '../components/DisclaimerBadge';

export const DoctorRecommendationsPage: React.FC = () => {
  const navigate = useNavigate();
  const [specialty, setSpecialty] = useState('Cardiology');

  const doctors = [
    {
      id: 1,
      name: "Dr. K. Srinivas Rao",
      specialty: "Cardiology & Interventional Angioplasty",
      experience_years: 22,
      qualification: "MBBS, MD, DM (Cardiology), FACC",
      hospital: "Apollo Hospitals Jubilee Hills",
      rating: 4.9,
      consultation_fee: 1200.0,
      availability: "Mon - Sat (10:00 AM - 4:00 PM)",
      reasons: [
        "✓ 22 Years experience in Interventional Angioplasty",
        "✓ Senior Consultant Cardiologist at Apollo Jubilee Hills",
        "✓ 4.9/5.0 Patient Satisfaction Rating"
      ]
    },
    {
      id: 2,
      name: "Dr. Ananya Sharma",
      specialty: "Surgical Oncology",
      experience_years: 18,
      qualification: "MBBS, MS, MCh (Surgical Oncology)",
      hospital: "Apollo Hospitals Jubilee Hills",
      rating: 4.9,
      consultation_fee: 1500.0,
      availability: "Mon, Wed, Fri (11:00 AM - 5:00 PM)",
      reasons: [
        "✓ 18 Years Oncology experience",
        "✓ Specialized in minimally invasive tumor resections"
      ]
    },
    {
      id: 3,
      name: "Dr. V. Ramesh Kumar",
      specialty: "Neurology",
      experience_years: 20,
      qualification: "MBBS, MD, DM (Neurology)",
      hospital: "Yashoda Hospitals Somajiguda",
      rating: 4.8,
      consultation_fee: 1100.0,
      availability: "Mon - Fri (9:00 AM - 3:00 PM)",
      reasons: [
        "✓ 20 Years experience in Stroke & Brain Tumor care"
      ]
    }
  ];

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      
      {/* Title */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900">Doctor Recommendations</h1>
          <p className="text-xs text-slate-500 mt-1">
            Top Clinical Specialists matched based on report findings, experience, and hospital affiliation
          </p>
        </div>

        <DisclaimerBadge type="database" text="Verified Doctor Profiles" />
      </div>

      {/* Doctor Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {doctors.map(doc => (
          <div key={doc.id} className="glass-card rounded-2xl p-6 border border-slate-200 hover:shadow-card-hover transition-all flex flex-col justify-between">
            <div>
              <div className="flex items-start justify-between gap-3 mb-2">
                <div>
                  <span className="text-[10px] font-bold text-sky-700 bg-sky-50 px-2.5 py-0.5 rounded-full border border-sky-100 uppercase">
                    {doc.specialty}
                  </span>
                  <h3 className="text-lg font-bold text-slate-900 mt-1">{doc.name}</h3>
                  <p className="text-xs text-slate-500">{doc.qualification}</p>
                </div>

                <div className="flex items-center gap-1 font-bold text-xs text-amber-600 bg-amber-50 px-2 py-0.5 rounded-md border border-amber-200">
                  <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-500" />
                  <span>{doc.rating}</span>
                </div>
              </div>

              <div className="text-xs text-slate-600 space-y-1 mb-4">
                <p className="flex items-center gap-1.5 font-semibold text-slate-800">
                  <Building2 className="w-3.5 h-3.5 text-sky-600" /> {doc.hospital}
                </p>
                <p><strong>Experience:</strong> {doc.experience_years} Years</p>
                <p><strong>Consultation Fee:</strong> ₹{doc.consultation_fee} INR</p>
                <p><strong>Availability:</strong> {doc.availability}</p>
              </div>

              {/* Reasons */}
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-700 mb-4 space-y-1">
                <p className="font-bold text-slate-900 mb-1">Recommendation Reasons:</p>
                {doc.reasons.map((r, idx) => (
                  <p key={idx}>{r}</p>
                ))}
              </div>
            </div>

            <button
              onClick={() => navigate('/appointments/book')}
              className="w-full py-2.5 rounded-xl font-bold text-xs text-white gradient-bg shadow hover:opacity-95 transition-opacity flex items-center justify-center gap-2"
            >
              <Calendar className="w-4 h-4" />
              <span>Book Appointment with {doc.name.split(' ')[1]}</span>
            </button>
          </div>
        ))}
      </div>

    </div>
  );
};
