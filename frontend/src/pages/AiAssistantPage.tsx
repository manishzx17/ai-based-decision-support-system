import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Bot, Send, User, Sparkles, BookOpen, AlertCircle,
  Loader2, AlertTriangle, PhoneCall, ShieldAlert, CheckCircle2,
  FileText
} from 'lucide-react';
import { DisclaimerBadge } from '../components/DisclaimerBadge';
import { sendAssistantChat, getChatHistory, getCurrentUserId, getActiveReportId, ChatResponse } from '../services/api';

export const AiAssistantPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const urlReportId = searchParams.get('report_id');
  const urlHospitalId = searchParams.get('hospital_id');
  const userId = getCurrentUserId();
  const [conversationId, setConversationId] = useState<number | undefined>(undefined);
  const [messages, setMessages] = useState<Array<{
    sender: string;
    text: string;
    citations?: string[];
    is_emergency?: boolean;
    emergency_alert?: string;
    llm_provider?: string;
    model_used?: string;
    safety_guardrails_triggered?: string[];
  }>>([
    {
      sender: 'assistant',
      text: 'Hello! I am your AI Healthcare Decision Support Assistant. I provide evidence-grounded information based on verified clinical practice guidelines and your active shared clinical profile. How can I assist with your treatment questions, clinical recovery, or specialist consultations today?',
      citations: ['Verified Clinical Practice Guidelines (ESC, ACC/AHA, AAOS, NCCN)'],
      llm_provider: 'ollama',
      model_used: 'llama3.2:1b'
    }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [patientContext, setPatientContext] = useState<ChatResponse['patient_context_applied'] | null>(null);
  const [suggestedPrompts, setSuggestedPrompts] = useState<string[]>([
    "Can I travel by flight after coronary angioplasty with stent?",
    "What DVT prevention precautions are needed for travel after joint surgery?",
    "Why is air travel restricted after craniotomy neurosurgery?",
    "What documents should I carry for medical travel?"
  ]);

  const handleSend = async (textToSend?: string) => {
    const query = textToSend || input;
    if (!query.trim() || isTyping) return;

    // Add user message
    const updated = [...messages, { sender: 'user', text: query, citations: [] }];
    setMessages(updated);
    setInput('');
    setIsTyping(true);

    // Active report synchronization: URL report_id -> Session state active_report_id -> undefined (latest backend fallback)
    const sessionReportId = getActiveReportId();
    const effectiveReportId = urlReportId ? Number(urlReportId) : (sessionReportId || undefined);

    try {
      const res: ChatResponse = await sendAssistantChat(
        query,
        conversationId,
        effectiveReportId,
        urlHospitalId ? Number(urlHospitalId) : undefined,
        userId
      );

      if (res.conversation_id) {
        setConversationId(res.conversation_id);
      }

      if (res.patient_context_applied && Object.keys(res.patient_context_applied).length > 0) {
        setPatientContext(res.patient_context_applied);
      }

      if (res.suggested_followups && res.suggested_followups.length > 0) {
        setSuggestedPrompts(res.suggested_followups);
      }

      setMessages([...updated, {
        sender: 'assistant',
        text: res.reply,
        citations: res.citations && res.citations.length > 0 ? res.citations : [],
        is_emergency: res.is_emergency,
        emergency_alert: res.emergency_alert,
        llm_provider: res.llm_provider,
        model_used: res.model_used,
        safety_guardrails_triggered: res.safety_guardrails_triggered
      }]);
    } catch (e: any) {
      console.warn('Chat API error', e);
      let errorText = 'Unable to connect to the healthcare assistant service. Please ensure the backend server is running and try again.';
      const errStr = e?.message || String(e);

      if (errStr.includes('401') || errStr.toLowerCase().includes('unauthorized') || errStr.toLowerCase().includes('authentication required')) {
        errorText = 'Authentication Required / Session Expired: Please log in again to access your clinical assistant.';
      } else if (errStr.includes('403') || errStr.toLowerCase().includes('forbidden') || errStr.toLowerCase().includes('authorization')) {
        errorText = 'Access Denied: You do not have authorization to access this patient profile or conversation session. A new conversation thread has been started.';
        setConversationId(undefined);
      } else if (errStr.includes('404') || errStr.toLowerCase().includes('not found')) {
        errorText = 'Clinical Context Notice: The selected medical report or conversation session could not be found.';
      } else if (errStr && !errStr.includes('Failed to fetch') && !errStr.includes('NetworkError') && !errStr.includes('HTTP Error')) {
        errorText = `Healthcare Assistant Notice: ${errStr}`;
      }

      setMessages([...updated, {
        sender: 'assistant',
        text: errorText,
        citations: []
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto h-[calc(100vh-8rem)] flex flex-col glass-card rounded-3xl border border-slate-200 shadow-xl overflow-hidden">
      
      {/* Header */}
      <div className="p-4 sm:p-5 bg-white border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl gradient-bg flex items-center justify-center text-white shadow">
            <Bot className="w-6 h-6" />
          </div>
          <div>
            <h1 className="font-extrabold text-slate-900 text-base">AI Healthcare Assistant</h1>
            <p className="text-xs text-slate-500">RAG-Grounded Conversational Decision Support</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <DisclaimerBadge type="ai" text="RAG-Grounded Evidence" />
        </div>
      </div>

      {/* Authenticated Patient Context Bar (Rendered ONLY from actual backend data) */}
      {patientContext && (
        <div className="px-5 py-2.5 bg-slate-50 border-b border-slate-200 text-xs flex flex-wrap items-center gap-3">
          <div className="font-bold text-slate-700 flex items-center gap-1.5">
            <FileText className="w-3.5 h-3.5 text-sky-600" />
            <span>Active Patient Context:</span>
          </div>

          {patientContext.age && (
            <span className="bg-white px-2.5 py-0.5 rounded-full border border-slate-200 text-slate-600 font-medium text-[11px]">
              Age: {patientContext.age}
            </span>
          )}

          {patientContext.gender && (
            <span className="bg-white px-2.5 py-0.5 rounded-full border border-slate-200 text-slate-600 font-medium text-[11px]">
              Gender: {patientContext.gender}
            </span>
          )}

          {patientContext.allergies && patientContext.allergies.length > 0 && (
            <span className="bg-rose-50 px-2.5 py-0.5 rounded-full border border-rose-200 text-rose-700 font-bold text-[11px]">
              Allergies: {patientContext.allergies.join(', ')}
            </span>
          )}

          {patientContext.chronic_conditions && patientContext.chronic_conditions.length > 0 && (
            <span className="bg-white px-2.5 py-0.5 rounded-full border border-slate-200 text-slate-600 font-medium text-[11px]">
              Conditions: {patientContext.chronic_conditions.join(', ')}
            </span>
          )}

          {patientContext.medical_history && patientContext.medical_history.length > 0 && (
            <span className="bg-white px-2.5 py-0.5 rounded-full border border-slate-200 text-slate-600 font-medium text-[11px]">
              History: {patientContext.medical_history.join(', ')}
            </span>
          )}

          {patientContext.specialty && (
            <span className="bg-sky-50 px-2.5 py-0.5 rounded-full border border-sky-200 text-sky-700 font-medium text-[11px]">
              Specialty: {patientContext.specialty}
            </span>
          )}

          {patientContext.report_id && (
            <span className="bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200 text-emerald-700 font-bold text-[11px]">
              Report #{patientContext.report_id}
            </span>
          )}
        </div>
      )}

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
              className={`max-w-2xl p-4 rounded-2xl text-xs leading-relaxed space-y-2 ${
                msg.sender === 'user'
                  ? 'bg-slate-900 text-white rounded-tr-none'
                  : 'bg-white text-slate-800 border border-slate-200/80 rounded-tl-none shadow-sm'
              }`}
            >
              {/* Emergency Alert Banner if triggered */}
              {msg.is_emergency && (
                <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-900 space-y-1">
                  <div className="font-extrabold flex items-center gap-1.5 text-rose-800">
                    <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
                    <span>EMERGENCY CLINICAL NOTICE</span>
                  </div>
                  <p className="text-[11px] leading-relaxed">
                    {msg.emergency_alert || "The symptoms described may indicate an acute medical emergency. Contact appropriate local emergency services immediately (112 or 108 in India) or proceed to the nearest emergency room."}
                  </p>
                  <div className="text-[10px] font-bold text-rose-700 pt-1 flex items-center gap-2">
                    <PhoneCall className="w-3 h-3" />
                    <span>Configured Emergency Hotlines: 112 / 108 (India) • Or Local Emergency Dispatch</span>
                  </div>
                </div>
              )}

              {/* Message Content */}
              <div className="whitespace-pre-line leading-relaxed">{msg.text}</div>

              {/* Verified Source Citations */}
              {msg.citations && msg.citations.length > 0 && (
                <div className="mt-3 pt-2.5 border-t border-slate-100 flex flex-wrap items-center gap-1.5 text-[10px] text-sky-700">
                  <BookOpen className="w-3.5 h-3.5 text-sky-600 shrink-0" />
                  <span className="font-bold">Verified Sources:</span>
                  {msg.citations.map((cite, cIdx) => (
                    <span
                      key={cIdx}
                      className="bg-sky-50 px-2 py-0.5 rounded-md border border-sky-100 font-semibold"
                    >
                      {cite}
                    </span>
                  ))}
                </div>
              )}

              {/* Provider & Safety Guardrail Metadata */}
              {msg.sender === 'assistant' && (
                <div className="mt-2 pt-2 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2 text-[10px]">
                  <div className="flex items-center gap-1.5">
                    {msg.llm_provider === 'ollama' ? (
                      <span className="bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded font-medium flex items-center gap-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                        Ollama Local LLM ({msg.model_used || 'llama3.2:1b'})
                      </span>
                    ) : (
                      <span className="bg-slate-100 text-slate-700 border border-slate-200 px-2 py-0.5 rounded font-medium flex items-center gap-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-slate-400"></span>
                        Deterministic Evidence Fallback
                      </span>
                    )}
                  </div>
                  {msg.safety_guardrails_triggered && msg.safety_guardrails_triggered.length > 0 && (
                    <div className="flex items-center gap-1">
                      {msg.safety_guardrails_triggered.map((g, gIdx) => (
                        <span key={gIdx} className="bg-amber-50 text-amber-700 border border-amber-200 px-1.5 py-0.5 rounded font-semibold text-[9px]">
                          🛡️ {g.replace(/_/g, ' ')}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full gradient-bg text-white flex items-center justify-center text-xs font-bold shrink-0">
              <Bot className="w-4 h-4" />
            </div>
            <div className="p-3.5 bg-white border border-slate-200/80 rounded-2xl rounded-tl-none shadow-sm text-xs text-slate-500 flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-sky-600" />
              <span>Retrieving verified clinical guidelines & synthesizing grounded response...</span>
            </div>
          </div>
        )}
      </div>

      {/* Suggested Quick Follow-Up Prompts */}
      <div className="p-3 bg-slate-100/70 border-t border-slate-200 flex items-center gap-2 overflow-x-auto text-xs">
        <Sparkles className="w-3.5 h-3.5 text-sky-600 shrink-0 ml-1" />
        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider shrink-0">Suggested:</span>
        {suggestedPrompts.map((p, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(p)}
            className="px-3 py-1 bg-white hover:bg-sky-50 text-slate-700 hover:text-sky-700 rounded-full border border-slate-200/80 shrink-0 font-medium transition-colors text-[11px]"
          >
            {p}
          </button>
        ))}
      </div>

      {/* Input Form Bar */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="p-4 bg-white border-t border-slate-200 flex items-center gap-3"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a medical question, inquire about flights, treatment precautions, or hospital care..."
          className="flex-1 px-4 py-2.5 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-sky-500 focus:outline-none"
        />

        <button
          type="submit"
          disabled={!input.trim() || isTyping}
          className="p-2.5 rounded-xl gradient-bg text-white shadow hover:opacity-95 transition-opacity disabled:opacity-40"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>

    </div>
  );
};
