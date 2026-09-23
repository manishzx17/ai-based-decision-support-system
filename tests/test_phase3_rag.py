import sys
import os
import pytest

# Add project root and backend to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from ai.rag_engine import rag_engine, SemanticRAGEngine
from datasets.seed_data import SEED_KNOWLEDGE_BASE


def test_semantic_retrieval_cardiology():
    """Verifies that cardiology travel queries semantically retrieve ESC/AHA/IATA cardiology guidelines."""
    query = "Can a patient travel by flight after undergoing angioplasty with stent placement?"
    results = rag_engine.retrieve_documents(query, top_k=3)

    assert len(results) > 0, "Should retrieve at least one cardiology guideline chunk"
    top_result = results[0]
    assert top_result["category"] == "Cardiology"
    assert any(term in top_result["title"].lower() for term in ["coronary", "angioplasty", "stent", "aviation", "fitness"])
    assert top_result["score"] >= 0.40, f"Expected strong semantic similarity (>=0.40), got {top_result['score']}"
    assert "source_reference" in top_result
    assert "organization" in top_result


def test_semantic_retrieval_orthopedics():
    """Verifies that orthopedics mobility and flight queries retrieve AAOS/BOA joint replacement guidelines."""
    query = "What precautions are needed for deep vein thrombosis when flying after knee replacement?"
    results = rag_engine.retrieve_documents(query, top_k=3)

    assert len(results) > 0
    categories = [r["category"] for r in results]
    assert "Orthopedics" in categories
    assert any("thrombo" in r["title"].lower() or "knee" in r["title"].lower() for r in results)
    assert results[0]["score"] >= 0.40


def test_semantic_retrieval_neurosurgery():
    """Verifies that neurosurgical craniotomy queries retrieve CNS/AAN pneumocephalus guidelines."""
    query = "How long must a patient wait before flying after craniotomy for brain tumor resection?"
    results = rag_engine.retrieve_documents(query, top_k=3)

    assert len(results) > 0
    top = results[0]
    assert top["category"] == "Neurology"
    assert "craniotomy" in top["title"].lower() or "pneumocephalus" in top["content"].lower()
    assert top["score"] >= 0.45


def test_unrelated_query_refusal_and_threshold_tuning():
    """
    Validation/Tuning Test:
    Demonstrates empirical score separation between in-domain medical queries
    and completely out-of-domain / unsupported questions, verifying non-fabrication.
    """
    # In-domain medical queries
    in_domain = "chemotherapy nadir infection precautions for flights"
    in_results = rag_engine.retrieve_documents(in_domain, top_k=1, threshold=0.0)
    in_score = in_results[0]["score"] if in_results else 0.0

    # Unrelated queries
    unrelated_queries = [
        "How do I repair a leaking car radiator?",
        "What is the best recipe for Italian pasta carbonara?",
        "Who won the 2022 football championship tournament?"
    ]

    print(f"\n[Threshold Tuning Observation] In-domain query score: {in_score:.4f}")
    assert in_score >= 0.45, f"In-domain score should be >= 0.45, got {in_score}"

    for uq in unrelated_queries:
        # Check raw score without threshold
        raw_results = rag_engine.retrieve_documents(uq, top_k=1, threshold=0.0)
        raw_score = raw_results[0]["score"] if raw_results else 0.0
        print(f"[Threshold Tuning Observation] Out-of-domain '{uq[:30]}...' score: {raw_score:.4f}")
        
        # Raw score must be significantly lower than in-domain
        assert raw_score < 0.20, f"Unrelated query scored unexpectedly high: {raw_score}"

        # With default engineering threshold (0.38), retrieval must return empty
        filtered = rag_engine.retrieve_documents(uq, top_k=3)
        assert len(filtered) == 0, f"Unrelated query must be filtered out, got {len(filtered)} results"

        # Generation must refuse to fabricate
        resp = rag_engine.generate_response(uq, filtered)
        assert resp["grounding_status"] == "INSUFFICIENT_EVIDENCE"
        assert len(resp["citations"]) == 0
        assert "insufficient verified clinical evidence" in resp["reply"].lower()


def test_persistent_faiss_index_integrity():
    """Verifies persistent FAISS index and chunk metadata exist on disk and reload cleanly."""
    storage_dir = os.path.join(BACKEND_DIR, "ai", "rag_storage")
    index_file = os.path.join(storage_dir, "faiss_index.bin")
    chunks_file = os.path.join(storage_dir, "chunks.json")
    hash_file = os.path.join(storage_dir, "corpus_hash.txt")

    assert os.path.exists(index_file), "faiss_index.bin must exist on disk"
    assert os.path.exists(chunks_file), "chunks.json must exist on disk"
    assert os.path.exists(hash_file), "corpus_hash.txt must exist on disk"

    # Instantiate a second engine instance and verify it loads directly from disk
    new_engine = SemanticRAGEngine()
    assert new_engine.index is not None
    assert len(new_engine.chunks) >= len(SEED_KNOWLEDGE_BASE)


def test_grounded_generation_citations():
    """Verifies that generated responses cite supporting clinical organizations and references."""
    query = "Is DAPT compliance mandatory after coronary stent placement for travel?"
    retrieved = rag_engine.retrieve_documents(query, top_k=2)
    assert len(retrieved) > 0

    response = rag_engine.generate_response(query, retrieved, report_context="Patient: 48M with LAD 85% Stenosis")
    assert response["grounding_status"] == "GROUNDED"
    assert len(response["citations"]) > 0
    assert any("ESC" in c or "ACC" in c or "Cardiology" in c for c in response["citations"])
    assert "Medical Safety Disclaimer" in response["reply"]


def test_report_analysis_guideline_grounding():
    """Verifies that report analysis grounds extracted findings with verified guidelines."""
    entities = [
        {"entity_type": "Disease", "entity_name": "Coronary Artery Disease"},
        {"entity_type": "Procedure", "entity_name": "Percutaneous Coronary Intervention"}
    ]
    grounding = rag_engine.ground_report_analysis(
        report_text="Impression: Severe CAD. Advised elective PCI.",
        entities=entities,
        specialty="Cardiology"
    )

    assert "grounding_notes" in grounding
    assert len(grounding["grounding_notes"]) > 20
    assert len(grounding["grounding_sources"]) > 0
    assert "European Society of Cardiology" in grounding["grounding_notes"] or "ACC" in grounding["grounding_notes"] or "IATA" in grounding["grounding_notes"]


def test_chat_api_endpoint_rag_integration():
    """Verifies the FastAPI /api/services/chat endpoint with genuine semantic RAG."""
    from fastapi.testclient import TestClient
    from main import app
    from init_db import init_db
    init_db()

    with TestClient(app) as client:
        # In-domain query
        resp = client.post("/api/services/chat?user_id=1", json={
            "message": "Can I travel by airplane after stent placement?"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["grounding_status"] == "GROUNDED"
        assert len(data["citations"]) > 0
        assert len(data["retrieved_evidence"]) > 0

        # Out-of-domain query
        resp_unrelated = client.post("/api/services/chat?user_id=1", json={
            "message": "How do I fix a broken car engine crankshaft?"
        })
        assert resp_unrelated.status_code == 200
        unrelated_data = resp_unrelated.json()
        assert unrelated_data["grounding_status"] == "INSUFFICIENT_EVIDENCE"
        assert len(unrelated_data["citations"]) == 0
        assert "insufficient verified clinical evidence" in unrelated_data["reply"].lower()


if __name__ == "__main__":
    pytest.main(["-v", __file__])
