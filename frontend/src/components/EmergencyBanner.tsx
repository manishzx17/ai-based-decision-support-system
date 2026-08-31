import React from 'react';
import { Link } from 'react-router-dom';
import { PhoneCall, AlertTriangle, ArrowRight } from 'lucide-react';

export const EmergencyBanner: React.FC = () => {
  return (
    <div className="bg-gradient-to-r from-red-600 via-rose-600 to-red-700 text-white py-2.5 px-4 shadow-md">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2 font-medium text-center sm:text-left">
          <AlertTriangle className="w-4 h-4 text-amber-300 shrink-0 animate-pulse" />
          <span>
            <strong>Need Immediate Emergency Medical Travel Assistance?</strong> Dial 108 or access 1-click Trauma Dispatch.
          </span>
        </div>
        <Link
          to="/emergency"
          className="flex items-center gap-1.5 bg-white text-red-700 font-extrabold px-3 py-1.5 rounded-lg shadow-sm hover:bg-red-50 transition-colors shrink-0"
        >
          <PhoneCall className="w-3.5 h-3.5" />
          <span>Emergency Assistance</span>
          <ArrowRight className="w-3 h-3" />
        </Link>
      </div>
    </div>
  );
};
