import React, { useState } from 'react';
import { Calendar, Clock, User, Building2, CheckCircle2, Ticket } from 'lucide-react';
import { DisclaimerBadge } from '../components/DisclaimerBadge';

export const AppointmentBookingPage: React.FC = () => {
  const [patientName, setPatientName] = useState('Rajesh Verma');
  const [hospital, setHospital] = useState('Apollo Hospitals Jubilee Hills');
  const [doctor, setDoctor] = useState('Dr. K. Srinivas Rao (Cardiology)');
  const [date, setDate] = useState('2026-08-22');
  const [time, setTime] = useState('10:30 AM');
  const [reason, setReason] = useState('Cardiology consultation & Angioplasty pre-op review');
  const [booked, setBooked] = useState(false);

  const handleBook = (e: React.FormEvent) => {
    e.preventDefault();
    setBooked(true);
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      
      <div>
        <h1 className="text-2xl font-black text-slate-900">Appointment Assistance & Booking</h1>
        <p className="text-xs text-slate-500 mt-1">Local appointment booking with hospital API connection ready</p>
      </div>

      {!booked ? (
        <form onSubmit={handleBook} className="glass-card rounded-3xl p-6 sm:p-8 border border-slate-200 shadow-lg space-y-5">
          
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Patient Name</label>
            <input
              type="text"
              value={patientName}
              onChange={(e) => setPatientName(e.target.value)}
              required
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-sky-500"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Select Hospital</label>
              <select
                value={hospital}
                onChange={(e) => setHospital(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-sky-500"
              >
                <option value="Apollo Hospitals Jubilee Hills">Apollo Hospitals Jubilee Hills</option>
                <option value="Yashoda Hospitals Somajiguda">Yashoda Hospitals Somajiguda</option>
                <option value="Fortis Hospital Bannerghatta">Fortis Hospital Bannerghatta</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Select Specialist Doctor</label>
              <select
                value={doctor}
                onChange={(e) => setDoctor(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-sky-500"
              >
                <option value="Dr. K. Srinivas Rao (Cardiology)">Dr. K. Srinivas Rao (Cardiology)</option>
                <option value="Dr. Ananya Sharma (Oncology)">Dr. Ananya Sharma (Oncology)</option>
                <option value="Dr. V. Ramesh Kumar (Neurology)">Dr. V. Ramesh Kumar (Neurology)</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Preferred Date</label>
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                required
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-sky-500"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Preferred Time Slot</label>
              <select
                value={time}
                onChange={(e) => setTime(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-sky-500"
              >
                <option value="09:30 AM">09:30 AM</option>
                <option value="10:30 AM">10:30 AM</option>
                <option value="02:00 PM">02:00 PM</option>
                <option value="04:00 PM">04:00 PM</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Reason for Visit / Symptoms</label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={2}
              className="w-full px-3.5 py-2 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-sky-500"
            ></textarea>
          </div>

          <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
            <DisclaimerBadge type="database" text="Hospital Booking Integration" />

            <button
              type="submit"
              className="flex items-center gap-2 font-bold text-xs text-white gradient-bg px-6 py-3 rounded-xl shadow hover:opacity-95 transition-opacity"
            >
              <Ticket className="w-4 h-4" />
              <span>Confirm & Generate Digital Ticket</span>
            </button>
          </div>

        </form>
      ) : (
        /* Digital Appointment Ticket */
        <div className="glass-card rounded-3xl p-8 border border-emerald-200 bg-emerald-50/40 text-center space-y-6 animate-fadeIn">
          <div className="w-14 h-14 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto shadow-sm">
            <CheckCircle2 className="w-8 h-8" />
          </div>

          <div>
            <span className="text-[10px] font-extrabold uppercase tracking-wider bg-emerald-100 text-emerald-800 px-3 py-1 rounded-full">
              CONFIRMED BOOKING #APT-9824
            </span>
            <h2 className="text-2xl font-black text-slate-900 mt-2">Appointment Ticket Issued</h2>
            <p className="text-xs text-slate-600 mt-1">Present this ticket at hospital reception upon arrival</p>
          </div>

          <div className="max-w-md mx-auto p-4 bg-white rounded-2xl border border-slate-200 text-left text-xs space-y-2">
            <p><strong>Patient:</strong> {patientName}</p>
            <p><strong>Hospital:</strong> {hospital}</p>
            <p><strong>Doctor:</strong> {doctor}</p>
            <p><strong>Date & Time:</strong> {date} at {time}</p>
            <p><strong>Reason:</strong> {reason}</p>
          </div>

          <button
            onClick={() => setBooked(false)}
            className="text-xs font-bold text-sky-600 hover:underline"
          >
            Book Another Appointment
          </button>
        </div>
      )}

    </div>
  );
};
