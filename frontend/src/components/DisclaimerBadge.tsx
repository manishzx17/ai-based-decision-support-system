import React from 'react';
import { Sparkles, Database, ShieldAlert, Globe } from 'lucide-react';

interface DisclaimerBadgeProps {
  type: 'ai' | 'database' | 'external' | 'emergency';
  text?: string;
}

export const DisclaimerBadge: React.FC<DisclaimerBadgeProps> = ({ type, text }) => {
  if (type === 'ai') {
    return (
      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-amber-50 border border-amber-200 text-amber-800 text-[11px] font-semibold">
        <Sparkles className="w-3.5 h-3.5 text-amber-600 shrink-0" />
        <span>{text || 'AI-Generated Decision Support (Consult Doctor)'}</span>
      </div>
    );
  }

  if (type === 'database') {
    return (
      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-emerald-50 border border-emerald-200 text-emerald-800 text-[11px] font-semibold">
        <Database className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
        <span>{text || 'Verified Hospital Database Record'}</span>
      </div>
    );
  }

  if (type === 'external') {
    return (
      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-sky-50 border border-sky-200 text-sky-800 text-[11px] font-semibold">
        <Globe className="w-3.5 h-3.5 text-sky-600 shrink-0" />
        <span>{text || 'External Real-time Map & Navigation Data'}</span>
      </div>
    );
  }

  return (
    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-red-50 border border-red-200 text-red-800 text-[11px] font-bold">
      <ShieldAlert className="w-3.5 h-3.5 text-red-600 shrink-0" />
      <span>{text || 'Immediate Emergency Service'}</span>
    </div>
  );
};
