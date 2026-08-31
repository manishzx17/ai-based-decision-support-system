import React, { useState } from 'react';
import { Bot, Send, User, Sparkles, BookOpen, Mic, AlertCircle } from 'lucide-react';
import { DisclaimerBadge } from '../components/DisclaimerBadge';

export const AiAssistantPage: React.FC = () => {
  const [messages, setMessages] = useState([
    {
      sender: 'assistant',
      text: 'Hello Rajesh! I am your 12C AI Healthcare Travel Assistant. I have loaded your medical report context (Cardiology Angiography - LAD 85% Stenosis). How can I assist with your hospital selection, travel itinerary, or treatment questions today?',
      citations: ['ESC Cardiology Guidelines 2024']
    }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  const suggestedPrompts = [
    "Which specialist should I consult for my LAD stenosis?",
    "Can I travel by flight after angioplasty?",
    "How does cashless insurance claim work for Apollo Hospital?",
    "What are the top 3 hospitals near Hyderabad airport?"
  ];

  const handleSend = (textToSend?: string) => {
    const query = textToSend || input;
    if (!query.trim()) return;

    // Add user message
    const newMsgs = [...messages, { sender: 'user', text: query, citations: [] }];
    setMessages(newMsgs);
    setInput('');
    setIsTyping(true);

    // Simulate RAG + Gemini LLM response
    setTimeout(() => {
      let reply = "Based on verified clinical guidelines and your medical report context:";
      let citations = ["Clinical Guidelines for Medical Travel 2024"];

      if (query.toLowerCase().includes("specialist") || query.toLowerCase().includes("lad")) {
        reply = "Based on the 85% proximal LAD stenosis identified in your angiography report, you should consult an **Interventional Cardiologist** (such as Dr. K. Srinivas Rao at Apollo Hospitals). They specialize in balloon angioplasty and drug-eluting stent placement.";
        citations = ["ESC Guidelines on Myocardial Revascularization"];
      } else if (query.toLowerCase().includes("flight") || query.toLowerCase().includes("travel")) {
        reply = "Commercial air travel is generally safe 3-5 days after an uncomplicated PCI angioplasty, provided your LVEF remains >40% and you are stable. Ensure you carry your dual antiplatelet medications (Aspirin + Clopidogrel) in your carry-on bag.";
        citations = ["Aerospace Medical Association Travel Guidelines"];
      } else if (query.toLowerCase().includes("cashless") || query.toLowerCase().includes("insurance")) {
        reply = "For cashless admission at Apollo Hospitals with Star Health or HDFC ERGO: 1) Submit your pre-authorization form at the hospital TPA desk 48 hours prior. 2) Attach your angiography report and doctor advice note. 3) The hospital TPA desk handles direct approval with the insurer.";
        citations = ["IRDAI Cashless Hospitalization Protocol"];
      } else {
        reply = `Thank you for your inquiry regarding "${query}". Based on your patient profile and medical travel guidelines, we recommend scheduling an outpatient consultation at an accredited tertiary hospital with cashless TPA support.`;
      }

      setMessages([...newMsgs, { sender: 'assistant', text: reply, citations }]);
      setIsTyping(false);
    }, 800);
  };

  return (
    <div className="max-w-4xl mx-auto h-[calc(100vh-8rem)] flex flex-col glass-card rounded-3xl border border-slate-200 shadow-xl overflow-hidden">
      
      {/* Header */}
      <div className="p-4 sm:p-6 bg-white border-b border-slate-200 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl gradient-bg flex items-center justify-center text-white shadow">
            <Bot className="w-6 h-6" />
          </div>
          <div>
            <h1 className="font-extrabold text-slate-900 text-base">AI Healthcare Assistant</h1>
            <p className="text-xs text-slate-500">Report-Aware Conversational Decision Support (Gemini RAG Engine)</p>
          </div>
        </div>

        <DisclaimerBadge type="ai" text="RAG Grounded Response" />
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 p-4 sm:p-6 overflow-y-auto space-y-4 bg-slate-50/50">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex items-start gap-3 ${msg.sender === 'user' ? 'flex-row-reverse' : ''}`}
          >
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
                msg.sender === 'user' ? 'bg-slate-800 text-white' : 'gradient-bg text-white'
              }`}
            >
              {msg.sender === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>

            <div
              className={`max-w-lg p-4 rounded-2xl text-xs leading-relaxed ${
                msg.sender === 'user'
                  ? 'bg-sky-600 text-white font-medium rounded-tr-none'
                  : 'bg-white text-slate-800 border border-slate-200 shadow-sm rounded-tl-none space-y-2'
              }`}
            >
              <p>{msg.text}</p>

              {msg.citations && msg.citations.length > 0 && (
                <div className="pt-2 border-t border-slate-100 flex items-center gap-1.5 text-[11px] text-sky-700 font-semibold">
                  <BookOpen className="w-3.5 h-3.5" />
                  <span>Grounding Citation: {msg.citations.join(', ')}</span>
                </div>
              )}
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="flex items-center gap-2 text-xs text-slate-400 italic">
            <Bot className="w-4 h-4 animate-spin text-sky-600" />
            <span>AI Assistant is synthesizing response with clinical guidelines...</span>
          </div>
        )}
      </div>

      {/* Suggested Prompts */}
      <div className="p-3 bg-slate-100/80 border-t border-slate-200 overflow-x-auto flex items-center gap-2 shrink-0">
        <span className="text-[11px] font-bold text-slate-500 whitespace-nowrap pl-2">Suggested:</span>
        {suggestedPrompts.map((p, i) => (
          <button
            key={i}
            onClick={() => handleSend(p)}
            className="text-[11px] font-semibold text-slate-700 bg-white hover:bg-sky-50 border border-slate-200 hover:border-sky-300 px-3 py-1 rounded-full whitespace-nowrap transition-colors"
          >
            {p}
          </button>
        ))}
      </div>

      {/* Input Box */}
      <div className="p-4 bg-white border-t border-slate-200 flex items-center gap-3">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask anything about your medical travel, report findings, or treatment..."
          className="flex-1 px-4 py-2.5 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-sky-500 focus:outline-none"
        />

        <button
          onClick={() => handleSend()}
          className="p-2.5 rounded-xl text-white gradient-bg hover:opacity-95 transition-opacity shadow"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>

    </div>
  );
};
