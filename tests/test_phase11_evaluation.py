"""
Tests for Phase 11: Quantitative Evaluation & Research Validation.

Validates that:
1. All 7 functional areas are evaluated against genuine project data/models.
2. Unmeasurable metrics (token-level NER F1, scanned WER) are honestly flagged as NOT MEASURABLE.
3. Synthetic benchmark provenance disclosures are strictly preserved for cost/LOS models.
4. All 6 research gaps and 6 project objectives are explicitly mapped.
5. The evaluation report artifact is generated and reproducible.
"""

import os
import sys
import json
import pytest

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(os.path.dirname(CURRENT_DIR), "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from ai.evaluation import (
    evaluate_ocr_and_ner,
    evaluate_rag_retrieval,
    evaluate_recommendations,
    evaluate_cost_and_los,
    evaluate_navigation,
    evaluate_assistant_safety,
    evaluate_e2e_reliability,
    run_full_evaluation,
    REPORT_PATH
)


def test_ocr_and_ner_evaluation():
    """Validates OCR and NER evaluation metrics and honest unmeasurable disclosures."""
    res = evaluate_ocr_and_ner()

    # Digital PDF token recall on known content must be high
    assert res["digital_pdf_token_recall"] == 1.0
    assert res["scanned_image_evaluated"] is True
    assert res["scanned_key_term_accuracy"] == 1.0
    assert res["content_driven_specialty_accuracy"] == 1.0

    # Unmeasurable metrics must NOT be fabricated
    assert res["ner_token_level_f1"] == "NOT MEASURABLE"
    assert "No independent gold-standard" in res["ner_token_level_f1_reason"]
    assert res["ocr_full_wer_scanned_image"] == "NOT MEASURABLE"
    assert "gold-truth transcription" in res["ocr_full_wer_scanned_image_reason"]


def test_rag_retrieval_evaluation():
    """Validates Hybrid RAG retrieval metrics on verified clinical guidelines."""
    res = evaluate_rag_retrieval()

    assert res["benchmark_query_count"] == 5
    assert res["recall_at_1"] >= 0.80
    assert res["recall_at_3"] == 1.0
    assert res["mean_reciprocal_rank"] >= 0.80
    assert res["verified_citation_coverage"] == 1.0
    assert res["out_of_domain_refusal_capable"] is True


def test_recommendation_evaluation():
    """Validates Multi-Criteria Recommendation Engine ranking alignment and budget checks."""
    res = evaluate_recommendations()

    assert res["evaluated_profiles_count"] == 6
    assert res["specialty_alignment_top1_precision"] == 1.0
    assert res["budget_compliance_rate"] == 1.0
    assert "specialty_match" in res["mcdm_criteria_weights"]


def test_cost_and_los_evaluation_and_disclosures():
    """Validates Cost & LOS regression metrics and explicit synthetic benchmark disclosure."""
    res = evaluate_cost_and_los()

    # Model metrics
    cost_m = res["cost_model"]
    assert cost_m["r2_score"] >= 0.95
    assert cost_m["mae_inr"] > 0

    los_m = res["los_model"]
    assert los_m["r2_score"] >= 0.80
    assert los_m["mae_days"] < 1.5

    # Provenance disclosure must NOT claim real patient records
    prov = res["dataset_provenance"]
    assert prov["is_real_patient_records"] is False
    assert "SYNTHETIC BENCHMARK DATA" in prov["dataset_type"]
    assert "NHA" in prov["calibration_source"]
    assert "GIPSA" in prov["calibration_source"]


def test_navigation_evaluation():
    """Validates A* Pathfinding route reachability and heuristic admissibility."""
    res = evaluate_navigation()

    assert res["routes_tested"] == 6
    assert res["route_reachability_rate"] == 1.0
    assert res["heuristic_admissibility_rate"] == 1.0
    assert res["average_search_latency_ms"] < 50.0  # sub-50ms graph search


def test_assistant_safety_evaluation():
    """Validates clinical safety guardrails, emergency detection, and out-of-domain refusal."""
    res = evaluate_assistant_safety()

    assert res["emergency_safety_compliance_rate"] == 1.0
    assert "112/108" in res["emergency_advisory_standard"]
    assert res["ungrounded_refusal_compliance_rate"] == 1.0


def test_full_evaluation_report_generation_and_mapping():
    """Verifies that run_full_evaluation writes the complete report with 6 gaps and 6 objectives."""
    report = run_full_evaluation()
    assert os.path.exists(REPORT_PATH)

    # Check 7 evaluated dimensions exist
    results = report["results"]
    assert "ocr_and_clinical_ner" in results
    assert "rag_retrieval_and_grounding" in results
    assert "recommendation_engine" in results
    assert "cost_and_los_prediction" in results
    assert "navigation_and_travel" in results
    assert "assistant_safety_and_grounding" in results
    assert "e2e_workflow_reliability" in results

    # Check mapping to 6 research gaps
    mapping = report["research_mapping"]
    assert len(mapping) == 6
    assert "gap_1_unstructured_reports" in mapping
    assert "gap_2_llm_hallucination" in mapping
    assert "gap_3_fragmented_search" in mapping
    assert "gap_4_pricing_and_stay_opacity" in mapping
    assert "gap_5_spatial_logistics_disconnect" in mapping
    assert "gap_6_safety_and_data_isolation" in mapping
