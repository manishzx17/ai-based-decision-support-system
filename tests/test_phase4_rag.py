"""
Phase 4 — Medical Knowledge + RAG Test Suite
Validates:
1. Knowledge-document ingestion and validation
2. Chunking and Sentence Transformer embeddings
3. FAISS retrieval and persistent storage
4. Retrieval relevance across Phase 2 clinical specialties
5. Citation and source preservation
6. Clinical Profile -> RAG context flow
7. Insufficient-evidence / no-fabrication refusal behavior
8. Ollama local LLM runtime integration and transparent fallback
"""

import sys
import os
import json
import pytest
from fastapi.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from ai.rag_engine import rag_engine, SemanticRAGEngine
from datasets.medical_knowledge.ingest import (
    load_knowledge_dataset,
    validate_document,
    chunk_document,
    compute_dataset_hash
)
from init_db import init_db
from database import SessionLocal
from models import User, PatientProfile
from main import app


@pytest.fixture(scope="module", autouse=True)
def setup_test_environment():
    init_db()
    db = SessionLocal()
    user = db.query(User).filter(User.id == 1).first()
    if not user:
        user = User(id=1, email="rag_test@example.com", hashed_password="pw", full_name="RAG Test Patient", role="patient")
        db.add(user)
        db.commit()

    profile = db.query(PatientProfile).filter(PatientProfile.user_id == 1).first()
    if not profile:
        profile = PatientProfile(
            user_id=1,
            age=58,
            gender="Male",
            conditions=["Coronary Artery Disease", "Angina Pectoris"],
            symptoms=["chest pain", "exertional dyspnea"],
            medications=["Aspirin 75mg OD", "Atorvastatin 40mg HS"],
            procedures=["Percutaneous Coronary Intervention"],
            current_city="Hyderabad"
        )
        db.add(profile)
        db.commit()
    db.close()


# 1. Test Knowledge Document Ingestion
def test_knowledge_document_ingestion():
    """Verifies that Dataset 2 loads cleanly and all documents adhere to the authoritative schema."""
    dataset_path = os.path.join(BACKEND_DIR, "datasets", "medical_knowledge", "medical_knowledge_dataset.json")
    assert os.path.exists(dataset_path), "medical_knowledge_dataset.json must exist"

    docs = load_knowledge_dataset(dataset_path)
    assert len(docs) >= 25, f"Expected 25-50 authoritative documents, got {len(docs)}"

    specialties = set()
    for idx, doc in enumerate(docs):
        assert validate_document(doc, idx) is True
        specialties.add(doc["specialty"])
        # Verify traceability
        assert doc["source_reference"], f"Doc {doc['id']} missing source reference"
        assert doc["reference_url"].startswith("http"), f"Doc {doc['id']} must have valid HTTP reference URL"

    expected_specialties = ["Cardiology", "Oncology", "Orthopedics", "Neurology", "Gastroenterology", "Nephrology", "Pulmonology"]
    for s in expected_specialties:
        assert any(s.lower() in spec.lower() for spec in specialties), f"Missing coverage for specialty {s}"


# 2. Test Chunking and Embedding Generation
def test_chunking_and_embedding_dimensions():
    """Verifies document chunking preserves metadata and produces 384-dimensional dense vectors."""
    sample_doc = {
        "id": 101,
        "title": "Clinical Guidance on Coronary Angioplasty",
        "specialty": "Cardiology",
        "organization": "European Society of Cardiology (ESC)",
        "source_reference": "Knuuti et al., 2019 ESC Guidelines",
        "reference_url": "https://doi.org/10.1093/eurheartj/ehz425",
        "clinical_evidence_level": "Class I, Level A",
        "content": (
            "Patients undergoing uncomplicated Percutaneous Coronary Intervention (PCI) with stent placement "
            "may safely travel 3 to 5 days post-procedure. Strict adherence to Dual Antiplatelet Therapy is mandatory. "
            "Heavy exertion and lifting baggage exceeding 5 kg should be avoided for 14 days."
        )
    }

    chunks = chunk_document(sample_doc)
    assert len(chunks) >= 1
    chunk = chunks[0]

    assert chunk["title"] == sample_doc["title"]
    assert chunk["organization"] == sample_doc["organization"]
    assert chunk["source_reference"] == sample_doc["source_reference"]
    assert chunk["reference_url"] == sample_doc["reference_url"]
    assert chunk["specialty"] == "Cardiology"

    # Verify embeddings
    model = rag_engine.get_embedding_model() if hasattr(rag_engine, "get_embedding_model") else None
    if model is None:
        from ai.rag_engine import get_embedding_model
        model = get_embedding_model()

    emb = model.encode([chunk["content"]], normalize_embeddings=True)
    assert emb.shape == (1, 384), f"Expected shape (1, 384), got {emb.shape}"


# 3. Test FAISS Retrieval & Storage
def test_faiss_retrieval_and_persistence():
    """Verifies persistent FAISS IndexFlatIP index exists and loads cleanly."""
    storage_dir = os.path.join(BACKEND_DIR, "ai", "rag_storage")
    index_file = os.path.join(storage_dir, "faiss_index.bin")
    chunks_file = os.path.join(storage_dir, "chunks.json")
    hash_file = os.path.join(storage_dir, "corpus_hash.txt")

    assert os.path.exists(index_file), "faiss_index.bin must exist on disk"
    assert os.path.exists(chunks_file), "chunks.json must exist on disk"
    assert os.path.exists(hash_file), "corpus_hash.txt must exist on disk"

    # Instantiate fresh engine to test clean disk loading
    engine = SemanticRAGEngine()
    assert engine.index is not None
    assert engine.index.ntotal > 0
    assert len(engine.chunks) == engine.index.ntotal


# 4. Test Retrieval Relevance Across Phase 2 Specialties
def test_retrieval_relevance_representative_queries():
    """Tests semantic retrieval across diverse Phase 2 clinical domains."""
    test_cases = [
        ("flight safety after coronary angioplasty stent", "Cardiology", 0.50),
        ("chemotherapy neutropenia infection fever travel precautions", "Oncology", 0.50),
        ("deep vein thrombosis prevention flying after knee replacement", "Orthopedics", 0.50),
        ("craniotomy intracranial pressure pneumocephalus flight timing", "Neurology", 0.50),
        ("upper endoscopy peptic ulcer bleeding travel clearance", "Gastroenterology", 0.50),
        ("chronic kidney disease stage 4 creatinine travel", "Nephrology", 0.45),
        ("COPD in flight hypoxemia portable oxygen concentrator", "Pulmonology", 0.50),
        ("insulin carry-on baggage crossing time zones with diabetes", "General Medicine", 0.50),
    ]

    for query, expected_specialty, min_score in test_cases:
        results = rag_engine.retrieve_documents(query, top_k=2)
        assert len(results) > 0, f"Query '{query}' failed to retrieve documents"
        top = results[0]
        assert top["score"] >= min_score, f"Query '{query}' score {top['score']} < {min_score}"
        spec_text = (top.get("specialty", "") + " " + top.get("category", "")).lower()
        assert expected_specialty.lower() in spec_text or any(w in top["title"].lower() for w in query.split()[:2]), \
            f"Expected specialty {expected_specialty} in top result: {top['title']}"


# 5. Test Citation and Source Preservation
def test_citation_and_source_preservation():
    """Verifies that generated answers cite authoritative organizations and real references."""
    query = "What is the recommended wait time before flying after craniotomy?"
    docs = rag_engine.retrieve_documents(query, top_k=2)
    assert len(docs) > 0

    response = rag_engine.generate_response(query, docs)
    assert response["grounding_status"] == "GROUNDED"
    assert len(response["citations"]) > 0
    assert any("CNS" in c or "Congress of Neurological Surgeons" in c for c in response["citations"])
    assert "Medical Safety Disclaimer" in response["reply"]


# 6. Test Clinical Profile -> RAG Context Flow
def test_clinical_profile_rag_context_flow():
    """Verifies that Phase 3 Shared Clinical Profile informs RAG retrieval and synthesis."""
    profile = {
        "conditions": ["Total Knee Arthroplasty", "Osteoarthritis"],
        "procedures": ["Total Knee Replacement"],
        "medications": ["Enoxaparin 40mg", "Paracetamol 1g"],
        "demographics": {"age": 64, "gender": "Female"}
    }

    # Query without explicit condition mention in user query
    user_query = "What precautions should I take during a 5 hour flight?"
    response = rag_engine.query_with_clinical_profile(user_query, profile, top_k=2)

    assert response["grounding_status"] == "GROUNDED"
    assert len(response["citations"]) > 0
    # The augmented search should find orthopedic DVT / arthroplasty guidelines
    citations_str = " ".join(response["citations"]).lower()
    assert "orthop" in citations_str or "aaos" in citations_str or "knee" in citations_str or "thrombo" in citations_str


# 7. Test Insufficient-Evidence & No-Fabrication Refusal Behavior
def test_insufficient_evidence_and_no_fabrication():
    """Verifies that out-of-domain / unsupported queries refuse to fabricate."""
    unrelated_queries = [
        "How do I repair a leaking bathroom pipe in my apartment?",
        "What are the best places to visit in Paris for sightseeing?",
        "How do I assemble an IKEA wooden dining table?"
    ]

    for q in unrelated_queries:
        # Check retrieval returns empty because of similarity threshold
        filtered = rag_engine.retrieve_documents(q, top_k=3)
        assert len(filtered) == 0, f"Unrelated query '{q}' should not pass relevance threshold"

        # Check generation produces safe refusal
        resp = rag_engine.generate_response(q, filtered)
        assert resp["grounding_status"] == "INSUFFICIENT_EVIDENCE"
        assert len(resp["citations"]) == 0
        assert resp["llm_provider"] == "none"
        assert "insufficient verified clinical evidence" in resp["reply"].lower()
        assert "refuses to fabricate" in resp["reply"].lower()


# 8. Test Deterministic Fallback Transparency
def test_deterministic_fallback_transparency():
    """Verifies clear distinction when Ollama is unavailable: returns deterministic evidence with visible system note."""
    query = "Can a patient fly with asthma?"
    docs = rag_engine.retrieve_documents(query, top_k=2)
    assert len(docs) > 0

    # Temporarily mock _call_ollama to simulate Ollama being unreachable
    original_call = rag_engine._call_ollama
    try:
        rag_engine._call_ollama = lambda *args, **kwargs: None
        response = rag_engine.generate_response(query, docs)

        assert response["grounding_status"] == "GROUNDED"
        assert response["llm_provider"] == "deterministic_evidence_fallback"
        assert response["model_used"] == "none (deterministic fallback)"
        assert "[System Note: Local LLM runtime (Ollama) unavailable" in response["reply"]
        assert len(response["citations"]) > 0
    finally:
        rag_engine._call_ollama = original_call


# 9. Test API Endpoints (/services/rag/query and /services/rag/profile-grounding)
def test_rag_api_endpoints():
    """Verifies FastAPI RAG endpoints work end-to-end with the application."""
    from security import create_access_token
    token = create_access_token(data={"sub": "1", "email": "rahul.verma@example.com", "role": "patient"})
    headers = {"Authorization": f"Bearer {token}"}
    with TestClient(app) as client:
        # In-domain query endpoint
        resp = client.post("/api/services/rag/query?user_id=1", json={
            "query": "Can I travel by flight 4 days after coronary stent placement?",
            "use_clinical_profile": True
        }, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["grounding_status"] == "GROUNDED"
        assert len(data["citations"]) > 0
        assert len(data["retrieved_evidence"]) > 0
        assert data["llm_provider"] in ["ollama", "deterministic_evidence_fallback"]

        # Out-of-domain query endpoint
        ood_resp = client.post("/api/services/rag/query?user_id=1", json={
            "query": "What is the capital city of Australia?",
            "use_clinical_profile": False
        }, headers=headers)
        assert ood_resp.status_code == 200
        ood_data = ood_resp.json()
        assert ood_data["grounding_status"] == "INSUFFICIENT_EVIDENCE"
        assert len(ood_data["citations"]) == 0

        # Profile grounding endpoint
        pg_resp = client.post("/api/services/rag/profile-grounding", json={
            "user_id": 1,
            "top_k": 2
        }, headers=headers)
        assert pg_resp.status_code == 200
        pg_data = pg_resp.json()
        assert pg_data["grounding_status"] in ["GROUNDED", "NO_MATCH"]
        assert "patient_conditions_evaluated" in pg_data


if __name__ == "__main__":
    pytest.main(["-v", __file__])
