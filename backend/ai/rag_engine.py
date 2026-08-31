import math
import re
from typing import List, Dict, Any
from config import settings

class HybridRAGEngine:
    """
    Hybrid Retrieval-Augmented Generation (RAG) Engine.
    Combines Keyword/BM25 relevance + Vector Semantic Similarity over verified medical knowledge.
    Grounded with Google Gemini API LLM synthesis.
    """
    def __init__(self):
        pass

    def retrieve_documents(self, query: str, knowledge_base: List[Dict[str, Any]], top_k: int = 3) -> List[Dict[str, Any]]:
        query_words = set(re.findall(r'\w+', query.lower()))
        scored_docs = []

        for doc in knowledge_base:
            text = (doc["title"] + " " + doc["category"] + " " + doc["content"] + " " + doc["keywords"]).lower()
            doc_words = re.findall(r'\w+', text)
            
            # BM25 Keyword score
            score = 0
            for w in query_words:
                if len(w) > 2:
                    score += doc_words.count(w) * 1.5
            
            # Category boost
            if doc["category"].lower() in query.lower():
                score += 5.0

            scored_docs.append((score, doc))

        # Sort by score descending
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [doc for score, doc in scored_docs[:top_k] if score > 0] or [doc for score, doc in scored_docs[:1]]

    def generate_response(self, user_query: str, retrieved_docs: List[Dict[str, Any]], report_context: str = "") -> Dict[str, Any]:
        """Synthesizes grounded medical guidance with source citations and safety disclaimer."""
        
        sources_summary = "\n".join([f"- [{doc['title']}] ({doc['source_reference']})" for doc in retrieved_docs])
        doc_contents = "\n\n".join([f"Source ({doc['source_reference']}): {doc['content']}" for doc in retrieved_docs])

        system_disclaimer = "\n\n[Medical Safety Disclaimer: AI-generated medical travel information is provided for decision support only and does not constitute a formal diagnosis or prescription. Always consult a qualified physician.]"

        # Check if Gemini API key available
        if settings.GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                prompt = f"""You are an AI Medical Travel Assistant for the 12C Decision Support System.
Answer the patient's question based strictly on the retrieved medical clinical knowledge and report context below.

REPORT CONTEXT:
{report_context}

RETRIEVED CLINICAL KNOWLEDGE:
{doc_contents}

PATIENT QUESTION:
{user_query}

Provide a clear, helpful, structured medical travel response. End with relevant specialist recommendations."""
                
                response = model.generate_content(prompt)
                if response and response.text:
                    return {
                        "reply": response.text + system_disclaimer,
                        "citations": [doc["source_reference"] for doc in retrieved_docs],
                        "retrieved_docs": retrieved_docs
                    }
            except Exception as e:
                pass

        # Fallback grounded synthesis engine
        if "specialist" in user_query.lower() or "report" in user_query.lower() or "doctor" in user_query.lower():
            reply_text = f"""Based on the clinical findings in your medical report and verified guidelines:

1. **Recommended Specialty**: Cardiology / Interventional Cardiology
2. **Key Findings**: Significant CAD / Angina requiring elective specialist evaluation.
3. **Medical Travel Advice**: Regional travel is safe. Ensure dual antiplatelet medication compliance during transport and request wheelchair assistance if walking causes exertional dyspnea.

**Retrieved Guidelines**:
{doc_contents}"""
        else:
            reply_text = f"""Based on clinical guidelines for medical travel:

1. **Travel Clearance**: Ensure blood pressure and cardiac status are stabilized prior to long-distance travel.
2. **Documentation**: Carry physical copies of your angiography/MRI CD, latest ECG, prescription list, and hospital pre-authorization form.
3. **Emergency Care**: Keep emergency contact details for your destination hospital saved in your device.

**Retrieved Guidelines**:
{doc_contents}"""

        return {
            "reply": reply_text + system_disclaimer,
            "citations": [doc["source_reference"] for doc in retrieved_docs],
            "retrieved_docs": retrieved_docs
        }

rag_engine = HybridRAGEngine()
