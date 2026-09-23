"""
Phase 4 — RAG Evaluation Benchmark.
Evaluates retrieval relevance, MRR, hit rates, citation preservation,
and out-of-domain rejection across Phase 2 clinical specialties.
"""

import os
import sys
import json
from typing import List, Dict, Any

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(CURRENT_DIR)
BASE_DIR = os.path.dirname(BACKEND_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from ai.rag_engine import rag_engine

BENCHMARK_QUERIES = [
    # 1. Cardiology: CAD / Stents / PCI
    {
        "id": "Q1_CARDIO_PCI",
        "query": "Can a patient fly after receiving a drug eluting stent for coronary artery disease?",
        "expected_specialty": "Cardiology",
        "expected_org": "ESC",
        "expected_keywords": ["stent", "angioplasty", "pci", "coronary"],
        "is_medical": True
    },
    # 2. Cardiology: DAPT
    {
        "id": "Q2_CARDIO_DAPT",
        "query": "What is the recommended duration of dual antiplatelet therapy after PCI when traveling?",
        "expected_specialty": "Cardiology",
        "expected_org": "ACC",
        "expected_keywords": ["dapt", "antiplatelet", "aspirin", "clopidogrel"],
        "is_medical": True
    },
    # 3. Oncology: Neutropenia
    {
        "id": "Q3_ONCO_NEUTROPENIA",
        "query": "Is it safe to travel during the chemotherapy neutropenic nadir?",
        "expected_specialty": "Oncology",
        "expected_org": "ASCO",
        "expected_keywords": ["neutropenia", "nadir", "anc", "infection"],
        "is_medical": True
    },
    # 4. Oncology: VTE Prophylaxis
    {
        "id": "Q4_ONCO_VTE",
        "query": "What are the thromboprophylaxis recommendations for cancer patients taking long flights?",
        "expected_specialty": "Oncology",
        "expected_org": "NCCN",
        "expected_keywords": ["thromboprophylaxis", "vte", "dvt", "lmwh"],
        "is_medical": True
    },
    # 5. Orthopedics: Knee Arthroplasty
    {
        "id": "Q5_ORTHO_TKA",
        "query": "When can a patient mobilize and travel after total knee replacement surgery?",
        "expected_specialty": "Orthopedics",
        "expected_org": "AAOS",
        "expected_keywords": ["knee", "arthroplasty", "tka", "mobilization"],
        "is_medical": True
    },
    # 6. Orthopedics: Plaster Casts
    {
        "id": "Q6_ORTHO_CAST",
        "query": "Why do airlines require plaster casts to be bivalved before commercial flights?",
        "expected_specialty": "Orthopedics",
        "expected_org": "BOA",
        "expected_keywords": ["cast", "bivalved", "compartment", "swelling"],
        "is_medical": True
    },
    # 7. Neurology: Craniotomy
    {
        "id": "Q7_NEURO_CRANIOTOMY",
        "query": "How long must a patient wait before flying after craniotomy for brain tumor removal?",
        "expected_specialty": "Neurology",
        "expected_org": "CNS",
        "expected_keywords": ["craniotomy", "pneumocephalus", "air", "intracranial"],
        "is_medical": True
    },
    # 8. Neurology: Epilepsy
    {
        "id": "Q8_NEURO_EPILEPSY",
        "query": "How should anti-seizure medication doses be adjusted when crossing multiple time zones?",
        "expected_specialty": "Neurology",
        "expected_org": "AAN",
        "expected_keywords": ["seizure", "time zone", "epilepsy", "medication"],
        "is_medical": True
    },
    # 9. Gastroenterology: Endoscopy
    {
        "id": "Q9_GI_BLEED",
        "query": "What precautions are required after endoscopic hemoclip placement for peptic ulcer bleeding?",
        "expected_specialty": "Gastroenterology",
        "expected_org": "ACG",
        "expected_keywords": ["peptic", "ulcer", "bleeding", "hemoclip", "endoscopy"],
        "is_medical": True
    },
    # 10. Nephrology: CKD
    {
        "id": "Q10_NEPHRO_CKD",
        "query": "What dietary and medication precautions should stage 4 CKD patients take during travel?",
        "expected_specialty": "Nephrology",
        "expected_org": "KDIGO",
        "expected_keywords": ["ckd", "kidney", "creatinine", "nsaid", "egfr"],
        "is_medical": True
    },
    # 11. Pulmonology: COPD Hypoxemia
    {
        "id": "Q11_PULMO_COPD",
        "query": "What in-flight oxygen considerations apply to severe COPD patients flying at cabin altitudes?",
        "expected_specialty": "Pulmonology",
        "expected_org": "BTS",
        "expected_keywords": ["oxygen", "copd", "hypoxemia", "altitude", "poc"],
        "is_medical": True
    },
    # 12. General Medicine: Diabetes & Insulin
    {
        "id": "Q12_GEN_DIABETES",
        "query": "Can insulin pens be placed in checked airline baggage when crossing time zones?",
        "expected_specialty": "General Medicine",
        "expected_org": "ADA",
        "expected_keywords": ["insulin", "diabetes", "carry-on", "baggage", "freezing"],
        "is_medical": True
    },
    # 13. Out-of-domain 1
    {
        "id": "Q13_OOD_AUTOMOTIVE",
        "query": "How do I replace the alternator and alternator belt on a Ford diesel truck?",
        "expected_specialty": None,
        "expected_org": None,
        "expected_keywords": [],
        "is_medical": False
    },
    # 14. Out-of-domain 2
    {
        "id": "Q14_OOD_RECIPE",
        "query": "What is the traditional Italian recipe for tiramisu and mascarpone cream?",
        "expected_specialty": None,
        "expected_org": None,
        "expected_keywords": [],
        "is_medical": False
    },
    # 15. Out-of-domain 3
    {
        "id": "Q15_OOD_SPORTS",
        "query": "Which cricket team won the World Cup final match in Melbourne?",
        "expected_specialty": None,
        "expected_org": None,
        "expected_keywords": [],
        "is_medical": False
    }
]


def run_benchmark():
    medical_queries = [q for q in BENCHMARK_QUERIES if q["is_medical"]]
    ood_queries = [q for q in BENCHMARK_QUERIES if not q["is_medical"]]

    hit_top1_count = 0
    hit_top3_count = 0
    reciprocal_ranks = []
    citation_preserved_count = 0
    detailed_results = []

    print(f"\n========================================================")
    print(f"   PHASE 4 RAG RETRIEVAL & GROUNDING EVALUATION BENCHMARK")
    print(f"========================================================\n")

    for item in medical_queries:
        docs = rag_engine.retrieve_documents(item["query"], top_k=3)
        gen = rag_engine.generate_response(item["query"], docs)

        ranks = []
        is_hit_top1 = False
        is_hit_top3 = False

        for rank, d in enumerate(docs, 1):
            specialty_match = item["expected_specialty"].lower() in d.get("category", "").lower() or item["expected_specialty"].lower() in d.get("specialty", "").lower()
            org_match = item["expected_org"].lower() in d.get("organization", "").lower()
            keyword_match = any(k in d["content"].lower() or k in d["title"].lower() for k in item["expected_keywords"])

            if specialty_match or org_match or keyword_match:
                ranks.append(rank)

        rr = 1.0 / ranks[0] if ranks else 0.0
        reciprocal_ranks.append(rr)

        if 1 in ranks:
            is_hit_top1 = True
            hit_top1_count += 1
        if any(r in [1, 2, 3] for r in ranks):
            is_hit_top3 = True
            hit_top3_count += 1

        has_citations = len(gen.get("citations", [])) > 0
        if has_citations:
            citation_preserved_count += 1

        top_score = docs[0]["score"] if docs else 0.0
        top_title = docs[0]["title"] if docs else "None"
        top_org = docs[0]["organization"] if docs else "None"

        detailed_results.append({
            "id": item["id"],
            "query": item["query"],
            "is_medical": True,
            "expected_specialty": item["expected_specialty"],
            "retrieved_count": len(docs),
            "top_score": top_score,
            "top_title": top_title,
            "top_org": top_org,
            "hit_top1": is_hit_top1,
            "hit_top3": is_hit_top3,
            "reciprocal_rank": rr,
            "grounding_status": gen.get("grounding_status"),
            "llm_provider": gen.get("llm_provider"),
            "citations_count": len(gen.get("citations", []))
        })

        print(f"[{item['id']}] Top Score: {top_score:.4f} | RR: {rr:.2f} | Org: {top_org[:25]} | Hit@1: {is_hit_top1}")

    # Evaluate Out-of-Domain queries (Negative Test)
    print("\nEvaluating Out-of-Domain Negative Queries (Anti-Fabrication Guardrail):")
    ood_rejected_count = 0
    for item in ood_queries:
        docs = rag_engine.retrieve_documents(item["query"], top_k=3)
        gen = rag_engine.generate_response(item["query"], docs)

        is_rejected = len(docs) == 0 and gen.get("grounding_status") == "INSUFFICIENT_EVIDENCE"
        if is_rejected:
            ood_rejected_count += 1

        detailed_results.append({
            "id": item["id"],
            "query": item["query"],
            "is_medical": False,
            "retrieved_count": len(docs),
            "top_score": docs[0]["score"] if docs else 0.0,
            "is_rejected": is_rejected,
            "grounding_status": gen.get("grounding_status"),
            "citations_count": len(gen.get("citations", []))
        })
        print(f"[{item['id']}] Retrieved: {len(docs)} | Status: {gen.get('grounding_status')} | Rejected: {is_rejected}")

    # Aggregates
    total_med = len(medical_queries)
    total_ood = len(ood_queries)
    hit_rate_at_1 = hit_top1_count / total_med if total_med else 0.0
    hit_rate_at_3 = hit_top3_count / total_med if total_med else 0.0
    mean_reciprocal_rank = sum(reciprocal_ranks) / total_med if total_med else 0.0
    citation_preservation_rate = citation_preserved_count / total_med if total_med else 0.0
    ood_rejection_rate = ood_rejected_count / total_ood if total_ood else 0.0

    summary_metrics = {
        "total_queries_evaluated": len(BENCHMARK_QUERIES),
        "medical_queries_count": total_med,
        "out_of_domain_queries_count": total_ood,
        "hit_rate_at_1": round(hit_rate_at_1, 4),
        "hit_rate_at_3": round(hit_rate_at_3, 4),
        "mean_reciprocal_rank_mrr": round(mean_reciprocal_rank, 4),
        "citation_preservation_rate": round(citation_preservation_rate, 4),
        "out_of_domain_rejection_rate": round(ood_rejection_rate, 4),
        "embedding_model": "all-MiniLM-L6-v2 (384-dim normalized)",
        "vector_store": "FAISS IndexFlatIP",
        "similarity_threshold": rag_engine.similarity_threshold,
        "llm_runtime": "Ollama local LLM (llama3.2:1b)"
    }

    output_dir = os.path.join(BACKEND_DIR, "datasets", "medical_knowledge")
    os.makedirs(output_dir, exist_ok=True)
    report_file = os.path.join(output_dir, "rag_evaluation_results.json")

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump({
            "metrics": summary_metrics,
            "detailed_results": detailed_results
        }, f, indent=2, ensure_ascii=False)

    print("\n--------------------------------------------------------")
    print(f"Hit Rate @ 1:                  {hit_rate_at_1 * 100:.1f}%")
    print(f"Hit Rate @ 3:                  {hit_rate_at_3 * 100:.1f}%")
    print(f"Mean Reciprocal Rank (MRR):    {mean_reciprocal_rank:.4f}")
    print(f"Citation Preservation Rate:    {citation_preservation_rate * 100:.1f}%")
    print(f"OOD Rejection Rate (No-Fab):   {ood_rejection_rate * 100:.1f}%")
    print(f"Benchmark results saved to:    {report_file}")
    print("--------------------------------------------------------\n")

    return summary_metrics


if __name__ == "__main__":
    run_benchmark()
