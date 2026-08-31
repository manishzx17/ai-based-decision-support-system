import React, { useState } from 'react';
import { Languages, ArrowRight, Copy, Check, Sparkles } from 'lucide-react';
import { DisclaimerBadge } from '../components/DisclaimerBadge';

export const MedicalTranslationPage: React.FC = () => {
  const [sourceLang, setSourceLang] = useState('English');
  const [targetLang, setTargetLang] = useState('Telugu');
  const [inputText, setInputText] = useState('Take medicine after food. Contact emergency if severe chest pain occurs.');
  const [translatedText, setTranslatedText] = useState('');
  const [copied, setCopied] = useState(false);

  const handleTranslate = (e: React.FormEvent) => {
    e.preventDefault();
    if (targetLang === 'Telugu') {
      setTranslatedText('ఆహారం తీసుకున్న తర్వాత మందు వాడండి. తీవ్రమైన ఛాతీ నొప్పి వస్తే వెంటనే అత్యవసర రంగాన్ని సంప్రదించండి. (Take medicine after food. Contact emergency if severe chest pain occurs.)');
    } else if (targetLang === 'Hindi') {
      setTranslatedText('खाना खाने के बाद दवा लें। यदि सीने में तेज दर्द हो तो तुरंत आपातकालीन विभाग से संपर्क करें।');
    } else {
      setTranslatedText(`[${targetLang} Translation]: ${inputText}`);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(translatedText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      
      <div className="text-center max-w-xl mx-auto">
        <h1 className="text-2xl font-black text-slate-900">Multilingual Medical Translator</h1>
        <p className="text-xs text-slate-500 mt-1">
          Translate prescriptions, symptoms, and hospital instructions across major Indian languages
        </p>
      </div>

      <form onSubmit={handleTranslate} className="glass-card rounded-3xl p-6 sm:p-8 border border-slate-200 shadow-lg space-y-4">
        
        {/* Language Selectors */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">From Language</label>
            <select
              value={sourceLang}
              onChange={(e) => setSourceLang(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-sky-500"
            >
              {['English', 'Telugu', 'Hindi', 'Tamil', 'Kannada', 'Malayalam'].map(l => (
                <option key={l} value={l}>{l}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">To Language</label>
            <select
              value={targetLang}
              onChange={(e) => setTargetLang(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-sky-500"
            >
              {['Telugu', 'Hindi', 'Tamil', 'Kannada', 'Malayalam', 'English'].map(l => (
                <option key={l} value={l}>{l}</option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="block text-xs font-bold text-slate-700 mb-1">Medical Text / Prescription Note</label>
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            rows={3}
            required
            className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-sky-500"
          ></textarea>
        </div>

        <div className="flex items-center justify-between pt-2">
          <DisclaimerBadge type="ai" text="Gemini Clinical Translation" />

          <button
            type="submit"
            className="flex items-center gap-2 font-bold text-xs text-white gradient-bg px-6 py-2.5 rounded-xl shadow hover:opacity-95 transition-opacity"
          >
            <Languages className="w-4 h-4" />
            <span>Translate Text</span>
          </button>
        </div>
      </form>

      {/* Output Translated Card */}
      {translatedText && (
        <div className="glass-card rounded-3xl p-6 border border-sky-200 bg-sky-50/40 space-y-3 animate-fadeIn">
          <div className="flex items-center justify-between">
            <span className="text-xs font-extrabold text-sky-800 uppercase tracking-wider">
              {targetLang} Translation
            </span>

            <button
              onClick={handleCopy}
              className="flex items-center gap-1 text-xs font-bold text-sky-600 hover:underline"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? "Copied!" : "Copy Translation"}</span>
            </button>
          </div>

          <p className="text-sm font-bold text-slate-900 leading-relaxed bg-white p-4 rounded-2xl border border-slate-200">
            {translatedText}
          </p>
        </div>
      )}

    </div>
  );
};
