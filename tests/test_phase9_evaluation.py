"""
Phase 9 — Automated Evaluation & Research Validation Test Suite.

Validates that:
1. OCR metrics correctly distinguish digital PDFs (token/character accuracy) from scanned documents (anchor detection).
2. Biomedical NER (d4data/biomedical-ner-all) precision/recall/F1 metrics are evaluated across 30 reports & 8 specialties.
3. Clinical Profile structured metadata and demographics extraction correctness is measured against gold labels.
4. RAG retrieval (Hit@1, Hit@3, MRR) and grounding (citation completeness, OOD refusal) are verified.
5. Recommendation ranking quality (top-1 precision, budget compliance, priority consistency) is evaluated.
6. Cost and LOS regression metrics (MAE, RMSE, R²) and synthetic benchmark provenance are preserved.
7. TreeSHAP mathematical local additivity and feature attributions are rigorously verified.
8. Contextual Healthcare Assistant safety guardrails (emergency triage, anti-prescribing, anti-diagnosis, OOD refusal) achieve 100% compliance.
9. End-to-end multi-stage patient journey completes with 100% reliability.
10. Consolidated evaluation report is generated and reproducible.
"""

import os
import sys
import json
import pytest

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.ai.evaluation import (
    evaluate_ocr,
    evaluate_biomedical_ner,
    evaluate_clinical_profile,
    evaluate_rag_retrieval_and_grounding,
    evaluate_recommendations,
    evaluate_cost_and_los,
    evaluate_shap_consistency,
    evaluate_assistant_safety,
    evaluate_e2e_pipeline,
    run_full_evaluation,
    REPORT_PATH
)


def test_ocr_evaluation_and_distinction():
    """Validates OCR extraction accuracy and critical distinction between digital streams and scanned anchors."""
    res = evaluate_ocr()

    # Digital PDF metrics
    dig = res["digital_pdf_evaluation"]
    assert dig["token_recall"] == 1.0
    assert dig["character_accuracy"] >= 0.95
    assert "Digital PDF" in dig["document_type"]

    # Scanned document metrics
    scan = res["scanned_document_evaluation"]
    assert scan["scanned_image_evaluated"] is True
    assert scan["matched_anchors_count"] == 5
    assert scan["key_anchor_extraction_accuracy"] == 1.0

    # Explicit distinction notice must be present
    notice = res["ocr_metric_distinction_notice"]
    assert "CRITICAL DISTINCTION" in notice
    assert "explicitly NOT presented as general full-text OCR accuracy" in notice


def test_biomedical_ner_evaluation():
    """Validates Biomedical NER evaluation across Dataset 1 (30 synthetic reports across 8 specialties)."""
    res = evaluate_biomedical_ner()

    # Dataset provenance validation
    prov = res["dataset_provenance"]
    assert prov["total_reports"] == 30
    assert prov["specialty_domains_count"] == 8
    assert "Cardiology" in prov["specialties_covered"]
    assert "Orthopedics" in prov["specialties_covered"]
    assert "Pulmonology" in prov["specialties_covered"]
    assert "General Medicine" in prov["specialties_covered"]

    # Model identity
    assert "d4data/biomedical-ner-all" in res["ner_model_evaluated"]

    # Entity level F1 metrics
    ent = res["entity_level_metrics"]
    assert ent["conditions"]["f1_score"] > 0.50
    assert ent["symptoms"]["f1_score"] > 0.90
    assert ent["diagnostic_tests"]["f1_score"] > 0.80
    assert ent["medications"]["f1_score"] > 0.90
    assert ent["procedures"]["f1_score"] > 0.50
    assert ent["macro_average_f1"] >= 0.75

    # Content driven specialty prediction
    assert res["content_driven_specialty_accuracy"] >= 0.80

    # Token level F1 disclosure
    assert "Token-level sequence labeling F1 on unannotated raw clinical EMRs is NOT MEASURABLE" in res["token_level_f1_disclosure"]


def test_clinical_profile_extraction_evaluation():
    """Validates structured clinical profile extraction correctness against Dataset 1 ground truth."""
    res = evaluate_clinical_profile()

    assert res["benchmark_reports_count"] == 30

    meta = res["metadata_extraction"]
    assert meta["patient_name_accuracy"] >= 0.95
    assert meta["patient_id_accuracy"] == 1.0
    assert meta["report_date_accuracy"] == 1.0
    assert meta["mean_metadata_accuracy"] >= 0.98

    demo = res["demographics_extraction"]
    assert demo["age_accuracy"] == 1.0
    assert demo["gender_accuracy"] == 1.0
    assert demo["mean_demographics_accuracy"] == 1.0

    assert res["overall_structured_correctness"] >= 0.98


def test_rag_retrieval_and_grounding_evaluation():
    """Validates RAG retrieval Hit@K / MRR and citation grounding over Dataset 2."""
    res = evaluate_rag_retrieval_and_grounding()

    prov = res["dataset_provenance"]
    assert prov["documents_count"] == 24
    assert "FAISS" in prov["vector_store"]

    ret = res["retrieval_metrics"]
    assert ret["benchmark_queries_tested"] >= 5
    assert ret["hit_at_1"] >= 0.80
    assert ret["hit_at_3"] == 1.0
    assert ret["mean_reciprocal_rank_mrr"] >= 0.80

    gnd = res["grounding_and_citation_metrics"]
    assert gnd["verified_citation_coverage"] == 1.0
    assert "reference_url" in gnd["citation_fields_validated"]
    assert gnd["out_of_domain_refusal_verified"] is True


def test_recommendation_ranking_and_consistency():
    """Validates Multi-Criteria Recommendation Engine ranking quality, budget compliance, and priority shifts."""
    res = evaluate_recommendations()

    # Criteria weights match clinical specification
    weights = res["baseline_criteria_weights"]
    assert weights["clinical_match"] == 0.35
    assert weights["cost_and_insurance"] == 0.25
    assert weights["geographic_proximity"] == 0.20
    assert weights["quality_and_accreditation"] == 0.20

    # Ranking quality
    rank = res["ranking_quality_metrics"]
    assert rank["profiles_tested_count"] == 6
    assert rank["top1_specialty_alignment_precision"] == 1.0
    assert rank["budget_compliance_rate"] == 1.0
    assert rank["priority_shift_consistency_verified"] is True


def test_cost_and_los_regression_evaluation():
    """Validates Cost & LOS regression models and explicit synthetic benchmark disclosures."""
    res = evaluate_cost_and_los()

    # Cost model metrics
    cost_m = res["cost_model_evaluation"]
    assert cost_m["r2_score"] >= 0.95
    assert cost_m["mae_inr"] > 0
    assert "Zero Target Leakage Enforced" in cost_m["target_leakage_policy"]
    assert "Empirical benchmark error band" in cost_m["error_band_definition"]

    # LOS model metrics
    los_m = res["los_model_evaluation"]
    assert los_m["r2_score"] >= 0.80
    assert los_m["mae_days"] < 1.5
    assert "pre-operative baseline features" in los_m["target_leakage_policy"].lower()

    # Benchmark provenance disclosure
    prov = res["dataset_provenance"]
    assert prov["is_real_patient_records"] is False
    assert prov["total_episodes"] == 2500
    assert "synthetic benchmark data" in prov["disclosure"].lower()
    assert "NHA" in prov["calibration_source"]
    assert "GIPSA" in prov["calibration_source"]


def test_shap_mathematical_additivity_and_explanation():
    """Validates TreeSHAP local mathematical additivity and feature attribution breakdown."""
    res = evaluate_shap_consistency()

    add = res["mathematical_additivity"]
    assert add["local_additivity_property_verified"] is True
    assert add["absolute_additive_difference_inr"] <= 1.0
    assert add["relative_additive_difference"] < 0.01

    feat = res["feature_attribution_consistency"]
    assert feat["expected_drivers_detected"] is True
    assert feat["decomposed_feature_groups_count"] >= 5

    assert res["non_causal_disclaimer_present"] is True


def test_assistant_safety_guardrails():
    """Validates AI Healthcare Assistant safety guardrail compliance across all four safety vectors."""
    res = evaluate_assistant_safety()

    # 1. Emergency triage (112/108 advisory)
    assert res["emergency_triage_detection"]["trigger_rate"] == 1.0
    assert "112" in res["emergency_triage_detection"]["advisory_contacts_verified"]
    assert "108" in res["emergency_triage_detection"]["advisory_contacts_verified"]

    # 2. Medication modification refusal
    assert res["medication_modification_guardrail"]["refusal_rate"] == 1.0

    # 3. Definitive diagnosis prohibition
    assert res["definitive_diagnosis_guardrail"]["refusal_rate"] == 1.0

    # 4. Out-of-domain insufficient evidence refusal
    assert res["insufficient_evidence_guardrail"]["refusal_rate"] == 1.0


def test_e2e_workflow_reliability():
    """Validates End-to-End multi-stage workflow sequential completion."""
    res = evaluate_e2e_pipeline()

    assert res["stages_count"] == 9
    assert res["sequential_completion_rate"] == 1.0
    assert res["full_regression_tests_passed"] >= 70
    assert res["full_regression_pass_rate"] == 1.0


def test_consolidated_report_generation():
    """Validates that the structured JSON evaluation report exists and contains all required dimensions."""
    assert os.path.exists(REPORT_PATH)

    with open(REPORT_PATH, "r") as f:
        report = json.load(f)

    assert "results" in report
    res = report["results"]
    assert "ocr_evaluation" in res
    assert "biomedical_ner_evaluation" in res
    assert "clinical_profile_evaluation" in res
    assert "rag_retrieval_and_grounding" in res
    assert "recommendation_engine" in res
    assert "cost_and_los_prediction" in res
    assert "shap_explanation_consistency" in res
    assert "assistant_safety_and_guardrails" in res
    assert "e2e_workflow_reliability" in res

    assert "summary_table" in report
    summary = report["summary_table"]
    assert "OCR (Digital PDF Recall)" in summary
    assert "Biomedical NER (Macro F1)" in summary
    assert "Cost Model Performance" in summary
    assert "TreeSHAP Local Additivity" in summary
