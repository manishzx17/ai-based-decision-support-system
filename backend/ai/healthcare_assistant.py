"""
AI Healthcare Assistant Engine for 12C Medical Travel Decision Support System.

Features:
1. Grounded Semantic RAG: Uses Phase 3 SemanticRAGEngine for dense vector search over verified clinical guidelines.
2. Clinical Safety Guardrails:
   - Acute emergency symptom detection: Advises contacting appropriate local emergency services (configured for 112/108 in India demo or local emergency dept).
   - Prohibition against independent medication-stop/start or dosage alterations.
   - Prohibition against definitive diagnoses or unilateral clinical decisions.
   - Strict distinction between patient-specific reported context and verified medical literature.
3. Strict Patient Isolation: Consumes only the authenticated user's profile and medical report context.
4. Multi-Turn Conversational Memory: Ingests prior dialog turns to support natural contextual follow-ups.
5. Grounded Generation: Employs Gemini (when configured) or deterministic evidence synthesis with verified citations.
6. Refusal: Returns INSUFFICIENT_EVIDENCE when clinical query is unsupported by the verified corpus.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from config import settings
from ai.rag_engine import rag_engine


class AIHealthcareAssistant:
    """
    RAG-grounded, context-aware, safety-guarded healthcare conversational assistant.
    """

    MANDATORY_SAFETY_DISCLAIMER = (
        "[Medical Safety Notice: AI Healthcare Assistant is strictly an informational decision support "
        "tool and does not provide formal medical diagnoses, clinical prescriptions, or emergency clearance. "
        "Always verify clinical considerations with your licensed healthcare specialist.]"
    )

    # Acute emergency symptom keywords requiring immediate triage routing
    EMERGENCY_SYMPTOM_PATTERNS = [
        r"\bchest pain\b",
        r"\bcrushing (pressure|pain)\b",
        r"\bpain (radiating|spreading) to (left arm|jaw|neck|back)\b",
        r"\bshortness of breath\b",
        r"\bsevere dyspnea\b",
        r"\bgasping for air\b",
        r"\b(struggling|difficulty|trouble|unable) to breathe\b",
        r"\b(can'?t|cannot) breathe\b",
        r"\bsudden (numbness|weakness|paralysis)\b",
        r"\b(facial|face) (is )?(droop|drooping)\b",
        r"\b(droop|drooping) face\b",
        r"\b(cannot|can'?t|unable to) lift (one |my )?arm\b",
        r"\barm (weakness|numbness|paralysis)\b",
        r"\bslurred speech\b",
        r"\b(difficulty|trouble) (speaking|talking)\b",
        r"\bunconscious(ness)?\b",
        r"\bfainting\b",
        r"\bsyncope\b",
        r"\buncontrolled bleeding\b",
        r"\bsevere anaphylaxis\b",
        r"\bswelling of (throat|tongue|airway)\b"
    ]

    # Patterns where patients ask for medication stoppage, starting, or dosage instructions
    MEDICATION_MODIFICATION_PATTERNS = [
        r"\b(should|can|do|may|could) i (stop|discontinue|pause|quit|skip|change|alter|taper|increase|decrease|raise|lower|reduce|double|halve|cut|adjust)\b.*\b(medication|medicine|drug|pill|aspirin|clopidogrel|dapt|blood thinner|statin|warfarin|inr|insulin|heparin|metformin|antibiotic|dose|dosage)\b",
        r"\b(stop|discontinue|pause|skip)\b.*\b(taking|my)\b.*\b(medication|medicine|pill|aspirin|clopidogrel|blood thinner|statin|warfarin)\b",
        r"\b(what|which|how much)\b.*\b(dose|dosage|amount|mg|milligram|pills|tablets)\b.*\b(take|prescribe|administer|consume)\b",
        r"\b(can|should|may|could|do) i (increase|decrease|raise|lower|reduce|double|halve|cut|change|adjust) (my )?(medication )?(dose|dosage)\b",
        r"\bshould i start taking\b",
        r"\bshould i (stop|discontinue|pause|change|increase|decrease) this medication\b"
    ]

    # Patterns where users ask for definitive diagnosis
    DIAGNOSIS_REQUEST_PATTERNS = [
        r"\bdo i have\b.*\b(cancer|heart attack|heart failure|stroke|tumor|stenosis|disease|infection|infarction)\b",
        r"\bdiagnose (me|my condition|my symptoms|my illness)\b",
        r"\bwhat is my (exact |definitive )?diagnosis\b",
        r"\btell me what (disease|condition|illness) i have\b",
        r"\bwhat (is wrong with|ails) me\b"
    ]

    def _detect_emergency_symptoms(self, query: str) -> Optional[str]:
        """
        Scans for acute life-threatening emergency symptoms.
        Advises contacting appropriate local emergency services (112/108 in India demo).
        """
        q_lower = query.lower()
        for pattern in self.EMERGENCY_SYMPTOM_PATTERNS:
            if re.search(pattern, q_lower):
                stroke_fast = ""
                if any(re.search(p, q_lower) for p in [
                    r"\b(facial|face) (is )?(droop|drooping)\b",
                    r"\b(droop|drooping) face\b",
                    r"\b(cannot|can'?t|unable to) lift (one |my )?arm\b",
                    r"\barm (weakness|numbness|paralysis)\b",
                    r"\bslurred speech\b",
                    r"\b(difficulty|trouble) (speaking|talking)\b"
                ]):
                    stroke_fast = " (FAST Stroke Warning: Facial droop, Arm weakness, Speech difficulty indicate potential acute stroke requiring immediate emergency care)"

                return (
                    f"🚨 CRITICAL MEDICAL ALERT: The symptoms you described may indicate an acute "
                    f"medical emergency{stroke_fast}. Do NOT wait for an online response, undertake travel, or delay care. "
                    f"Please contact your appropriate local emergency service immediately "
                    f"(call 112 or 108 in India, or your local national emergency number) "
                    f"or proceed to the nearest accredited hospital emergency department."
                )
        return None

    def _detect_medication_modification(self, query: str) -> Optional[str]:
        """
        Identifies requests for independent medication alterations.
        Enforces refusal to issue prescription changes.
        """
        q_lower = query.lower()
        for pattern in self.MEDICATION_MODIFICATION_PATTERNS:
            if re.search(pattern, q_lower):
                return (
                    "Safety Guardrail: As an AI decision support assistant, I cannot provide independent "
                    "instructions to start, stop, or adjust prescription dosages (such as antiplatelet agents, "
                    "blood thinners, or chronic medications). Dual Antiplatelet Therapy (DAPT) or anticoagulation "
                    "protocols must only be modified under the direct instruction and written authorization "
                    "of your prescribing specialist or attending cardiologist."
                )
        return None

    def _detect_definitive_diagnosis_request(self, query: str) -> Optional[str]:
        """Identifies requests for definitive diagnostic proclamations."""
        q_lower = query.lower()
        for pattern in self.DIAGNOSIS_REQUEST_PATTERNS:
            if re.search(pattern, q_lower):
                return (
                    "Clinical Safety Notice: This AI system is designed strictly for medical travel decision support "
                    "and cannot provide definitive clinical diagnoses. A valid diagnosis requires an in-person physical "
                    "examination, formal clinical evaluation, and diagnostic review by a licensed healthcare specialist. "
                    "Diagnostic reports and symptoms alone in this assistant cannot establish whether you have this condition. "
                    "Please schedule an in-person consultation with a qualified specialist or physician for definitive clinical evaluation."
                )
        return None

    def _format_patient_context(
        self,
        patient_profile: Optional[Dict[str, Any]],
        medical_report: Optional[Dict[str, Any]],
        hospital_context: Optional[Dict[str, Any]]
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Assembles active patient context and clinical profile.
        Strictly reflects data present in the user's records without fabrication.
        """
        context_parts = []
        applied_summary = {}

        if patient_profile:
            demographics = patient_profile.get("demographics", {})
            age = demographics.get("age") if isinstance(demographics, dict) else None
            if not age:
                age = patient_profile.get("age")
            if age:
                applied_summary["age"] = age

            gender = demographics.get("gender") if isinstance(demographics, dict) else None
            if not gender:
                gender = patient_profile.get("gender")
            if gender:
                applied_summary["gender"] = gender

            raw_allergies = patient_profile.get("allergies")
            if not raw_allergies and isinstance(demographics, dict):
                raw_allergies = demographics.get("allergies")
            if isinstance(raw_allergies, str):
                allergies_list = [a.strip() for a in raw_allergies.split(",") if a.strip() and a.lower() != "none"]
            elif isinstance(raw_allergies, list):
                allergies_list = [str(a).strip() for a in raw_allergies if str(a).strip() and str(a).lower() != "none"]
            else:
                allergies_list = []
            applied_summary["allergies"] = allergies_list

            conds_list = []
            cond_sources = [patient_profile.get("chronic_conditions")]
            if isinstance(demographics, dict):
                cond_sources.append(demographics.get("chronic_conditions"))
            cond_sources.append(patient_profile.get("conditions"))

            seen_conds = set()
            for src in cond_sources:
                if isinstance(src, str):
                    for c in src.split(","):
                        c_clean = c.strip()
                        if c_clean and c_clean.lower() != "none" and c_clean.lower() not in seen_conds:
                            seen_conds.add(c_clean.lower())
                            conds_list.append(c_clean)
                elif isinstance(src, list):
                    for c in src:
                        c_clean = str(c).strip()
                        if c_clean and c_clean.lower() != "none" and c_clean.lower() not in seen_conds:
                            seen_conds.add(c_clean.lower())
                            conds_list.append(c_clean)
            applied_summary["chronic_conditions"] = conds_list

            history_list = []
            hist_sources = [patient_profile.get("medical_history")]
            if isinstance(demographics, dict):
                hist_sources.append(demographics.get("medical_history"))
            seen_hist = set()
            for src in hist_sources:
                if isinstance(src, str):
                    for h in src.split(","):
                        h_clean = h.strip()
                        if h_clean and h_clean.lower() != "none" and h_clean.lower() not in seen_hist:
                            seen_hist.add(h_clean.lower())
                            history_list.append(h_clean)
                elif isinstance(src, list):
                    for h in src:
                        h_clean = str(h).strip()
                        if h_clean and h_clean.lower() != "none" and h_clean.lower() not in seen_hist:
                            seen_hist.add(h_clean.lower())
                            history_list.append(h_clean)
            if history_list:
                applied_summary["medical_history"] = history_list

            meds = patient_profile.get("medications", [])
            if isinstance(meds, str):
                meds = [m.strip() for m in meds.split(",") if m.strip() and m.lower() != "none"]
            elif isinstance(meds, list):
                meds = [str(m).strip() for m in meds if str(m).strip() and str(m).lower() != "none"]
            else:
                meds = []
            if meds:
                applied_summary["medications"] = meds

            procs = patient_profile.get("procedures", [])
            if isinstance(procs, str):
                procs = [p.strip() for p in procs.split(",") if p.strip() and p.lower() != "none"]
            elif isinstance(procs, list):
                procs = [str(p).strip() for p in procs if str(p).strip() and str(p).lower() != "none"]
            else:
                procs = []
            if procs:
                applied_summary["procedures"] = procs

            test_res = patient_profile.get("test_results", [])
            if test_res:
                applied_summary["test_results"] = test_res

            p_lines = []
            if age:
                p_lines.append(f"Patient Age: {age}")
            if gender:
                p_lines.append(f"Patient Gender: {gender}")
            if allergies_list:
                p_lines.append(f"Documented Allergies: {', '.join(allergies_list)}")
            if conds_list:
                p_lines.append(f"Documented Conditions: {', '.join(conds_list)}")
            if history_list:
                p_lines.append(f"Past Medical / Surgical History: {', '.join(history_list)}")
            if meds:
                p_lines.append(f"Active Medications: {', '.join(meds)}")
            if procs:
                p_lines.append(f"Prior Procedures: {', '.join(procs)}")
            if test_res:
                tr_strs = [f"{t.get('test_name', 'Test')}: {t.get('value', 'N/A')}" for t in test_res[:4] if isinstance(t, dict)]
                if tr_strs:
                    p_lines.append(f"Key Test Results: {'; '.join(tr_strs)}")

            if p_lines:
                context_parts.append("Active Patient Context (Shared Clinical Profile):\n" + "\n".join(f"- {l}" for l in p_lines))

        if medical_report:
            if medical_report.get("id"):
                applied_summary["report_id"] = medical_report["id"]
            applied_summary["report_summary"] = medical_report.get("summary")
            applied_summary["specialty"] = medical_report.get("recommended_specialty")
            applied_summary["entities"] = medical_report.get("entities", [])

            r_lines = [f"Clinical Specialty: {medical_report.get('recommended_specialty', 'General')}"]
            if medical_report.get("summary"):
                r_lines.append(f"Diagnostic Report Summary: {medical_report['summary']}")
            if medical_report.get("entities"):
                r_lines.append(f"Extracted Entities: {', '.join(medical_report['entities'][:8])}")
            context_parts.append("Latest Diagnostic Record (For Reference Only):\n" + "\n".join(f"- {l}" for l in r_lines))

        if hospital_context:
            applied_summary["hospital_name"] = hospital_context.get("name")
            applied_summary["hospital_city"] = hospital_context.get("city")
            context_parts.append(
                f"Selected Healthcare Facility: {hospital_context.get('name')} "
                f"({hospital_context.get('city', '')})"
            )

        formatted_str = "\n\n".join(context_parts) if context_parts else ""
        return (formatted_str, applied_summary)

    def _generate_suggested_followups(
        self,
        query: str,
        retrieved_docs: List[Dict[str, Any]],
        grounding_status: str
    ) -> List[str]:
        """Generates contextual follow-up questions for patient discovery."""
        if grounding_status in ["INSUFFICIENT_EVIDENCE", "EMERGENCY_TRIAGE"]:
            return [
                "Which accredited hospitals specialize in my condition?",
                "What documents should I carry for medical travel?",
                "How do I consult an accredited specialist before traveling?"
            ]

        q_low = query.lower()
        if "stent" in q_low or "angioplasty" in q_low or "cardio" in q_low or "heart" in q_low:
            return [
                "What are the airline fit-to-fly rules after angioplasty?",
                "How does dual antiplatelet therapy (DAPT) affect travel?",
                "Which hospitals in Hyderabad have 24/7 cardiac cath labs?"
            ]
        elif "knee" in q_low or "hip" in q_low or "ortho" in q_low or "joint" in q_low:
            return [
                "What DVT prevention precautions are needed when flying after knee surgery?",
                "Do orthopedic joint implants trigger airport security scanners?",
                "What accessible accommodations are located near orthopedic hospitals?"
            ]
        elif "brain" in q_low or "craniotomy" in q_low or "neuro" in q_low:
            return [
                "Why is cabin pressure a concern following craniotomy?",
                "How many days must I wait before flying after neurosurgery?",
                "What emergency trauma centers are available in Hyderabad?"
            ]
        else:
            return [
                "What are the pre-procedure consultation requirements?",
                "How do cashless hospital insurance claims work?",
                "Can you help plan my medical travel itinerary?"
            ]

    def process_chat_query(
        self,
        user_query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        patient_profile: Optional[Dict[str, Any]] = None,
        medical_report: Optional[Dict[str, Any]] = None,
        hospital_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes end-to-end RAG processing with safety guardrails and patient context.
        """
        safety_triggered = []
        clean_query = user_query.strip()

        # 1. Assemble authenticated patient context (strictly isolated to this user)
        patient_context_str, patient_applied = self._format_patient_context(
            patient_profile, medical_report, hospital_context
        )

        # 2. Emergency symptom triage check (takes absolute priority over routine advice)
        emergency_alert = self._detect_emergency_symptoms(clean_query)
        is_emergency = emergency_alert is not None
        if is_emergency:
            safety_triggered.append("EMERGENCY_TRIAGE_ACTIVATED")
            emergency_reply = (
                f"{emergency_alert}\n\n"
                f"Emergency Safety Instruction: Emergency medical triage overrides standard decision support. "
                f"Personalized clinical travel guidance is suspended until acute emergency stabilization is confirmed by an emergency physician.\n\n"
                f"{self.MANDATORY_SAFETY_DISCLAIMER}"
            )
            return {
                "reply": emergency_reply,
                "citations": [],
                "grounding_status": "EMERGENCY_TRIAGE",
                "retrieved_evidence": [],
                "is_emergency": True,
                "emergency_alert": emergency_alert,
                "patient_context_applied": patient_applied,
                "suggested_followups": [
                    "How to contact local emergency medical services (112 / 108)?",
                    "What emergency information should I provide to dispatch?",
                    "Where is the nearest emergency trauma center?"
                ],
                "safety_guardrails_triggered": safety_triggered,
                "disclaimer": self.MANDATORY_SAFETY_DISCLAIMER,
                "llm_provider": "deterministic_emergency_triage",
                "model_used": "emergency_guardrail"
            }

        # 3. Medication modification guardrail check
        med_warning = self._detect_medication_modification(clean_query)
        if med_warning:
            safety_triggered.append("MEDICATION_MODIFICATION_GUARDRAIL")

        # 4. Definitive diagnosis guardrail check
        diag_warning = self._detect_definitive_diagnosis_request(clean_query)
        if diag_warning:
            safety_triggered.append("DIAGNOSIS_PROHIBITION_GUARDRAIL")

        # 5. Format conversation history context
        history_context_str = ""
        if conversation_history:
            recent_turns = conversation_history[-6:]  # Last 3 turns
            formatted_turns = []
            for t in recent_turns:
                sender_label = "Patient" if t.get("sender") == "user" else "Assistant"
                formatted_turns.append(f"{sender_label}: {t.get('text', '')[:200]}")
            history_context_str = "Recent Conversation Context:\n" + "\n".join(formatted_turns)

        # 6. Retrieve verified clinical evidence via Phase 3 Semantic RAG
        # Dynamically build retrieval context from current question + authenticated user's patient profile + current active report
        search_query = clean_query
        context_tokens = []

        # Contextualize elliptical follow-ups from prior conversation turns
        if conversation_history and len(conversation_history) > 0:
            prior_user_turns = [t.get("text", "") for t in conversation_history if t.get("sender") == "user"]
            if prior_user_turns:
                last_turn = prior_user_turns[-1].lower()
                elliptical_cues = ["timing", "when", "how long", "schedule", "what about", "how about", "condition specifically", "my condition", "risks", "precautions"]
                if len(clean_query.split()) <= 7 or any(c in clean_query.lower() for c in elliptical_cues):
                    for kw in ["travel", "flying", "flight", "surgery", "treatment", "procedure", "stent", "angioplasty", "knee", "hip", "craniotomy", "asthma", "cancer", "medication", "recovery"]:
                        if kw in last_turn and kw not in clean_query.lower():
                            context_tokens.append(kw)
                            break

        # Relevant specialty or condition from active report or profile
        active_specialty = patient_applied.get("specialty") or (patient_profile.get("specialty") if patient_profile else None)
        if active_specialty and active_specialty.lower() not in clean_query.lower() and active_specialty.lower() != "general medicine":
            context_tokens.append(active_specialty)

        # Chronic conditions from patient profile
        for cond in patient_applied.get("chronic_conditions", []):
            if cond.lower() not in clean_query.lower():
                context_tokens.append(cond)
                break  # Incorporate primary comorbidity

        # Relevant report findings/entities
        for ent in patient_applied.get("entities", [])[:2]:
            if ent.lower() not in clean_query.lower():
                context_tokens.append(ent)

        if context_tokens:
            search_query = f"{' '.join(context_tokens[:2])}: {clean_query}"

        retrieved = rag_engine.retrieve_documents(search_query, top_k=3)
        if not retrieved and search_query != clean_query:
            # Fallback to direct query if context tokens caused strict threshold miss
            retrieved = rag_engine.retrieve_documents(clean_query, top_k=3)

        # 7. Check for Insufficient Evidence Refusal
        if not retrieved:
            refusal_body = (
                "Insufficient verified clinical evidence was found in our medical knowledge base "
                "to address your specific query safely.\n\n"
                "Our decision support system strictly adheres to clinical safety guidelines and "
                "refuses to fabricate unverified treatments, dosages, or advice. Please consult a "
                "qualified physician or accredited hospital specialist for medical evaluation."
            )

            # Prepend emergency or guardrail alerts if triggered
            active_banners = []
            if emergency_alert:
                active_banners.append(emergency_alert)
            if med_warning:
                active_banners.append(med_warning)
            if diag_warning:
                active_banners.append(diag_warning)

            full_reply = ("\n\n".join(active_banners) + "\n\n" + refusal_body) if active_banners else refusal_body
            full_reply = full_reply.strip() + "\n\n" + self.MANDATORY_SAFETY_DISCLAIMER

            return {
                "reply": full_reply,
                "citations": [],
                "grounding_status": "INSUFFICIENT_EVIDENCE",
                "retrieved_evidence": [],
                "is_emergency": is_emergency,
                "emergency_alert": emergency_alert,
                "patient_context_applied": patient_applied,
                "suggested_followups": self._generate_suggested_followups(clean_query, [], "INSUFFICIENT_EVIDENCE"),
                "safety_guardrails_triggered": safety_triggered,
                "disclaimer": self.MANDATORY_SAFETY_DISCLAIMER
            }

        # 8. Synthesize Grounded Medical Guidance
        citations = []
        citations_seen = set()
        for doc in retrieved:
            ref_str = f"{doc['organization']}: {doc['title']}"
            if ref_str not in citations_seen:
                citations_seen.add(ref_str)
                citations.append(ref_str)

        # Format evidence blocks for prompting
        evidence_blocks = [
            f"[Source: {d['organization']} - {d['title']}]\n{d['content']}\nReference: {d.get('source_reference', '')}"
            for d in retrieved
        ]
        evidence_text = "\n\n".join(evidence_blocks)

        # Call Ollama local LLM runtime with full patient context, evidence, and conversation memory
        ollama_reply = rag_engine._call_ollama(
            user_query=clean_query,
            evidence_text=evidence_text,
            patient_context=patient_context_str,
            conversation_history=history_context_str
        )

        if ollama_reply:
            assistant_reply = ollama_reply
            llm_provider = "ollama"
            model_used = settings.OLLAMA_MODEL
        else:
            # Deterministic, non-hallucinatory verified synthesizer fallback
            evidence_points = []
            for doc in retrieved:
                evidence_points.append(
                    f"• **{doc['organization']} ({doc['title']})**:\n"
                    f"  {doc['content']}\n"
                    f"  *(Reference: {doc.get('source_reference', '')})*"
                )
            evidence_summary = "\n\n".join(evidence_points)

            patient_note = ""
            if patient_applied.get("allergies") or patient_applied.get("chronic_conditions") or patient_applied.get("procedures"):
                notes = []
                if patient_applied.get("allergies"):
                    notes.append(f"documented allergy to {', '.join(patient_applied['allergies'])}")
                if patient_applied.get("chronic_conditions"):
                    notes.append(f"history of {', '.join(patient_applied['chronic_conditions'])}")
                if patient_applied.get("procedures"):
                    notes.append(f"procedure history of {', '.join(patient_applied['procedures'])}")
                patient_note = f"**Patient Clinical Context**: In light of your {' and '.join(notes)}, ensure your healthcare provider reviews your records.\n\n"

            assistant_reply = (
                f"{patient_note}"
                f"**Verified Clinical Guidelines (RAG-Retrieved)**:\n\n"
                f"{evidence_summary}\n\n"
                f"**Clinical Advisory**: Informational decision support only. Discuss these specific guidelines "
                f"with your attending specialist prior to making travel or clinical preparations."
            )
            llm_provider = "deterministic_fallback"
            model_used = "none"

        # Prepend any emergency or medication safety guardrail banners
        active_banners = []
        if emergency_alert:
            active_banners.append(emergency_alert)
        if med_warning:
            active_banners.append(med_warning)
        if diag_warning:
            active_banners.append(diag_warning)

        final_reply = ("\n\n".join(active_banners) + "\n\n" + assistant_reply) if active_banners else assistant_reply
        final_reply = final_reply.strip() + "\n\n" + self.MANDATORY_SAFETY_DISCLAIMER

        return {
            "reply": final_reply,
            "citations": citations,
            "grounding_status": "GROUNDED",
            "retrieved_evidence": [
                {
                    "title": d["title"],
                    "organization": d["organization"],
                    "source_reference": d["source_reference"],
                    "reference_url": d.get("reference_url", ""),
                    "score": d.get("score", 0.0),
                    "content": d.get("content", "")
                }
                for d in retrieved
            ],
            "is_emergency": is_emergency,
            "emergency_alert": emergency_alert,
            "patient_context_applied": patient_applied,
            "suggested_followups": self._generate_suggested_followups(clean_query, retrieved, "GROUNDED"),
            "safety_guardrails_triggered": safety_triggered,
            "disclaimer": self.MANDATORY_SAFETY_DISCLAIMER,
            "llm_provider": llm_provider,
            "model_used": model_used
        }


healthcare_assistant = AIHealthcareAssistant()
