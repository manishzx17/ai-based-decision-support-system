"""
Automated Evaluation Script for Phase 2 — Medical Report Intelligence Benchmark
Evaluates OCR & Biomedical NER extraction against independently verified ground_truth.json across 30 reports.
"""

import os
import sys
import json
from typing import Dict, Any, List, Set

# Add project root to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.ai.ocr_engine import ocr_engine
from backend.ai.clinical_bert import clinical_bert_extractor

DATASET_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(DATASET_DIR, "reports")
GROUND_TRUTH_FILE = os.path.join(DATASET_DIR, "ground_truth.json")
RESULTS_FILE = os.path.join(DATASET_DIR, "evaluation_results.json")


def fuzzy_match(candidate: str, target: str) -> bool:
    """Case-insensitive fuzzy token overlap check."""
    c_tokens = set(re.findall(r"\w+", candidate.lower()))
    t_tokens = set(re.findall(r"\w+", target.lower()))
    if not c_tokens or not t_tokens:
        return False
    overlap = c_tokens.intersection(t_tokens)
    return len(overlap) / max(len(t_tokens), 1) >= 0.5 or target.lower() in candidate.lower() or candidate.lower() in target.lower()


import re

def compute_prf1(extracted_list: List[str], truth_list: List[str]):
    """Calculates Precision, Recall, and F1 for a list of string entities."""
    if not truth_list and not extracted_list:
        return 1.0, 1.0, 1.0
    if not truth_list:
        return 0.0, 1.0, 0.0
    if not extracted_list:
        return 1.0, 0.0, 0.0

    tp = 0
    matched_gt = set()
    for ext in extracted_list:
        matched = False
        for i, truth in enumerate(truth_list):
            if i not in matched_gt and fuzzy_match(ext, truth):
                matched = True
                matched_gt.add(i)
                break
        if matched:
            tp += 1

    precision = tp / max(len(extracted_list), 1)
    recall = tp / max(len(truth_list), 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-9)
    return precision, recall, f1


def run_evaluation():
    if not os.path.exists(GROUND_TRUTH_FILE):
        print(f"Error: Ground truth file not found at {GROUND_TRUTH_FILE}")
        return

    with open(GROUND_TRUTH_FILE, "r") as f:
        ground_truth: List[Dict[str, Any]] = json.load(f)

    print("=" * 80)
    print("PHASE 2 MEDICAL REPORT INTELLIGENCE — DATASET BENCHMARK EVALUATION")
    print(f"Total Synthetic Benchmark Reports: {len(ground_truth)}")
    print("=" * 80)

    report_metrics = []

    total_meta_name_correct = 0
    total_meta_id_correct = 0
    total_meta_date_correct = 0
    total_demo_age_correct = 0
    total_demo_gender_correct = 0

    condition_f1s = []
    symptom_f1s = []
    test_f1s = []
    med_f1s = []
    proc_f1s = []

    for idx, gt in enumerate(ground_truth):
        filename = gt["filename"]
        file_path = os.path.join(REPORTS_DIR, filename)
        fmt = gt["format"]
        spec_domain = gt["specialty_domain"]

        if not os.path.exists(file_path):
            print(f"[{idx+1:02d}/30] Missing file: {filename}")
            continue

        # Pipeline Step 1: Preprocessing & OCR / Text Extraction
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        ocr_text = ocr_engine.extract_text(file_bytes, filename)
        ocr_method = "PDF Text Extraction" if fmt == "digital_pdf" else "Multi-Pass OCR Engine"

        # Pipeline Step 2: Clinical NER & Structured Clinical Extraction
        structured = clinical_bert_extractor.extract_structured_clinical_info(ocr_text)

        # Metadata Validation
        pred_meta = structured.get("metadata", {})
        gt_meta = gt.get("metadata", {})

        name_ok = fuzzy_match(pred_meta.get("patient_name") or "", gt_meta.get("patient_name") or "")
        id_ok = fuzzy_match(pred_meta.get("patient_id") or "", gt_meta.get("patient_id") or "")
        date_ok = fuzzy_match(pred_meta.get("report_date") or "", gt_meta.get("report_date") or "")

        if name_ok: total_meta_name_correct += 1
        if id_ok: total_meta_id_correct += 1
        if date_ok: total_meta_date_correct += 1

        # Demographics Validation
        pred_demo = structured.get("demographics", {})
        gt_demo = gt.get("demographics", {})
        age_ok = pred_demo.get("age") == gt_demo.get("age")
        gender_ok = (pred_demo.get("gender") or "").lower() == (gt_demo.get("gender") or "").lower()

        if age_ok: total_demo_age_correct += 1
        if gender_ok: total_demo_gender_correct += 1

        # Clinical Entities PRF1
        c_p, c_r, c_f1 = compute_prf1(structured.get("conditions", []), gt.get("conditions", []))
        s_p, s_r, s_f1 = compute_prf1(structured.get("symptoms", []), gt.get("symptoms", []))
        t_p, t_r, t_f1 = compute_prf1(structured.get("tests", []), gt.get("tests", []))
        m_p, m_r, m_f1 = compute_prf1(structured.get("medications", []), gt.get("medications", []))
        p_p, p_r, p_f1 = compute_prf1(structured.get("procedures", []), gt.get("procedures", []))

        condition_f1s.append(c_f1)
        symptom_f1s.append(s_f1)
        test_f1s.append(t_f1)
        med_f1s.append(m_f1)
        proc_f1s.append(p_f1)

        rep_res = {
            "id": gt["id"],
            "filename": filename,
            "format": fmt,
            "specialty": spec_domain,
            "ocr_method": ocr_method,
            "ocr_length": len(ocr_text),
            "metadata_accuracy": {
                "name": name_ok,
                "id": id_ok,
                "date": date_ok
            },
            "demographics_accuracy": {
                "age": age_ok,
                "gender": gender_ok
            },
            "condition_f1": round(c_f1, 3),
            "symptom_f1": round(s_f1, 3),
            "test_f1": round(t_f1, 3),
            "medication_f1": round(m_f1, 3),
            "procedure_f1": round(p_f1, 3)
        }
        report_metrics.append(rep_res)
        print(f"[{idx+1:02d}/30] {filename:<38} | {fmt:<11} | Cond F1: {c_f1:.2f} | Sym F1: {s_f1:.2f} | Med F1: {m_f1:.2f}")

    n = len(ground_truth)
    summary = {
        "total_reports": n,
        "metadata_accuracy": {
            "patient_name_acc": round(total_meta_name_correct / n, 3),
            "patient_id_acc": round(total_meta_id_correct / n, 3),
            "report_date_acc": round(total_meta_date_correct / n, 3),
            "mean_metadata_acc": round((total_meta_name_correct + total_meta_id_correct + total_meta_date_correct) / (3 * n), 3)
        },
        "demographics_accuracy": {
            "age_acc": round(total_demo_age_correct / n, 3),
            "gender_acc": round(total_demo_gender_correct / n, 3),
            "mean_demographics_acc": round((total_demo_age_correct + total_demo_gender_correct) / (2 * n), 3)
        },
        "mean_clinical_entity_f1": {
            "conditions_f1": round(sum(condition_f1s) / max(len(condition_f1s), 1), 3),
            "symptoms_f1": round(sum(symptom_f1s) / max(len(symptom_f1s), 1), 3),
            "tests_f1": round(sum(test_f1s) / max(len(test_f1s), 1), 3),
            "medications_f1": round(sum(med_f1s) / max(len(med_f1s), 1), 3),
            "procedures_f1": round(sum(proc_f1s) / max(len(proc_f1s), 1), 3),
        }
    }

    full_evaluation = {
        "summary": summary,
        "reports": report_metrics
    }

    with open(RESULTS_FILE, "w") as f:
        json.dump(full_evaluation, f, indent=2)

    print("\n" + "=" * 80)
    print("EVALUATION BENCHMARK SUMMARY")
    print("=" * 80)
    print(f"Patient Name Accuracy : {summary['metadata_accuracy']['patient_name_acc'] * 100:.1f}%")
    print(f"Patient ID Accuracy   : {summary['metadata_accuracy']['patient_id_acc'] * 100:.1f}%")
    print(f"Report Date Accuracy  : {summary['metadata_accuracy']['report_date_acc'] * 100:.1f}%")
    print(f"Age Accuracy          : {summary['demographics_accuracy']['age_acc'] * 100:.1f}%")
    print(f"Gender Accuracy       : {summary['demographics_accuracy']['gender_acc'] * 100:.1f}%")
    print("-" * 80)
    print(f"Conditions F1 Score   : {summary['mean_clinical_entity_f1']['conditions_f1']:.3f}")
    print(f"Symptoms F1 Score     : {summary['mean_clinical_entity_f1']['symptoms_f1']:.3f}")
    print(f"Tests F1 Score        : {summary['mean_clinical_entity_f1']['tests_f1']:.3f}")
    print(f"Medications F1 Score  : {summary['mean_clinical_entity_f1']['medications_f1']:.3f}")
    print(f"Procedures F1 Score   : {summary['mean_clinical_entity_f1']['procedures_f1']:.3f}")
    print("=" * 80)
    print(f"Results saved to: {RESULTS_FILE}")


if __name__ == "__main__":
    run_evaluation()
