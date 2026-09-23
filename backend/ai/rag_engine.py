import os
import re
import json
import hashlib
from typing import List, Dict, Any, Optional
import numpy as np
import requests
from config import settings

# Path for persistent FAISS vector storage
RAG_STORAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rag_storage")
os.makedirs(RAG_STORAGE_DIR, exist_ok=True)

INDEX_FILE = os.path.join(RAG_STORAGE_DIR, "faiss_index.bin")
CHUNKS_FILE = os.path.join(RAG_STORAGE_DIR, "chunks.json")
HASH_FILE = os.path.join(RAG_STORAGE_DIR, "corpus_hash.txt")

DATASET_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "datasets",
    "medical_knowledge",
    "medical_knowledge_dataset.json"
)

# Embedding model singleton
_embedding_model = None

def get_embedding_model():
    """Lazily loads the lightweight SentenceTransformer model on CPU for macOS stability."""
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
    return _embedding_model


class SemanticRAGEngine:
    """
    Evidence-grounded Medical Knowledge & RAG Engine (Phase 4).

    Pipeline:
    Medical Knowledge Documents
    → Cleaning + Chunking
    → Sentence Transformer Embeddings (all-MiniLM-L6-v2, 384-dim)
    → FAISS Semantic Retrieval (IndexFlatIP)
    → Relevant Evidence + Citations
    → Phase 3 Clinical Profile Context Flow
    → Ollama Local LLM (llama3.2:1b)
    → Grounded Response + Traceable Citations

    Safety Guardrails:
    - Zero fabrication: refuse when similarity is below empirical threshold.
    - Explicit distinction between Ollama responses and deterministic evidence fallback.
    - Traceable citations linking publishing clinical organizations and references.
    """

    MANDATORY_SAFETY_DISCLAIMER = (
        "\n\n[Medical Safety Disclaimer: AI-generated medical decision support is strictly informational "
        "and does not constitute a clinical diagnosis, prescription, or emergency clearance. "
        "Always verify with a licensed specialist before medical travel.]"
    )

    def __init__(self, similarity_threshold: Optional[float] = None):
        self.similarity_threshold = (
            similarity_threshold if similarity_threshold is not None else settings.RAG_SIMILARITY_THRESHOLD
        )
        self.index = None
        self.chunks: List[Dict[str, Any]] = []
        self._ensure_index_initialized()

    def _load_corpus(self) -> List[Dict[str, Any]]:
        """Loads the authoritative medical knowledge dataset or falls back to seed data."""
        if os.path.exists(DATASET_FILE):
            try:
                with open(DATASET_FILE, "r", encoding="utf-8") as f:
                    docs = json.load(f)
                    if isinstance(docs, list) and len(docs) > 0:
                        return docs
            except Exception:
                pass

        # Fallback to seed data if file is missing
        from datasets.seed_data import SEED_KNOWLEDGE_BASE
        return SEED_KNOWLEDGE_BASE

    def _compute_corpus_hash(self, kb_data: List[Dict[str, Any]]) -> str:
        """Computes a SHA256 fingerprint of the knowledge base to detect modifications."""
        serialized = json.dumps([{
            "id": d["id"],
            "title": d["title"],
            "content": d["content"],
            "specialty": d.get("specialty", d.get("category", "")),
            "source_reference": d.get("source_reference", "")
        } for d in kb_data], sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def _chunk_document(self, doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Splits medical guidelines into focused, self-contained clinical chunks
        while preserving complete citation and provenance metadata.
        """
        content = doc.get("content", "").strip()
        doc_id = doc.get("id", 0)
        title = doc.get("title", "")
        category = doc.get("specialty", doc.get("category", ""))
        organization = doc.get("organization", "Clinical Organization")
        source_reference = doc.get("source_reference", "")
        reference_url = doc.get("reference_url", "")
        condition_covered = doc.get("condition_covered", "")
        evidence_level = doc.get("clinical_evidence_level", "")

        clean_text = re.sub(r'\s+', ' ', content).strip()
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', clean_text) if len(s.strip()) > 10]

        chunks = []
        if len(sentences) <= 3:
            chunks.append({
                "chunk_id": f"doc_{doc_id}_c0",
                "doc_id": doc_id,
                "title": title,
                "category": category,
                "specialty": category,
                "condition_covered": condition_covered,
                "organization": organization,
                "source_reference": source_reference,
                "reference_url": reference_url,
                "clinical_evidence_level": evidence_level,
                "content": clean_text
            })
        else:
            step = 2
            window = 3
            c_idx = 0
            for i in range(0, len(sentences), step):
                chunk_sentences = sentences[i:i + window]
                chunk_text = " ".join(chunk_sentences)
                if len(chunk_text) > 40:
                    chunks.append({
                        "chunk_id": f"doc_{doc_id}_c{c_idx}",
                        "doc_id": doc_id,
                        "title": title,
                        "category": category,
                        "specialty": category,
                        "condition_covered": condition_covered,
                        "organization": organization,
                        "source_reference": source_reference,
                        "reference_url": reference_url,
                        "clinical_evidence_level": evidence_level,
                        "content": chunk_text
                    })
                    c_idx += 1
        return chunks

    def build_or_load_index(self, knowledge_base: Optional[List[Dict[str, Any]]] = None) -> None:
        """
        Loads the persistent FAISS vector index from disk if valid,
        or indexes the authoritative medical knowledge corpus and persists it.
        """
        import faiss

        if knowledge_base is None:
            knowledge_base = self._load_corpus()

        current_hash = self._compute_corpus_hash(knowledge_base)

        if os.path.exists(INDEX_FILE) and os.path.exists(CHUNKS_FILE) and os.path.exists(HASH_FILE):
            try:
                with open(HASH_FILE, "r") as f:
                    saved_hash = f.read().strip()
                if saved_hash == current_hash:
                    self.index = faiss.read_index(INDEX_FILE)
                    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
                        self.chunks = json.load(f)
                    return
            except Exception:
                pass

        all_chunks = []
        for doc in knowledge_base:
            all_chunks.extend(self._chunk_document(doc))

        self.chunks = all_chunks
        texts_to_embed = [
            f"{c['title']} | Specialty: {c['category']} | {c['content']}"
            for c in all_chunks
        ]

        model = get_embedding_model()
        embeddings = model.encode(texts_to_embed, normalize_embeddings=True, show_progress_bar=False)
        embeddings_np = np.array(embeddings, dtype=np.float32)

        dim = embeddings_np.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(embeddings_np)

        try:
            faiss.write_index(self.index, INDEX_FILE)
            with open(CHUNKS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.chunks, f, indent=2, ensure_ascii=False)
            with open(HASH_FILE, "w", encoding="utf-8") as f:
                f.write(current_hash)
        except Exception:
            pass

    def _ensure_index_initialized(self):
        if self.index is None or len(self.chunks) == 0:
            self.build_or_load_index()

    def retrieve_documents(
        self,
        query: str,
        knowledge_base: Optional[List[Dict[str, Any]]] = None,
        top_k: int = 3,
        threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Performs semantic vector search over the verified medical knowledge chunks.

        Returns:
            List of retrieved chunks sorted by cosine similarity, filtered by threshold.
            If highest score is below threshold, returns an empty list to prevent hallucination.
        """
        self._ensure_index_initialized()
        if not query or not query.strip():
            return []

        active_threshold = threshold if threshold is not None else self.similarity_threshold

        model = get_embedding_model()
        query_vec = model.encode([query.strip()], normalize_embeddings=True, show_progress_bar=False)
        query_np = np.array(query_vec, dtype=np.float32)

        k = min(top_k, len(self.chunks))
        if k == 0:
            return []

        scores, indices = self.index.search(query_np, k)

        retrieved = []
        for score, idx in zip(scores[0], indices[0]):
            score_float = float(score)
            if 0 <= idx < len(self.chunks):
                chunk = dict(self.chunks[idx])
                chunk["score"] = round(score_float, 4)
                retrieved.append(chunk)

        if not retrieved or retrieved[0]["score"] < active_threshold:
            return []

        return [c for c in retrieved if c["score"] >= active_threshold]

    def _call_ollama(
        self,
        user_query: str,
        evidence_text: str,
        patient_context: str = "",
        conversation_history: str = ""
    ) -> Optional[str]:
        """
        Calls local Ollama LLM runtime with a strict evidence-grounding prompt.
        Returns generated text or None if Ollama is unreachable.
        """
        prompt = f"""You are an authoritative clinical decision-support assistant.
Your task is to answer the user's clinical/medical query STRICTLY and ONLY based on the RETRIEVED CLINICAL EVIDENCE provided below.

CRITICAL GROUNDING RULES:
1. Ground every medical claim directly in the RETRIEVED CLINICAL EVIDENCE.
2. DO NOT fabricate, guess, or invent any clinical facts, medications, dosages, or advice not present in the evidence.
3. If the evidence does not fully answer the query, clearly state what is known from the evidence and where evidence is lacking.
4. Attribute specific guidelines and recommendations to the named medical organizations (e.g., ESC, ACC/AHA, NCCN, AAOS, KDIGO, BTS, ADA).
5. If patient clinical profile context is provided, integrate it carefully to tailor the answer, but distinguish individual patient data from verified clinical guidelines.
6. If recent conversation history is provided, use it to understand conversational context and resolve follow-up references.

{f'PATIENT CLINICAL PROFILE CONTEXT:\n{patient_context}\n' if patient_context else ''}
{f'RECENT CONVERSATION HISTORY:\n{conversation_history}\n' if conversation_history else ''}
RETRIEVED CLINICAL EVIDENCE:
{evidence_text}

USER QUERY:
{user_query}

Provide a concise, structured, grounded clinical answer:"""

        try:
            url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate"
            payload = {
                "model": settings.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Low temperature for strict factual grounding
                    "top_p": 0.9
                }
            }
            res = requests.post(url, json=payload, timeout=8)
            if res.status_code == 200:
                raw_text = res.json().get("response", "").strip()
                if len(raw_text) > 15:
                    return raw_text
        except Exception:
            pass

        return None

    def generate_response(
        self,
        user_query: str,
        retrieved_docs: List[Dict[str, Any]],
        report_context: str = "",
        clinical_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Synthesizes a response strictly grounded in the retrieved evidence.
        Enforces refusal on unsupported queries and prevents fabrication.
        Clearly distinguishes Ollama generated responses from deterministic fallback.
        """
        # 1. Refusal check when retrieved evidence is empty or below relevance threshold
        if not retrieved_docs:
            refusal_text = (
                "Insufficient verified clinical evidence was found in our medical knowledge base "
                "to address your specific query safely.\n\n"
                "Our decision support system strictly adheres to clinical safety guidelines and "
                "refuses to fabricate unverified treatments, dosages, or advice. Please consult a "
                "qualified physician or accredited hospital specialist for medical evaluation."
            )
            return {
                "reply": refusal_text + self.MANDATORY_SAFETY_DISCLAIMER,
                "citations": [],
                "grounding_status": "INSUFFICIENT_EVIDENCE",
                "retrieved_evidence": [],
                "retrieved_docs": [],
                "llm_provider": "none",
                "model_used": "none"
            }

        # Build citations
        citations = []
        citations_seen = set()
        for doc in retrieved_docs:
            ref_str = f"{doc['organization']}: {doc['title']}"
            if ref_str not in citations_seen:
                citations_seen.add(ref_str)
                citations.append(ref_str)

        # Build evidence text
        evidence_blocks = []
        for i, doc in enumerate(retrieved_docs, 1):
            evidence_blocks.append(
                f"[Evidence {i}] Organization: {doc['organization']}\n"
                f"Title: {doc['title']} (Specialty: {doc.get('category', doc.get('specialty', 'Medical'))})\n"
                f"Source: {doc.get('source_reference', '')}\n"
                f"URL: {doc.get('reference_url', '')}\n"
                f"Content: {doc['content']}"
            )
        evidence_text = "\n\n".join(evidence_blocks)

        # Format patient context from profile or report_context
        patient_context_str = report_context
        if clinical_profile:
            profile_lines = []
            if clinical_profile.get("demographics"):
                d = clinical_profile["demographics"]
                profile_lines.append(f"Demographics: Age {d.get('age')}, Gender {d.get('gender')}")
            if clinical_profile.get("conditions"):
                profile_lines.append(f"Conditions: {', '.join(clinical_profile['conditions'])}")
            if clinical_profile.get("symptoms"):
                profile_lines.append(f"Symptoms: {', '.join(clinical_profile['symptoms'])}")
            if clinical_profile.get("medications"):
                profile_lines.append(f"Medications: {', '.join(clinical_profile['medications'])}")
            if clinical_profile.get("procedures"):
                profile_lines.append(f"Procedures: {', '.join(clinical_profile['procedures'])}")
            if clinical_profile.get("test_results"):
                tr_list = [f"{t.get('test_name')}: {t.get('value')}" for t in clinical_profile["test_results"][:4]]
                profile_lines.append(f"Key Tests: {'; '.join(tr_list)}")
            patient_context_str = "\n".join(profile_lines)

        # 2. Try Ollama local LLM runtime first
        ollama_reply = self._call_ollama(user_query, evidence_text, patient_context_str)
        if ollama_reply:
            return {
                "reply": ollama_reply + self.MANDATORY_SAFETY_DISCLAIMER,
                "citations": citations,
                "grounding_status": "GROUNDED",
                "retrieved_evidence": retrieved_docs,
                "retrieved_docs": retrieved_docs,
                "llm_provider": "ollama",
                "model_used": settings.OLLAMA_MODEL
            }

        # 3. Deterministic Evidence-Only Fallback (transparently labeled)
        points = []
        for doc in retrieved_docs:
            points.append(
                f"• **{doc['organization']}** — *{doc['title']}*:\n"
                f"  {doc['content']}\n"
                f"  *(Citation: {doc.get('source_reference', '')})*"
            )
        structured_evidence = "\n\n".join(points)

        reply_body = (
            f"[System Note: Local LLM runtime (Ollama) unavailable. The following response is a "
            f"deterministic, evidence-grounded summary extracted directly from verified clinical guidelines.]\n\n"
            f"**Verified Clinical Guidelines**:\n\n"
            f"{structured_evidence}\n\n"
            f"**Clinical Summary**: The above verified guidelines address the clinical parameters and travel considerations "
            f"relevant to your query. Consult your treating specialist to align these protocols with your individual clinical plan."
        )

        if patient_context_str:
            reply_body = (
                f"**Patient Clinical Profile Reference**:\n{patient_context_str}\n\n"
                f"{reply_body}"
            )

        return {
            "reply": reply_body + self.MANDATORY_SAFETY_DISCLAIMER,
            "citations": citations,
            "grounding_status": "GROUNDED",
            "retrieved_evidence": retrieved_docs,
            "retrieved_docs": retrieved_docs,
            "llm_provider": "deterministic_evidence_fallback",
            "model_used": "none (deterministic fallback)"
        }

    def query_with_clinical_profile(
        self,
        user_query: str,
        clinical_profile: Dict[str, Any],
        top_k: int = 3,
        threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Fuses a user query with the patient's Phase 3 Shared Clinical Profile context
        to perform evidence-grounded retrieval and synthesis.
        """
        # Formulate augmented search terms fusing patient profile context
        conditions = clinical_profile.get("conditions", [])
        procedures = clinical_profile.get("procedures", [])

        profile_terms = []
        if conditions:
            profile_terms.extend(conditions[:2])
        if procedures:
            profile_terms.extend(procedures[:2])

        # If user query does not mention the patient's condition/procedure, fuse them into search
        combined_search = user_query.strip()
        if profile_terms and not any(term.lower() in user_query.lower() for term in profile_terms):
            combined_search = f"{user_query.strip()} {' '.join(profile_terms)}"

        retrieved = self.retrieve_documents(combined_search, top_k=top_k, threshold=threshold)

        if not retrieved and profile_terms:
            # Fallback search directly on primary patient condition
            retrieved = self.retrieve_documents(f"{profile_terms[0]} clinical travel guidelines", top_k=top_k, threshold=threshold)

        return self.generate_response(
            user_query=user_query,
            retrieved_docs=retrieved,
            clinical_profile=clinical_profile
        )

    def ground_clinical_profile(
        self,
        clinical_profile: Dict[str, Any],
        top_k: int = 2
    ) -> Dict[str, Any]:
        """
        Grounds the conditions and procedures present in a Phase 3 Clinical Profile
        against authoritative medical guidelines.
        """
        conditions = clinical_profile.get("conditions", [])
        procedures = clinical_profile.get("procedures", [])
        demographics = clinical_profile.get("demographics", {})

        all_matches = []
        seen_titles = set()

        for term in conditions + procedures:
            docs = self.retrieve_documents(f"{term} clinical travel guidelines", top_k=top_k, threshold=0.35)
            for d in docs:
                if d["title"] not in seen_titles:
                    seen_titles.add(d["title"])
                    all_matches.append(d)

        citations = [f"{d['organization']}: {d['title']}" for d in all_matches]

        return {
            "grounding_status": "GROUNDED" if all_matches else "NO_MATCH",
            "matched_guidelines": all_matches,
            "citations": citations,
            "patient_conditions_evaluated": conditions,
            "patient_procedures_evaluated": procedures
        }

    def ground_report_analysis(
        self,
        report_text: str,
        entities: List[Dict[str, Any]],
        specialty: str,
        clinical_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Grounds an uploaded medical report with verified clinical travel guidelines
        derived strictly from extracted conditions and specialty, contextualized
        with the patient's authenticated clinical profile (chronic conditions, age group,
        high-impact medications, prior clinical history, and allergy guardrails).
        NEVER invents or injects unmentioned findings into the report itself.
        """
        diseases = [e["entity_name"] for e in entities if e.get("entity_type") == "Disease"]
        procedures = [e["entity_name"] for e in entities if e.get("entity_type") == "Procedure"]

        query_terms = [specialty]
        if diseases:
            query_terms.extend(diseases[:2])
        if procedures:
            query_terms.extend(procedures[:2])

        profile_context_summary = {}
        retrieval_influences = []

        if clinical_profile:
            demographics = clinical_profile.get("demographics", {})
            if not isinstance(demographics, dict):
                demographics = {}

            # 1. Age & Age-Group Stratification (Geriatric / Pediatric travel guidelines)
            age = demographics.get("age") or clinical_profile.get("age")
            if age is not None:
                profile_context_summary["age"] = age
                if age >= 65:
                    profile_context_summary["age_group"] = "geriatric"
                    query_terms.append("geriatric elderly")
                    retrieval_influences.append("age_group: geriatric")
                elif age < 18:
                    profile_context_summary["age_group"] = "pediatric"
                    query_terms.append("pediatric")
                    retrieval_influences.append("age_group: pediatric")
                else:
                    profile_context_summary["age_group"] = "adult"
                    # Adult age numbers not injected to avoid vector token pollution

            # 2. Gender (Demographic context; not injected into query to avoid vector dilution)
            gender = demographics.get("gender") or clinical_profile.get("gender")
            if gender:
                profile_context_summary["gender"] = gender

            # 3. Chronic Conditions / Comorbidities (High clinical relevance for travel risk)
            raw_conds = clinical_profile.get("chronic_conditions") or clinical_profile.get("conditions")
            if not raw_conds:
                raw_conds = demographics.get("chronic_conditions")
            if isinstance(raw_conds, str):
                conds_list = [c.strip() for c in raw_conds.split(",") if c.strip() and c.lower() != "none"]
            elif isinstance(raw_conds, list):
                conds_list = [str(c).strip() for c in raw_conds if str(c).strip() and str(c).lower() != "none"]
            else:
                conds_list = []
            if conds_list:
                profile_context_summary["chronic_conditions"] = conds_list
                for c in conds_list[:2]:
                    if not any(c.lower() in d.lower() for d in diseases):
                        query_terms.append(c)
                        retrieval_influences.append(f"chronic_condition: {c}")

            # 4. Medical History / Prior Interventions (e.g. Prior CABG, Stent, Pacemaker)
            raw_history = clinical_profile.get("medical_history") or demographics.get("medical_history")
            if isinstance(raw_history, str):
                history_list = [h.strip() for h in raw_history.split(",") if h.strip() and h.lower() != "none"]
            elif isinstance(raw_history, list):
                history_list = [str(h).strip() for h in raw_history if str(h).strip() and str(h).lower() != "none"]
            else:
                history_list = []
            if history_list:
                profile_context_summary["medical_history"] = history_list
                # Prior surgical/procedural history has significant travel clearance impact
                for h in history_list[:2]:
                    if not any(h.lower() in p.lower() for p in procedures) and not any(h.lower() in d.lower() for d in diseases):
                        query_terms.append(h)
                        retrieval_influences.append(f"medical_history: {h}")

            # 5. Medications (High-impact travel/procedure medications: anticoagulants, insulin)
            raw_meds = clinical_profile.get("medications") or demographics.get("medications")
            if isinstance(raw_meds, str):
                meds_list = [m.strip() for m in raw_meds.split(",") if m.strip() and m.lower() != "none"]
            elif isinstance(raw_meds, list):
                meds_list = [str(m).strip() for m in raw_meds if str(m).strip() and str(m).lower() != "none"]
            else:
                meds_list = []
            if meds_list:
                profile_context_summary["medications"] = meds_list
                # Selectively incorporate high-impact travel-risk medications
                high_impact_keywords = ["warfarin", "apixaban", "heparin", "enoxaparin", "blood thinner", "anticoagulant", "insulin", "clopidogrel"]
                for med in meds_list:
                    med_lower = med.lower()
                    if any(hk in med_lower for hk in high_impact_keywords):
                        query_terms.append(med)
                        retrieval_influences.append(f"high_impact_medication: {med}")
                        break

            # 6. Allergies (Evaluated as safety guardrails, NOT injected into vector query)
            raw_allergies = clinical_profile.get("allergies") or demographics.get("allergies")
            if isinstance(raw_allergies, str):
                allergies_list = [a.strip() for a in raw_allergies.split(",") if a.strip() and a.lower() != "none"]
            elif isinstance(raw_allergies, list):
                allergies_list = [str(a).strip() for a in raw_allergies if str(a).strip() and str(a).lower() != "none"]
            else:
                allergies_list = []
            if allergies_list:
                profile_context_summary["allergies"] = allergies_list

            profile_context_summary["retrieval_influences"] = retrieval_influences

        query_terms.append("travel clearance clinical guidelines")
        search_query = " ".join(query_terms)
        retrieved = self.retrieve_documents(search_query, top_k=3, threshold=0.25)

        if not retrieved:
            retrieved = self.retrieve_documents(f"{specialty} medical travel guidelines", top_k=2, threshold=0.20)

        allergy_warnings = []
        if retrieved:
            top = retrieved[0]
            grounding_text = (
                f"Verified Clinical Guideline ({top['organization']} - {top['title']}): "
                f"\"{top['content']}\" (Ref: {top.get('source_reference', '')})"
            )
            if profile_context_summary.get("chronic_conditions"):
                grounding_text += f" [Comorbidity Context Evaluated: {', '.join(profile_context_summary['chronic_conditions'])}]"
            if profile_context_summary.get("medical_history"):
                grounding_text += f" [Prior Clinical History: {', '.join(profile_context_summary['medical_history'])}]"
            if profile_context_summary.get("medications"):
                grounding_text += f" [Active Medications: {', '.join(profile_context_summary['medications'])}]"
            if profile_context_summary.get("allergies"):
                grounding_text += f" [Documented Allergies: {', '.join(profile_context_summary['allergies'])}]"

            # Allergy Safety Guardrail: Scan retrieved guidelines against documented allergies
            if profile_context_summary.get("allergies"):
                corpus_to_check = f"{top['title']} {top.get('content', '')}".lower()
                for allergy in profile_context_summary["allergies"]:
                    a_clean = allergy.strip().lower()
                    if a_clean and a_clean != "none":
                        pattern = r"\b" + re.escape(a_clean) + r"\b"
                        if re.search(pattern, corpus_to_check):
                            warn_msg = f"⚠️ [Allergy Alert: Guideline references documented allergen '{allergy}']"
                            allergy_warnings.append(allergy)
                            grounding_text += f" {warn_msg}"
                            break

            sources = [{
                "title": r["title"],
                "organization": r["organization"],
                "source_reference": r.get("source_reference", ""),
                "reference_url": r.get("reference_url", ""),
                "score": r.get("score", 0.0)
            } for r in retrieved]
        else:
            grounding_text = "No direct verified guideline match found for this specific condition."
            sources = []

        if allergy_warnings:
            profile_context_summary["allergy_warnings"] = allergy_warnings

        return {
            "grounding_notes": grounding_text,
            "grounding_sources": sources,
            "patient_context_applied": profile_context_summary if profile_context_summary else None
        }


# Maintain HybridRAGEngine alias for backwards compatibility
HybridRAGEngine = SemanticRAGEngine
rag_engine = SemanticRAGEngine()
